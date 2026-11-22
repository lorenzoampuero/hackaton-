"""Recortes de imagen por sitio: color real y NDVI de Sentinel-2, con escala fija y contorno.

Contiene datos modificados de Copernicus Sentinel. No se usan imágenes de Google.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import rasterio
from PIL import Image, ImageDraw

from pipeline import s2

REFLECTANCIA_MAX_COLOR = 0.30  # escala fija del color real
# Escala fija del NDVI (valor, color); la página usa la misma para la leyenda.
RAMPA_NDVI = [
    (-0.2, (140, 81, 10)), (0.0, (216, 179, 101)), (0.15, (246, 232, 195)), (0.3, (199, 233, 192)),
    (0.5, (90, 174, 97)), (0.7, (27, 120, 55)), (0.9, (0, 68, 27)),
]


GAMMA_COLOR = 1.35       # antes 1,8: dejaba la ciudad casi blanca
SATURACION_COLOR = 1.35  # separa mejor pasto, tierra y techos


def color_real(rojo: np.ndarray, verde: np.ndarray, azul: np.ndarray) -> np.ndarray:
    """Color natural con escala fija (comparable entre fechas), gamma suave y algo más de saturación."""
    rgb = np.stack([rojo, verde, azul], axis=-1).astype(np.float32)
    rgb = np.clip(rgb / REFLECTANCIA_MAX_COLOR, 0, 1) ** (1 / GAMMA_COLOR)
    luz = rgb.mean(axis=-1, keepdims=True)
    rgb = np.clip(luz + (rgb - luz) * SATURACION_COLOR, 0, 1)
    return (rgb * 255).astype(np.uint8)


def color_ndvi(ndvi: np.ndarray) -> np.ndarray:
    paradas = np.array([p[0] for p in RAMPA_NDVI])
    canales = [np.interp(ndvi, paradas, [p[1][c] for p in RAMPA_NDVI]) for c in range(3)]
    rgb = np.stack(canales, axis=-1)
    rgb[~np.isfinite(ndvi)] = 200  # gris: sin dato
    return rgb.astype(np.uint8)


def _contornos(geom) -> list:
    partes = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    return [anillo for p in partes for anillo in [p.exterior, *p.interiors]]


def elegir_fechas_imagen(escenas: list[dict], cfg: dict) -> list[str]:
    """La escena limpia más reciente y la limpia más cercana a un año antes (±45 días)."""
    minimo = cfg["imagenes"]["comuna_valida_min_pct"]
    limpias = [e for e in escenas if (e["comuna_valida_pct"] or 0) >= minimo]
    if not limpias:
        return []
    reciente = limpias[-1]["fecha"]
    objetivo = date.fromisoformat(reciente) - timedelta(days=365)
    cercanas = [(abs((date.fromisoformat(e["fecha"]) - objetivo).days), e["fecha"]) for e in limpias[:-1]]
    cercanas = [c for c in cercanas if c[0] <= 45]
    return ([min(cercanas)[1]] if cercanas else []) + [reciente]


def guardar_recortes(item, grilla: s2.Grilla, sitios: list[dict], carpeta, cfg: dict, falta_offset: bool) -> int:
    """Color real y NDVI de cada sitio para una escena; devuelve cuántos sitios se dibujaron."""
    fecha = item.properties["datetime"][:10]
    pendientes = [s for s in sitios if not (carpeta / s["site_id"] / f"{fecha}_ndvi.png").exists()]
    if not pendientes:
        return 0
    with rasterio.Env(**s2.ENTORNO_GDAL):
        bandas = {
            c: s2.reflectancia(item, c, grilla.v10, falta_offset)[0] for c in ("red", "green", "blue", "nir")
        }
    color = color_real(bandas["red"], bandas["green"], bandas["blue"])
    con_dato = (bandas["red"] != 0) | (bandas["nir"] != 0)
    ndvi = color_ndvi(s2.indice_normalizado(bandas["nir"], bandas["red"], con_dato))
    alto, ancho = grilla.forma10
    margen, lado = cfg["imagenes"]["margen_m"], cfg["imagenes"]["lado_px"]
    x_origen, y_origen = grilla.t10.c, grilla.t10.f
    for sitio in pendientes:
        geom = sitio["geom_utm"]
        minx, miny, maxx, maxy = geom.bounds
        medio = max(maxx - minx, maxy - miny) / 2 + margen
        cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
        c0 = max(0, int((cx - medio - x_origen) // 10))
        c1 = min(ancho, int((cx + medio - x_origen) // 10) + 1)
        f0 = max(0, int((y_origen - cy - medio) // 10))
        f1 = min(alto, int((y_origen - cy + medio) // 10) + 1)
        if c1 - c0 < 3 or f1 - f0 < 3:
            continue
        factor = lado / max(c1 - c0, f1 - f0)
        salida = (round((c1 - c0) * factor), round((f1 - f0) * factor))
        destino = carpeta / sitio["site_id"]
        destino.mkdir(parents=True, exist_ok=True)
        for nombre, matriz in (("color", color), ("ndvi", ndvi)):
            imagen = Image.fromarray(np.ascontiguousarray(matriz[f0:f1, c0:c1])).resize(salida, Image.NEAREST)
            lapiz = ImageDraw.Draw(imagen)
            for anillo in _contornos(geom):
                puntos = [
                    (((x - x_origen) / 10 - c0) * factor, ((y_origen - y) / 10 - f0) * factor)
                    for x, y in anillo.coords
                ]
                lapiz.line(puntos, fill=(0, 0, 0), width=4)
                lapiz.line(puntos, fill=(255, 255, 255), width=2)
            imagen.save(destino / f"{fecha}_{nombre}.png", optimize=True)
    return len(pendientes)
