"""Paso 2: NDVI y NDMI por sitio con Sentinel-2 L2A (AWS Earth Search) y recortes de imagen.

Salidas:
  data/raw/<slug>/escenas_<firma>/<id>.json   caché por escena (permite reanudar)
  data/raw/<slug>/paso02.json                 observaciones por sitio y escenas usadas
  web/data/<slug>/img/<site_id>/<fecha>_color.png y <fecha>_ndvi.png

- El NDVI se calcula a 10 m y el NDMI en su grilla nativa de 20 m (B8A y B11), sin remuestrear.
- Cada sitio se achica `sitios.borde_interior_m` hacia adentro para no mezclar píxeles de borde.
- El offset de reflectancia se trata en pipeline/s2.py.
Contiene datos modificados de Copernicus Sentinel.
"""

from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import rasterio
from pystac_client import Client
from shapely.geometry import box, shape

from pipeline import comun, recortes, s2


def procesar_escena(item, grilla: s2.Grilla, mascaras: dict, idx_comuna: np.ndarray, cfg: dict) -> dict:
    descartar = cfg["sentinel2"]["scl_descartar"]
    minimo10 = cfg["sitios"]["pixeles_minimos"]
    minimo20 = max(2, round(minimo10 / 4))  # misma superficie mínima, en píxeles de 20 m
    with rasterio.Env(**s2.ENTORNO_GDAL):
        with rasterio.open(item.assets["scl"].href) as ds:
            if ds.transform != grilla.transform_escena:
                raise RuntimeError("la escena no comparte la grilla de referencia")
            scl = ds.read(1, window=grilla.v20)
        valido20 = ~np.isin(scl, descartar)
        scl10 = np.repeat(np.repeat(valido20, 2, axis=0), 2, axis=1)
        rojo_crudo = s2.leer(item.assets["red"].href, grilla.v10)
        falta_offset, criterio = s2.juzgar_offset(item, rojo_crudo, scl10)
        rojo, ok_rojo = s2.a_reflectancia(rojo_crudo, s2.metadatos_banda(item, "red"), falta_offset)
        nir, ok_nir = s2.reflectancia(item, "nir", grilla.v10, falta_offset)
        nir08, ok_nir08 = s2.reflectancia(item, "nir08", grilla.v20, falta_offset)
        swir, ok_swir = s2.reflectancia(item, "swir16", grilla.v20, falta_offset)
    valido10 = scl10 & ok_rojo & ok_nir
    ndvi = s2.indice_normalizado(nir, rojo, valido10).ravel()
    ndmi = s2.indice_normalizado(nir08, swir, valido20 & ok_nir08 & ok_swir).ravel()
    valores = {}
    for site_id, (idx10, idx20) in mascaras.items():
        v_ndvi, n10 = s2.mediana_valida(ndvi[idx10], minimo10, idx10.size)
        v_ndmi, n20 = s2.mediana_valida(ndmi[idx20], minimo20, idx20.size)
        valores[site_id] = [comun.redondear(v_ndvi, 4), comun.redondear(v_ndmi, 4), n10, n20]
    return {
        "id": item.id,
        "fecha": item.properties["datetime"][:10],
        "plataforma": item.properties.get("platform"),
        "nubes_escena_pct": comun.redondear(item.properties.get("eo:cloud_cover"), 1),
        "comuna_valida_pct": comun.redondear(100.0 * float(valido20.ravel()[idx_comuna].mean()), 1),
        "offset_restado_aqui": falta_offset,
        "criterio_offset": criterio,
        "valores": valores,
    }


def _preparar(comuna: dict, cfg: dict) -> tuple:
    """Lee el paso 1, busca las escenas y arma la grilla y las máscaras de cada sitio."""
    raw = comun.dir_raw(comuna["slug"])
    paso01 = comun.leer_json(raw / "paso01.json")
    sitios = paso01["sitios"]
    for sitio in sitios:
        sitio["geom_utm"] = comun.a_utm(shape(sitio["geometria"]))
    limite_utm = comun.a_utm(shape(comun.leer_json(raw / "limite.geojson")["geometry"]))
    cfg_s2 = cfg["sentinel2"]
    hoy = comun.fecha_proceso()
    desde = s2.inicio_historia(hoy, cfg_s2["meses_historia"])
    busqueda = Client.open(cfg_s2["stac_url"]).search(
        collections=[cfg_s2["coleccion"]], bbox=list(paso01["comuna"]["bbox"]),
        datetime=f"{desde.isoformat()}/{hoy.isoformat()}",
        query={"eo:cloud_cover": {"lt": cfg_s2["nubes_escena_max_pct"]}},
    )
    items = s2.elegir_escenas(list(busqueda.items()), box(*paso01["comuna"]["bbox"]))
    if not items:
        raise RuntimeError(f"Earth Search no devolvió escenas que cubran {comuna['nombre']}.")
    grilla = s2.Grilla(items[-1], limite_utm.buffer(cfg["imagenes"]["margen_m"] + 20).bounds)
    borde = cfg["sitios"]["borde_interior_m"]
    mascaras = {}
    for sitio in sitios:
        interior = sitio["geom_utm"].buffer(-borde)
        mascaras[sitio["site_id"]] = (grilla.indices(interior, 10), grilla.indices(interior, 20))
    return raw, sitios, items, grilla, mascaras, grilla.indices(limite_utm, 20), desde, hoy


