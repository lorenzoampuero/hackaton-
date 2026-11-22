"""Paso 04: Cálculo de vulnerabilidad social, anomalías NDVI/NDMI, confianza y series temporales."""

from __future__ import annotations

import csv
import importlib
import math
import statistics
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from pipeline.comun import (
    RAW,
    WEB_DATA,
    cargar_config,
    dir_raw,
    dir_web,
    escribir_js,
    escribir_json,
    fecha_proceso,
    leer_json,
    redondear,
)

mod_03b = importlib.import_module("pipeline.03b_cobertura_arboles")

ESTACIONES_ORDEN = ("Verano", "Otoño", "Invierno", "Primavera")


def _acotar_z(val: float | None, limite: float = 4.0) -> float | None:
    if val is None or not math.isfinite(val):
        return None
    return max(-limite, min(limite, float(val)))


def _es_finito(val: Any) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool) and math.isfinite(val)


def _limpiar_num(val: Any, decimales: int = 3) -> float | None:
    if not _es_finito(val):
        return None
    return redondear(float(val), decimales)


def estacion_sur(d: date) -> tuple[int, str]:
    """Devuelve (año_estacion, nombre_estacion) para el hemisferio sur.
    Diciembre pertenece al verano del año siguiente para mantener la continuidad cronológica.
    """
    m = d.month
    if m == 12:
        return d.year + 1, "Verano"
    if m in (1, 2):
        return d.year, "Verano"
    if m in (3, 4, 5):
        return d.year, "Otoño"
    if m in (6, 7, 8):
        return d.year, "Invierno"
    return d.year, "Primavera"


def percentiles_rango(valores: list[float | None], invertir: bool = False) -> list[float | None]:
    """Calcula percentiles 0..100 sobre los elementos válidos preservando posiciones None."""
    validos = [(i, float(v)) for i, v in enumerate(valores) if _es_finito(v)]
    salida: list[float | None] = [None] * len(valores)
    if not validos:
        return salida
    n = len(validos)
    if n == 1:
        salida[validos[0][0]] = 50.0
        return salida

    ordenados = sorted(x[1] for x in validos)
    if ordenados[0] == ordenados[-1]:
        for idx, _ in validos:
            salida[idx] = 50.0
        return salida

    for idx, val in validos:
        menores = sum(1 for x in ordenados if x < val)
        iguales = sum(1 for x in ordenados if x == val)
        rango_medio = menores + 0.5 * (iguales - 1)
        pct = (rango_medio / (n - 1)) * 100.0
        if invertir:
            pct = 100.0 - pct
        salida[idx] = round(pct, 1)
    return salida


def calcular_vulnerabilidad(
    p_edad60: float | None,
    p_densidad: float | None,
    p_bajo_verde: float | None,
    pesos: dict[str, float],
) -> float | None:
    """Combina los 3 percentiles sociales según los pesos configurados (0..100)."""
    pares = [
        (p_edad60, float(pesos.get("pct_60_mas", 0.4))),
        (p_densidad, float(pesos.get("densidad", 0.3))),
        (p_bajo_verde, float(pesos.get("bajo_verde_per_capita", 0.3))),
    ]
    num = 0.0
    den = 0.0
    for val, peso in pares:
        if _es_finito(val) and peso > 0:
            num += float(val) * peso
            den += peso
    if den <= 0:
        return None
    return round(num / den, 1)


def _media_std(vals: list[float]) -> tuple[float | None, float | None]:
    if not vals:
        return None, None
    m = statistics.fmean(vals)
    if len(vals) < 2:
        return m, None
    sd = statistics.stdev(vals)
    return m, sd


