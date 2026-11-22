"""Backend FastAPI de RE-VIDA (local y Vercel Serverless):
- Sirve la aplicación web estática (local) y los endpoints /api/*.
- Redacta informes y responde en el Asistente IA multimodal sin exponer claves al navegador.
- Persiste perfiles, planes ("Plan aceptado"), casos con fotografía y consultas IA en Supabase.
"""

from __future__ import annotations

import importlib
import json
import os
import threading
import time
import urllib.parse
from collections import deque
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pipeline.comun import RAIZ, WEB_DATA, cargar_env, leer_json

mod_05 = importlib.import_module("pipeline.05_senales")
mod_06 = importlib.import_module("pipeline.06_paquete_caso")
mod_07 = importlib.import_module("pipeline.07_informe_ia")

app = FastAPI(title="RE-VIDA — API y Servidor", docs_url=None, redoc_url=None)

from app.votos import router as router_votos  # noqa: E402  (votación vecinal: épocas, votos y resultados)

app.include_router(router_votos)

# Entradas de la web (en Vercel lo mismo lo hace vercel.json): el vecino entra a su vista; la institución y
# el modo profesional tienen su propia ruta.
from fastapi.responses import FileResponse, RedirectResponse  # noqa: E402


@app.get("/", include_in_schema=False)
def entrada_vecino() -> RedirectResponse:
    return RedirectResponse("/vecino.html")


@app.get("/institucion", include_in_schema=False)
def entrada_institucion() -> FileResponse:
    return FileResponse(RAIZ / "web" / "institucion.html")


@app.get("/profesional", include_in_schema=False)
def entrada_profesional() -> FileResponse:
    return FileResponse(RAIZ / "web" / "index.html")


@app.get("/qr", include_in_schema=False)
def entrada_qr() -> FileResponse:
    return FileResponse(RAIZ / "web" / "qr.html")

_llamadas: deque[float] = deque()
_candado = threading.Lock()
_lock_db = threading.Lock()

PLANES_CONFIG: dict[str, dict[str, Any]] = {
    "gratis": {
        "plan_id": "gratis",
        "plan_nombre": "Gratis (Demo / Público)",
        "precio_uf": 0.0,
        "precio_clp": 0,
        "exportaciones_limite": 2,
        "informes_ia_limite": 0,
    },
    "pase_proyecto": {
        "plan_id": "pase_proyecto",
        "plan_nombre": "Pase por Proyecto (Pago único)",
        "precio_uf": 1.5,
        "precio_clp": 62000,
        "exportaciones_limite": 20,
        "informes_ia_limite": 1,
    },
    "profesional": {
        "plan_id": "profesional",
        "plan_nombre": "Profesional (Independiente)",
        "precio_uf": 1.5,
        "precio_clp": 62000,
        "precio_uf_anual": 1.2,
        "precio_clp_anual": 50000,
        "exportaciones_limite": 50,
        "informes_ia_limite": 3,
    },
    "consultora": {
        "plan_id": "consultora",
        "plan_nombre": "Consultora ⭐ (Plan principal)",
        "precio_uf": 4.5,
        "precio_clp": 186000,
        "precio_uf_anual": 3.7,
        "precio_clp_anual": 153000,
        "exportaciones_limite": 500,
        "informes_ia_limite": 15,
    },
    "empresa": {
        "plan_id": "empresa",
        "plan_nombre": "Empresa (Multi-territorio)",
        "precio_uf": 9.5,
        "precio_clp": 392000,
        "precio_uf_anual": 7.8,
        "precio_clp_anual": 322000,
        "exportaciones_limite": 9999,
        "informes_ia_limite": 9999,
    },
}

INSTRUCCIONES_CHAT_IA = """Eres el Asistente Territorial de RE-VIDA en Chile.
Ayudas a alcaldes, equipos municipales (SECPLA/Ornato), consultoras ambientales e inmobiliarias a decidir dónde plantar árboles y reducir calor urbano.
Reglas obligatorias:
1. Habla en español claro, cercano y sin tecnicismos innecesarios: explica qué significan los números en palabras simples (ej. calor del suelo en °C, porcentaje de árboles vs cemento, porcentaje de techos de zinc, confianza del dato %). Evita jerga cruda como 'NDMI z-score' sin traducirla.
2. Usa ÚNICAMENTE los datos reales entregados en el contexto (comuna, parque, caso guardado o tabla de cartera). No inventes cifras.
3. Todo monto en CLP que menciones debe acompañarse de "hipótesis (sin verificar)".
4. No prometas retornos financieros ni afirmes causalidad absoluta ('causó'); usa 'coincide con' o 'es compatible con'.
5. Si el usuario adjunta una fotografía o captura del parque, describe recomendaciones prácticas (especies de bajo consumo hídrico, sombreaderos, verificación de riego y mantención) integrándolas con los indicadores del parque.
6. Estructura la respuesta en viñetas cortas y claras listas para leer o presentar."""