def ejecutar(comuna: dict, cfg: dict) -> None:
    slug, nombre = comuna["slug"], comuna["nombre"]
    cfg_s2 = cfg["sentinel2"]
    raw, sitios, items, grilla, mascaras, idx_comuna, desde, hoy = _preparar(comuna, cfg)

    # La firma cambia si cambian los sitios o las reglas: así nunca se reutiliza un caché que no corresponde.
    firma = hashlib.sha1(repr((
        s2.VERSION_METODO, sorted(mascaras), cfg["sitios"]["borde_interior_m"], cfg_s2["scl_descartar"],
        cfg["sitios"]["pixeles_minimos"], s2.FRACCION_VALIDA_MINIMA, tuple(grilla.t20)[:6], grilla.forma20,
    )).encode()).hexdigest()[:8]
    cache = raw / f"escenas_{firma}"
    cache.mkdir(parents=True, exist_ok=True)

    def trabajo(item) -> dict | None:
        ruta = cache / f"{item.id}.json"
        if ruta.exists():
            return comun.leer_json(ruta)
        try:
            resultado = procesar_escena(item, grilla, mascaras, idx_comuna, cfg)
        except Exception as exc:  # noqa: BLE001 - una escena que falla no bota la comuna
            print(f"    escena {item.id} omitida: {repr(exc)[:120]}", flush=True)
            return None
        comun.escribir_json(ruta, resultado)
        return resultado

    print(f"  [02] {nombre}: {len(items)} escenas entre {desde} y {hoy}; procesando…", flush=True)
    with ThreadPoolExecutor(max_workers=cfg_s2["hilos"]) as grupo:
        escenas = [e for e in grupo.map(trabajo, items) if e]
    escenas.sort(key=lambda e: e["fecha"])
    if not escenas:
        raise RuntimeError(f"Ninguna escena se pudo leer para {nombre}.")
    omitidas = len(items) - len(escenas)

    fechas_imagen = recortes.elegir_fechas_imagen(escenas, cfg)
    medibles = [s for s in sitios if s["area_m2"] >= cfg["imagenes"]["area_minima_m2"]]
    carpeta = comun.dir_web(slug) / "img"
    por_id = {i.id: i for i in items}
    for escena in escenas:
        if escena["fecha"] in fechas_imagen:
            recortes.guardar_recortes(
                por_id[escena["id"]], grilla, medibles, carpeta, cfg, escena["offset_restado_aqui"]
            )
    contradicen = sum(1 for e in escenas if e["criterio_offset"] == "pixeles_contradicen_bandera")
    sin_verificar = sum(1 for e in escenas if e["criterio_offset"] == "bandera_sin_verificar")

    observaciones = {}
    for sitio in sitios:
        idx10, idx20 = mascaras[sitio["site_id"]]
        filas = []
        for escena in escenas:
            ndvi, ndmi, n10, _n20 = escena["valores"][sitio["site_id"]]
            no_valido = comun.redondear(100.0 * (1 - n10 / idx10.size), 1) if idx10.size else None
            filas.append([escena["fecha"], ndvi, ndmi, n10, no_valido])
        observaciones[sitio["site_id"]] = {
            "pixeles_10m": int(idx10.size), "pixeles_20m": int(idx20.size), "obs": filas,
        }

    comun.escribir_json(raw / "paso02.json", {
        "fuente": "Sentinel-2 L2A (Copernicus) vía AWS Earth Search",
        "stac_url": cfg_s2["stac_url"],
        "grilla": items[-1].properties.get("grid:code"),
        "desde": desde.isoformat(), "hasta": hoy.isoformat(),
        "escenas_omitidas_por_error": omitidas,
        "escenas_bandera_offset_contradicha": contradicen,
        "escenas_offset_sin_verificar": sin_verificar,
        "columnas_obs": ["fecha", "ndvi", "ndmi", "pixeles_validos_10m", "no_valido_pct"],
        "escenas": [{k: v for k, v in e.items() if k != "valores"} for e in escenas],
        "fechas_imagen": fechas_imagen,
        "sitios_con_imagen": [s["site_id"] for s in medibles],
        "sitios": observaciones,
    })
    con_dato = sum(1 for o in observaciones.values() if any(f[1] is not None for f in o["obs"]))
    print(f"  [02] {nombre}: {len(escenas)} escenas leídas ({omitidas} omitidas por error); "
          f"{con_dato} de {len(sitios)} sitios con NDVI; "
          f"offset: {contradicen} escenas con bandera contradicha por los píxeles, {sin_verificar} sin verificar; "
          f"imágenes de {', '.join(fechas_imagen) or 'ninguna fecha limpia'}.")