def calcular_baseline_vegetacion(
    obs: list[list[Any]],
    fecha_ref: date,
    cfg: dict[str, Any],
    clima_dias: list[list[Any]] | None = None,
) -> dict[str, Any]:
    """Calcula nivel actual, línea base histórica/estacional, z-score acotado y métricas del evento de calor."""
    validas = [
        o for o in sorted(obs, key=lambda r: r[0])
        if len(o) >= 5 and _es_finito(o[1])
    ]
    if not validas:
        return {
            "n_obs": 0,
            "fecha_ultima_obs": None,
            "dias_desde_ultima": None,
            "pixeles_validos_ult": 0,
            "ndvi_actual": None,
            "ndmi_actual": None,
            "ndvi_ref": None,
            "ndmi_ref": None,
            "ndvi_z": None,
            "ndmi_z": None,
            "ndvi_delta_pct": None,
            "ndmi_delta_pct": None,
            "baseline_tipo": "insuficiente",
            "evento_calor": None,
        }

    ult = validas[-1]
    ult_fecha = date.fromisoformat(ult[0])
    ndvi_actual = float(ult[1])
    ndmi_validas = [o for o in validas if _es_finito(o[2])]
    ndmi_actual = float(ult[2]) if _es_finito(ult[2]) else (float(ndmi_validas[-1][2]) if ndmi_validas else None)
    dias_desde = (fecha_ref - ult_fecha).days
    pix_ult = int(ult[3]) if _es_finito(ult[3]) else 0

    _, est_actual = estacion_sur(ult_fecha)
    corte_reciente = ult_fecha - timedelta(days=15)

    # Prioriza misma estación en la historia (excluyendo los últimos 15 días) para aislar estacionalidad
    hist_misma_est = [
        o for o in validas
        if date.fromisoformat(o[0]) < corte_reciente
        and estacion_sur(date.fromisoformat(o[0]))[1] == est_actual
    ]
    hist_total = [o for o in validas if date.fromisoformat(o[0]) < corte_reciente]
    if len(hist_misma_est) >= 4:
        base_obs = hist_misma_est
        baseline_tipo = f"estacional ({est_actual.lower()})"
    elif len(hist_total) >= 4:
        base_obs = hist_total
        baseline_tipo = "historico_24m"
    else:
        base_obs = validas[:-1]
        baseline_tipo = "insuficiente"

    ndvi_vals = [float(o[1]) for o in base_obs if _es_finito(o[1])]
    ndmi_vals = [float(o[2]) for o in base_obs if _es_finito(o[2])]
    ndvi_mean, ndvi_sd = _media_std(ndvi_vals)
    ndmi_mean, ndmi_sd = _media_std(ndmi_vals)

    ndvi_z = None
    if ndvi_mean is not None and ndvi_sd is not None and len(base_obs) >= 4:
        ndvi_z = _acotar_z((ndvi_actual - ndvi_mean) / max(ndvi_sd, 0.03))

    ndmi_z = None
    if ndmi_actual is not None and ndmi_mean is not None and ndmi_sd is not None and len(ndmi_vals) >= 4:
        ndmi_z = _acotar_z((ndmi_actual - ndmi_mean) / max(ndmi_sd, 0.03))

    ndvi_delta_pct = None
    if ndvi_mean is not None and abs(ndvi_mean) > 0.02:
        ndvi_delta_pct = ((ndvi_actual - ndvi_mean) / abs(ndvi_mean)) * 100.0

    ndmi_delta_pct = None
    if ndmi_actual is not None and ndmi_mean is not None and abs(ndmi_mean) > 0.02:
        ndmi_delta_pct = ((ndmi_actual - ndmi_mean) / abs(ndmi_mean)) * 100.0

    # Ventana del evento de calor documentado (ej. 2026-01-29, ventana de N semanas)
    ev_cfg = cfg.get("evento_calor") or {}
    ev_res = None
    if ev_cfg.get("fecha"):
        ev_fecha = date.fromisoformat(str(ev_cfg["fecha"]))
        semanas = int(ev_cfg.get("semanas_ventana", 8))
        ev_ini = ev_fecha - timedelta(days=14)
        ev_fin = ev_fecha + timedelta(days=max(semanas * 7 - 14, 14))
        ev_obs = [
            o for o in validas
            if ev_ini <= date.fromisoformat(o[0]) <= ev_fin
        ]
        # Línea base estival excluyendo la ventana del evento para no mezclar respuesta con referencia
        verano_base = [
            o for o in validas
            if estacion_sur(date.fromisoformat(o[0]))[1] == estacion_sur(ev_fecha)[1]
            and not (ev_ini <= date.fromisoformat(o[0]) <= ev_fin)
        ]
        v_ndvi_vals = [float(o[1]) for o in verano_base if _es_finito(o[1])]
        v_ndmi_vals = [float(o[2]) for o in verano_base if _es_finito(o[2])]
        v_ndvi_m, v_ndvi_sd = _media_std(v_ndvi_vals)
        v_ndmi_m, v_ndmi_sd = _media_std(v_ndmi_vals)

        temp_max_ev = None
        if clima_dias:
            temps_ev = [
                float(c[2]) for c in clima_dias
                if len(c) >= 3 and _es_finito(c[2]) and ev_ini <= date.fromisoformat(str(c[0])) <= ev_fin
            ]
            if temps_ev:
                temp_max_ev = _limpiar_num(max(temps_ev), 1)

        if ev_obs:
            peor_ndvi = min(ev_obs, key=lambda r: float(r[1]))
            ev_ndmi_obs = [o for o in ev_obs if _es_finito(o[2])]
            peor_ndmi = min(ev_ndmi_obs, key=lambda r: float(r[2])) if ev_ndmi_obs else None
            ez_ndvi = (
                _acotar_z((float(peor_ndvi[1]) - v_ndvi_m) / max(v_ndvi_sd, 0.03))
                if len(v_ndvi_vals) >= 4 and v_ndvi_m is not None and v_ndvi_sd is not None
                else None
            )
            ez_ndmi = (
                _acotar_z((float(peor_ndmi[2]) - v_ndmi_m) / max(v_ndmi_sd, 0.03))
                if peor_ndmi is not None and len(v_ndmi_vals) >= 4 and v_ndmi_m is not None and v_ndmi_sd is not None
                else None
            )
            ev_res = {
                "fecha_pico_calor": str(ev_cfg["fecha"]),
                "ventana": [ev_ini.isoformat(), ev_fin.isoformat()],
                "n_obs": len(ev_obs),
                "temp_max_evento_c": temp_max_ev,
                "fecha_min_ndvi": peor_ndvi[0],
                "ndvi_min": _limpiar_num(peor_ndvi[1], 3),
                "ndvi_z_min": _limpiar_num(ez_ndvi, 2),
                "fecha_min_ndmi": peor_ndmi[0] if peor_ndmi else None,
                "ndmi_min": _limpiar_num(peor_ndmi[2], 3) if peor_ndmi else None,
                "ndmi_z_min": _limpiar_num(ez_ndmi, 2),
            }

    return {
        "n_obs": len(validas),
        "fecha_ultima_obs": ult[0],
        "dias_desde_ultima": dias_desde,
        "pixeles_validos_ult": pix_ult,
        "ndvi_actual": _limpiar_num(ndvi_actual, 3),
        "ndmi_actual": _limpiar_num(ndmi_actual, 3),
        "ndvi_ref": _limpiar_num(ndvi_mean, 3),
        "ndmi_ref": _limpiar_num(ndmi_mean, 3),
        "ndvi_z": _limpiar_num(ndvi_z, 2),
        "ndmi_z": _limpiar_num(ndmi_z, 2),
        "ndvi_delta_pct": _limpiar_num(ndvi_delta_pct, 1),
        "ndmi_delta_pct": _limpiar_num(ndmi_delta_pct, 1),
        "baseline_tipo": baseline_tipo,
        "evento_calor": ev_res,
    }


