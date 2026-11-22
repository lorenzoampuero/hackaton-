"""Lectura de Sentinel-2 L2A desde AWS Earth Search: escenas, reflectancia y grilla de la comuna.

Reflectancia: Earth Search declara `offset: -0.1` en los metadatos de cada banda, pero en estos
COG el offset suele venir YA restado en los píxeles. La bandera `earthsearch:boa_offset_applied`
no es confiable: en la RM, unas 11 de 180 escenas (sobre todo Sentinel-2C de nov-2024 a mar-2025)
dicen `false` y sus píxeles son iguales a los de las escenas que dicen `true`. Restar el offset
de nuevo infla el NDVI (se vieron valores de 0,79 y hasta 1,0 donde las fechas vecinas dan 0,38).
Por eso se decide con los píxeles (ver `offset_pendiente`) y se registra cuando la bandera se contradice.
"""

from __future__ import annotations

import math
from datetime import date
from typing import Any

import numpy as np
import rasterio
from affine import Affine
from rasterio.features import geometry_mask
from rasterio.windows import Window, from_bounds
from shapely.geometry import shape

ENTORNO_GDAL = {
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif",
    "GDAL_HTTP_MAX_RETRY": "4",
    "GDAL_HTTP_RETRY_DELAY": "2",
    "GDAL_HTTP_TIMEOUT": "60",
    "AWS_NO_SIGN_REQUEST": "YES",
}
FRACCION_VALIDA_MINIMA = 0.5  # con más de la mitad del sitio tapado, la mediana no es confiable


VERSION_METODO = 2            # entra en la firma del caché: al cambiar el método, se recalcula
PIXELES_MINIMOS_PRUEBA = 500  # con menos píxeles válidos no se puede juzgar el offset


def offset_pendiente(rojo_crudo: np.ndarray, valido: np.ndarray, banda: dict | None) -> bool | None:
    """¿Falta restar el offset de reflectancia? Se decide con los píxeles de la banda roja.

    Si el offset (1000 números digitales) aún no se restó, casi ningún píxel puede valer menos de
    1000, porque sería reflectancia negativa. Si el percentil 1 de los píxeles válidos está bajo
    ese valor, el offset ya viene restado. Devuelve None si no hay píxeles suficientes para juzgar.
    """
    escala = float((banda or {}).get("scale", 0.0001))
    offset = float((banda or {}).get("offset", 0.0))
    if offset >= 0:
        return False
    muestra = rojo_crudo[valido & (rojo_crudo > 0)]
    if muestra.size < PIXELES_MINIMOS_PRUEBA:
        return None
    return bool(np.percentile(muestra, 1) >= -offset / escala)


def escala_y_offset(banda: dict | None, falta_offset: bool) -> tuple[float, float]:
    """Escala y offset para pasar de número digital a reflectancia (ver nota del módulo)."""
    escala = float((banda or {}).get("scale", 0.0001))
    offset = float((banda or {}).get("offset", 0.0)) if falta_offset else 0.0
    return escala, offset


def indice_normalizado(a: np.ndarray, b: np.ndarray, valido: np.ndarray) -> np.ndarray:
    """(a − b) / (a + b), con NaN donde no hay dato válido o el denominador no es positivo."""
    suma = a + b
    ok = valido & (suma > 0)
    salida = np.full(a.shape, np.nan, dtype=np.float32)
    salida[ok] = (a[ok] - b[ok]) / suma[ok]
    return salida


def mediana_valida(valores: np.ndarray, minimo: int, total: int) -> tuple[float | None, int]:
    """Mediana de los valores finitos si hay suficientes píxeles y suficiente fracción del sitio."""
    finitos = valores[np.isfinite(valores)]
    n = int(finitos.size)
    if n < minimo or total == 0 or n / total < FRACCION_VALIDA_MINIMA:
        return None, n
    return float(np.median(finitos)), n


