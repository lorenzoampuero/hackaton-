"""Votación vecinal: épocas (períodos) de votación, votos anónimos y resultados.

Reglas de diseño:
- Cada persona (dispositivo) vota una vez por sitio y por época; se guarda solo un hash del dispositivo.
- Mientras la época está abierta no se publican porcentajes (solo cuántos votos hay): así nadie vota
  siguiendo a la mayoría. Al cerrar, se publican los porcentajes por sitio.
- Un sitio con menos de MIN_VOTOS_PUBLICAR votos no muestra porcentajes (evita decisiones con 2 votos).
- Los votos se guardan en Supabase si están las tablas (ver supabase/migrations) y, si no, en SQLite local.
  En Vercel el disco no persiste: allí hacen falta las tablas de Supabase.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import random
import re
import sqlite3
import threading
import time
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from pipeline.comun import RAIZ, WEB_DATA, cargar_env, leer_json

router = APIRouter(prefix="/api/votacion", tags=["votacion"])

DIAS_EPOCA_POR_DEFECTO = 14
RANGOS_EDAD = {"menos_18", "18_29", "30_44", "45_59", "60_mas"}
LARGO_OTRO = 280
_lock = threading.Lock()


# --------------------------------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------------------------------
def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def _parse(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _verdadero(nombre: str) -> bool:
    cargar_env()
    return os.environ.get(nombre, "").strip().lower() in ("1", "true", "si", "sí", "yes")


def epocas_automaticas() -> bool:
    """En Vercel (o con PULMON_EPOCAS_AUTO=1) las épocas son ventanas fijas de 14 días con id determinístico.

    Así todas las instancias del servidor (que no comparten memoria) hablan de la misma votación.
    """
    return _verdadero("PULMON_EPOCAS_AUTO") or _verdadero("PULMON_DEMO_AUTO") or bool(os.environ.get("VERCEL"))


def demo_automatica() -> bool:
    """Con PULMON_DEMO_AUTO=1 y almacén local, se crea sola la votación cerrada con votos SIMULADOS."""
    return _verdadero("PULMON_DEMO_AUTO")


def ventana_auto(comuna_slug: str, ahora: datetime | None = None) -> dict[str, Any]:
    ahora = ahora or _ahora()
    n = int(ahora.timestamp() // (DIAS_EPOCA_POR_DEFECTO * 86400))
    abre = datetime.fromtimestamp(n * DIAS_EPOCA_POR_DEFECTO * 86400, tz=timezone.utc)
    return {
        "id": f"auto-{comuna_slug}-{n}", "comuna_slug": comuna_slug, "nombre": f"Votación del {abre:%d-%m-%Y}",
        "abre_en": _iso(abre), "cierra_en": _iso(abre + timedelta(days=DIAS_EPOCA_POR_DEFECTO)),
        "cerrado_manual": False, "demo": False, "creado_en": _iso(_ahora()),
    }


def min_votos_publicar() -> int:
    cargar_env()
    try:
        return max(1, int(os.environ.get("PULMON_MIN_VOTOS", "10")))
    except ValueError:
        return 10


def _sal() -> str:
    cargar_env()
    return os.environ.get("PULMON_VOTOS_SAL", "pulmon-urbano-sal-local")


def hash_dispositivo(dispositivo: str) -> str:
    return hashlib.sha256(f"{_sal()}:{dispositivo}".encode()).hexdigest()


def limpiar_texto(texto: str | None) -> str | None:
    if not texto:
        return None
    limpio = re.sub(r"\s+", " ", texto).strip()
    return limpio[:LARGO_OTRO] or None


def estado_epoca(p: dict[str, Any], ahora: datetime | None = None) -> str:
    ahora = ahora or _ahora()
    if p.get("cerrado_manual"):
        return "cerrado"
    if ahora < _parse(p["abre_en"]):
        return "proximo"
    if ahora >= _parse(p["cierra_en"]):
        return "cerrado"
    return "abierto"


def _catalogo() -> dict[str, dict[str, Any]]:
    datos = leer_json(RAIZ / "data" / "opciones_votacion.json")
    return {o["id"]: o for o in datos["opciones"]}


SINONIMOS = {
    "sombra_arboles": ["arboles", "sombra", "plantar", "verde", "bosque"],
    "bancas_bebedero": ["bancas", "bancos", "sentarse", "agua", "bebederos", "descansar"],
    "juegos_infantiles": ["juegos", "ninos", "columpios", "resbalin", "plaza de juegos", "infancia"],
    "jardin_infantil": ["guarderia", "sala cuna", "ninos", "jardin", "pre escolar", "educacion"],
    "maquinas_ejercicio": ["gimnasio", "ejercicio", "maquinas", "fitness", "entrenar", "plaza activa"],
    "cancha_comunitaria": ["futbol", "cancha", "pelota", "pasto sintetico", "futbolito"],
    "multicancha": ["basquetbol", "basket", "voleibol", "baby futbol", "deporte", "cancha"],
    "skatepark": ["skate", "patineta", "bmx", "patin", "rampa"],
    "plantas_nativas": ["nativas", "pasto", "sequia", "poco riego", "jardin", "plantas", "agua"],
    "riego_eficiente": ["riego", "agua", "goteo", "regar"],
    "refugio_climatico": ["refugio", "calor", "sombra", "agua", "ola de calor"],
    "jardin_lluvia": ["lluvia", "agua lluvia", "inundacion", "suelo", "cemento", "permeable"],
    "iluminacion_seguridad": ["luz", "luces", "seguridad", "iluminacion", "noche", "alumbrado"],
    "piscina": ["piscina", "nadar", "pileta", "natacion", "agua"],
}


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para que 'cámaras' encuentre 'camaras'."""
    sin_tildes = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sin_tildes.lower()).strip()


