"""Utilidades compartidas del pipeline: rutas, configuración, red y geometría."""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import shapely
import yaml
from pyproj import Transformer

RAIZ = Path(__file__).resolve().parents[1]
RUTA_CONFIG = RAIZ / "config.yml"
RAW = RAIZ / "data" / "raw"          # descargas e intermedios; no se publican
WEB_DATA = RAIZ / "web" / "data"     # resultados que lee la página
CABECERAS = {"User-Agent": "PulmonUrbano/0.1 (prototipo academico de hackathon)"}

# UTM 19S, como pide el informe. Sirve para Chile central; más al sur habría que cambiar de zona.
EPSG_METRICO = 32719
_A_UTM = Transformer.from_crs(4326, EPSG_METRICO, always_xy=True)
_A_WGS = Transformer.from_crs(EPSG_METRICO, 4326, always_xy=True)


def cargar_config() -> dict[str, Any]:
    return yaml.safe_load(RUTA_CONFIG.read_text(encoding="utf-8"))


def cargar_env(ruta: Path | None = None) -> None:
    """Lee CLAVE=valor desde .env (no se sube al repositorio) sin pisar variables ya definidas."""
    archivo = ruta or (RAIZ / ".env")
    if not archivo.exists():
        return
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        clave = clave.strip().removeprefix("export ").strip()
        valor = valor.strip().strip("\"'")
        if clave and valor:
            os.environ.setdefault(clave, valor)


def fecha_proceso() -> date:
    """Devuelve PULMON_FECHA_PROCESO (YYYY-MM-DD) si está definida; si no, la fecha actual."""
    fija = os.environ.get("PULMON_FECHA_PROCESO", "").strip()
    if fija:
        return date.fromisoformat(fija)
    return date.today()


def slug_de(nombre: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", sin_tildes.lower()).strip("_")


def dir_raw(slug: str) -> Path:
    ruta = RAW / slug
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def dir_web(slug: str) -> Path:
    ruta = WEB_DATA / slug
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def leer_json(ruta: Path) -> Any:
    return json.loads(ruta.read_text(encoding="utf-8"))


def escribir_json(ruta: Path, obj: Any, compacto: bool = True) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if compacto:
        texto = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    else:
        texto = json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)
    ruta.write_text(texto, encoding="utf-8")


def escribir_js(ruta: Path, clave: str, obj: Any) -> None:
    """Escribe los datos como script, para que la página funcione abierta con doble clic (file://)."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    cuerpo = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    ruta.write_text(
        f"window.PU_DATOS=window.PU_DATOS||{{}};window.PU_DATOS[{json.dumps(clave)}]={cuerpo};\n",
        encoding="utf-8",
    )


def pedir(metodo: str, url: str, intentos: int = 4, espera: float = 4.0, **kwargs: Any) -> httpx.Response:
    """Petición HTTP con reintentos; lanza la última excepción si todos fallan."""
    kwargs.setdefault("timeout", 90)
    kwargs.setdefault("headers", CABECERAS)
    ultimo: Exception | None = None
    for intento in range(intentos):
        try:
            resp = httpx.request(metodo, url, follow_redirects=True, **kwargs)
            resp.raise_for_status()
            return resp
        except Exception as exc:  # noqa: BLE001 - se reintenta ante cualquier fallo de red
            ultimo = exc
            time.sleep(espera * (intento + 1))
    raise RuntimeError(f"No se pudo obtener {url}: {ultimo!r}")


def a_utm(geom: shapely.Geometry) -> shapely.Geometry:
    return shapely.transform(geom, lambda c: np.column_stack(_A_UTM.transform(c[:, 0], c[:, 1])))


def a_wgs(geom: shapely.Geometry) -> shapely.Geometry:
    return shapely.transform(geom, lambda c: np.column_stack(_A_WGS.transform(c[:, 0], c[:, 1])))


def punto_a_utm(lon: float, lat: float) -> tuple[float, float]:
    x, y = _A_UTM.transform(lon, lat)
    return float(x), float(y)


def solo_poligonos(geom: shapely.Geometry) -> shapely.Geometry:
    """Deja solo las partes poligonales de una geometría (tras recortes o reparaciones)."""
    if geom.is_empty:
        return shapely.Polygon()
    if geom.geom_type in ("Polygon", "MultiPolygon"):
        return geom
    partes = [g for g in getattr(geom, "geoms", []) if g.geom_type in ("Polygon", "MultiPolygon")]
    return shapely.unary_union(partes) if partes else shapely.Polygon()


def redondear(valor: float | None, decimales: int = 3) -> float | None:
    if valor is None or not np.isfinite(valor):
        return None
    return round(float(valor), decimales)