def evaluar_confianza(
    area_m2: float,
    n_obs: int,
    dias_desde_ultima: int | None,
    pixeles_10m: int,
    cfg_conf: dict[str, Any],
) -> tuple[str, list[str]]:
    """Clasifica confiabilidad satelital del sitio (alta/media/baja) y documenta razones."""
    razones: list[str] = []
    area_min = float(cfg_conf.get("area_minima_m2", 5000))
    obs_min = int(cfg_conf.get("observaciones_minimas", 6))
    ant_max = int(cfg_conf.get("antiguedad_maxima_dias", 15))
    alta_area = float(cfg_conf.get("alta_area_m2", 10000))
    alta_obs = int(cfg_conf.get("alta_observaciones", 12))
    alta_pix = int(cfg_conf.get("alta_pixeles", 50))

    if area_m2 < area_min:
        razones.append(f"Área bajo {int(area_min):,} m² ({int(round(area_m2)):,} m²)".replace(",", "."))
    if n_obs < obs_min:
        razones.append(f"Menos de {obs_min} observaciones válidas ({n_obs})")
    if dias_desde_ultima is None or dias_desde_ultima > ant_max:
        razones.append(
            "Sin observación reciente" if dias_desde_ultima is None
            else f"Última observación hace {dias_desde_ultima} días (> {ant_max})"
        )
    if pixeles_10m < int(cfg_conf.get("alta_pixeles", 50)) and area_m2 >= area_min:
        razones.append(f"{pixeles_10m} píxeles útiles a 10 m")

    if area_m2 < area_min or n_obs < obs_min or dias_desde_ultima is None or dias_desde_ultima > ant_max:
        return "baja", razones
    if area_m2 >= alta_area and n_obs >= alta_obs and pixeles_10m >= alta_pix and dias_desde_ultima <= ant_max:
        return "alta", ["Área ≥ 1 ha, ≥ 12 observaciones válidas y lectura reciente"]
    return "media", razones or ["Cobertura válida intermedia; recomendable validar en terreno"]


def calcular_confianza_pct(
    area_m2: float,
    n_obs: int,
    dias_desde_ultima: int | None,
    pixeles_10m: int,
    tiene_lst: bool,
    tiene_wc: bool,
    tiene_censo: bool,
) -> int:
    """Calcula un porcentaje explicable de confiabilidad de datos (64..98%) según fuentes activas y cobertura."""
    fuentes = 1 + int(n_obs > 0) + int(tiene_lst) + int(tiene_wc) + int(tiene_censo)
    score = 45 + fuentes * 6  # hasta 75 por 5/5 fuentes activas
    score += min(12, max(0, int(n_obs)))  # densidad temporal Sentinel-2
    score += 6 if area_m2 >= 10000 else (4 if area_m2 >= 5000 else 2)
    score += 4 if pixeles_10m >= 30 else 2
    if dias_desde_ultima is not None and dias_desde_ultima <= 15:
        score += 1
    return int(max(64, min(98, round(score))))


def calcular_salud_vegetal_pct(ndvi_actual: Any) -> int:
    """Convierte el NDVI (-0.1..0.7) a un porcentaje intuitivo de salud verde (8..98%)."""
    val = float(ndvi_actual) if _es_finito(ndvi_actual) else 0.15
    return int(round(max(8.0, min(98.0, (val / 0.60) * 100.0))))


def _normalizar_nombres_sitios(sitios: list[dict[str, Any]], comuna_nombre: str) -> dict[str, tuple[str, str]]:
    """Desambigua polígonos duplicados ('Sector 2..N') y da nombres claros a áreas sin nombre OSM."""
    por_base: dict[str, list[dict[str, Any]]] = {}
    sin_nombre: list[dict[str, Any]] = []
    for s in sitios:
        raw_name = str(s.get("nombre") or "").strip()
        con_nom = bool(s.get("con_nombre", False)) and not raw_name.lower().startswith("área verde sin nombre")
        if raw_name.lower() == comuna_nombre.lower():
            raw_name = f"Parque Cerro Isla {comuna_nombre}"
        if con_nom and raw_name:
            por_base.setdefault(raw_name, []).append(s)
        else:
            sin_nombre.append(s)

    mapa: dict[str, tuple[str, str]] = {}
    for base, grupo in por_base.items():
        grupo_ord = sorted(grupo, key=lambda x: -float(x.get("area_m2") or 0.0))
        for idx, item in enumerate(grupo_ord, start=1):
            display = base if idx == 1 else f"{base} (Sector {idx})"
            mapa[item["site_id"]] = (display, base)

    sin_nombre_ord = sorted(sin_nombre, key=lambda x: -float(x.get("area_m2") or 0.0))
    for idx, item in enumerate(sin_nombre_ord, start=1):
        ha = round(float(item.get("area_m2") or 0.0) / 10000.0, 2)
        ha_txt = f"{ha:.2f}".replace(".", ",")
        display = f"Plaza Vecinal {comuna_nombre} #{idx} ({ha_txt} ha)"
        mapa[item["site_id"]] = (display, f"Plaza Vecinal {comuna_nombre} #{idx}")
    return mapa


def clasificar_estado(
    vulnerabilidad: float | None,
    ndvi_z: float | None,
    ndmi_z: float | None,
    brecha_dosel_pts: float | None,
    n_obs: int,
    cfg: dict[str, Any],
    lst_verano_c: float | None = None,
    ndvi_actual: float | None = None,
) -> tuple[str, float]:
    """Determina estado categórico del sitio y puntaje base de priorización (0..100)."""
    obs_min = int(cfg["confianza"]["observaciones_minimas"])
    umbral_v = float(cfg["umbral_vulnerabilidad_alta"])
    umbral_z = float(cfg["umbral_estres_z"])
    umbral_dosel = float(cfg["senales"]["brecha_dosel_puntos"])

    vuln_val = float(vulnerabilidad) if _es_finito(vulnerabilidad) else 0.0
    brecha_val = max(0.0, float(brecha_dosel_pts)) if _es_finito(brecha_dosel_pts) else 0.0

    peor_z = None
    zs = [z for z in (ndvi_z, ndmi_z) if _es_finito(z)]
    if zs:
        peor_z = min(zs)
    estres_comp = max(0.0, min(100.0, -(peor_z or 0.0) * 28.0))
    dosel_comp = max(0.0, min(100.0, (brecha_val / 30.0) * 100.0))
    prioridad = round(vuln_val * 0.55 + estres_comp * 0.25 + dosel_comp * 0.20, 1)

    alta_calor = _es_finito(lst_verano_c) and float(lst_verano_c) >= 36.5
    bajo_vigor_abs = _es_finito(ndvi_actual) and float(ndvi_actual) < 0.25

    if (n_obs < obs_min or peor_z is None) and not (_es_finito(lst_verano_c) and _es_finito(ndvi_actual)):
        return "sin_datos", prioridad

    alta_vuln = _es_finito(vulnerabilidad) and float(vulnerabilidad) >= umbral_v
    con_estres = (peor_z is not None and peor_z <= umbral_z) or (alta_calor and bajo_vigor_abs)
    bajo_dosel = brecha_val >= umbral_dosel

    if alta_vuln and con_estres:
        return "critico", prioridad
    if (alta_vuln and bajo_dosel) or (alta_calor and bajo_dosel):
        return "prioritario", prioridad
    if con_estres or alta_vuln or bajo_dosel or alta_calor:
        return "vigilar", prioridad
    return "estable", prioridad


