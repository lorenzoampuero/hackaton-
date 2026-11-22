"""Paso 1: límite comunal y áreas verdes desde OpenStreetMap (Overpass).

Salidas en data/raw/<slug>/: limite.geojson, verde_todo.json (para el verde per cápita) y
paso01.json (sitios de más de `sitios.area_minima_m2`, recortados al límite comunal).
Datos © colaboradores de OpenStreetMap, licencia ODbL.
"""

from __future__ import annotations

import time
from typing import Any

import httpx
import shapely
from shapely.geometry import LineString, Polygon, mapping
from shapely.ops import polygonize, unary_union
from shapely.strtree import STRtree

from pipeline import comun

SERVIDORES = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
CLASES_PARQUE = {"park", "garden"}
CLASES_CESPED = {"grass", "village_green"}


def consultar_overpass(consulta: str, cache) -> dict[str, Any]:
    if cache.exists():
        return comun.leer_json(cache)
    ultimo = None
    for vuelta in range(5):
        for servidor in SERVIDORES:
            try:
                resp = httpx.post(servidor, data={"data": consulta}, timeout=180, headers=comun.CABECERAS)
                resp.raise_for_status()
                datos = resp.json()
                if "elements" in datos:
                    comun.escribir_json(cache, datos)
                    return datos
            except Exception as exc:  # noqa: BLE001 - Overpass falla seguido; se prueba otro servidor
                ultimo = exc
                print(f"    Overpass falló en {servidor.split('/')[2]}: {repr(exc)[:90]}", flush=True)
                time.sleep(6 + 4 * vuelta)
    raise RuntimeError(f"Overpass no respondió tras varios intentos: {ultimo!r}")


def _lineas(miembros: list[dict], rol_interior: bool) -> list[LineString]:
    return [
        LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
        for m in miembros
        if m.get("type") == "way" and m.get("geometry") and len(m["geometry"]) >= 2
        and (m.get("role") == "inner") == rol_interior
    ]


def geometria_elemento(elem: dict) -> shapely.Geometry | None:
    """Convierte una vía cerrada o una relación multipolígono de Overpass en un polígono WGS84."""
    if elem["type"] == "way":
        puntos = [(p["lon"], p["lat"]) for p in elem.get("geometry") or []]
        if len(puntos) < 4 or puntos[0] != puntos[-1]:
            return None
        geom = shapely.make_valid(Polygon(puntos))
    elif elem["type"] == "relation":
        exteriores = _lineas(elem.get("members", []), rol_interior=False)
        if not exteriores:
            return None
        geom = unary_union(list(polygonize(unary_union(exteriores))))
        interiores = _lineas(elem.get("members", []), rol_interior=True)
        if interiores:
            geom = geom.difference(unary_union(list(polygonize(unary_union(interiores)))))
    else:
        return None
    geom = comun.solo_poligonos(geom)
    return None if geom.is_empty else geom


def clasificar_tipo(nombre: str, clase: str, area_m2: float, geom_utm: shapely.Geometry) -> str:
    """Tipo estimado por nombre y forma; es una heurística, no un dato de OSM."""
    bajo = nombre.lower()
    if "bandej" in bajo:
        return "bandejon"
    if bajo.startswith("plaza") or bajo.startswith("plazoleta"):
        return "plaza"
    if bajo.startswith("parque"):
        return "parque"
    compacidad = 12.566 * area_m2 / (geom_utm.length ** 2) if geom_utm.length else 1.0
    if clase in CLASES_CESPED and compacidad < 0.15:
        return "bandejon"
    return "parque" if area_m2 >= 5000 else "plaza"


def descargar_limite(nombre: str, cfg: dict, raw) -> tuple[shapely.Geometry, dict]:
    sur, oeste, norte, este = cfg["region_bbox"]
    consulta = (
        f'[out:json][timeout:120];relation["boundary"="administrative"]["admin_level"="8"]'
        f'["name"="{nombre}"]({sur},{oeste},{norte},{este});out geom;'
    )
    datos = consultar_overpass(consulta, raw / "osm_limite.json")
    relaciones = [e for e in datos["elements"] if e["type"] == "relation"]
    if not relaciones:
        raise RuntimeError(f"OSM no tiene una comuna llamada '{nombre}' dentro de region_bbox.")
    if len(relaciones) > 1:
        print(f"    Aviso: {len(relaciones)} comunas llamadas '{nombre}'; se usa la primera.")
    limite = geometria_elemento(relaciones[0])
    if limite is None:
        raise RuntimeError(f"No se pudo armar el límite de '{nombre}'.")
    return limite, relaciones[0].get("tags", {})


