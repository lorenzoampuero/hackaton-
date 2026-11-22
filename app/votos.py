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
            return [dict(r) for r in con.execute("select site_id, opcion_id, otro_texto, edad_rango, via_qr from votacion_votos where periodo_id = ?", (periodo_id,))]

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
            lote = self._get(f"votacion_votos?select=site_id,opcion_id,otro_texto,edad_rango,via_qr&periodo_id=eq.{periodo_id}&order=creado_en.asc&limit=1000&offset={desde}")
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
    if v.opcion_id != "otro" and v.opcion_id not in _catalogo():
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
        return {"epoca": epoca, "publicado": False, "votos_por_sitio": conteo, "total_votos": len(votos),
                "mensaje": "Los porcentajes se publican cuando cierra la votación."}
    minimo = min_votos_publicar()
    return {"epoca": epoca, "publicado": True, "min_votos": minimo, "total_votos": len(votos),
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
    rng = random.Random(semilla)
    datos = _sitios_de(comuna_slug)
    if not datos:
        raise ValueError(f"No hay datos de la comuna {comuna_slug}; corre el paso 08.")
    abre = _ahora() - timedelta(days=30)
    epoca = nueva_epoca(comuna_slug, "Votación de demostración (votos simulados)", dias=14, demo=True, abre=abre)
    if id_fijo:
        epoca["id"] = id_fijo
    almacen.crear_periodo(epoca)
    elegidos = sorted(datos.values(), key=lambda s: -s["area_m2"])[:sitios]
    filas = []
    for s in elegidos:
        ids = [o["id"] for o in s["opciones"]]
        pesos = [0.45, 0.25, 0.15, 0.10, 0.05][: len(ids)]
        for k in range(votos_por_sitio):
            opcion = rng.choices(ids, weights=pesos)[0] if rng.random() > 0.08 else "otro"
            filas.append({
                "id": str(uuid.uuid4()), "periodo_id": epoca["id"], "comuna_slug": comuna_slug, "site_id": s["id"], "opcion_id": opcion,
                "otro_texto": "Una feria vecinal los fines de semana (simulado)" if opcion == "otro" else None,
                "edad_rango": rng.choice(sorted(RANGOS_EDAD)), "dispositivo_hash": hashlib.sha256(f"demo:{comuna_slug}:{s['id']}:{k}".encode()).hexdigest(),
                "via_qr": rng.random() < 0.5, "demo": True, "creado_en": _iso(abre + timedelta(hours=rng.randint(1, 300))),
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