class PedidoInforme(BaseModel):
    ambito: str | None = None
    caso_id: str | None = None
    comuna_slug: str | None = None
    site_id: str | None = None
    email: str | None = None


class PedidoLogin(BaseModel):
    email: str = "demo@pulmonurbano.cl"
    nombre: str = "Equipo Evaluador"
    organizacion: str = "Municipalidad Demo"
    rol: str = "Planificación Urbana"


class PedidoActivarPlan(BaseModel):
    email: str = "demo@pulmonurbano.cl"
    plan_id: str
    modalidad: str = "mensual"


class PedidoExportacion(BaseModel):
    email: str = "demo@pulmonurbano.cl"
    tipo: str = "csv"


class PedidoCasoGuardar(BaseModel):
    id: str
    user_email: str = "demo@pulmonurbano.cl"
    comuna_slug: str = "cerro_navia"
    site_id: str | None = None
    titulo: str
    tipo_label: str = "Caso con IA"
    nota: str = ""
    foto_data_url: str | None = None
    pregunta_ia: str | None = None
    respuesta_ia: str | None = None
    confianza_pct: int = 94
    paquete: dict[str, Any] | None = None
    informe: dict[str, Any] | None = None


class PedidoChat(BaseModel):
    pregunta: str
    comuna_slug: str = "cerro_navia"
    site_id: str | None = None
    caso_titulo: str | None = None
    contexto_datos: dict[str, Any] | None = None
    imagen_data_url: str | None = None
    email: str = "demo@pulmonurbano.cl"


def _ruta_db_local() -> Path:
    primario = RAIZ / "data" / "mvp_db.json"
    try:
        primario.parent.mkdir(parents=True, exist_ok=True)
        if primario.exists() or os.access(primario.parent, os.W_OK):
            return primario
    except OSError:
        pass
    return Path("/tmp/pulmon_urbano_mvp_db.json")


def _leer_db_local() -> dict[str, Any]:
    with _lock_db:
        ruta = _ruta_db_local()
        if ruta.exists():
            try:
                return json.loads(ruta.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"perfiles": {}, "casos": [], "consultas": []}


def _guardar_db_local(db: dict[str, Any]) -> None:
    with _lock_db:
        ruta = _ruta_db_local()
        ruta.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")


