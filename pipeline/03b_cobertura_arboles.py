"""Paso 3b: cobertura de árboles alrededor de cada sitio con ESA WorldCover 10 m.

Para el entorno de cada sitio (polígono ampliado `sitios.radio_entorno_m`) se calcula el porcentaje
de píxeles de clase 10 (árboles), la brecha frente a la meta de `dosel.meta_pct` y un rango de
árboles y de costo. El rango de copa y el costo por árbol son HIPÓTESIS sin verificar.
El mapa es de 2021 y no se actualiza solo. © ESA WorldCover project 2021, CC BY 4.0.
Salida: data/raw/<slug>/paso03b.json
"""

from __future__ import annotations

import math

import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds
from shapely.geometry import shape

from pipeline import comun

BASE = "https://esa-worldcover.s3.eu-central-1.amazonaws.com"
ENTORNO_GDAL = {
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif",
    "GDAL_HTTP_MAX_RETRY": "4",
    "GDAL_HTTP_RETRY_DELAY": "2",
    "AWS_NO_SIGN_REQUEST": "YES",
}


def url_mosaico(lon: float, lat: float, cfg: dict) -> str:
    """Los mosaicos de WorldCover miden 3° y se nombran por su esquina suroeste."""
    wc = cfg["worldcover"]
    sur, oeste = math.floor(lat / 3) * 3, math.floor(lon / 3) * 3
    ns = f"{'S' if sur < 0 else 'N'}{abs(sur):02d}"
    eo = f"{'W' if oeste < 0 else 'E'}{abs(oeste):03d}"
    return f"{BASE}/{wc['version']}/{wc['anio']}/map/ESA_WorldCover_10m_{wc['anio']}_{wc['version']}_{ns}{eo}_Map.tif"


def brecha_dosel(area_entorno_m2: float, cobertura_pct: float, cfg: dict) -> dict:
    """Brecha a la meta, y rango de árboles y de costo (hipótesis)."""
    dosel = cfg["dosel"]
    brecha_m2 = max(0.0, dosel["meta_pct"] / 100 * area_entorno_m2 - cobertura_pct / 100 * area_entorno_m2)
    minimo = math.ceil(brecha_m2 / dosel["copa_m2_max"])
    maximo = math.ceil(brecha_m2 / dosel["copa_m2_min"])
    return {
        "brecha_dosel_puntos": comun.redondear(max(0.0, dosel["meta_pct"] - cobertura_pct), 1),
        "brecha_dosel_ha": comun.redondear(brecha_m2 / 1e4, 2),
        "arboles_necesarios_min": minimo,
        "arboles_necesarios_max": maximo,
        "costo_clp_min": minimo * dosel["costo_arbol_clp_min"],
        "costo_clp_max": maximo * dosel["costo_arbol_clp_max"],
    }


def ejecutar(comuna: dict, cfg: dict) -> None:
    slug, nombre = comuna["slug"], comuna["nombre"]
    raw = comun.dir_raw(slug)
    paso01 = comun.leer_json(raw / "paso01.json")
    radio = cfg["sitios"]["radio_entorno_m"]
    clase = cfg["worldcover"]["clase_arboles"]
    lon, lat = paso01["comuna"]["centro"]
    url = url_mosaico(lon, lat, cfg)

    entornos = {s["site_id"]: comun.a_utm(shape(s["geometria"])).buffer(radio) for s in paso01["sitios"]}
    limite_utm = comun.a_utm(shape(comun.leer_json(raw / "limite.geojson")["geometry"]))
    oeste, sur, este, norte = comun.a_wgs(limite_utm.buffer(radio + 100)).bounds
    with rasterio.Env(**ENTORNO_GDAL), rasterio.open(url) as ds:
        if not (ds.bounds.left <= oeste and este <= ds.bounds.right and ds.bounds.bottom <= sur and norte <= ds.bounds.top):
            raise RuntimeError(f"{nombre} cruza dos mosaicos de WorldCover; este prototipo lee solo uno.")
        ventana = from_bounds(oeste, sur, este, norte, ds.transform).round_offsets().round_lengths()
        cobertura = ds.read(1, window=ventana)
        transform = ds.window_transform(ventana)
    arboles = cobertura == clase
    con_dato = cobertura != 0

    def porcentaje(geom_utm) -> float | None:
        mascara = geometry_mask([comun.a_wgs(geom_utm)], out_shape=cobertura.shape, transform=transform, invert=True)
        total = int((mascara & con_dato).sum())
        return 100.0 * int((mascara & arboles).sum()) / total if total else None

    sitios = {}
    for site_id, entorno in entornos.items():
        pct = porcentaje(entorno)
        if pct is None:
            sitios[site_id] = {"cobertura_arboles_400m_pct": None}
            continue
        sitios[site_id] = {"cobertura_arboles_400m_pct": comun.redondear(pct, 1), **brecha_dosel(entorno.area, pct, cfg)}

    pct_comuna = porcentaje(limite_utm)
    comun.escribir_json(raw / "paso03b.json", {
        "fuente": f"ESA WorldCover 10 m, {cfg['worldcover']['anio']} ({cfg['worldcover']['version']})",
        "url": url,
        "licencia": "CC BY 4.0",
        "fecha_consulta": comun.fecha_proceso().isoformat(),
        "nota": "Mapa de 2021; la clase 10 (árboles) a 10 m subestima el arbolado de calle aislado.",
        "cobertura_arboles_comuna_pct": comun.redondear(pct_comuna, 1),
        "sitios": sitios,
    })
    print(f"  [03b] {nombre}: árboles en la comuna {pct_comuna:.1f} % (WorldCover {cfg['worldcover']['anio']}).")
