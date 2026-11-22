"""Paso 3: población y personas de 60 años o más alrededor de cada sitio (Censo 2024, INE).

Fuente: teselas vectoriales por manzana que publica el visualizador del INE (archivo PMTiles).
El informe pedía 65+, pero esa capa publica el tramo de 60 años o más: se usa 60+ y se rotula así.
El "entorno" de un sitio es su polígono ampliado `sitios.radio_entorno_m` (400 m) hacia afuera.
La población de cada manzana se reparte en proporción al área que cae dentro del entorno.
Salida: data/raw/<slug>/paso03.json
"""

from __future__ import annotations

import gzip
import math

import httpx
import mapbox_vector_tile
import numpy as np
import shapely
from pmtiles.reader import Reader
from shapely.geometry import box, shape
from shapely.strtree import STRtree

from pipeline import comun

CAPA = "Manzanas_Entidades_CPV24"


def tesela_de(lon: float, lat: float, z: int) -> tuple[int, int]:
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n)
    return x, y


def limites_tesela(x: int, y: int, z: int) -> tuple[float, float, float, float]:
    """Recuadro (oeste, sur, este, norte) de una tesela en grados."""
    n = 2 ** z

    def lat(fila: float) -> float:
        return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * fila / n))))

    return x / n * 360.0 - 180.0, lat(y + 1), (x + 1) / n * 360.0 - 180.0, lat(y)


def _a_grados(geom, x: int, y: int, z: int, extension: int):
    """Pasa una geometría en coordenadas de tesela (y hacia abajo) a longitud y latitud."""
    n = 2 ** z

    def convertir(c):
        lon = (x + c[:, 0] / extension) / n * 360.0 - 180.0
        fila = (y + c[:, 1] / extension) / n
        lat = np.degrees(np.arctan(np.sinh(math.pi * (1 - 2 * fila))))
        return np.column_stack([lon, lat])

    return shapely.transform(geom, convertir)


class Teselas:
    """Lee teselas del PMTiles remoto con peticiones por rango, con caché en disco."""

    def __init__(self, url: str, carpeta) -> None:
        self.url, self.carpeta = url, carpeta
        self.cliente = httpx.Client(timeout=90, headers=comun.CABECERAS, follow_redirects=True)
        self.memoria: dict[tuple[int, int], bytes] = {}
        self.lector = Reader(self._bytes)
        carpeta.mkdir(parents=True, exist_ok=True)

    def _bytes(self, inicio: int, largo: int) -> bytes:
        clave = (inicio, largo)
        if clave not in self.memoria:
            resp = self.cliente.get(self.url, headers={"Range": f"bytes={inicio}-{inicio + largo - 1}"})
            resp.raise_for_status()
            self.memoria[clave] = resp.content
        return self.memoria[clave]

    def leer(self, z: int, x: int, y: int) -> bytes | None:
        ruta = self.carpeta / f"{z}_{x}_{y}.pbf"
        if ruta.exists():
            return ruta.read_bytes() or None
        ultimo: Exception | None = None
        for _ in range(4):
            try:
                datos = self.lector.get(z, x, y)
                break
            except Exception as exc:  # noqa: BLE001 - red inestable: se reintenta
                ultimo = exc
        else:
            raise RuntimeError(f"No se pudo leer la tesela {z}/{x}/{y} del Censo: {ultimo!r}")
        if datos and datos[:2] == b"\x1f\x8b":
            datos = gzip.decompress(datos)
        ruta.write_bytes(datos or b"")  # vacío = tesela sin manzanas
        return datos or None