def _sb_creds() -> tuple[str | None, str | None, str | None]:
    cargar_env()
    url = (os.environ.get("SUPABASE_URL") or "").strip().rstrip("/")
    pub = (os.environ.get("SUPABASE_PUBLISHABLE_KEY") or os.environ.get("SUPABASE_ANON_KEY") or "").strip()
    sec = (os.environ.get("SUPABASE_SECRET_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    key = sec or pub
    return (url or None, pub or None, key or None)


def _sb_headers(key: str, prefer: str | None = None) -> dict[str, str]:
    hdrs = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if prefer:
        hdrs["Prefer"] = prefer
    return hdrs


def _sb_tablas_estado() -> tuple[bool, bool]:
    url, _pub, key = _sb_creds()
    if not url or not key:
        return False, False
    conectado = False
    tablas_listas = False
    try:
        r_h = httpx.get(f"{url}/auth/v1/health", headers={"apikey": key}, timeout=3.0)
        conectado = r_h.status_code == 200
        r_t = httpx.get(
            f"{url}/rest/v1/perfiles_planes?select=email&limit=1",
            headers=_sb_headers(key),
            timeout=3.0,
        )
        tablas_listas = r_t.status_code == 200
    except Exception:
        pass
    return conectado, tablas_listas


def _perfil_default(email: str = "demo@pulmonurbano.cl", nombre: str = "Equipo Evaluador", organizacion: str = "Municipalidad Demo", rol: str = "Planificación Urbana") -> dict[str, Any]:
    base = dict(PLANES_CONFIG["gratis"])
    return {
        "email": email.strip().lower() or "demo@pulmonurbano.cl",
        "nombre": nombre,
        "organizacion": organizacion,
        "rol": rol,
        "plan_id": base["plan_id"],
        "plan_nombre": base["plan_nombre"],
        "modalidad": "mensual",
        "precio_uf": 0,
        "precio_clp": 0,
        "exportaciones_usadas": 0,
        "exportaciones_limite": base["exportaciones_limite"],
        "informes_ia_usados": 0,
        "informes_ia_limite": base["informes_ia_limite"],
        "estado": "activo",
    }


def _obtener_o_crear_perfil(email: str) -> tuple[dict[str, Any], str]:
    norm_email = (email or "demo@pulmonurbano.cl").strip().lower()
    url, _pub, key = _sb_creds()
    if url and key:
        try:
            q_email = urllib.parse.quote(norm_email, safe="")
            r = httpx.get(
                f"{url}/rest/v1/perfiles_planes?email=eq.{q_email}&limit=1",
                headers=_sb_headers(key),
                timeout=4.0,
            )
            if r.status_code == 200:
                rows = r.json()
                if rows:
                    return rows[0], "supabase"
                nuevo = _perfil_default(email=norm_email)
                r_ins = httpx.post(
                    f"{url}/rest/v1/perfiles_planes",
                    headers=_sb_headers(key, "return=representation,resolution=merge-duplicates"),
                    json=nuevo,
                    timeout=4.0,
                )
                if r_ins.status_code in (200, 201) and r_ins.json():
                    return r_ins.json()[0], "supabase"
        except Exception:
            pass

    db = _leer_db_local()
    perf = db["perfiles"].get(norm_email)
    if not perf:
        perf = _perfil_default(email=norm_email)
        db["perfiles"][norm_email] = perf
        _guardar_db_local(db)
    return perf, "local_fallback"


def _guardar_perfil(perfil: dict[str, Any]) -> tuple[dict[str, Any], str]:
    norm_email = perfil["email"].strip().lower()
    url, _pub, key = _sb_creds()
    db = _leer_db_local()
    db["perfiles"][norm_email] = perfil
    _guardar_db_local(db)

    if url and key:
        try:
            payload = {k: v for k, v in perfil.items() if k != "id"}
            r = httpx.post(
                f"{url}/rest/v1/perfiles_planes?on_conflict=email",
                headers=_sb_headers(key, "return=representation,resolution=merge-duplicates"),
                json=payload,
                timeout=4.0,
            )
            if r.status_code in (200, 201) and r.json():
                return r.json()[0], "supabase"
        except Exception:
            pass
    return perfil, "local_fallback"


def _buscar_paquete(pedido: PedidoInforme) -> dict[str, Any] | None:
    """El paquete se lee del disco: el navegador solo dice cuál quiere, no puede mandar cifras propias."""
    if pedido.ambito:
        carteras = leer_json(WEB_DATA / "informes_inversion.json")
        return (carteras.get(pedido.ambito) or {}).get("paquete")
    if pedido.caso_id:
        for caso in leer_json(WEB_DATA / "casos.json"):
            if caso.get("caso_id") == pedido.caso_id:
                return caso
    if pedido.comuna_slug and pedido.site_id:
        ruta_gj = WEB_DATA / pedido.comuna_slug / "sitios.geojson"
        if not ruta_gj.exists():
            return None
        gj = leer_json(ruta_gj)
        feat = next((f for f in gj.get("features", []) if f.get("properties", {}).get("site_id") == pedido.site_id), None)
        if feat is None:
            return None
        resumen = leer_json(WEB_DATA / "resumen.json")
        res_com = next((c for c in resumen.get("comunas", []) if c["slug"] == pedido.comuna_slug), None)
        if res_com is None:
            return None
        return mod_06.construir_paquete_sitio(
            caso_id=f"sitio-{pedido.comuna_slug}-{pedido.site_id}",
            tipo_caso="Ficha prioritaria municipal",
            titulo=f"{feat['properties']['nombre']} ({res_com['nombre']})",
            pregunta_decision=f"¿Qué acción priorizar y verificar en terreno para {feat['properties']['nombre']}?",
            comuna_resumen=res_com,
            sitio_props=feat["properties"],
            catalogo=mod_05.cargar_catalogo_intervenciones(),
        )
    return None


def _hay_cupo() -> bool:
    cargar_env()
    maximo = int(os.environ.get("PULMON_IA_MAX_HORA", "60"))
    ahora = time.time()
    with _candado:
        while _llamadas and ahora - _llamadas[0] > 3600:
            _llamadas.popleft()
        if len(_llamadas) >= maximo:
            return False
        _llamadas.append(ahora)
        return True


def _construir_contexto_chat(req: PedidoChat) -> str:
    resumen = leer_json(WEB_DATA / "resumen.json")
    com_info = next((c for c in resumen.get("comunas", []) if c["slug"] == req.comuna_slug), None)
    sitio_info = None
    if req.comuna_slug and req.site_id:
        ruta_gj = WEB_DATA / req.comuna_slug / "sitios.geojson"
        if ruta_gj.exists():
            gj = leer_json(ruta_gj)
            feat = next((f for f in gj.get("features", []) if f.get("properties", {}).get("site_id") == req.site_id), None)
            if feat:
                p = feat["properties"]
                sitio_info = {
                    "nombre": p.get("nombre"),
                    "area_ha": round(float(p.get("area_m2") or 0) / 10000, 2),
                    "prioridad": p.get("prioridad_score"),
                    "calor_verano_c": p.get("lst_verano_c"),
                    "salud_vegetal_pct": p.get("salud_vegetal_pct"),
                    "arboles_entorno_400m_pct": p.get("cobertura_arboles_400m_pct"),
                    "cemento_entorno_400m_pct": p.get("impermeable_400m_pct"),
                    "techos_zinc_400m_pct": p.get("pct_techo_calor_400m"),
                    "arboles_necesarios": f"{p.get('arboles_necesarios_min')} a {p.get('arboles_necesarios_max')}",
                    "presupuesto_clp": f"${p.get('costo_clp_min')} a ${p.get('costo_clp_max')} CLP (hipótesis (sin verificar))",
                    "confianza_pct": p.get("confianza_pct"),
                    "fondos_sugeridos": [f.get("nombre") for f in p.get("fondos_sugeridos", [])],
                }
    carteras = leer_json(WEB_DATA / "informes_inversion.json")
    cartera_com = carteras.get(req.comuna_slug or "cerro_navia") or carteras.get("intercomunal")
    top3_parques = []
    if cartera_com:
        for s in (cartera_com.get("paquete", {}).get("cartera_sitios") or [])[:4]:
            top3_parques.append({
                "nombre": s.get("nombre"),
                "comuna": s.get("comuna"),
                "calor_verano_c": s.get("lst_verano_c"),
                "arboles_pct": s.get("cobertura_arboles_400m_pct"),
                "cemento_pct": s.get("impermeable_400m_pct"),
                "arboles_faltantes": f"{s.get('arboles_necesarios_min')}–{s.get('arboles_necesarios_max')}",
                "fondo": s.get("fondo_sugerido"),
                "confianza_pct": s.get("confianza_pct"),
            })
    bloque = {
        "comuna": {
            "nombre": com_info.get("nombre") if com_info else req.comuna_slug,
            "calor_verano_c": com_info.get("lst_verano_mediana_c") if com_info else None,
            "arboles_pct": com_info.get("cobertura_arboles_comuna_pct") if com_info else None,
            "cemento_pct": com_info.get("impermeable_comuna_pct") if com_info else None,
            "arboles_meta_30": f"{com_info.get('arboles_necesarios_min_total')}–{com_info.get('arboles_necesarios_max_total')}" if com_info else None,
            "confianza_comuna_pct": com_info.get("confianza_comuna_pct", 94) if com_info else 94,
            "aire_pm25": (com_info.get("aire") or {}).get("pm2_5_media") if com_info else None,
        },
        "sitio_seleccionado": sitio_info,
        "caso_referencia": req.caso_titulo,
        "top_parques_comuna": top3_parques,
        "contexto_extra": req.contexto_datos,
    }
    return json.dumps(bloque, ensure_ascii=False)


def _llamar_chat_llm(req: PedidoChat, contexto_json: str) -> tuple[str, str]:
    prov = mod_07.proveedor_configurado()
    if prov is None:
        raise RuntimeError("Sin clave LLM configurada")
    proveedor, modelo = prov
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
    api_key = os.environ["OPENAI_API_KEY"].strip()

    prompt_texto = f"Datos verificados de RE-VIDA:\n{contexto_json}\n\nPregunta del usuario: {req.pregunta}"
    if req.imagen_data_url:
        prompt_texto += "\n(El usuario adjuntó una fotografía/captura del parque para análisis visual y recomendación práctica.)"

    content: Any = prompt_texto
    if req.imagen_data_url and proveedor in ("deepseek", "openai") and req.imagen_data_url.startswith("data:image/"):
        content = [
            {"type": "text", "text": prompt_texto},
            {"type": "image_url", "image_url": {"url": req.imagen_data_url}},
        ]

    def _post(msg_content: Any) -> str:
        payload: dict[str, Any] = {
            "model": modelo,
            "messages": [
                {"role": "system", "content": INSTRUCCIONES_CHAT_IA},
                {"role": "user", "content": msg_content},
            ],
            "temperature": 0.2,
        }
        if proveedor == "deepseek":
            payload["reasoning_effort"] = os.environ.get("PULMON_DEEPSEEK_EFFORT", "low")
        resp = httpx.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=45.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    try:
        return _post(content), f"{proveedor}:{modelo}"
    except Exception:
        if isinstance(content, list):
            return _post(prompt_texto + " [Nota: imagen adjunta registrada en el expediente.]"), f"{proveedor}:{modelo}"
        raise


def _registrar_consulta_ia(req: PedidoChat, respuesta: str, modelo: str) -> bool:
    url, _pub, key = _sb_creds()
    db = _leer_db_local()
    db["consultas"].insert(0, {
        "user_email": req.email.strip().lower(),
        "comuna_slug": req.comuna_slug,
        "site_id": req.site_id,
        "caso_id": req.caso_titulo,
        "pregunta": req.pregunta,
        "tiene_imagen": bool(req.imagen_data_url),
        "respuesta": respuesta,
        "modelo": modelo,
    })
    db["consultas"] = db["consultas"][:100]
    _guardar_db_local(db)

    if url and key:
        try:
            r = httpx.post(
                f"{url}/rest/v1/consultas_ia",
                headers=_sb_headers(key, "return=minimal"),
                json={
                    "user_email": req.email.strip().lower(),
                    "comuna_slug": req.comuna_slug,
                    "site_id": req.site_id,
                    "caso_id": req.caso_titulo,
                    "pregunta": req.pregunta,
                    "tiene_imagen": bool(req.imagen_data_url),
                    "respuesta": respuesta,
                    "modelo": modelo,
                },
                timeout=4.0,
            )
            return r.status_code in (200, 201, 204)
        except Exception:
            pass
    return False


@app.get("/api/estado")
def estado() -> dict[str, Any]:
    prov = mod_07.proveedor_configurado()
    sb_url, sb_pub, _sb_key = _sb_creds()
    sb_conectado, sb_tablas = _sb_tablas_estado()
    return {
        "servidor": True,
        "ia_disponible": prov is not None,
        "proveedor": prov[0] if prov else None,
        "modelo": prov[1] if prov else None,
        "supabase_disponible": bool(sb_url and sb_pub),
        "supabase_conectado": sb_conectado,
        "supabase_tablas_listas": sb_tablas,
        "supabase_url": sb_url,
    }


@app.get("/api/plan/actual")
def obtener_plan_actual(email: str = Query(default="demo@pulmonurbano.cl")) -> dict[str, Any]:
    perfil, origen = _obtener_o_crear_perfil(email)
    return {"ok": True, "almacenamiento": origen, "perfil": perfil}


@app.post("/api/auth/login")
def login_visual(pedido: PedidoLogin) -> dict[str, Any]:
    email_limpio = (pedido.email or "demo@pulmonurbano.cl").strip().lower()
    perfil, _ = _obtener_o_crear_perfil(email_limpio)
    perfil["nombre"] = pedido.nombre.strip() or "Usuario Demo"
    perfil["organizacion"] = pedido.organizacion.strip() or "Municipalidad / Consultora"
    perfil["rol"] = pedido.rol.strip() or "Evaluador Territorial"
    guardado, origen = _guardar_perfil(perfil)
    return {"ok": True, "almacenamiento": origen, "perfil": guardado}


@app.post("/api/plan/activar")
def activar_plan(pedido: PedidoActivarPlan) -> dict[str, Any]:
    cfg_plan = PLANES_CONFIG.get(pedido.plan_id)
    if not cfg_plan:
        raise HTTPException(status_code=404, detail="Plan no reconocido.")
    perfil, _ = _obtener_o_crear_perfil(pedido.email)
    es_anual = pedido.modalidad == "anual" and "precio_uf_anual" in cfg_plan
    perfil.update({
        "plan_id": cfg_plan["plan_id"],
        "plan_nombre": cfg_plan["plan_nombre"],
        "modalidad": "anual" if es_anual else "mensual",
        "precio_uf": cfg_plan.get("precio_uf_anual", cfg_plan["precio_uf"]) if es_anual else cfg_plan["precio_uf"],
        "precio_clp": cfg_plan.get("precio_clp_anual", cfg_plan["precio_clp"]) if es_anual else cfg_plan["precio_clp"],
        "exportaciones_limite": cfg_plan["exportaciones_limite"],
        "informes_ia_limite": cfg_plan["informes_ia_limite"],
        "exportaciones_usadas": 0 if cfg_plan["plan_id"] == "gratis" else perfil.get("exportaciones_usadas", 0),
        "estado": "activo",
    })
    guardado, origen = _guardar_perfil(perfil)
    return {
        "ok": True,
        "mensaje": f"Plan aceptado: {cfg_plan['plan_nombre']} activado.",
        "almacenamiento": origen,
        "perfil": guardado,
    }


@app.post("/api/plan/consumir-exportacion")
def consumir_exportacion(pedido: PedidoExportacion) -> dict[str, Any]:
    perfil, _ = _obtener_o_crear_perfil(pedido.email)
    limite = int(perfil.get("exportaciones_limite") or 2)
    usadas = int(perfil.get("exportaciones_usadas") or 0)
    if usadas >= limite:
        raise HTTPException(
            status_code=402,
            detail=f"Alcanzaste el límite de {limite} exportaciones del plan {perfil.get('plan_nombre')}. Activa un plan en 1 clic.",
        )
    if perfil.get("plan_id") == "gratis" and pedido.tipo in ("docx", "pdf"):
        raise HTTPException(
            status_code=402,
            detail="Las exportaciones Word y PDF ejecutivos están disponibles desde Pase por Proyecto (1,5 UF) o Consultora ⭐.",
        )
    perfil["exportaciones_usadas"] = usadas + 1
    guardado, origen = _guardar_perfil(perfil)
    return {"ok": True, "almacenamiento": origen, "perfil": guardado}


@app.get("/api/casos")
def listar_casos(email: str = Query(default="demo@pulmonurbano.cl")) -> dict[str, Any]:
    norm_email = email.strip().lower()
    url, _pub, key = _sb_creds()
    if url and key:
        try:
            q = urllib.parse.quote(norm_email, safe="")
            r = httpx.get(
                f"{url}/rest/v1/casos_guardados?user_email=eq.{q}&order=created_at.desc",
                headers=_sb_headers(key),
                timeout=4.0,
            )
            if r.status_code == 200:
                return {"ok": True, "almacenamiento": "supabase", "casos": r.json()}
        except Exception:
            pass
    db = _leer_db_local()
    casos = [c for c in db.get("casos", []) if c.get("user_email", "demo@pulmonurbano.cl") == norm_email]
    return {"ok": True, "almacenamiento": "local_fallback", "casos": casos}


@app.post("/api/casos")
def guardar_caso(pedido: PedidoCasoGuardar) -> dict[str, Any]:
    row = pedido.model_dump()
    row["user_email"] = (row.get("user_email") or "demo@pulmonurbano.cl").strip().lower()
    db = _leer_db_local()
    db["casos"] = [c for c in db.get("casos", []) if c.get("id") != row["id"]]
    db["casos"].insert(0, row)
    _guardar_db_local(db)

    url, _pub, key = _sb_creds()
    origen = "local_fallback"
    if url and key:
        try:
            r = httpx.post(
                f"{url}/rest/v1/casos_guardados?on_conflict=id",
                headers=_sb_headers(key, "return=representation,resolution=merge-duplicates"),
                json=row,
                timeout=5.0,
            )
            if r.status_code in (200, 201):
                origen = "supabase"
        except Exception:
            pass
    return {"ok": True, "almacenamiento": origen, "caso": row}


@app.delete("/api/casos/{caso_id}")
def eliminar_caso(caso_id: str) -> dict[str, Any]:
    db = _leer_db_local()
    db["casos"] = [c for c in db.get("casos", []) if c.get("id") != caso_id]
    _guardar_db_local(db)
    url, _pub, key = _sb_creds()
    if url and key:
        try:
            cid = urllib.parse.quote(caso_id, safe="")
            httpx.delete(f"{url}/rest/v1/casos_guardados?id=eq.{cid}", headers=_sb_headers(key), timeout=4.0)
        except Exception:
            pass
    return {"ok": True}


@app.post("/api/chat")
def chat_ia(pedido: PedidoChat) -> dict[str, Any]:
    perfil, _ = _obtener_o_crear_perfil(pedido.email)
    if perfil.get("plan_id") == "gratis" and int(perfil.get("informes_ia_limite") or 0) <= 0:
        raise HTTPException(
            status_code=402,
            detail="El Asistente IA con análisis de fotos y casos requiere activar Pase por Proyecto, Profesional o Consultora ⭐ (puedes activarlo en 1 clic).",
        )
    if mod_07.proveedor_configurado() is None:
        raise HTTPException(status_code=503, detail="Falta la clave de IA en variables de entorno.")
    if not _hay_cupo():
        raise HTTPException(status_code=429, detail="Se alcanzó el límite de consultas IA por hora.")

    contexto_json = _construir_contexto_chat(pedido)
    try:
        respuesta, modelo_usado = _llamar_chat_llm(pedido, contexto_json)
    except Exception as exc:
        ctx = json.loads(contexto_json)
        com = ctx.get("comuna") or {}
        respuesta = (
            f"Resumen directo para {com.get('nombre', pedido.comuna_slug)} (confianza del dato {com.get('confianza_comuna_pct', 94)}%):\n"
            f"• Calor de verano medido: {com.get('calor_verano_c', 's/d')} °C con {com.get('arboles_pct', 's/d')}% de árboles frente a {com.get('cemento_pct', 's/d')}% de cemento.\n"
            f"• Brecha estimada hacia meta 30%: {com.get('arboles_meta_30', 's/d')} árboles (presupuestos como hipótesis (sin verificar)).\n"
            f"• Recomendación práctica: priorizar los primeros parques del ranking y postular a Programa de Espacios Públicos (MINVU) o PMU SUBDERE. "
            f"(Nota técnica temporal: {type(exc).__name__})."
        )
        modelo_usado = "respaldo_deterministico"

    perfil["informes_ia_usados"] = int(perfil.get("informes_ia_usados") or 0) + 1
    _guardar_perfil(perfil)
    sb_ok = _registrar_consulta_ia(pedido, respuesta, modelo_usado)
    return {
        "ok": True,
        "respuesta": respuesta,
        "modelo": modelo_usado,
        "guardado_supabase": sb_ok,
        "perfil": perfil,
    }


@app.post("/api/informe")
def informe(pedido: PedidoInforme) -> dict[str, Any]:
    paquete = _buscar_paquete(pedido)
    if paquete is None:
        raise HTTPException(status_code=404, detail="No existe un paquete de datos para ese ámbito o caso.")
    if pedido.email:
        perfil, _ = _obtener_o_crear_perfil(pedido.email)
        if perfil.get("plan_id") == "gratis" and int(perfil.get("informes_ia_limite") or 0) <= 0:
            raise HTTPException(
                status_code=402,
                detail="Tu plan Gratis no incluye redacción de informes IA en vivo. Activa un plan en 1 clic para desbloquearlo.",
            )
    if mod_07.proveedor_configurado() is None:
        raise HTTPException(status_code=503, detail="Falta la clave de API: crea el archivo .env a partir de .env.example.")
    if not _hay_cupo():
        raise HTTPException(status_code=429, detail="Se alcanzó el límite de informes con IA por hora.")
    resultado, diagnostico = mod_07.generar_informe_detallado(paquete)
    return {"informe": resultado, "diagnostico": diagnostico}


if (RAIZ / "web").exists():
    app.mount("/", StaticFiles(directory=RAIZ / "web", html=True), name="web")