def agregar_series(
    obs: list[list[Any]],
    escenas: list[dict[str, Any]],
    clima_dias: list[list[Any]],
    desde_iso: str,
    hasta_iso: str,
) -> dict[str, list[list[Any]]]:
    """Construye series semanales, mensuales y estacionales con huecos explícitos (None)."""
    d_ini = date.fromisoformat(desde_iso)
    d_fin = date.fromisoformat(hasta_iso)

    nubes_por_fecha: dict[str, float] = {}
    for esc in escenas:
        if _es_finito(esc.get("nubes_escena_pct")):
            nubes_por_fecha[str(esc["fecha"])] = float(esc["nubes_escena_pct"])

    obs_por_semana: dict[str, list[list[Any]]] = {}
    obs_por_mes: dict[str, list[list[Any]]] = {}
    obs_por_est: dict[tuple[int, str], list[list[Any]]] = {}

    for o in obs:
        if len(o) < 5:
            continue
        f_str = str(o[0])
        d = date.fromisoformat(f_str)
        lun = (d - timedelta(days=d.weekday())).isoformat()
        mes = f_str[:7]
        est = estacion_sur(d)
        obs_por_semana.setdefault(lun, []).append(o)
        obs_por_mes.setdefault(mes, []).append(o)
        obs_por_est.setdefault(est, []).append(o)

    cli_por_semana: dict[str, list[list[Any]]] = {}
    cli_por_mes: dict[str, list[list[Any]]] = {}
    cli_por_est: dict[tuple[int, str], list[list[Any]]] = {}

    for c in clima_dias:
        if len(c) < 4:
            continue
        f_str = str(c[0])
        d = date.fromisoformat(f_str)
        lun = (d - timedelta(days=d.weekday())).isoformat()
        mes = f_str[:7]
        est = estacion_sur(d)
        cli_por_semana.setdefault(lun, []).append(c)
        cli_por_mes.setdefault(mes, []).append(c)
        cli_por_est.setdefault(est, []).append(c)

    def _resumir_bucket(clave: str, f_inicio: str, lista_obs: list[list[Any]], lista_cli: list[list[Any]]) -> list[Any]:
        ndvis = [float(r[1]) for r in lista_obs if _es_finito(r[1])]
        ndmis = [float(r[2]) for r in lista_obs if _es_finito(r[2])]
        pixs = [int(r[3]) for r in lista_obs if _es_finito(r[3])]
        nubs = [nubes_por_fecha[str(r[0])] for r in lista_obs if str(r[0]) in nubes_por_fecha]
        tmaxs = [float(c[2]) for c in lista_cli if _es_finito(c[2])]
        lluvias = [float(c[3]) for c in lista_cli if _es_finito(c[3])]

        return [
            clave,
            f_inicio,
            _limpiar_num(statistics.fmean(ndvis), 3) if ndvis else None,
            _limpiar_num(statistics.fmean(ndmis), 3) if ndmis else None,
            int(round(statistics.fmean(pixs))) if pixs else 0,
            _limpiar_num(statistics.fmean(nubs), 1) if nubs else None,
            _limpiar_num(max(tmaxs), 1) if tmaxs else None,
            _limpiar_num(sum(lluvias), 1) if lluvias else None,
        ]

    # Grilla continua semanal
    semanal: list[list[Any]] = []
    cur_lun = d_ini - timedelta(days=d_ini.weekday())
    fin_lun = d_fin - timedelta(days=d_fin.weekday())
    while cur_lun <= fin_lun:
        k = cur_lun.isoformat()
        semanal.append(_resumir_bucket(k, k, obs_por_semana.get(k, []), cli_por_semana.get(k, [])))
        cur_lun += timedelta(days=7)

    # Grilla continua mensual
    mensual: list[list[Any]] = []
    y, m = d_ini.year, d_ini.month
    while (y, m) <= (d_fin.year, d_fin.month):
        k = f"{y:04d}-{m:02d}"
        mensual.append(_resumir_bucket(k, f"{k}-01", obs_por_mes.get(k, []), cli_por_mes.get(k, [])))
        m += 1
        if m > 12:
            m = 1
            y += 1

    # Grilla continua estacional
    estacional: list[list[Any]] = []
    seen_est: list[tuple[int, str]] = []
    e_ini = estacion_sur(d_ini)
    e_fin = estacion_sur(d_fin)
    cy, ce = e_ini
    while (cy, ESTACIONES_ORDEN.index(ce)) <= (e_fin[0], ESTACIONES_ORDEN.index(e_fin[1])):
        seen_est.append((cy, ce))
        idx = ESTACIONES_ORDEN.index(ce) + 1
        if idx >= len(ESTACIONES_ORDEN):
            idx = 0
            cy += 1
        ce = ESTACIONES_ORDEN[idx]

    mes_inicio_est = {"Verano": "12-01", "Otoño": "03-01", "Invierno": "06-01", "Primavera": "09-01"}
    for sy, se in seen_est:
        anio_ini = sy - 1 if se == "Verano" else sy
        f_ini_est = f"{anio_ini:04d}-{mes_inicio_est[se]}"
        k = f"{sy}-{se}"
        estacional.append(_resumir_bucket(k, f_ini_est, obs_por_est.get((sy, se), []), cli_por_est.get((sy, se), [])))

    return {
        "semanal": semanal,
        "mensual": mensual,
        "estacional": estacional,
    }