def _ideas_extra() -> dict[str, Any]:
    ruta = RAIZ / "data" / "ideas_busqueda.json"
    return leer_json(ruta) if ruta.exists() else {"populares": [], "ideas": []}


def _opciones_validas() -> set[str]:
    return set(_catalogo()) | {i["id"] for i in _ideas_extra()["ideas"]} | {"otro"}


def _indice_busqueda() -> list[dict[str, Any]]:
    """Todo lo que se puede buscar: las 14 opciones con costo y las ideas extra (sin costo verificado)."""
    entradas = []
    for o in _catalogo().values():
        entradas.append({**o, "palabras": SINONIMOS.get(o["id"], []), "extra": False})
    for i in _ideas_extra()["ideas"]:
        entradas.append({"id": i["id"], "nombre": i["nombre"], "descripcion": i["descripcion"], "palabras": i.get("palabras", []),
                         "costo_min_M": None, "costo_max_M": None, "costo_nota": "por cotizar con el municipio (no hay dato verificado)", "ejemplos": [], "extra": True})
    return entradas


def buscar_ideas(q: str, recomendadas: set[str] | None = None, limite: int = 8) -> dict[str, Any]:
    """Busca por nombre, descripción y palabras parecidas. Si hay pocas coincidencias, completa con ideas populares."""
    recomendadas = recomendadas or set()
    frase = normalizar(q)
    fichas = _indice_busqueda()
    por_id = {f["id"]: f for f in fichas}
    tokens = [x for x in frase.split(" ") if len(x) >= 2]
    puntuadas = []
    for f in fichas:
        nom, desc = normalizar(f["nombre"]), normalizar(f["descripcion"])
        palabras = [normalizar(p) for p in f.get("palabras", [])]
        pts = 0
        if frase and frase in nom:
            pts += 6
        for tk in tokens:
            if tk in nom:
                pts += 3
            if any(tk in p or p in tk for p in palabras if len(p) >= 3):
                pts += 2
            if tk in desc:
                pts += 1
        if pts and f["id"] in recomendadas:
            pts += 1
        if pts:
            puntuadas.append((pts, f))
    puntuadas.sort(key=lambda x: (-x[0], x[1]["nombre"]))
    resultados = [{**f, "popular": False, "recomendada": f["id"] in recomendadas} for _p, f in puntuadas][:limite]
    coincidencias = len(resultados)
    relleno = False
    if coincidencias < 6:
        relleno = True
        vistos = {r["id"] for r in resultados}
        for pid in _ideas_extra()["populares"]:
            if pid in por_id and pid not in vistos and len(resultados) < max(6, min(limite, 8)):
                resultados.append({**por_id[pid], "popular": True, "recomendada": pid in recomendadas})
                vistos.add(pid)
    return {"q": q, "coincidencias": coincidencias, "relleno": relleno, "resultados": resultados[:limite]}


def calcular_participacion(votos: list[dict[str, Any]]) -> dict[str, Any]:
    """Cuántos votaron, quiénes (edad) y cuándo: nada que revele lo que votó cada persona."""
    edades = {k: 0 for k in sorted(RANGOS_EDAD)}
    edades["sin_dato"] = 0
    por_dia: dict[str, int] = {}
    qr = 0
    for v in votos:
        edades[v["edad_rango"] if v.get("edad_rango") in RANGOS_EDAD else "sin_dato"] += 1
        qr += int(bool(v.get("via_qr")))
        if v.get("creado_en"):
            d = str(v["creado_en"])[:10]
            por_dia[d] = por_dia.get(d, 0) + 1
    return {"total": len(votos), "via_qr": qr, "edades": edades, "por_dia": [{"fecha": d, "votos": n} for d, n in sorted(por_dia.items())]}


