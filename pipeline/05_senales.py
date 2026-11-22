"""Paso 05: Detección de señales tempranas y recomendación de intervenciones y fondos públicos."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

from pipeline.comun import (
    RAIZ,
    WEB_DATA,
    cargar_config,
    dir_raw,
    dir_web,
    escribir_js,
    escribir_json,
    leer_json,
)

ETIQUETAS_SENALES = {
    "isla_calor": "Isla de calor superficial estival (Landsat 8/9 LST)",
    "veg_caida": "Caída marcada de vigor vegetal (NDVI)",
    "estres_hidrico": "Estrés hídrico en vegetación / hojas (NDMI)",
    "brecha_dosel": "Brecha de dosel arbóreo bajo meta 30% (WorldCover 2021)",
    "calor_vulnerabilidad": "Alta exposición habitacional/térmica con déficit de sombra",
    "sin_senal": "Sin alerta activa o cobertura satelital insuficiente",
}


def _es_finito(val: Any) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool) and math.isfinite(val)


def cargar_catalogo_intervenciones(ruta: Path | None = None) -> dict[str, Any]:
    objetivo = ruta or (RAIZ / "data" / "intervenciones.json")
    return leer_json(objetivo)


def evaluar_senales_sitio(
    props: dict[str, Any],
    cfg: dict[str, Any],
    catalogo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evalúa señales tempranas determinísticas y asocia intervenciones y fondos públicos."""
    umbral_cfg = cfg["senales"]
    obs_min = int(cfg["confianza"]["observaciones_minimas"])
    umbral_vuln = float(cfg["umbral_vulnerabilidad_alta"])

    n_obs = int(props.get("n_obs") or 0)
    ndvi_z = props.get("ndvi_z")
    ndmi_z = props.get("ndmi_z")
    ndvi_delta = props.get("ndvi_delta_pct")
    brecha_pts = props.get("brecha_dosel_puntos")
    vuln = props.get("vulnerabilidad")
    ev = props.get("evento_calor") or {}

    senales: list[str] = []
    detalles: list[dict[str, Any]] = []

    if n_obs >= obs_min:
        caida_umbral = float(umbral_cfg["veg_caida_pct"])
        estr_umbral = float(umbral_cfg["estres_hidrico_z"])

        if (_es_finito(ndvi_delta) and float(ndvi_delta) <= caida_umbral) or (
            _es_finito(ndvi_z) and float(ndvi_z) <= estr_umbral
        ):
            senales.append("veg_caida")
            detalles.append({
                "codigo": "veg_caida",
                "etiqueta": ETIQUETAS_SENALES["veg_caida"],
                "evidencia": (
                    f"NDVI actual {props.get('ndvi_actual')} frente a referencia {props.get('ndvi_ref')} "
                    f"(variación {ndvi_delta}% | z={ndvi_z}). Requiere verificar en terreno."
                ),
            })

        ndmi_ev_z = ev.get("ndmi_z_min")
        if (_es_finito(ndmi_z) and float(ndmi_z) <= estr_umbral) or (
            _es_finito(ndmi_ev_z) and float(ndmi_ev_z) <= estr_umbral
        ):
            senales.append("estres_hidrico")
            detalles.append({
                "codigo": "estres_hidrico",
                "etiqueta": ETIQUETAS_SENALES["estres_hidrico"],
                "evidencia": (
                    f"NDMI (humedad foliar de la vegetación) z={ndmi_z}; "
                    f"mínimo en ventana estival z={ndmi_ev_z}. No mide humedad directa del suelo."
                ),
            })

    dosel_umbral = float(umbral_cfg["brecha_dosel_puntos"])
    if _es_finito(brecha_pts) and float(brecha_pts) >= dosel_umbral:
        senales.append("brecha_dosel")
        detalles.append({
            "codigo": "brecha_dosel",
            "etiqueta": ETIQUETAS_SENALES["brecha_dosel"],
            "evidencia": (
                f"Cobertura arbórea WorldCover 2021 de {props.get('cobertura_arboles_400m_pct')}% "
                f"en 400 m (brecha de {brecha_pts} puntos porcentuales bajo meta 30%)."
            ),
        })

    lst_c = props.get("lst_verano_c")
    brecha_calor = props.get("brecha_calor_vs_vitacura_c")
    if (_es_finito(lst_c) and float(lst_c) >= 36.5) or (_es_finito(brecha_calor) and float(brecha_calor) >= 4.0):
        senales.append("isla_calor")
        detalles.append({
            "codigo": "isla_calor",
            "etiqueta": ETIQUETAS_SENALES["isla_calor"],
            "evidencia": (
                f"Temperatura superficial estival Landsat 8/9 de {lst_c} °C en el sitio "
                f"(+{brecha_calor} °C frente a mediana de Vitacura; entorno 400 m: {props.get('lst_entorno_400m_c')} °C)."
            ),
        })

    ndvi_ev_z = ev.get("ndvi_z_min")
    ev_estres = (_es_finito(ndvi_ev_z) and float(ndvi_ev_z) <= float(cfg["umbral_estres_z"])) or (
        _es_finito(ev.get("ndmi_z_min")) and float(ev.get("ndmi_z_min")) <= float(cfg["umbral_estres_z"])
    )
    if _es_finito(vuln) and float(vuln) >= umbral_vuln and (
        "brecha_dosel" in senales or "estres_hidrico" in senales or "isla_calor" in senales or ev_estres
    ):
        senales.append("calor_vulnerabilidad")
        techo_pct = props.get("pct_techo_calor_400m")
        if _es_finito(lst_c) and _es_finito(techo_pct):
            ev_txt = (
                f"Vulnerabilidad térmica-habitacional {vuln}/100 ({techo_pct}% viviendas con techo zinc/fibrocemento/precario en 400 m) "
                f"coincide con temperatura superficial Landsat de {lst_c} °C y déficit de sombra."
            )
        else:
            ev_txt = (
                f"Vulnerabilidad {vuln}/100 ({props.get('pct_60_mas_400m')}% población 60+ años en 400 m) "
                f"coincide con déficit de sombra o estrés estival."
            )
        detalles.append({
            "codigo": "calor_vulnerabilidad",
            "etiqueta": ETIQUETAS_SENALES["calor_vulnerabilidad"],
            "evidencia": ev_txt,
        })

    if not senales:
        senales = ["sin_senal"]
        razon = (
            f"Solo {n_obs} observaciones válidas (mínimo {obs_min})"
            if n_obs < obs_min
            else "Indicadores dentro del rango esperado para el período"
        )
        detalles.append({
            "codigo": "sin_senal",
            "etiqueta": ETIQUETAS_SENALES["sin_senal"],
            "evidencia": razon,
        })

    interv_sugeridas: list[dict[str, Any]] = []
    fondos_sugeridos: list[dict[str, Any]] = []
    if catalogo:
        fondos_idx = {f["id"]: f for f in catalogo.get("fondos_publicos", [])}
        fondos_vistos: set[str] = set()
        senales_match = set(senales)
        if "isla_calor" in senales_match:
            senales_match.add("calor_vulnerabilidad")
        for interv in catalogo.get("intervenciones", []):
            aplica = set(interv.get("cuando_aplica", []))
            if aplica.intersection(senales_match):
                item = dict(interv)
                if interv["id"] == "arborizacion_calles" and props.get("arboles_necesarios_min") is not None:
                    item["arboles_min"] = props.get("arboles_necesarios_min")
                    item["arboles_max"] = props.get("arboles_necesarios_max")
                    item["costo_estimado_min_clp"] = props.get("costo_clp_min")
                    item["costo_estimado_max_clp"] = props.get("costo_clp_max")
                interv_sugeridas.append(item)
                fid = interv.get("fondo_principal")
                if fid and fid in fondos_idx and fid not in fondos_vistos:
                    fondos_vistos.add(fid)
                    fondos_sugeridos.append(fondos_idx[fid])

    return {
        "senales": senales,
        "senal_principal": senales[0],
        "etiqueta_principal": ETIQUETAS_SENALES[senales[0]],
        "detalles": detalles,
        "intervenciones_sugeridas": interv_sugeridas,
        "fondos_sugeridos": fondos_sugeridos,
    }


