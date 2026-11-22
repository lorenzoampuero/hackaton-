"""Servidor local mínimo: sirve la página y redacta informes con IA sin exponer la clave al navegador.

Es el «modo B» del informe v4 (proxy mínimo). La página sigue funcionando sin él (doble clic o
`python -m http.server`), mostrando los informes pre-generados y verificados.

  .venv/bin/uvicorn app.servidor:app --port 8765
"""

from __future__ import annotations

import importlib
import os
import threading
import time
from collections import deque
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pipeline.comun import RAIZ, WEB_DATA, cargar_config, cargar_env, leer_json

mod_05 = importlib.import_module("pipeline.05_senales")
mod_06 = importlib.import_module("pipeline.06_paquete_caso")
mod_07 = importlib.import_module("pipeline.07_informe_ia")

app = FastAPI(title="Pulmón Urbano — servidor local", docs_url=None, redoc_url=None)

_llamadas: deque[float] = deque()
_candado = threading.Lock()


class PedidoInforme(BaseModel):
    ambito: str | None = None      # cartera: "intercomunal" o el slug de una comuna
    caso_id: str | None = None     # uno de los casos del pitch
    comuna_slug: str | None = None # ficha individual por comuna y site_id
    site_id: str | None = None


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
    maximo = int(os.environ.get("PULMON_IA_MAX_HORA", "30"))
    ahora = time.time()
    with _candado:
        while _llamadas and ahora - _llamadas[0] > 3600:
            _llamadas.popleft()
        if len(_llamadas) >= maximo:
            return False
        _llamadas.append(ahora)
        return True


@app.get("/api/estado")
def estado() -> dict[str, Any]:
    prov = mod_07.proveedor_configurado()
    return {
        "servidor": True,
        "ia_disponible": prov is not None,
        "proveedor": prov[0] if prov else None,
        "modelo": prov[1] if prov else None,
    }


@app.post("/api/informe")
def informe(pedido: PedidoInforme) -> dict[str, Any]:
    paquete = _buscar_paquete(pedido)
    if paquete is None:
        raise HTTPException(status_code=404, detail="No existe un paquete de datos para ese ámbito o caso.")
    if mod_07.proveedor_configurado() is None:
        raise HTTPException(status_code=503, detail="Falta la clave de API: crea el archivo .env a partir de .env.example.")
    if not _hay_cupo():
        raise HTTPException(status_code=429, detail="Se alcanzó el límite de informes con IA por hora.")
    resultado, diagnostico = mod_07.generar_informe_detallado(paquete)
    return {"informe": resultado, "diagnostico": diagnostico}


app.mount("/", StaticFiles(directory=RAIZ / "web", html=True), name="web")