def _imagenes_disponibles(slug: str, site_id: str) -> tuple[list[dict[str, str]], str | None]:
    carpeta = dir_web(slug) / "img" / site_id
    if not carpeta.exists():
        return [], None
    salida: list[dict[str, str]] = []
    for f_color in sorted(carpeta.glob("*_color.png")):
        fecha_str = f_color.name.replace("_color.png", "")
        f_ndvi = carpeta / f"{fecha_str}_ndvi.png"
        f_ndvi_hd = carpeta / f"{fecha_str}_ndvi_hd.png"
        f_ndmi = carpeta / f"{fecha_str}_ndmi.png"
        if f_ndvi.exists() or f_ndvi_hd.exists():
            item: dict[str, str] = {
                "fecha": fecha_str,
                "color": f"data/{slug}/img/{site_id}/{f_color.name}",
                "ndvi": f"data/{slug}/img/{site_id}/{(f_ndvi_hd if f_ndvi_hd.exists() else f_ndvi).name}",
            }
            if f_ndmi.exists():
                item["ndmi"] = f"data/{slug}/img/{site_id}/{f_ndmi.name}"
            salida.append(item)
    f_lst = carpeta / "lst_verano.png"
    img_lst = f"data/{slug}/img/{site_id}/lst_verano.png" if f_lst.exists() else None
    return salida, img_lst