def calcular_confianza(votos: list[dict[str, Any]], minimo: int) -> dict[str, Any]:
    """Qué tanto confiar en un resultado: cantidad de votos, QR, edad declarada y ráfagas. No revela qué votó nadie.

    El QR todavía se declara en el enlace (no está firmado): por eso pesa solo 30 de 100 puntos.
    """
    n = len(votos)
    if n == 0:
        return {"n": 0, "puntos": 0, "nivel": "baja", "qr_pct": 0.0, "edad_pct": 0.0, "rafaga_pct": 0.0, "razones": ["Sin votos"]}
    qr = sum(1 for v in votos if v.get("via_qr")) / n
    con_edad = sum(1 for v in votos if v.get("edad_rango") in RANGOS_EDAD) / n
    fechas = sorted(_parse(str(v["creado_en"])) for v in votos if v.get("creado_en"))
    rafaga, j = 0.0, 0
    if len(fechas) >= 5:
        mejor = 0
        for i in range(len(fechas)):
            while fechas[i] - fechas[j] > timedelta(minutes=60):
                j += 1
            mejor = max(mejor, i - j + 1)
        rafaga = mejor / len(fechas)
    rafaga_ok = 1.0 if (n < 10 or rafaga <= 0.5) else max(0.0, 1.0 - (rafaga - 0.5) / 0.5)
    puntos = round(40 * min(1.0, n / 50) + 30 * qr + 15 * con_edad + 15 * rafaga_ok)
    nivel = "alta" if puntos >= 70 else "media" if puntos >= 45 else "baja"
    razones = []
    if n < minimo:
        razones.append(f"Pocos votos ({n}): faltan {minimo - n} para publicar porcentajes")
    elif n < 30:
        razones.append(f"Solo {n} votos: el resultado puede cambiar con unos pocos más")
    if qr < 0.3:
        razones.append(f"Solo {round(qr * 100)} % dijo entrar por el QR del parque (se declara en el enlace; aún sin firma)")
    if con_edad < 0.5:
        razones.append("Menos de la mitad indicó su edad: cuesta saber si representa al barrio")
    if n >= 10 and rafaga > 0.5:
        razones.append(f"{round(rafaga * 100)} % de los votos llegó en una sola hora: puede ser una convocatoria o un intento de manipular")
    if not razones:
        razones.append("Muchos votos, repartidos en el tiempo y con edad declarada")
    return {"n": n, "puntos": puntos, "nivel": nivel, "qr_pct": round(qr * 100, 1), "edad_pct": round(con_edad * 100, 1), "rafaga_pct": round(rafaga * 100, 1), "razones": razones}


def confianza_por_sitio(votos: list[dict[str, Any]], minimo: int) -> dict[str, Any]:
    por_sitio: dict[str, list[dict[str, Any]]] = {}
    for v in votos:
        por_sitio.setdefault(v["site_id"], []).append(v)
    return {sid: calcular_confianza(lista, minimo) for sid, lista in por_sitio.items()}


def _sitios_de(comuna_slug: str) -> dict[str, dict[str, Any]]:
    ruta = WEB_DATA / "vecino" / f"{comuna_slug}.json"
    if not ruta.exists():
        return {}
    return {s["id"]: s for s in leer_json(ruta)["sitios"]}


def _zonas() -> list[dict[str, Any]]:
    ruta = WEB_DATA / "vecino" / "zonas.json"
    return leer_json(ruta)["zonas"] if ruta.exists() else []


# --------------------------------------------------------------------------------------------------
# Almacenes
# --------------------------------------------------------------------------------------------------
DDL_SQLITE = """
create table if not exists votacion_periodos (
  id text primary key, comuna_slug text not null, nombre text not null,
  abre_en text not null, cierra_en text not null, cerrado_manual integer not null default 0,
  demo integer not null default 0, creado_en text not null
);
create table if not exists votacion_votos (
  id text primary key, periodo_id text not null, comuna_slug text not null, site_id text not null,
  opcion_id text not null, otro_texto text, edad_rango text, dispositivo_hash text not null,
  via_qr integer not null default 0, demo integer not null default 0, creado_en text not null,
  unique (periodo_id, site_id, dispositivo_hash)
);
create index if not exists votacion_votos_periodo on votacion_votos (periodo_id, site_id);
"""


