"""Paso 02c: Enriquecimiento multi-satélite (Landsat 8/9 térmico LST °C, Sentinel-2 SAVI/NDMI/HD,
recuperación de plazas angostas, WorldCover superficie impermeable, CAMS Calidad del Aire y Censo térmico).
"""

from __future__ import annotations

import gzip
import importlib
import math
from typing import Any

import httpx
import mapbox_vector_tile
import numpy as np
import planetary_computer
import rasterio
import shapely
from PIL import Image, ImageDraw
from pyproj import Transformer
from pystac_client import Client
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds
from shapely.geometry import box, shape
from shapely.ops import transform as shp_transform

from pipeline import comun, recortes, s2

mod_03 = importlib.import_module("pipeline.03_censo_social")
mod_03b = importlib.import_module("pipeline.03b_cobertura_arboles")

PLANETARY_STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Rampas de alto contraste para visualización satelital nítida
RAMPA_LST = [
    (26.0, (44, 123, 182)),   # fresco relativo
    (31.0, (128, 205, 193)),  # templado
    (35.0, (254, 224, 139)),  # cálido
    (39.0, (244, 109, 67)),   # isla de calor alta
    (44.0, (165, 0, 38)),     # calor extremo
]

RAMPA_NDMI = [
    (-0.25, (140, 81, 10)),   # estrés hídrico foliar severo
    (-0.08, (216, 179, 101)), # seco
    (0.05, (245, 245, 245)),  # neutro
    (0.20, (128, 205, 193)),  # humedad media
    (0.45, (1, 102, 94)),     # alta humedad foliar
]

RAMPA_NDVI_HD = [
    (-0.05, (127, 59, 8)),
    (0.10, (216, 179, 101)),
    (0.22, (254, 224, 139)),
    (0.35, (166, 217, 106)),
    (0.55, (26, 152, 80)),
    (0.80, (0, 69, 41)),
]


REDIBUJAR = False  # True: vuelve a dibujar los PNG aunque existan (ver regenerar_imagenes)


def _colorear_rampa(arr: np.ndarray, rampa: list[tuple[float, tuple[int, int, int]]]) -> np.ndarray:
    paradas = np.array([p[0] for p in rampa], dtype=np.float32)
    canales = [np.interp(arr, paradas, [p[1][c] for p in rampa]) for c in range(3)]
    rgb = np.stack(canales, axis=-1)
    rgb[~np.isfinite(arr)] = 215
    return np.clip(rgb, 0, 255).astype(np.uint8)


def _limpiar(v: Any, dec: int = 2) -> float | None:
    if v is None:
        return None
    val = float(v)
    return comun.redondear(val, dec) if math.isfinite(val) else None


def _dibujar_recorte(
    matriz_rgb: np.ndarray,
    geom_crs,
    x0: float,
    y0: float,
    res_m: float,
    alto: int,
    ancho: int,
    ruta_png,
    margen_m: float = 90.0,
    lado_px: int = 480,
    forzar: bool = False,
) -> bool:
    if not (forzar or REDIBUJAR) and ruta_png.exists() and ruta_png.stat().st_size > 1000:
        return True
    minx, miny, maxx, maxy = geom_crs.bounds
    medio = max(maxx - minx, maxy - miny) / 2.0 + margen_m
    cx, cy = (minx + maxx) / 2.0, (miny + maxy) / 2.0
    # Encuadre exacto en metros (con fracciones de píxel) y no ajustado a la grilla de cada sensor:
    # así el recorte de 10 m de Sentinel-2 y el de 30 m de Landsat cubren el mismo cuadro y calzan en la cortina.
    izq = max(0.0, (cx - medio - x0) / res_m)
    der = min(float(ancho), (cx + medio - x0) / res_m)
    arr = max(0.0, (y0 - cy - medio) / res_m)
    aba = min(float(alto), (y0 - cy + medio) / res_m)
    if der - izq < 2 or aba - arr < 2:
        return False

    factor = lado_px / max(der - izq, aba - arr)
    salida = (max(48, round((der - izq) * factor)), max(48, round((aba - arr) * factor)))
    c0, f0 = int(izq), int(arr)
    c1, f1 = min(ancho, math.ceil(der) + 1), min(alto, math.ceil(aba) + 1)
    rec = np.ascontiguousarray(matriz_rgb[f0:f1, c0:c1])
    img = Image.fromarray(rec).resize(
        salida, Image.Resampling.BICUBIC, box=(izq - c0, arr - f0, der - c0, aba - f0)
    )
    lapiz = ImageDraw.Draw(img)
    for anillo in recortes._contornos(geom_crs):
        pts = [(((x - x0) / res_m - izq) * factor, ((y0 - y) / res_m - arr) * factor) for x, y in anillo.coords]
        if len(pts) >= 2:
            lapiz.line(pts, fill=(10, 15, 12), width=4)
            lapiz.line(pts, fill=(255, 255, 255), width=2)
    ruta_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(ruta_png, optimize=True)
    return True