def descargar_verdes(limite_utm: shapely.Geometry, cfg: dict, raw) -> list[dict]:
    """Áreas verdes públicas dentro de la comuna y de un margen (para el entorno de 400 m)."""
    margen = cfg["sitios"]["radio_entorno_m"] + 100
    oe, su, es, no = comun.a_wgs(limite_utm.buffer(margen)).bounds
    recuadro = f"{su:.5f},{oe:.5f},{no:.5f},{es:.5f}"
    consulta = (
        "[out:json][timeout:170];("
        f'way["leisure"~"^(park|garden)$"]({recuadro});'
        f'relation["leisure"~"^(park|garden)$"]({recuadro});'
        f'way["landuse"~"^(grass|village_green)$"]({recuadro});'
        f'relation["landuse"~"^(grass|village_green)$"]({recuadro});'
        ");out geom;"
    )
    datos = consultar_overpass(consulta, raw / "osm_verde.json")
    verdes: list[dict] = []
    for elem in datos["elements"]:
        tags = elem.get("tags", {})
        if tags.get("access") in ("private", "no") or tags.get("garden:type") == "residential":
            continue
        geom = geometria_elemento(elem)
        if geom is None:
            continue
        geom_utm = comun.solo_poligonos(shapely.make_valid(comun.a_utm(geom)))
        if geom_utm.is_empty:
            continue
        verdes.append({
            "osm_tipo": elem["type"], "osm_id": elem["id"], "nombre": (tags.get("name") or "").strip(),
            "clase": tags.get("leisure") or tags.get("landuse"), "geom": geom_utm,
        })
    return verdes


def quitar_cesped_dentro_de_parques(verdes: list[dict]) -> list[dict]:
    """El césped mapeado dentro de un parque duplicaría superficie: se descarta."""
    parques = [v for v in verdes if v["clase"] in CLASES_PARQUE]
    if not parques:
        return verdes
    arbol = STRtree([p["geom"] for p in parques])
    unicos = []
    for verde in verdes:
        if verde["clase"] in CLASES_CESPED and verde["geom"].area > 0:
            dentro = sum(
                verde["geom"].intersection(parques[i]["geom"]).area for i in arbol.query(verde["geom"])
            )
            if dentro / verde["geom"].area >= 0.8:
                continue
        unicos.append(verde)
    return unicos


def armar_sitios(verdes: list[dict], limite_utm: shapely.Geometry, slug: str, nombre: str, cfg: dict) -> list[dict]:
    minimo = cfg["sitios"]["area_minima_m2"]
    prefijo = "".join(parte[0] for parte in slug.split("_"))[:3]
    sitios = []
    for verde in verdes:
        recorte = comun.solo_poligonos(verde["geom"].intersection(limite_utm))
        if recorte.is_empty or recorte.area < minimo:
            continue
        simple = comun.solo_poligonos(recorte.simplify(1.0))
        if simple.is_empty:
            continue
        nombre_sitio = verde["nombre"] or f"Área verde sin nombre (OSM {verde['osm_id']})"
        centro = comun.a_wgs(simple.representative_point())
        sitios.append({
            "site_id": f"{prefijo}-{verde['osm_tipo'][0]}{verde['osm_id']}",
            "nombre": nombre_sitio,
            "con_nombre": bool(verde["nombre"]),
            "tipo": clasificar_tipo(nombre_sitio, verde["clase"], recorte.area, recorte),
            "clase_osm": verde["clase"],
            "osm_url": f"https://www.openstreetmap.org/{verde['osm_tipo']}/{verde['osm_id']}",
            "comuna": nombre,
            "area_m2": round(recorte.area),
            "recortado_al_limite": bool(recorte.area < verde["geom"].area * 0.98),
            "centro": [round(centro.x, 6), round(centro.y, 6)],
            "geometria": mapping(shapely.set_precision(comun.a_wgs(simple), 1e-6)),
        })
    sitios.sort(key=lambda s: -s["area_m2"])
    return sitios


def ejecutar(comuna: dict, cfg: dict) -> None:
    slug, nombre = comuna["slug"], comuna["nombre"]
    raw = comun.dir_raw(slug)
    limite, etiquetas = descargar_limite(nombre, cfg, raw)
    limite_utm = comun.a_utm(limite)
    verdes = descargar_verdes(limite_utm, cfg, raw)
    unicos = quitar_cesped_dentro_de_parques(verdes)
    sitios = armar_sitios(unicos, limite_utm, slug, nombre, cfg)

    union_verde = unary_union([v["geom"] for v in unicos]) if unicos else Polygon()
    comun.escribir_json(raw / "verde_todo.json", mapping(shapely.set_precision(comun.a_wgs(union_verde), 1e-6)))
    comun.escribir_json(raw / "limite.geojson", {
        "type": "Feature", "properties": {"nombre": nombre},
        "geometry": mapping(shapely.set_precision(comun.a_wgs(limite_utm.simplify(5.0)), 1e-6)),
    })
    centro = limite.representative_point()
    comun.escribir_json(raw / "paso01.json", {
        "comuna": {
            "slug": slug, "nombre": nombre,
            "cut": etiquetas.get("ref:INE") or etiquetas.get("dpachile:id"),
            "area_km2": round(limite_utm.area / 1e6, 2),
            "bbox": [round(v, 6) for v in limite.bounds],
            "centro": [round(centro.x, 6), round(centro.y, 6)],
        },
        "fecha_consulta_osm": comun.fecha_proceso().isoformat(),
        "sitios": sitios,
    })
    umbral = cfg["confianza"]["area_minima_m2"]
    grandes = sum(1 for s in sitios if s["area_m2"] >= umbral)
    print(f"  [01] {nombre}: {len(sitios)} sitios de {cfg['sitios']['area_minima_m2']} m² o más "
          f"({grandes} sobre {umbral} m²); {len(verdes) - len(unicos)} céspedes dentro de parques descartados.")