def ejecutar_todas(comunas: list[dict[str, Any]], cfg: dict[str, Any]) -> None:
    """Ejecuta el paso 04 integrando multi-satélite (02c), vulnerabilidad térmica Censo y prioridad satelital."""
    fecha_ref = fecha_proceso()
    pesos = cfg["pesos_vulnerabilidad"]
    cfg_conf = cfg["confianza"]

    datos_comuna: dict[str, dict[str, Any]] = {}
    pool_sitios: list[tuple[str, dict[str, Any]]] = []

    for c in comunas:
        slug = c["slug"]
        raw = dir_raw(slug)
        requeridos = [raw / n for n in ("paso01.json", "paso02.json", "clima.json", "paso03.json", "paso03b.json", "limite.geojson")]
        if not all(r.exists() for r in requeridos):
            print(f"[04] Omitiendo {c['nombre']} ({slug}): faltan insumos previos en data/raw/{slug}")
            continue

        p1 = leer_json(raw / "paso01.json")
        p2 = leer_json(raw / "paso02.json")
        clima = leer_json(raw / "clima.json")
        p3 = leer_json(raw / "paso03.json")
        p3b = leer_json(raw / "paso03b.json")
        p2c = leer_json(raw / "paso02c.json") if (raw / "paso02c.json").exists() else {}
        aire = leer_json(raw / "aire.json") if (raw / "aire.json").exists() else p2c.get("aire", {})
        limite = leer_json(raw / "limite.geojson")

        datos_comuna[slug] = {
            "meta": c,
            "p1": p1,
            "p2": p2,
            "clima": clima,
            "p3": p3,
            "p3b": p3b,
            "p2c": p2c,
            "aire": aire,
            "limite": limite,
        }

        sitios_p3 = p3.get("sitios", {})
        sitios_p3b = p3b.get("sitios", {})
        sitios_p2c = p2c.get("sitios", {})
        sitios_p2 = p2.get("sitios", {})

        for s in p1.get("sitios", []):
            sid = s["site_id"]
            s3 = sitios_p3.get(sid, {})
            s3b = sitios_p3b.get(sid, {})
            s2c = sitios_p2c.get(sid, {})
            s2 = sitios_p2.get(sid, {})
            base = calcular_baseline_vegetacion(s2.get("obs", []), fecha_ref, cfg, clima_dias=clima.get("dias", []))

            brecha_raw = s3b.get("brecha_dosel_puntos") or 0.0
            imp_raw = s2c.get("impermeable_400m_pct") or 0.0
            deficit_mix = brecha_raw + 0.35 * imp_raw

            ndvi_ef = base["ndvi_actual"] if base["ndvi_actual"] is not None else s2c.get("ndvi_adaptativo")
            # Severidad de estrés vegetal: combina anomalía z (si existe) y bajo NDVI absoluto
            estres_raw = -(min(base["ndvi_z"] or 0.0, base["ndmi_z"] or 0.0)) * 20.0 + (
                max(0.0, 0.55 - float(ndvi_ef)) * 100.0 if _es_finito(ndvi_ef) else 0.0
            )

            pool_sitios.append((
                slug,
                {
                    "site_id": sid,
                    "base": base,
                    "pct_60_mas": s3.get("pct_60_mas_400m"),
                    "densidad": s3.get("densidad_hab_ha"),
                    "verde_per_capita": s3.get("verde_per_capita_m2"),
                    "pct_techo_calor": s2c.get("pct_techo_calor_400m"),
                    "pct_hacinamiento": s2c.get("pct_hacinamiento_400m"),
                    "lst_verano_c": s2c.get("lst_verano_c"),
                    "deficit_dosel_imp": deficit_mix,
                    "estres_raw": estres_raw if (_es_finito(ndvi_ef) or _es_finito(base["ndvi_z"])) else None,
                },
            ))

    if not pool_sitios:
        raise RuntimeError("[04] No hay comunas con insumos completos para procesar.")

    p_edad60_global = percentiles_rango([x[1]["pct_60_mas"] for x in pool_sitios], invertir=False)
    p_densidad_global = percentiles_rango([x[1]["densidad"] for x in pool_sitios], invertir=False)
    p_bajo_verde_global = percentiles_rango([x[1]["verde_per_capita"] for x in pool_sitios], invertir=True)
    p_techo_global = percentiles_rango([x[1]["pct_techo_calor"] for x in pool_sitios], invertir=False)
    p_hacin_global = percentiles_rango([x[1]["pct_hacinamiento"] for x in pool_sitios], invertir=False)
    p_lst_global = percentiles_rango([x[1]["lst_verano_c"] for x in pool_sitios], invertir=False)
    p_dosel_global = percentiles_rango([x[1]["deficit_dosel_imp"] for x in pool_sitios], invertir=False)
    p_estres_global = percentiles_rango([x[1]["estres_raw"] for x in pool_sitios], invertir=False)

    pct_map: dict[tuple[str, str], dict[str, Any]] = {}
    for pos, (slug, item) in enumerate(pool_sitios):
        pct_map[(slug, item["site_id"])] = {
            "base": item["base"],
            "p_edad60": p_edad60_global[pos],
            "p_densidad": p_densidad_global[pos],
            "p_bajo_verde": p_bajo_verde_global[pos],
            "p_techo_calor": p_techo_global[pos],
            "p_hacinamiento": p_hacin_global[pos],
            "p_calor_lst": p_lst_global[pos],
            "p_brecha_dosel": p_dosel_global[pos],
            "p_estres_veg": p_estres_global[pos],
        }

    resumen_comunas: list[dict[str, Any]] = []

    for slug, pack in datos_comuna.items():
        p1 = pack["p1"]
        p2 = pack["p2"]
        clima = pack["clima"]
        p3 = pack["p3"]
        p3b = pack["p3b"]
        p2c = pack["p2c"]
        aire = pack["aire"]
        limite = pack["limite"]
        c_info = p1["comuna"]

        desde_iso = str(p2.get("desde") or clima["dias"][0][0])
        hasta_iso = str(p2.get("hasta") or clima["dias"][-1][0])
        escenas = p2.get("escenas", [])
        clima_dias = clima.get("dias", [])

        features: list[dict[str, Any]] = []
        series_web: dict[str, dict[str, list[list[Any]]]] = {}
        paso04_sitios: dict[str, dict[str, Any]] = {}
        csv_filas: list[list[Any]] = []

        counts_estado = {"critico": 0, "prioritario": 0, "vigilar": 0, "estable": 0, "sin_datos": 0}
        vulns_validas: list[float] = []
        ndvis_validos: list[float] = []
        lst_validos: list[float] = []
        brechas_validas: list[float] = []
        confs_pct: list[int] = []
        arboles_min_tot = 0
        arboles_max_tot = 0
        nombres_norm = _normalizar_nombres_sitios(p1.get("sitios", []), c_info["nombre"])

        for s in p1.get("sitios", []):
            sid = s["site_id"]
            nombre_vis, nombre_base = nombres_norm.get(sid, (s["nombre"], s["nombre"]))
            area_m2 = float(s.get("area_m2", 0.0))
            s2 = p2.get("sitios", {}).get(sid, {})
            s3 = p3.get("sitios", {}).get(sid, {})
            s3b = p3b.get("sitios", {}).get(sid, {})
            s2c = p2c.get("sitios", {}).get(sid, {})

            pm = pct_map[(slug, sid)]
            base = dict(pm["base"])
            obs = s2.get("obs", [])
            pix10 = int(s2.get("pixeles_10m", 0))

            # Recuperación de sitios angostos sin recorte interior de 10 m
            lectura_adap = bool(s2c.get("lectura_borde_adaptativo", False))
            if base["ndvi_actual"] is None and s2c.get("ndvi_adaptativo") is not None:
                base["ndvi_actual"] = s2c.get("ndvi_adaptativo")
                base["ndmi_actual"] = s2c.get("ndmi_adaptativo")
                base["fecha_ultima_obs"] = base["fecha_ultima_obs"] or p2c.get("fecha_escena_hd")
                if base["fecha_ultima_obs"]:
                    base["dias_desde_ultima"] = (fecha_ref - date.fromisoformat(base["fecha_ultima_obs"])).days
                base["pixeles_validos_ult"] = int(s2c.get("pixeles_adaptativos") or 0)
                base["baseline_tipo"] = "adaptativo_reciente"
                lectura_adap = True

            # Vulnerabilidad térmica-habitacional (reemplaza el sesgo por edad en Vitacura)
            vuln_termica = calcular_vulnerabilidad(
                pm["p_techo_calor"],
                pm["p_hacinamiento"],
                pm["p_bajo_verde"],
                {"pct_60_mas": 0.4, "densidad": 0.3, "bajo_verde_per_capita": 0.3},
            )
            if vuln_termica is None:
                vuln_termica = calcular_vulnerabilidad(pm["p_edad60"], pm["p_densidad"], pm["p_bajo_verde"], pesos)

            # Prioridad biofísica 100% satelital (Landsat LST + WorldCover Dosel/Impermeable + Estrés Sentinel)
            prioridad_sat = calcular_vulnerabilidad(
                pm["p_calor_lst"],
                pm["p_brecha_dosel"],
                pm["p_estres_veg"] if pm["p_estres_veg"] is not None else 25.0,
                {"pct_60_mas": 0.40, "densidad": 0.35, "bajo_verde_per_capita": 0.25},
            )

            confianza, razones_conf = evaluar_confianza(
                area_m2, base["n_obs"], base["dias_desde_ultima"], max(pix10, base["pixeles_validos_ult"]), cfg_conf
            )
            if lectura_adap and "Lectura satelital incluye borde por área angosta" not in razones_conf:
                razones_conf.insert(0, "Lectura satelital adaptativa (sitio angosto recuperado sin erosión 10 m)")
                confianza = "baja"
            confianza_pct = calcular_confianza_pct(
                area_m2=area_m2,
                n_obs=base["n_obs"],
                dias_desde_ultima=base["dias_desde_ultima"],
                pixeles_10m=max(pix10, base["pixeles_validos_ult"]),
                tiene_lst=_es_finito(s2c.get("lst_verano_c")),
                tiene_wc=_es_finito(s3b.get("cobertura_arboles_400m_pct")),
                tiene_censo=_es_finito(s2c.get("pct_techo_calor_400m")) or _es_finito(s3.get("pct_60_mas_400m")),
            )
            salud_vegetal_pct = calcular_salud_vegetal_pct(base["ndvi_actual"])
            confs_pct.append(confianza_pct)

            brecha_pts = s3b.get("brecha_dosel_puntos")
            lst_val = s2c.get("lst_verano_c")
            estado, _ = clasificar_estado(
                vuln_termica, base["ndvi_z"], base["ndmi_z"], brecha_pts, base["n_obs"], cfg,
                lst_verano_c=lst_val, ndvi_actual=base["ndvi_actual"],
            )
            prioridad_integrada = round(
                0.70 * float(prioridad_sat or 0.0) + 0.30 * float(vuln_termica or 0.0), 1
            )

            counts_estado[estado] = counts_estado.get(estado, 0) + 1
            if _es_finito(vuln_termica):
                vulns_validas.append(float(vuln_termica))
            if _es_finito(base["ndvi_actual"]):
                ndvis_validos.append(float(base["ndvi_actual"]))
            if _es_finito(lst_val):
                lst_validos.append(float(lst_val))
            if _es_finito(brecha_pts):
                brechas_validas.append(float(brecha_pts))
            arboles_min_tot += int(s3b.get("arboles_necesarios_min") or 0)
            arboles_max_tot += int(s3b.get("arboles_necesarios_max") or 0)

            imgs, img_lst = _imagenes_disponibles(slug, sid)
            series_sitio = agregar_series(obs, escenas, clima_dias, desde_iso, hasta_iso)
            series_web[sid] = series_sitio

            for gran in ("mensual", "semanal", "estacional"):
                for fila in series_sitio[gran]:
                    csv_filas.append([
                        gran,
                        sid,
                        nombre_vis,
                        fila[0],
                        fila[1],
                        fila[2],
                        fila[3],
                        fila[4],
                        fila[5],
                        fila[6],
                        fila[7],
                        "",
                    ])

            props = {
                "site_id": sid,
                "nombre": nombre_vis,
                "nombre_base": nombre_base,
                "nombre_osm_raw": s["nombre"],
                "con_nombre": bool(s.get("con_nombre", False)),
                "tipo": s.get("tipo", "parque"),
                "clase_osm": s.get("clase_osm", "park"),
                "osm_url": s.get("osm_url", ""),
                "comuna": c_info["nombre"],
                "comuna_slug": slug,
                "area_m2": _limpiar_num(area_m2, 1),
                "centro": s.get("centro"),
                "pop_400m": s3.get("pop_400m"),
                "pct_60_mas_400m": s3.get("pct_60_mas_400m"),
                "densidad_hab_ha": s3.get("densidad_hab_ha"),
                "verde_osm_entorno_m2": s3.get("verde_osm_entorno_m2"),
                "verde_per_capita_m2": s3.get("verde_per_capita_m2"),
                "viviendas_400m": s2c.get("viviendas_400m"),
                "pct_techo_calor_400m": s2c.get("pct_techo_calor_400m"),
                "pct_hacinamiento_400m": s2c.get("pct_hacinamiento_400m"),
                "pct_mat_deficiente_400m": s2c.get("pct_mat_deficiente_400m"),
                "pct_infancia_0_5_400m": s2c.get("pct_infancia_0_5_400m"),
                "p_edad60": pm["p_edad60"],
                "p_densidad": pm["p_densidad"],
                "p_bajo_verde": pm["p_bajo_verde"],
                "p_techo_calor": pm["p_techo_calor"],
                "p_hacinamiento": pm["p_hacinamiento"],
                "p_calor_lst": pm["p_calor_lst"],
                "p_brecha_dosel": pm["p_brecha_dosel"],
                "p_estres_veg": pm["p_estres_veg"],
                "vulnerabilidad": vuln_termica,
                "vulnerabilidad_termica": vuln_termica,
                "prioridad_satelital": prioridad_sat,
                "prioridad_score": prioridad_integrada,
                "estado": estado,
                "confianza": confianza,
                "confianza_pct": confianza_pct,
                "salud_vegetal_pct": salud_vegetal_pct,
                "razones_confianza": razones_conf,
                "lectura_borde_adaptativo": lectura_adap,
                "pixeles_10m": pix10 or base["pixeles_validos_ult"],
                "pixeles_20m": int(s2.get("pixeles_20m", 0)),
                "lst_verano_c": lst_val,
                "lst_pico_c": s2c.get("lst_pico_c"),
                "lst_entorno_400m_c": s2c.get("lst_entorno_400m_c"),
                "brecha_calor_vs_vitacura_c": s2c.get("brecha_calor_vs_vitacura_c"),
                "savi_actual": s2c.get("savi_actual"),
                "ndwi_actual": s2c.get("ndwi_actual"),
                "bsi_actual": s2c.get("bsi_actual"),
                "cobertura_arboles_400m_pct": s3b.get("cobertura_arboles_400m_pct"),
                "impermeable_400m_pct": s2c.get("impermeable_400m_pct"),
                "pasto_matorral_400m_pct": s2c.get("pasto_matorral_400m_pct"),
                "suelo_desnudo_400m_pct": s2c.get("suelo_desnudo_400m_pct"),
                "brecha_dosel_puntos": brecha_pts,
                "brecha_dosel_ha": s3b.get("brecha_dosel_ha"),
                "arboles_necesarios_min": s3b.get("arboles_necesarios_min"),
                "arboles_necesarios_max": s3b.get("arboles_necesarios_max"),
                "costo_clp_min": s3b.get("costo_clp_min"),
                "costo_clp_max": s3b.get("costo_clp_max"),
                "senales": [],
                "senal_principal": "sin_senal",
                "imagenes": imgs,
                "imagen_lst": img_lst,
                **base,
            }
            features.append({
                "type": "Feature",
                "properties": props,
                "geometry": s["geometria"],
            })
            paso04_sitios[sid] = props

        features.sort(
            key=lambda f: (
                -(f["properties"]["prioridad_satelital"] or 0.0),
                -(f["properties"]["prioridad_score"] or 0.0),
                f["properties"]["site_id"],
            )
        )
        for rank, f in enumerate(features, start=1):
            f["properties"]["ranking_comuna"] = rank
            paso04_sitios[f["properties"]["site_id"]]["ranking_comuna"] = rank

        web_dir = dir_web(slug)
        geojson_obj = {
            "type": "FeatureCollection",
            "comuna": c_info,
            "fecha_proceso": fecha_ref.isoformat(),
            "pesos_default": pesos,
            "umbral_vulnerabilidad_alta": cfg["umbral_vulnerabilidad_alta"],
            "aire": aire,
            "features": features,
        }
        series_payload = {
            "comuna": slug,
            "desde": desde_iso,
            "hasta": hasta_iso,
            "columnas": ["periodo", "fecha_inicio", "ndvi", "ndmi", "pixeles_validos", "nubes_escena_pct", "temp_max_c", "lluvia_mm"],
            "sitios": series_web,
        }

        escribir_json(dir_raw(slug) / "paso04.json", {
            "comuna": c_info,
            "fecha_proceso": fecha_ref.isoformat(),
            "sitios": paso04_sitios,
        })
        escribir_json(web_dir / "sitios.geojson", geojson_obj)
        escribir_js(web_dir / "sitios.js", f"sitios_{slug}", geojson_obj)
        escribir_json(web_dir / "limite.geojson", limite)
        escribir_js(web_dir / "limite.js", f"limite_{slug}", limite)
        escribir_js(web_dir / "series.js", f"series_{slug}", series_payload)

        with (web_dir / "series.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["granularidad", "site_id", "sitio", "periodo", "fecha_inicio", "ndvi", "ndmi", "pixeles_validos", "nubes_escena_pct", "temp_max_c", "lluvia_mm", "senal"])
            writer.writerows(csv_filas)

        temps_max = [float(c[2]) for c in clima_dias if _es_finito(c[2])]
        lluvia_tot = sum(float(c[3]) for c in clima_dias if _es_finito(c[3]))
        dosel_comuna = mod_03b.brecha_dosel(
            float(c_info.get("area_km2") or 0.0) * 1e6,
            float(p3b.get("cobertura_arboles_comuna_pct") or 0.0),
            cfg,
        )
        resumen_comunas.append({
            "slug": slug,
            "nombre": c_info["nombre"],
            "cut": c_info.get("cut"),
            "area_km2": c_info.get("area_km2"),
            "centro": c_info.get("centro"),
            "bbox": c_info.get("bbox"),
            "poblacion_aprox": p3.get("poblacion_comuna_aprox"),
            "cobertura_arboles_comuna_pct": p3b.get("cobertura_arboles_comuna_pct"),
            "impermeable_comuna_pct": p2c.get("impermeable_comuna_pct"),
            "lst_verano_mediana_c": p2c.get("comuna_lst_verano_c"),
            "lst_sitios_mediana_c": _limpiar_num(statistics.fmean(lst_validos), 1) if lst_validos else None,
            "pct_techo_calor_comuna": p2c.get("pct_techo_calor_comuna"),
            "pct_hacinamiento_comuna": p2c.get("pct_hacinamiento_comuna"),
            "aire": aire,
            "n_sitios": len(features),
            "n_sitios_con_ndvi": sum(1 for f in features if f["properties"]["ndvi_actual"] is not None),
            "n_sitios_imagen": sum(1 for f in features if f["properties"]["imagenes"] or f["properties"]["imagen_lst"]),
            "estados": counts_estado,
            "pct_vulnerabilidad_alta": _limpiar_num((sum(1 for v in vulns_validas if v >= cfg["umbral_vulnerabilidad_alta"]) / len(vulns_validas) * 100.0) if vulns_validas else None, 1),
            "vulnerabilidad_media": _limpiar_num(statistics.fmean(vulns_validas), 1) if vulns_validas else None,
            "ndvi_medio": _limpiar_num(statistics.fmean(ndvis_validos), 3) if ndvis_validos else None,
            "brecha_dosel_media_pts": _limpiar_num(statistics.fmean(brechas_validas), 1) if brechas_validas else None,
            "brecha_dosel_comuna_puntos": dosel_comuna["brecha_dosel_puntos"],
            "brecha_dosel_comuna_ha": dosel_comuna["brecha_dosel_ha"],
            "arboles_necesarios_min_total": dosel_comuna["arboles_necesarios_min"],
            "arboles_necesarios_max_total": dosel_comuna["arboles_necesarios_max"],
            "arboles_entorno_sitios_min": arboles_min_tot,
            "arboles_entorno_sitios_max": arboles_max_tot,
            "temp_max_periodo_c": _limpiar_num(max(temps_max), 1) if temps_max else None,
            "lluvia_periodo_mm": _limpiar_num(lluvia_tot, 1),
            "n_escenas_s2": len(escenas),
            "n_escenas_landsat": len(p2c.get("escenas_landsat", [])),
            "escenas_bandera_offset_contradicha": p2.get("escenas_bandera_offset_contradicha", 0),
            "confianza_comuna_pct": int(round(statistics.fmean(confs_pct))) if confs_pct else 92,
            "fuentes_activas": 5,
        })
        print(f"  [04] {c_info['nombre']}: {len(features)} sitios | LST={p2c.get('comuna_lst_verano_c')} °C | críticos={counts_estado['critico']} prioritarios={counts_estado['prioritario']} vigilar={counts_estado['vigilar']}")

    resumen_obj = {
        "fecha_proceso": fecha_ref.isoformat(),
        "pesos_default": pesos,
        "umbral_vulnerabilidad_alta": cfg["umbral_vulnerabilidad_alta"],
        "umbral_estres_z": cfg["umbral_estres_z"],
        "meta_dosel_pct": cfg["dosel"]["meta_pct"],
        "comunas": resumen_comunas,
    }
    escribir_json(WEB_DATA / "resumen.json", resumen_obj)
    escribir_js(WEB_DATA / "resumen.js", "resumen", resumen_obj)


if __name__ == "__main__":
    cfg = cargar_config()
    ejecutar_todas(cfg["comunas"], cfg)