class AlmacenLocal:
    nombre = "local"

    def __init__(self, ruta: Path) -> None:
        self.ruta = ruta
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with self._con() as con:
            con.executescript(DDL_SQLITE)

    def _con(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.ruta, timeout=10)
        con.row_factory = sqlite3.Row
        return con

    def periodos(self, comuna_slug: str | None = None) -> list[dict[str, Any]]:
        sql, args = "select * from votacion_periodos", ()
        if comuna_slug:
            sql, args = sql + " where comuna_slug = ?", (comuna_slug,)
        with _lock, self._con() as con:
            filas = [dict(r) for r in con.execute(sql + " order by abre_en desc", args)]
        for f in filas:
            f["cerrado_manual"], f["demo"] = bool(f["cerrado_manual"]), bool(f["demo"])
        return filas

    def obtener_periodo(self, periodo_id: str) -> dict[str, Any] | None:
        with _lock, self._con() as con:
            r = con.execute("select * from votacion_periodos where id = ?", (periodo_id,)).fetchone()
        if not r:
            return None
        d = dict(r)
        d["cerrado_manual"], d["demo"] = bool(d["cerrado_manual"]), bool(d["demo"])
        return d

    def crear_periodo(self, p: dict[str, Any]) -> None:
        with _lock, self._con() as con:
            con.execute(
                "insert into votacion_periodos (id, comuna_slug, nombre, abre_en, cierra_en, cerrado_manual, demo, creado_en)"
                " values (?,?,?,?,?,?,?,?)",
                (p["id"], p["comuna_slug"], p["nombre"], p["abre_en"], p["cierra_en"], int(p.get("cerrado_manual", False)), int(p.get("demo", False)), p["creado_en"]),
            )

    def cerrar_periodo(self, periodo_id: str) -> None:
        with _lock, self._con() as con:
            con.execute("update votacion_periodos set cerrado_manual = 1 where id = ?", (periodo_id,))

    def insertar_voto(self, v: dict[str, Any]) -> bool:
        try:
            with _lock, self._con() as con:
                con.execute(
                    "insert into votacion_votos (id, periodo_id, comuna_slug, site_id, opcion_id, otro_texto, edad_rango, dispositivo_hash, via_qr, demo, creado_en)"
                    " values (?,?,?,?,?,?,?,?,?,?,?)",
                    (v["id"], v["periodo_id"], v["comuna_slug"], v["site_id"], v["opcion_id"], v.get("otro_texto"), v.get("edad_rango"), v["dispositivo_hash"], int(v.get("via_qr", False)), int(v.get("demo", False)), v["creado_en"]),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def insertar_votos(self, filas: list[dict[str, Any]]) -> int:
        """Inserta muchos votos de una vez (ignora los repetidos). Devuelve cuántos entraron."""
        datos = [(v["id"], v["periodo_id"], v["comuna_slug"], v["site_id"], v["opcion_id"], v.get("otro_texto"), v.get("edad_rango"), v["dispositivo_hash"], int(v.get("via_qr", False)), int(v.get("demo", False)), v["creado_en"]) for v in filas]
        with _lock, self._con() as con:
            antes = con.execute("select count(*) from votacion_votos").fetchone()[0]
            con.executemany("insert or ignore into votacion_votos (id, periodo_id, comuna_slug, site_id, opcion_id, otro_texto, edad_rango, dispositivo_hash, via_qr, demo, creado_en) values (?,?,?,?,?,?,?,?,?,?,?)", datos)
            return con.execute("select count(*) from votacion_votos").fetchone()[0] - antes

    def votos_de_periodo(self, periodo_id: str) -> list[dict[str, Any]]:
        with _lock, self._con() as con:
            return [dict(r) for r in con.execute("select site_id, opcion_id, otro_texto, edad_rango, via_qr, creado_en from votacion_votos where periodo_id = ?", (periodo_id,))]

    def sitios_votados(self, periodo_id: str, hash_disp: str) -> list[str]:
        with _lock, self._con() as con:
            return [r["site_id"] for r in con.execute("select site_id from votacion_votos where periodo_id = ? and dispositivo_hash = ?", (periodo_id, hash_disp))]


class AlmacenSupabase:
    nombre = "supabase"

    def __init__(self, url: str, key: str) -> None:
        self.url, self.key = url, key

    def _h(self, prefer: str | None = None) -> dict[str, str]:
        h = {"apikey": self.key, "Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        if prefer:
            h["Prefer"] = prefer
        return h

    def _get(self, ruta: str) -> list[dict[str, Any]]:
        r = httpx.get(f"{self.url}/rest/v1/{ruta}", headers=self._h(), timeout=8.0)
        r.raise_for_status()
        return r.json()

    def periodos(self, comuna_slug: str | None = None) -> list[dict[str, Any]]:
        filtro = f"&comuna_slug=eq.{comuna_slug}" if comuna_slug else ""
        return self._get(f"votacion_periodos?select=*&order=abre_en.desc{filtro}")

    def obtener_periodo(self, periodo_id: str) -> dict[str, Any] | None:
        filas = self._get(f"votacion_periodos?select=*&id=eq.{periodo_id}&limit=1")
        return filas[0] if filas else None

    def crear_periodo(self, p: dict[str, Any]) -> None:
        r = httpx.post(f"{self.url}/rest/v1/votacion_periodos", headers=self._h("return=minimal"), json=p, timeout=8.0)
        r.raise_for_status()

    def cerrar_periodo(self, periodo_id: str) -> None:
        r = httpx.patch(f"{self.url}/rest/v1/votacion_periodos?id=eq.{periodo_id}", headers=self._h("return=minimal"), json={"cerrado_manual": True}, timeout=8.0)
        r.raise_for_status()

    def insertar_voto(self, v: dict[str, Any]) -> bool:
        r = httpx.post(f"{self.url}/rest/v1/votacion_votos", headers=self._h("return=minimal"), json=v, timeout=8.0)
        if r.status_code == 409:
            return False
        r.raise_for_status()
        return True

    def insertar_votos(self, filas: list[dict[str, Any]]) -> int:
        for i in range(0, len(filas), 500):
            r = httpx.post(f"{self.url}/rest/v1/votacion_votos?on_conflict=periodo_id,site_id,dispositivo_hash", headers=self._h("return=minimal,resolution=ignore-duplicates"), json=filas[i:i + 500], timeout=30.0)
            r.raise_for_status()
        return len(filas)

    def votos_de_periodo(self, periodo_id: str) -> list[dict[str, Any]]:
        salida, desde = [], 0
        while True:
            lote = self._get(f"votacion_votos?select=site_id,opcion_id,otro_texto,edad_rango,via_qr,creado_en&periodo_id=eq.{periodo_id}&order=creado_en.asc&limit=1000&offset={desde}")
            salida.extend(lote)
            if len(lote) < 1000:
                return salida
            desde += 1000

    def sitios_votados(self, periodo_id: str, hash_disp: str) -> list[str]:
        return [f["site_id"] for f in self._get(f"votacion_votos?select=site_id&periodo_id=eq.{periodo_id}&dispositivo_hash=eq.{hash_disp}")]


_cache_almacen: dict[str, Any] = {"t": 0.0, "obj": None, "clave": None}


def _ruta_local() -> Path:
    cargar_env()
    ruta = os.environ.get("PULMON_VOTOS_DB")
    if ruta:
        return Path(ruta)
    primario = RAIZ / "data" / "votos_local.db"
    if os.access(primario.parent, os.W_OK):
        return primario
    return Path("/tmp/pulmon_votos_local.db")


def obtener_almacen() -> AlmacenLocal | AlmacenSupabase:
    """Supabase si sus tablas existen; si no, SQLite local. Se revisa cada 60 s."""
    cargar_env()
    modo = os.environ.get("PULMON_VOTOS_BACKEND", "auto")
    url = (os.environ.get("SUPABASE_URL") or "").strip().rstrip("/")
    key = (os.environ.get("SUPABASE_SECRET_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    clave = (modo, url, str(_ruta_local()))
    if _cache_almacen["obj"] is not None and _cache_almacen["clave"] == clave and time.time() - _cache_almacen["t"] < 60:
        return _cache_almacen["obj"]
    almacen: AlmacenLocal | AlmacenSupabase | None = None
    if modo != "local" and url and key:
        try:
            r = httpx.get(f"{url}/rest/v1/votacion_periodos?select=id&limit=1", headers={"apikey": key, "Authorization": f"Bearer {key}"}, timeout=4.0)
            if r.status_code == 200:
                almacen = AlmacenSupabase(url, key)
        except Exception:
            almacen = None
    if almacen is None:
        almacen = AlmacenLocal(_ruta_local())
    _cache_almacen.update({"t": time.time(), "obj": almacen, "clave": clave})
    return almacen


# --------------------------------------------------------------------------------------------------
# Épocas
# --------------------------------------------------------------------------------------------------
def nueva_epoca(comuna_slug: str, nombre: str, dias: int = DIAS_EPOCA_POR_DEFECTO, demo: bool = False, abre: datetime | None = None) -> dict[str, Any]:
    abre = abre or _ahora()
    return {
        "id": str(uuid.uuid4()), "comuna_slug": comuna_slug, "nombre": nombre,
        "abre_en": _iso(abre), "cierra_en": _iso(abre + timedelta(days=dias)),
        "cerrado_manual": False, "demo": demo, "creado_en": _iso(_ahora()),
    }


def epoca_actual(almacen: Any, comuna_slug: str) -> dict[str, Any]:
    """La época abierta de la comuna; si no hay ninguna, crea una nueva (14 días) para que la página funcione."""
    existentes = almacen.periodos(comuna_slug)
    reales = [p for p in existentes if not p.get("demo")]
    for p in reales:
        if estado_epoca(p) == "abierto":
            return p
    if epocas_automaticas():
        nueva = ventana_auto(comuna_slug)
        if not any(p["id"] == nueva["id"] for p in reales):
            try:
                almacen.crear_periodo(nueva)
            except Exception:  # otra instancia la creó al mismo tiempo
                pass
        return almacen.obtener_periodo(nueva["id"]) or nueva
    if not reales:
        nueva = nueva_epoca(comuna_slug, "Votación 1")
        almacen.crear_periodo(nueva)
        return nueva
    return reales[0]  # la más reciente (cerrada o próxima)


def describir_epoca(p: dict[str, Any]) -> dict[str, Any]:
    est = estado_epoca(p)
    segundos = (_parse(p["cierra_en"]) - _ahora()).total_seconds()
    return {
        "id": p["id"], "comuna": p["comuna_slug"], "nombre": p["nombre"], "estado": est,
        "abre_en": p["abre_en"], "cierra_en": p["cierra_en"], "demo": bool(p.get("demo")),
        "dias_restantes": max(0, int(-(-segundos // 86400))) if est == "abierto" else 0,
    }


# --------------------------------------------------------------------------------------------------
# Modelos
# --------------------------------------------------------------------------------------------------
class Voto(BaseModel):
    periodo_id: str
    site_id: str
    opcion_id: str
    otro_texto: str | None = Field(default=None, max_length=600)
    edad_rango: str | None = None
    dispositivo: str = Field(min_length=16, max_length=80)
    via_qr: bool = False


class PedidoEpoca(BaseModel):
    comuna_slug: str
    nombre: str = Field(min_length=3, max_length=80)
    dias: int = Field(default=DIAS_EPOCA_POR_DEFECTO, ge=1, le=90)


class PedidoCerrar(BaseModel):
    periodo_id: str


def _exigir_admin(token: str | None) -> None:
    cargar_env()
    esperado = os.environ.get("PULMON_ADMIN_TOKEN", "")
    if not esperado:
        raise HTTPException(status_code=403, detail="Las acciones de administración están desactivadas: define PULMON_ADMIN_TOKEN en .env.")
    if not token or not hmac.compare_digest(token, esperado):
        raise HTTPException(status_code=401, detail="Token de administración inválido.")


# --------------------------------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------------------------------
@router.get("/estado")
def estado() -> dict[str, Any]:
    alm = obtener_almacen()
    return {"almacen": alm.nombre, "min_votos_publicar": min_votos_publicar(), "admin_activo": bool(os.environ.get("PULMON_ADMIN_TOKEN"))}


@router.get("/zonas")
def zonas() -> dict[str, Any]:
    alm = obtener_almacen()
    asegurar_demo(alm)
    salida = []
    for z in _zonas():
        p = epoca_actual(alm, z["slug"])
        salida.append({**z, "epoca": describir_epoca(p)})
    return {"zonas": salida}


@router.get("/periodos")
def periodos(comuna: str = Query(...)) -> dict[str, Any]:
    alm = obtener_almacen()
    asegurar_demo(alm)
    epoca_actual(alm, comuna)
    return {"periodos": [describir_epoca(p) for p in alm.periodos(comuna)]}


@router.get("/ideas")
def ideas(q: str = Query(default="", max_length=60), comuna: str | None = None, site_id: str | None = None, limite: int = Query(default=8, ge=1, le=20)) -> dict[str, Any]:
    """Buscador de ideas para votar. Por ahora lee archivos; después leerá una tabla de la base de datos."""
    recomendadas: set[str] = set()
    if comuna and site_id:
        sitio = _sitios_de(comuna).get(site_id)
        if sitio:
            recomendadas = {o["id"] for o in sitio["opciones"]}
    return buscar_ideas(q, recomendadas, limite)


@router.post("/votar")
def votar(v: Voto) -> dict[str, Any]:
    alm = obtener_almacen()
    p = alm.obtener_periodo(v.periodo_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Esa votación no existe.")
    if estado_epoca(p) != "abierto":
        raise HTTPException(status_code=409, detail="Esta votación no está abierta.")
    if v.site_id not in _sitios_de(p["comuna_slug"]):
        raise HTTPException(status_code=404, detail="Ese lugar no pertenece a la comuna de esta votación.")
    if v.opcion_id not in _opciones_validas():
        raise HTTPException(status_code=422, detail="Opción inválida.")
    if v.edad_rango is not None and v.edad_rango not in RANGOS_EDAD:
        raise HTTPException(status_code=422, detail="Rango de edad inválido.")
    otro = limpiar_texto(v.otro_texto)
    if v.opcion_id == "otro" and (not otro or len(otro) < 3):
        raise HTTPException(status_code=422, detail="Cuéntanos qué te gustaría (mínimo 3 letras).")
    if v.opcion_id != "otro":
        otro = None
    fila = {
        "id": str(uuid.uuid4()), "periodo_id": v.periodo_id, "comuna_slug": p["comuna_slug"], "site_id": v.site_id,
        "opcion_id": v.opcion_id, "otro_texto": otro, "edad_rango": v.edad_rango,
        "dispositivo_hash": hash_dispositivo(v.dispositivo), "via_qr": v.via_qr, "demo": bool(p.get("demo")), "creado_en": _iso(_ahora()),
    }
    if not alm.insertar_voto(fila):
        raise HTTPException(status_code=409, detail="Ya votaste en este lugar en esta votación.")
    return {"ok": True, "almacen": alm.nombre}


@router.get("/mis-votos")
def mis_votos(periodo_id: str, dispositivo: str = Query(min_length=16, max_length=80)) -> dict[str, Any]:
    alm = obtener_almacen()
    return {"sitios": alm.sitios_votados(periodo_id, hash_dispositivo(dispositivo))}


def calcular_resultados(votos: list[dict[str, Any]], minimo: int) -> dict[str, Any]:
    por_sitio: dict[str, list[dict[str, Any]]] = {}
    for v in votos:
        por_sitio.setdefault(v["site_id"], []).append(v)
    salida: dict[str, Any] = {}
    for sid, lista in por_sitio.items():
        total = len(lista)
        if total < minimo:
            salida[sid] = {"total": total, "oculto": True}
            continue
        cuenta: dict[str, int] = {}
        for v in lista:
            cuenta[v["opcion_id"]] = cuenta.get(v["opcion_id"], 0) + 1
        opciones = sorted(({"id": k, "votos": n, "pct": round(100.0 * n / total, 1)} for k, n in cuenta.items()), key=lambda o: (-o["votos"], o["id"]))
        otros = [v["otro_texto"] for v in lista if v["opcion_id"] == "otro" and v.get("otro_texto")][:20]
        salida[sid] = {"total": total, "oculto": False, "opciones": opciones, "otros": otros}
    return salida


@router.get("/resultados")
def resultados(periodo_id: str) -> dict[str, Any]:
    alm = obtener_almacen()
    p = alm.obtener_periodo(periodo_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Esa votación no existe.")
    votos = alm.votos_de_periodo(periodo_id)
    epoca = describir_epoca(p)
    if epoca["estado"] != "cerrado":
        conteo: dict[str, int] = {}
        for v in votos:
            conteo[v["site_id"]] = conteo.get(v["site_id"], 0) + 1
        return {"epoca": epoca, "publicado": False, "votos_por_sitio": conteo, "total_votos": len(votos), "participacion": calcular_participacion(votos), "confianza": confianza_por_sitio(votos, min_votos_publicar()), "confianza_global": calcular_confianza(votos, min_votos_publicar()),
                "mensaje": "Los porcentajes se publican cuando cierra la votación."}
    minimo = min_votos_publicar()
    return {"epoca": epoca, "publicado": True, "min_votos": minimo, "total_votos": len(votos), "participacion": calcular_participacion(votos), "confianza": confianza_por_sitio(votos, min_votos_publicar()), "confianza_global": calcular_confianza(votos, min_votos_publicar()),
            "sitios": calcular_resultados(votos, minimo)}


@router.post("/admin/epocas")
def admin_crear_epoca(pedido: PedidoEpoca, x_admin_token: str | None = Header(default=None)) -> dict[str, Any]:
    _exigir_admin(x_admin_token)
    if not _sitios_de(pedido.comuna_slug):
        raise HTTPException(status_code=404, detail="Comuna desconocida.")
    alm = obtener_almacen()
    for p in alm.periodos(pedido.comuna_slug):
        if not p.get("demo") and estado_epoca(p) == "abierto":
            raise HTTPException(status_code=409, detail="Ya hay una votación abierta en esa comuna: ciérrala antes.")
    nueva = nueva_epoca(pedido.comuna_slug, pedido.nombre, pedido.dias)
    alm.crear_periodo(nueva)
    return {"epoca": describir_epoca(nueva)}


@router.post("/admin/cerrar")
def admin_cerrar(pedido: PedidoCerrar, x_admin_token: str | None = Header(default=None)) -> dict[str, Any]:
    _exigir_admin(x_admin_token)
    alm = obtener_almacen()
    p = alm.obtener_periodo(pedido.periodo_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Esa votación no existe.")
    alm.cerrar_periodo(pedido.periodo_id)
    return {"epoca": describir_epoca({**p, "cerrado_manual": True})}


# --------------------------------------------------------------------------------------------------
# Datos de demostración (votos simulados, marcados como demo en la base y en la página)
# --------------------------------------------------------------------------------------------------
def sembrar_demo(almacen: Any, comuna_slug: str = "cerro_navia", sitios: int = 12, votos_por_sitio: int = 40, semilla: int = 7, id_fijo: str | None = None) -> dict[str, Any]:
    """Crea una votación cerrada con votos SIMULADOS. Sirve solo para mostrar cómo se ven los resultados."""
    rng = random.Random(f"{semilla}:{comuna_slug}")  # cada comuna tiene sus propios votos simulados
    datos = _sitios_de(comuna_slug)
    if not datos:
        raise ValueError(f"No hay datos de la comuna {comuna_slug}; corre el paso 08.")
    abre = _ahora() - timedelta(days=30)
    epoca = nueva_epoca(comuna_slug, "Votación de demostración (votos simulados)", dias=14, demo=True, abre=abre)
    if id_fijo:
        epoca["id"] = id_fijo
    almacen.crear_periodo(epoca)
    elegidos = sorted(datos.values(), key=lambda s: -s["area_m2"])[:sitios]
    extras = [i["id"] for i in _ideas_extra()["ideas"]]
    edades, pesos_edad = ["menos_18", "18_29", "30_44", "45_59", "60_mas"], [0.08, 0.24, 0.34, 0.24, 0.10]  # simulado: pocas personas de 60 o más
    filas = []
    for s in elegidos:
        ids = [o["id"] for o in s["opciones"]]
        pesos = [0.45, 0.25, 0.15, 0.10, 0.05][: len(ids)]
        n_sitio = max(3, round(votos_por_sitio * (0.15 + 1.6 * rng.random() ** 1.5)))  # simulado: unos lugares reciben muchos votos y otros pocos
        con_rafaga = s is elegidos[3] if len(elegidos) > 3 else False  # simulado: un lugar recibe casi todos sus votos en una hora
        for k in range(n_sitio):
            opcion = rng.choices(ids, weights=pesos)[0] if rng.random() > 0.08 else rng.choice(extras)
            filas.append({
                "id": str(uuid.uuid4()), "periodo_id": epoca["id"], "comuna_slug": comuna_slug, "site_id": s["id"], "opcion_id": opcion,
                "otro_texto": None, "edad_rango": rng.choices(edades, weights=pesos_edad)[0],
                "dispositivo_hash": hashlib.sha256(f"demo:{comuna_slug}:{s['id']}:{k}".encode()).hexdigest(),
                "via_qr": (rng.random() < 0.15) if con_rafaga else (rng.random() < 0.5), "demo": True,
                "creado_en": _iso(abre + (timedelta(hours=200, minutes=rng.randint(0, 50)) if con_rafaga and rng.random() < 0.8 else timedelta(hours=int(300 * rng.random() ** 0.7) + 1))),
            })
    n = almacen.insertar_votos(filas)
    return {"epoca": describir_epoca(epoca), "votos": n}


_demo_listo: set[str] = set()


def asegurar_demo(almacen: Any) -> None:
    """Con PULMON_DEMO_AUTO=1 y almacén local (p. ej. Vercel sin Supabase), crea la votación simulada de cada comuna."""
    if not demo_automatica() or almacen.nombre != "local":
        return
    clave = str(getattr(almacen, "ruta", ""))
    if clave in _demo_listo:
        return
    for z in _zonas():
        pid = f"demo-{z['slug']}"
        if almacen.obtener_periodo(pid) is None:
            try:
                sembrar_demo(almacen, z["slug"], id_fijo=pid)
            except Exception:
                pass
    _demo_listo.add(clave)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Utilidades de votación")
    ap.add_argument("--demo", action="store_true", help="crear una votación cerrada con votos SIMULADOS")
    ap.add_argument("--comuna", default="cerro_navia")
    args = ap.parse_args()
    if args.demo:
        print(sembrar_demo(obtener_almacen(), args.comuna))