def _calcular_landsat_lst(datos_comunas: dict[str, dict[str, Any]], cfg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Extrae LST de verano Landsat 8/9 (°C) desde Planetary Computer sobre todas las comunas."""
    bboxes = [d["p1"]["comuna"]["bbox"] for d in datos_comunas.values()]
    bbox_global = [
        min(b[0] for b in bboxes),
        min(b[1] for b in bboxes),
        max(b[2] for b in bboxes),
        max(b[3] for b in bboxes),
    ]

    client = Client.open(PLANETARY_STAC, modifier=planetary_computer.sign_inplace)
    items = list(
        client.search(
            collections=["landsat-c2-l2"],
            bbox=bbox_global,
            datetime="2025-12-01/2026-03-15",
            query={"eo:cloud_cover": {"lt": 20}},
            max_items=20,
        ).items()
    )

    # Una escena más clara por fecha, hasta 5 escenas estivales
    por_fecha: dict[str, Any] = {}
    for it in items:
        if "lwir11" not in it.assets or "qa_pixel" not in it.assets:
            continue
        f = it.datetime.date().isoformat()
        cc = float(it.properties.get("eo:cloud_cover", 100.0))
        if f not in por_fecha or cc < float(por_fecha[f].properties.get("eo:cloud_cover", 100.0)):
            por_fecha[f] = it

    seleccionadas = sorted(por_fecha.values(), key=lambda i: float(i.properties.get("eo:cloud_cover", 100.0)))[:5]
    if not seleccionadas:
        print("[02c] ADVERTENCIA: sin escenas Landsat 8/9 utilizables en verano 2025-2026.")
        return {slug: {"escenas_landsat": [], "comuna_lst_verano_c": None, "sitios": {}} for slug in datos_comunas}

    fechas_meta = [
        {
            "id": it.id,
            "fecha": it.datetime.date().isoformat(),
            "plataforma": it.properties.get("platform"),
            "nubes_pct": round(float(it.properties.get("eo:cloud_cover", 0.0)), 1),
        }
        for it in seleccionadas
    ]
    print(f"  [02c] Landsat 8/9 térmico: {len(seleccionadas)} escenas estivales limpias ({[f['fecha'] for f in fechas_meta]})")

    resultados: dict[str, dict[str, Any]] = {}
    with rasterio.Env(**s2.ENTORNO_GDAL):
        for slug, pack in datos_comunas.items():
            lim_geom_wgs = shape(pack["limite"]["geometry"])
            stack_lst: list[np.ndarray] = []
            ref_crs = None
            ref_tr = None

            for it in seleccionadas:
                rb = it.assets["lwir11"].extra_fields.get("raster:bands", [{}])[0]
                scale = float(rb.get("scale", 0.00341802))
                offset = float(rb.get("offset", 149.0))
                with rasterio.open(it.assets["lwir11"].href) as src_th, rasterio.open(it.assets["qa_pixel"].href) as src_qa:
                    tr_wgs_src = Transformer.from_crs("EPSG:4326", src_th.crs, always_xy=True)
                    lim_src = shp_transform(tr_wgs_src.transform, lim_geom_wgs)
                    minx, miny, maxx, maxy = lim_src.buffer(600).bounds
                    win = from_bounds(minx, miny, maxx, maxy, src_th.transform).round_offsets().round_lengths()
                    lwir = src_th.read(1, window=win).astype(np.float32)
                    qa = src_qa.read(1, window=win)
                    if ref_crs is None:
                        ref_crs = src_th.crs
                        ref_tr = src_th.window_transform(win)
                    elif lwir.shape != stack_lst[0].shape:
                        continue

                    invalid_qa = (qa & ((1 << 1) | (1 << 3) | (1 << 4) | (1 << 5))) != 0
                    cel = np.where((lwir > 0) & (~invalid_qa), lwir * scale + offset - 273.15, np.nan)
                    cel[(cel < 5.0) | (cel > 65.0)] = np.nan
                    stack_lst.append(cel)

            if not stack_lst or ref_crs is None or ref_tr is None:
                resultados[slug] = {"escenas_landsat": fechas_meta, "comuna_lst_verano_c": None, "sitios": {}}
                continue

            arr_stack = np.stack(stack_lst, axis=0)
            validos_cnt = np.sum(np.isfinite(arr_stack), axis=0)
            med_lst = np.full(arr_stack.shape[1:], np.nan, dtype=np.float32)
            max_lst = np.full(arr_stack.shape[1:], np.nan, dtype=np.float32)
            ok_px = validos_cnt > 0
            med_lst[ok_px] = np.nanmedian(arr_stack[:, ok_px], axis=0)
            max_lst[ok_px] = np.nanmax(arr_stack[:, ok_px], axis=0)

            tr_utm_src = Transformer.from_crs(comun.EPSG_METRICO, ref_crs, always_xy=True)
            tr_wgs_src = Transformer.from_crs("EPSG:4326", ref_crs, always_xy=True)
            lim_src = shp_transform(tr_wgs_src.transform, lim_geom_wgs)
            mask_com = geometry_mask([lim_src], out_shape=med_lst.shape, transform=ref_tr, invert=True)
            vals_com = med_lst[mask_com & np.isfinite(med_lst)]
            com_med = _limpiar(np.median(vals_com), 1) if vals_com.size else None

            rgb_lst = _colorear_rampa(med_lst, RAMPA_LST)
            res_m = abs(float(ref_tr.a))
            alto, ancho = med_lst.shape

            sitios_lst: dict[str, dict[str, Any]] = {}
            for s in pack["p1"]["sitios"]:
                sid = s["site_id"]
                g_utm = s["geom_utm"]
                g_src = shp_transform(tr_utm_src.transform, g_utm)
                g_buf_src = shp_transform(tr_utm_src.transform, g_utm.buffer(400))

                m_parque = geometry_mask([g_src], out_shape=med_lst.shape, transform=ref_tr, invert=True, all_touched=True)
                m_buf = geometry_mask([g_buf_src], out_shape=med_lst.shape, transform=ref_tr, invert=True, all_touched=True)

                v_parque = med_lst[m_parque & np.isfinite(med_lst)]
                v_pico = max_lst[m_parque & np.isfinite(max_lst)]
                v_buf = med_lst[m_buf & np.isfinite(med_lst)]

                img_lst_rel = None
                if float(s.get("area_m2", 0.0)) >= float(cfg["imagenes"]["area_minima_m2"]):
                    ruta_png = comun.dir_web(slug) / "img" / sid / "lst_verano.png"
                    if _dibujar_recorte(rgb_lst, g_src, float(ref_tr.c), float(ref_tr.f), res_m, alto, ancho, ruta_png, margen_m=float(cfg["imagenes"]["margen_m"]), lado_px=int(cfg["imagenes"]["lado_px"])):
                        img_lst_rel = f"data/{slug}/img/{sid}/lst_verano.png"

                sitios_lst[sid] = {
                    "lst_verano_c": _limpiar(np.median(v_parque), 1) if v_parque.size else None,
                    "lst_pico_c": _limpiar(np.percentile(v_pico, 90), 1) if v_pico.size else None,
                    "lst_entorno_400m_c": _limpiar(np.median(v_buf), 1) if v_buf.size else None,
                    "imagen_lst": img_lst_rel,
                }

            resultados[slug] = {
                "escenas_landsat": fechas_meta,
                "comuna_lst_verano_c": com_med,
                "sitios": sitios_lst,
            }
            print(f"  [02c] Landsat LST {pack['meta']['nombre']}: mediana comunal verano={com_med} °C | sitios={len(sitios_lst)}")

    return resultados


def _calcular_sentinel_extra(datos_comunas: dict[str, dict[str, Any]], cfg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Calcula SAVI/NDWI/BSI, recupera plazas angostas sin recorte de borde y renderiza PNGs HD (NDVI y NDMI)."""
    stac_url = cfg["sentinel2"]["stac_url"]
    coleccion = cfg["sentinel2"]["coleccion"]
    client = Client.open(stac_url)
    min_area_img = float(cfg["imagenes"]["area_minima_m2"])
    salida: dict[str, dict[str, Any]] = {}

    for slug, pack in datos_comunas.items():
        p1 = pack["p1"]
        p2 = pack["p2"]
        escenas = p2.get("escenas", [])
        fechas_img = p2.get("fechas_imagen", []) or ([escenas[-1]["fecha"]] if escenas else [])
        esc_por_fecha = {e["fecha"]: e for e in escenas}

        bbox = p1["comuna"]["bbox"]
        lim_utm = pack["lim_utm"]
        sitios = p1["sitios"]

        sitios_s2_extra: dict[str, dict[str, Any]] = {}
        fecha_ultima = sorted(fechas_img)[-1] if fechas_img else None
        grilla_cache: dict[tuple[Any, Any], tuple[s2.Grilla, list[tuple[dict[str, Any], np.ndarray]]]] = {}

        for f_target in sorted(set(fechas_img)):
            esc_meta = esc_por_fecha.get(f_target)
            items = list(
                client.search(
                    collections=[coleccion],
                    bbox=bbox,
                    datetime=f"{f_target}T00:00:00Z/{f_target}T23:59:59Z",
                ).items()
            )
            if esc_meta and esc_meta.get("id"):
                match = [it for it in items if it.id == esc_meta["id"]]
                item = match[0] if match else (items[0] if items else None)
            else:
                item = items[0] if items else None
            if item is None:
                continue

            grilla = s2.Grilla(item, lim_utm.bounds)
            clave_grilla = (grilla.forma10, (grilla.t10.c, grilla.t10.f))
            if clave_grilla not in grilla_cache:
                mascaras_adap = [
                    (sit, geometry_mask([sit["geom_utm"]], out_shape=grilla.forma10, transform=grilla.t10, invert=True, all_touched=True))
                    for sit in sitios
                ]
                grilla_cache[clave_grilla] = (grilla, mascaras_adap)
            mascaras_adap = grilla_cache[clave_grilla][1]

            with rasterio.Env(**s2.ENTORNO_GDAL):
                scl20 = s2.leer(item.assets["scl"].href, grilla.v20)
                scl = np.repeat(np.repeat(scl20, 2, axis=0), 2, axis=1)
                rojo_crudo = s2.leer(item.assets["red"].href, grilla.v10)
                valido_esc = ~np.isin(scl, cfg["sentinel2"]["scl_descartar"]) & (rojo_crudo > 0)
                falta_offset, _ = s2.juzgar_offset(item, rojo_crudo, valido_esc)

                red, _ = s2.a_reflectancia(rojo_crudo, s2.metadatos_banda(item, "red"), falta_offset)
                green, _ = s2.reflectancia(item, "green", grilla.v10, falta_offset)
                blue, _ = s2.reflectancia(item, "blue", grilla.v10, falta_offset)
                nir, _ = s2.reflectancia(item, "nir", grilla.v10, falta_offset)
                nir08_20, _ = s2.reflectancia(item, "nir08", grilla.v20, falta_offset)
                swir16_20, _ = s2.reflectancia(item, "swir16", grilla.v20, falta_offset)

            nir08_10 = np.repeat(np.repeat(nir08_20, 2, axis=0), 2, axis=1)
            swir16_10 = np.repeat(np.repeat(swir16_20, 2, axis=0), 2, axis=1)

            con_dato = valido_esc & ((red != 0) | (nir != 0))
            ndvi = s2.indice_normalizado(nir, red, con_dato)
            ndmi = s2.indice_normalizado(nir08_10, swir16_10, con_dato)
            ndwi = s2.indice_normalizado(green, nir, con_dato)

            denom_savi = nir + red + 0.5
            savi = np.full(nir.shape, np.nan, dtype=np.float32)
            ok_savi = con_dato & (denom_savi > 0)
            savi[ok_savi] = 1.5 * (nir[ok_savi] - red[ok_savi]) / denom_savi[ok_savi]

            num_bsi = (swir16_10 + red) - (nir + blue)
            den_bsi = (swir16_10 + red) + (nir + blue)
            bsi = np.full(nir.shape, np.nan, dtype=np.float32)
            ok_bsi = con_dato & (den_bsi != 0)
            bsi[ok_bsi] = num_bsi[ok_bsi] / den_bsi[ok_bsi]

            rgb_ndvi_hd = _colorear_rampa(ndvi, RAMPA_NDVI_HD)
            rgb_ndmi = _colorear_rampa(ndmi, RAMPA_NDMI)
            rgb_color = recortes.color_real(red, green, blue)
            alto, ancho = grilla.forma10
            margen = float(cfg["imagenes"]["margen_m"])
            lado = int(cfg["imagenes"]["lado_px"])

            for sit, m_adap in mascaras_adap:
                sid = sit["site_id"]
                if float(sit.get("area_m2", 0.0)) >= min_area_img:
                    carp = comun.dir_web(slug) / "img" / sid
                    # El color natural se vuelve a dibujar siempre: mismo encuadre y suavizado que NDVI HD y NDMI.
                    _dibujar_recorte(rgb_color, sit["geom_utm"], float(grilla.t10.c), float(grilla.t10.f), 10.0, alto, ancho, carp / f"{f_target}_color.png", margen_m=margen, lado_px=lado, forzar=True)
                    _dibujar_recorte(rgb_ndvi_hd, sit["geom_utm"], float(grilla.t10.c), float(grilla.t10.f), 10.0, alto, ancho, carp / f"{f_target}_ndvi_hd.png", margen_m=margen, lado_px=lado)
                    _dibujar_recorte(rgb_ndmi, sit["geom_utm"], float(grilla.t10.c), float(grilla.t10.f), 10.0, alto, ancho, carp / f"{f_target}_ndmi.png", margen_m=margen, lado_px=lado)

                if f_target == fecha_ultima:
                    v_ndvi = ndvi[m_adap & np.isfinite(ndvi)]
                    v_ndmi = ndmi[m_adap & np.isfinite(ndmi)]
                    v_savi = savi[m_adap & np.isfinite(savi)]
                    v_ndwi = ndwi[m_adap & np.isfinite(ndwi)]
                    v_bsi = bsi[m_adap & np.isfinite(bsi)]
                    obs_p2 = p2.get("sitios", {}).get(sid, {}).get("obs", [])
                    tuvo_p2 = any(o[1] is not None for o in obs_p2)
                    sitios_s2_extra[sid] = {
                        "ndvi_adaptativo": _limpiar(np.median(v_ndvi), 3) if v_ndvi.size else None,
                        "ndmi_adaptativo": _limpiar(np.median(v_ndmi), 3) if v_ndmi.size else None,
                        "savi_actual": _limpiar(np.median(v_savi), 3) if v_savi.size else None,
                        "ndwi_actual": _limpiar(np.median(v_ndwi), 3) if v_ndwi.size else None,
                        "bsi_actual": _limpiar(np.median(v_bsi), 3) if v_bsi.size else None,
                        "pixeles_adaptativos": int(v_ndvi.size),
                        "lectura_borde_adaptativo": bool(not tuvo_p2 and v_ndvi.size > 0),
                    }

        salida[slug] = {"fecha_escena_hd": fecha_ultima, "sitios": sitios_s2_extra}
        recup = sum(1 for v in sitios_s2_extra.values() if v.get("lectura_borde_adaptativo"))
        print(f"  [02c] Sentinel-2 HD + recuperación {pack['meta']['nombre']}: recuperados={recup} sitios angostos")

    return salida


def _calcular_worldcover_multiclase(datos_comunas: dict[str, dict[str, Any]], cfg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Desglosa cobertura construida/cemento (50), pasto/matorral (20+30) y suelo desnudo (60) de WorldCover 2021."""
    salida: dict[str, dict[str, Any]] = {}
    with rasterio.Env(**mod_03b.ENTORNO_GDAL):
        for slug, pack in datos_comunas.items():
            p1 = pack["p1"]
            lon, lat = p1["comuna"]["centro"]
            url = mod_03b.url_mosaico(lon, lat, cfg)
            tr_wgs = Transformer.from_crs(comun.EPSG_METRICO, "EPSG:4326", always_xy=True)

            with rasterio.open(url) as src:
                w, s, e, n = p1["comuna"]["bbox"]
                d = 0.01
                win = from_bounds(w - d, s - d, e + d, n + d, src.transform)
                wc = src.read(1, window=win)
                wt = src.window_transform(win)

            lim_wgs = shp_transform(tr_wgs.transform, pack["lim_utm"])
            mask_com = geometry_mask([lim_wgs], out_shape=wc.shape, transform=wt, invert=True)
            vals_com = wc[mask_com]
            tot_com = max(int(vals_com.size), 1)
            imp_com = _limpiar(np.sum(vals_com == 50) / tot_com * 100.0, 1)

            sitios_wc: dict[str, dict[str, Any]] = {}
            radio = float(cfg["sitios"]["radio_entorno_m"])
            for sit in p1["sitios"]:
                ent_wgs = shp_transform(tr_wgs.transform, sit["geom_utm"].buffer(radio))
                m_ent = geometry_mask([ent_wgs], out_shape=wc.shape, transform=wt, invert=True)
                vals = wc[m_ent]
                tot = max(int(vals.size), 1)
                sitios_wc[sit["site_id"]] = {
                    "impermeable_400m_pct": _limpiar(np.sum(vals == 50) / tot * 100.0, 1),
                    "pasto_matorral_400m_pct": _limpiar(np.sum((vals == 20) | (vals == 30)) / tot * 100.0, 1),
                    "suelo_desnudo_400m_pct": _limpiar(np.sum(vals == 60) / tot * 100.0, 1),
                }

            salida[slug] = {"impermeable_comuna_pct": imp_com, "sitios": sitios_wc}
            print(f"  [02c] WorldCover multiclase {pack['meta']['nombre']}: construido/impermeable={imp_com}%")

    return salida


def _calcular_calidad_aire(datos_comunas: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Descarga últimos 30 días de Copernicus CAMS / Open-Meteo Air Quality por comuna."""
    salida: dict[str, dict[str, Any]] = {}
    for slug, pack in datos_comunas.items():
        lon, lat = pack["p1"]["comuna"]["centro"]
        r = httpx.get(
            AIR_QUALITY_URL,
            params={
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "hourly": "pm2_5,pm10,nitrogen_dioxide,ozone,uv_index,european_aqi",
                "past_days": 30,
                "timezone": "America/Santiago",
            },
            timeout=20.0,
        )
        r.raise_for_status()
        h = r.json().get("hourly", {})
        pm25 = [x for x in h.get("pm2_5", []) if x is not None]
        pm10 = [x for x in h.get("pm10", []) if x is not None]
        no2 = [x for x in h.get("nitrogen_dioxide", []) if x is not None]
        uv = [x for x in h.get("uv_index", []) if x is not None]
        aqi = [x for x in h.get("european_aqi", []) if x is not None]

        aire_obj = {
            "fuente": "Copernicus CAMS vía Open-Meteo Air Quality (CC BY 4.0 no comercial)",
            "dias_ventana": 30,
            "pm2_5_media": _limpiar(np.mean(pm25), 1) if pm25 else None,
            "pm2_5_max": _limpiar(np.max(pm25), 1) if pm25 else None,
            "pm10_media": _limpiar(np.mean(pm10), 1) if pm10 else None,
            "no2_media": _limpiar(np.mean(no2), 1) if no2 else None,
            "uv_max": _limpiar(np.max(uv), 1) if uv else None,
            "eaqi_medio": _limpiar(np.mean(aqi), 0) if aqi else None,
        }
        comun.escribir_json(comun.dir_raw(slug) / "aire.json", aire_obj)
        salida[slug] = aire_obj
        print(f"  [02c] Calidad del aire {pack['meta']['nombre']}: PM2.5={aire_obj['pm2_5_media']} ug/m3 | UV máx={aire_obj['uv_max']}")
    return salida


def _calcular_censo_termico(datos_comunas: dict[str, dict[str, Any]], cfg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Extrae variables habitacionales térmicas reales del Censo 2024 (techos zinc/precarios, hacinamiento, infancia)."""
    cache_dir = comun.RAW / "_censo_teselas"
    pbfs = sorted(cache_dir.glob("*.pbf")) if cache_dir.exists() else []
    trozos_por_comuna: dict[str, dict[Any, dict[str, Any]]] = {s: {} for s in datos_comunas}
    cuts_objetivo = {int(d["p1"]["comuna"]["cut"]): s for s, d in datos_comunas.items() if d["p1"]["comuna"].get("cut")}

    for pbf_path in pbfs:
        partes = pbf_path.stem.split("_")
        if len(partes) != 3:
            continue
        z, x, y = int(partes[0]), int(partes[1]), int(partes[2])
        raw = pbf_path.read_bytes()
        if not raw:
            continue
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        dec = mapbox_vector_tile.decode(raw, default_options={"y_coord_down": True})
        if not dec:
            continue
        layer = dec.get(mod_03.CAPA) or next(iter(dec.values()))
        marco = box(*mod_03.limites_tesela(x, y, z))
        ext = layer.get("extent", 4096)

        for feat in layer.get("features", []):
            pr = feat.get("properties", {})
            cut = pr.get("CUT")
            slug = cuts_objetivo.get(int(cut)) if cut is not None else None
            if not slug or not feat.get("geometry"):
                continue
            geom = shapely.make_valid(shape(feat["geometry"]))
            geom_wgs = comun.solo_poligonos(mod_03._a_grados(geom, x, y, z, ext).intersection(marco))
            if geom_wgs.is_empty:
                continue
            mid = pr.get("MANZENT") or id(feat)
            bucket = trozos_por_comuna[slug].setdefault(mid, {"pr": pr, "partes": []})
            bucket["partes"].append(geom_wgs)

    salida: dict[str, dict[str, Any]] = {}
    radio = float(cfg["sitios"]["radio_entorno_m"])

    for slug, pack in datos_comunas.items():
        unicas: list[tuple[Any, float, dict[str, Any]]] = []
        for bucket in trozos_por_comuna.get(slug, {}).values():
            g_utm = comun.solo_poligonos(shapely.make_valid(comun.a_utm(shapely.unary_union(bucket["partes"]))))
            if not g_utm.is_empty and g_utm.area > 0:
                unicas.append((g_utm, g_utm.area, bucket["pr"]))

        tot_viv = sum(float(pr.get("n_vp_ocupada") or 0) for _, _, pr in unicas)
        tot_per = sum(float(pr.get("n_per") or 0) for _, _, pr in unicas)
        tot_techo = sum(
            float((pr.get("n_mat_techo_zinc") or 0) + (pr.get("n_mat_techo_fibrocemento") or 0) + (pr.get("n_mat_techo_precarios") or 0))
            for _, _, pr in unicas
        )
        tot_hac = sum(float(pr.get("n_viv_hacinadas") or 0) for _, _, pr in unicas)

        sitios_censo: dict[str, dict[str, Any]] = {}
        for sit in pack["p1"]["sitios"]:
            buf = sit["geom_utm"].buffer(radio)
            bminx, bminy, bmaxx, bmaxy = buf.bounds
            viv = 0.0
            per = 0.0
            techo = 0.0
            hac = 0.0
            mat_def = 0.0
            inf05 = 0.0
            for g_utm, area, pr in unicas:
                gminx, gminy, gmaxx, gmaxy = g_utm.bounds
                if gmaxx < bminx or gminx > bmaxx or gmaxy < bminy or gminy > bmaxy:
                    continue
                inter = g_utm.intersection(buf).area
                if inter <= 0:
                    continue
                frac = min(inter / area, 1.0)
                viv += float(pr.get("n_vp_ocupada") or 0) * frac
                per += float(pr.get("n_per") or 0) * frac
                techo += float((pr.get("n_mat_techo_zinc") or 0) + (pr.get("n_mat_techo_fibrocemento") or 0) + (pr.get("n_mat_techo_precarios") or 0)) * frac
                hac += float(pr.get("n_viv_hacinadas") or 0) * frac
                mat_def += float((pr.get("n_materialidad_irrecuperable") or 0) + (pr.get("n_materialidad_recuperable") or 0)) * frac
                inf05 += float(pr.get("n_edad_0_5") or 0) * frac

            sitios_censo[sit["site_id"]] = {
                "viviendas_400m": round(viv) if viv > 0 else 0,
                "pct_techo_calor_400m": _limpiar((techo / viv) * 100.0, 1) if viv >= 5 else None,
                "pct_hacinamiento_400m": _limpiar((hac / viv) * 100.0, 1) if viv >= 5 else None,
                "pct_mat_deficiente_400m": _limpiar((mat_def / viv) * 100.0, 1) if viv >= 5 else None,
                "pct_infancia_0_5_400m": _limpiar((inf05 / per) * 100.0, 1) if per >= 10 else None,
            }

        salida[slug] = {
            "pct_techo_calor_comuna": _limpiar((tot_techo / tot_viv) * 100.0, 1) if tot_viv > 0 else None,
            "pct_hacinamiento_comuna": _limpiar((tot_hac / tot_viv) * 100.0, 1) if tot_viv > 0 else None,
            "sitios": sitios_censo,
        }
        print(f"  [02c] Censo térmico {pack['meta']['nombre']}: techos zinc/precarios={salida[slug]['pct_techo_calor_comuna']}% | hacinamiento={salida[slug]['pct_hacinamiento_comuna']}%", flush=True)

    return salida


def _cargar_datos_comunas(comunas: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    datos_comunas: dict[str, dict[str, Any]] = {}
    for c in comunas:
        slug = c["slug"]
        raw = comun.dir_raw(slug)
        if not (raw / "paso01.json").exists() or not (raw / "paso02.json").exists():
            continue
        p1 = comun.leer_json(raw / "paso01.json")
        for sit in p1["sitios"]:
            sit["geom_utm"] = comun.a_utm(shape(sit["geometria"]))
        lim = comun.leer_json(raw / "limite.geojson")
        datos_comunas[slug] = {
            "meta": c,
            "p1": p1,
            "p2": comun.leer_json(raw / "paso02.json"),
            "limite": lim,
            "lim_utm": comun.solo_poligonos(comun.a_utm(shape(lim["geometry"]))),
        }

    if not datos_comunas:
        raise RuntimeError("[02c] No hay comunas con pasos 01 y 02 listos.")
    return datos_comunas


def regenerar_imagenes(comunas: list[dict[str, Any]], cfg: dict[str, Any]) -> None:
    """Solo vuelve a dibujar los recortes (color natural, NDVI HD, NDMI y térmico Landsat); no cambia ninguna cifra."""
    global REDIBUJAR
    datos = _cargar_datos_comunas(comunas)
    REDIBUJAR = True
    try:
        _calcular_sentinel_extra(datos, cfg)
        _calcular_landsat_lst(datos, cfg)
    finally:
        REDIBUJAR = False


def ejecutar_todas(comunas: list[dict[str, Any]], cfg: dict[str, Any]) -> None:
    """Ejecuta enriquecimiento multi-satélite, WorldCover multiclase, CAMS aire y Censo térmico."""
    datos_comunas = _cargar_datos_comunas(comunas)

    lst_res = _calcular_landsat_lst(datos_comunas, cfg)
    s2_res = _calcular_sentinel_extra(datos_comunas, cfg)
    wc_res = _calcular_worldcover_multiclase(datos_comunas, cfg)
    aire_res = _calcular_calidad_aire(datos_comunas)
    censo_res = _calcular_censo_termico(datos_comunas, cfg)

    vitacura_lst = (lst_res.get("vitacura") or {}).get("comuna_lst_verano_c")

    for slug, pack in datos_comunas.items():
        sitios_out: dict[str, Any] = {}
        for sit in pack["p1"]["sitios"]:
            sid = sit["site_id"]
            l_s = (lst_res.get(slug, {}).get("sitios") or {}).get(sid, {})
            s2_s = (s2_res.get(slug, {}).get("sitios") or {}).get(sid, {})
            wc_s = (wc_res.get(slug, {}).get("sitios") or {}).get(sid, {})
            ce_s = (censo_res.get(slug, {}).get("sitios") or {}).get(sid, {})
            lst_val = l_s.get("lst_verano_c")
            brecha_calor = _limpiar(lst_val - vitacura_lst, 1) if lst_val is not None and vitacura_lst is not None else None
            sitios_out[sid] = {
                **l_s,
                "brecha_calor_vs_vitacura_c": brecha_calor,
                **s2_s,
                **wc_s,
                **ce_s,
            }

        out_obj = {
            "comuna": pack["meta"],
            "fecha_consulta": comun.fecha_proceso().isoformat(),
            "escenas_landsat": lst_res.get(slug, {}).get("escenas_landsat", []),
            "comuna_lst_verano_c": lst_res.get(slug, {}).get("comuna_lst_verano_c"),
            "vitacura_lst_referencia_c": vitacura_lst,
            "fecha_escena_hd": s2_res.get(slug, {}).get("fecha_escena_hd"),
            "impermeable_comuna_pct": wc_res.get(slug, {}).get("impermeable_comuna_pct"),
            "pct_techo_calor_comuna": censo_res.get(slug, {}).get("pct_techo_calor_comuna"),
            "pct_hacinamiento_comuna": censo_res.get(slug, {}).get("pct_hacinamiento_comuna"),
            "aire": aire_res.get(slug, {}),
            "sitios": sitios_out,
        }
        comun.escribir_json(comun.dir_raw(slug) / "paso02c.json", out_obj)
        print(f"[02c] Guardado data/raw/{slug}/paso02c.json ({len(sitios_out)} sitios)")


if __name__ == "__main__":
    import sys

    cfg = comun.cargar_config()
    if "--solo-imagenes" in sys.argv:
        regenerar_imagenes(cfg["comunas"], cfg)
    else:
        ejecutar_todas(cfg["comunas"], cfg)