def cargar_manzanas(recuadro_wgs: tuple[float, float, float, float], cfg: dict, carpeta) -> list[dict]:
    """Manzanas (en UTM) que tocan el recuadro, uniendo los trozos que quedaron en teselas distintas."""
    z = cfg["censo"]["zoom"]
    oeste, sur, este, norte = recuadro_wgs
    x0, y0 = tesela_de(oeste, norte, z)
    x1, y1 = tesela_de(este, sur, z)
    teselas = Teselas(cfg["censo"]["pmtiles_url"], carpeta)
    trozos: dict[int, dict] = {}
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            datos = teselas.leer(z, x, y)
            if not datos:
                continue
            capa = mapbox_vector_tile.decode(datos, default_options={"y_coord_down": True}).get(CAPA)
            if not capa:
                continue
            marco = box(*limites_tesela(x, y, z))
            for rasgo in capa["features"]:
                p = rasgo["properties"]
                if p.get("MANZENT") is None or not rasgo.get("geometry"):
                    continue
                geom = shapely.make_valid(shape(rasgo["geometry"]))
                geom = _a_grados(geom, x, y, z, capa["extent"]).intersection(marco)  # quita el borde repetido
                geom = comun.solo_poligonos(geom)
                if geom.is_empty:
                    continue
                dato = trozos.setdefault(p["MANZENT"], {
                    "id": p["MANZENT"], "cut": p.get("CUT"), "n_per": p.get("n_per") or 0,
                    "n_60": p.get("n_edad_60_mas"), "partes": [],
                })
                dato["partes"].append(geom)
    manzanas = []
    for dato in trozos.values():
        geom = comun.solo_poligonos(shapely.make_valid(comun.a_utm(shapely.unary_union(dato.pop("partes")))))
        if not geom.is_empty and geom.area > 0:
            manzanas.append({**dato, "geom": geom, "area": geom.area})
    return manzanas


def ejecutar(comuna: dict, cfg: dict) -> None:
    slug, nombre = comuna["slug"], comuna["nombre"]
    raw = comun.dir_raw(slug)
    paso01 = comun.leer_json(raw / "paso01.json")
    radio = cfg["sitios"]["radio_entorno_m"]
    limite_utm = comun.a_utm(shape(comun.leer_json(raw / "limite.geojson")["geometry"]))
    verde_utm = shapely.make_valid(comun.a_utm(shape(comun.leer_json(raw / "verde_todo.json"))))

    recuadro = comun.a_wgs(limite_utm.buffer(radio + 50)).bounds
    manzanas = cargar_manzanas(recuadro, cfg, comun.RAW / "_censo_teselas")
    if not manzanas:
        raise RuntimeError(f"El Censo no devolvió manzanas para {nombre}.")
    arbol = STRtree([m["geom"] for m in manzanas])

    sitios = {}
    for sitio in paso01["sitios"]:
        entorno = comun.a_utm(shape(sitio["geometria"])).buffer(radio)
        poblacion = mayores = poblacion_con_edad = 0.0
        for i in arbol.query(entorno):
            manzana = manzanas[i]
            if not manzana["n_per"]:
                continue
            fraccion = manzana["geom"].intersection(entorno).area / manzana["area"]
            if fraccion <= 0:
                continue
            poblacion += manzana["n_per"] * fraccion
            if manzana["n_60"] is not None:  # el INE omite el tramo de edad en algunas manzanas
                mayores += manzana["n_60"] * fraccion
                poblacion_con_edad += manzana["n_per"] * fraccion
        verde_m2 = verde_utm.intersection(entorno).area
        sitios[sitio["site_id"]] = {
            "area_entorno_ha": comun.redondear(entorno.area / 1e4, 1),
            "pop_400m": round(poblacion),
            "pct_60_mas_400m": comun.redondear(100 * mayores / poblacion_con_edad, 1) if poblacion_con_edad else None,
            "densidad_hab_ha": comun.redondear(poblacion / (entorno.area / 1e4), 1),
            "verde_osm_entorno_m2": round(verde_m2),
            "verde_per_capita_m2": comun.redondear(verde_m2 / poblacion, 2) if poblacion >= 1 else None,
        }

    en_comuna = [m for m in manzanas if m["geom"].representative_point().within(limite_utm)]
    comun.escribir_json(raw / "paso03.json", {
        "fuente": "INE, Censo de Población y Vivienda 2024, manzanas y entidades (teselas del visualizador)",
        "url": cfg["censo"]["pmtiles_url"],
        "fecha_consulta": comun.fecha_proceso().isoformat(),
        "nivel": "manzana",
        "nota_edad": "El dato por manzana publica el tramo de 60 años o más (no 65+).",
        "metodo": f"Entorno = polígono del sitio ampliado {radio} m; población repartida por área de intersección.",
        "poblacion_comuna_aprox": round(sum(m["n_per"] for m in en_comuna)),
        "manzanas_leidas": len(manzanas),
        "sitios": sitios,
    })
    sin_gente = sum(1 for s in sitios.values() if s["pop_400m"] == 0)
    print(f"  [03] {nombre}: {len(manzanas)} manzanas; población comunal aprox. "
          f"{round(sum(m['n_per'] for m in en_comuna)):,}".replace(",", ".")
          + f"; {sin_gente} sitios sin población en {radio} m.")