def inicio_historia(hoy: date, meses: int) -> date:
    """Primer día del mes que queda `meses` meses antes de `hoy`."""
    total = hoy.year * 12 + (hoy.month - 1) - meses
    return date(total // 12, total % 12 + 1, 1)


def elegir_escenas(items: list, recuadro) -> list:
    """Una sola grilla MGRS (la que más veces cubre toda la comuna) y una escena por día."""
    por_grilla: dict[str, list] = {}
    for item in items:
        if item.geometry and shape(item.geometry).contains(recuadro):
            por_grilla.setdefault(item.properties.get("grid:code", "?"), []).append(item)
    if not por_grilla:
        return []
    grilla = max(por_grilla, key=lambda g: len(por_grilla[g]))
    por_dia: dict[str, Any] = {}
    for item in sorted(por_grilla[grilla], key=lambda i: i.id):
        por_dia[item.properties["datetime"][:10]] = item  # si hay reprocesos, gana el último id
    return [por_dia[d] for d in sorted(por_dia)]


def leer(href: str, ventana: Window) -> np.ndarray:
    ultimo: Exception | None = None
    for _ in range(3):
        try:
            with rasterio.open(href) as ds:
                return ds.read(1, window=ventana)
        except Exception as exc:  # noqa: BLE001 - lecturas remotas: se reintenta
            ultimo = exc
    raise RuntimeError(f"No se pudo leer {href}: {ultimo!r}")


def metadatos_banda(item, clave: str) -> dict | None:
    return (item.assets[clave].to_dict().get("raster:bands") or [None])[0]


def a_reflectancia(crudo: np.ndarray, banda: dict | None, falta_offset: bool) -> tuple[np.ndarray, np.ndarray]:
    """Devuelve la reflectancia y la máscara de píxeles con dato."""
    escala, offset = escala_y_offset(banda, falta_offset)
    return crudo.astype(np.float32) * escala + offset, crudo > 0


def reflectancia(item, clave: str, ventana: Window, falta_offset: bool) -> tuple[np.ndarray, np.ndarray]:
    return a_reflectancia(leer(item.assets[clave].href, ventana), metadatos_banda(item, clave), falta_offset)


def juzgar_offset(item, rojo_crudo: np.ndarray, valido10: np.ndarray) -> tuple[bool, str]:
    """Decide si falta restar el offset y devuelve también cómo se decidió."""
    bandera_aplicado = bool(item.properties.get("earthsearch:boa_offset_applied"))
    falta = offset_pendiente(rojo_crudo, valido10, metadatos_banda(item, "red"))
    if falta is None:  # escena casi toda nublada en la comuna: no hay con qué juzgar
        return (not bandera_aplicado), "bandera_sin_verificar"
    return falta, ("pixeles" if falta == (not bandera_aplicado) else "pixeles_contradicen_bandera")


class Grilla:
    """Ventana de la comuna en la grilla de 20 m de la escena y su equivalente de 10 m."""

    def __init__(self, item, limites_utm: tuple[float, float, float, float]) -> None:
        with rasterio.Env(**ENTORNO_GDAL), rasterio.open(item.assets["scl"].href) as ds:
            self.transform_escena = ds.transform
            v = from_bounds(*limites_utm, ds.transform)
            col, fila = max(0, math.floor(v.col_off)), max(0, math.floor(v.row_off))
            ancho = min(ds.width, math.ceil(v.col_off + v.width)) - col
            alto = min(ds.height, math.ceil(v.row_off + v.height)) - fila
            self.v20 = Window(col, fila, ancho, alto)
            self.t20 = ds.window_transform(self.v20)
        self.v10 = Window(col * 2, fila * 2, ancho * 2, alto * 2)
        self.t10 = self.t20 * Affine.scale(0.5)
        self.forma20, self.forma10 = (alto, ancho), (alto * 2, ancho * 2)

    def indices(self, geom, resolucion: int) -> np.ndarray:
        """Índices (aplanados) de los píxeles cuyo centro cae dentro de la geometría."""
        if geom.is_empty:
            return np.empty(0, dtype=np.int64)
        forma, transform = (self.forma10, self.t10) if resolucion == 10 else (self.forma20, self.t20)
        return np.flatnonzero(geometry_mask([geom], out_shape=forma, transform=transform, invert=True))