def _actualizar_series_csv(ruta_csv: Path, senal_por_sitio: dict[str, str]) -> None:
    if not ruta_csv.exists():
        return
    with ruta_csv.open("r", encoding="utf-8", newline="") as f:
        filas = list(csv.reader(f))
    if not filas:
        return
    cabecera = filas[0]
    if "site_id" not in cabecera or "senal" not in cabecera:
        return
    idx_sid = cabecera.index("site_id")
    idx_sen = cabecera.index("senal")
    for fila in filas[1:]:
        if len(fila) > max(idx_sid, idx_sen):
            fila[idx_sen] = senal_por_sitio.get(fila[idx_sid], "sin_senal")
    with ruta_csv.open("w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(filas)


def ejecutar_todas(comunas: list[dict[str, Any]], cfg: dict[str, Any]) -> None:
    """Ejecuta el paso 05 leyendo geojson/paso04 y anotando señales e intervenciones."""
    catalogo = cargar_catalogo_intervenciones()
    resumen_path = WEB_DATA / "resumen.json"
    resumen = leer_json(resumen_path) if resumen_path.exists() else {"comunas": []}
    resumen_idx = {c["slug"]: c for c in resumen.get("comunas", [])}

    for c in comunas:
        slug = c["slug"]
        web_dir = dir_web(slug)
        gj_path = web_dir / "sitios.geojson"
        if not gj_path.exists():
            print(f"[05] Omitiendo {c['nombre']} ({slug}): falta {gj_path}")
            continue

        gj = leer_json(gj_path)
        senal_por_sitio: dict[str, str] = {}
        conteo_senales: dict[str, int] = {k: 0 for k in ETIQUETAS_SENALES}
        paso05_sitios: dict[str, Any] = {}

        for feat in gj.get("features", []):
            props = feat["properties"]
            sid = props["site_id"]
            ev_s = evaluar_senales_sitio(props, cfg, catalogo)
            props["senales"] = ev_s["senales"]
            props["senal_principal"] = ev_s["senal_principal"]
            props["senales_detalle"] = ev_s["detalles"]
            props["intervenciones_sugeridas"] = [
                {
                    "id": i["id"],
                    "nombre": i["nombre"],
                    "unidad": i["unidad"],
                    "etiqueta_costo": i["etiqueta_costo"],
                    "costo_min_clp": i.get("costo_estimado_min_clp") or i.get("costo_rango_min_clp") or i.get("costo_unitario_min_clp"),
                    "costo_max_clp": i.get("costo_estimado_max_clp") or i.get("costo_rango_max_clp") or i.get("costo_unitario_max_clp"),
                    "fondo_principal": i.get("fondo_principal"),
                }
                for i in ev_s["intervenciones_sugeridas"]
            ]
            props["fondos_sugeridos"] = [
                {"id": f["id"], "nombre": f["nombre"], "institucion": f["institucion"]}
                for f in ev_s["fondos_sugeridos"]
            ]

            senal_por_sitio[sid] = ev_s["senal_principal"]
            for s_code in ev_s["senales"]:
                conteo_senales[s_code] = conteo_senales.get(s_code, 0) + 1
            paso05_sitios[sid] = ev_s

        escribir_json(gj_path, gj)
        escribir_js(web_dir / "sitios.js", f"sitios_{slug}", gj)
        escribir_json(dir_raw(slug) / "paso05.json", {
            "comuna": gj.get("comuna"),
            "conteo_senales": conteo_senales,
            "sitios": paso05_sitios,
        })
        _actualizar_series_csv(web_dir / "series.csv", senal_por_sitio)

        if slug in resumen_idx:
            resumen_idx[slug]["senales"] = conteo_senales

        print(f"  [05] {c['nombre']}: alertas={conteo_senales}")

    if resumen_path.exists():
        escribir_json(resumen_path, resumen)
        escribir_js(WEB_DATA / "resumen.js", "resumen", resumen)


if __name__ == "__main__":
    cfg = cargar_config()
    ejecutar_todas(cfg["comunas"], cfg)
