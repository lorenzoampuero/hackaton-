"""Paso 06: Paquetes de caso verificados, carteras de inversión ejecutivas e informes listos para el visor."""

from __future__ import annotations

import importlib
from typing import Any

from pipeline.comun import (
    RAW,
    WEB_DATA,
    cargar_config,
    dir_web,
    escribir_js,
    escribir_json,
    fecha_proceso,
    leer_json,
    redondear,
)
from pipeline.verificar_informe import verificar_informe

mod_05 = importlib.import_module("pipeline.05_senales")
mod_07 = importlib.import_module("pipeline.07_informe_ia")


def construir_paquete_sitio(
    caso_id: str,
    tipo_caso: str,
    titulo: str,
    pregunta_decision: str,
    comuna_resumen: dict[str, Any],
    sitio_props: dict[str, Any],
    catalogo: dict[str, Any],
    comuna_control: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Empaqueta las cifras multi-satélite y censales verificadas de un sitio."""
    area_m2 = float(sitio_props.get("area_m2") or 0.0)
    ev = sitio_props.get("evento_calor")
    aire = comuna_resumen.get("aire") or {}

    interv_ids = {i["id"] for i in sitio_props.get("intervenciones_sugeridas", [])}
    fondo_ids = {f["id"] for f in sitio_props.get("fondos_sugeridos", [])}
    intervs_full = [i for i in catalogo.get("intervenciones", []) if i["id"] in interv_ids] or catalogo.get("intervenciones", [])[:2]
    fondos_full = [f for f in catalogo.get("fondos_publicos", []) if f["id"] in fondo_ids] or catalogo.get("fondos_publicos", [])[:2]

    numeros: dict[str, Any] = {
        "area_m2": sitio_props.get("area_m2"),
        "area_ha": redondear(area_m2 / 10000.0, 2),
        "pop_400m": sitio_props.get("pop_400m"),
        "pct_60_mas_400m": sitio_props.get("pct_60_mas_400m"),
        "pct_techo_calor_400m": sitio_props.get("pct_techo_calor_400m"),
        "pct_hacinamiento_400m": sitio_props.get("pct_hacinamiento_400m"),
        "pct_mat_deficiente_400m": sitio_props.get("pct_mat_deficiente_400m"),
        "pct_infancia_0_5_400m": sitio_props.get("pct_infancia_0_5_400m"),
        "densidad_hab_ha": sitio_props.get("densidad_hab_ha"),
        "verde_per_capita_m2": sitio_props.get("verde_per_capita_m2"),
        "vulnerabilidad": sitio_props.get("vulnerabilidad"),
        "prioridad_satelital": sitio_props.get("prioridad_satelital"),
        "prioridad_score": sitio_props.get("prioridad_score"),
        "n_obs": sitio_props.get("n_obs"),
        "pixeles_10m": sitio_props.get("pixeles_10m"),
        "ndvi_actual": sitio_props.get("ndvi_actual"),
        "ndvi_ref": sitio_props.get("ndvi_ref"),
        "ndvi_z": sitio_props.get("ndvi_z"),
        "ndvi_delta_pct": sitio_props.get("ndvi_delta_pct"),
        "ndmi_actual": sitio_props.get("ndmi_actual"),
        "ndmi_ref": sitio_props.get("ndmi_ref"),
        "ndmi_z": sitio_props.get("ndmi_z"),
        "savi_actual": sitio_props.get("savi_actual"),
        "ndwi_actual": sitio_props.get("ndwi_actual"),
        "bsi_actual": sitio_props.get("bsi_actual"),
        "lst_verano_c": sitio_props.get("lst_verano_c"),
        "lst_pico_c": sitio_props.get("lst_pico_c"),
        "lst_entorno_400m_c": sitio_props.get("lst_entorno_400m_c"),
        "brecha_calor_vs_vitacura_c": sitio_props.get("brecha_calor_vs_vitacura_c"),
        "cobertura_arboles_400m_pct": sitio_props.get("cobertura_arboles_400m_pct"),
        "impermeable_400m_pct": sitio_props.get("impermeable_400m_pct"),
        "suelo_desnudo_400m_pct": sitio_props.get("suelo_desnudo_400m_pct"),
        "brecha_dosel_puntos": sitio_props.get("brecha_dosel_puntos"),
        "brecha_dosel_ha": sitio_props.get("brecha_dosel_ha"),
        "arboles_necesarios_min": sitio_props.get("arboles_necesarios_min"),
        "arboles_necesarios_max": sitio_props.get("arboles_necesarios_max"),
        "costo_clp_min": sitio_props.get("costo_clp_min"),
        "costo_clp_max": sitio_props.get("costo_clp_max"),
        "cobertura_arboles_comuna_pct": comuna_resumen.get("cobertura_arboles_comuna_pct"),
        "pct_vulnerabilidad_alta": comuna_resumen.get("pct_vulnerabilidad_alta"),
        "temp_max_periodo_c": comuna_resumen.get("temp_max_periodo_c"),
        "lluvia_periodo_mm": comuna_resumen.get("lluvia_periodo_mm"),
        "pm2_5_media": aire.get("pm2_5_media"),
        "ranking_comuna": sitio_props.get("ranking_comuna"),
        "n_sitios_comuna": comuna_resumen.get("n_sitios"),
        "confianza_pct": sitio_props.get("confianza_pct"),
        "salud_vegetal_pct": sitio_props.get("salud_vegetal_pct"),
    }
    if ev:
        numeros.update({
            "temp_max_evento_c": ev.get("temp_max_evento_c"),
            "evento_ndvi_min": ev.get("ndvi_min"),
            "evento_ndvi_z_min": ev.get("ndvi_z_min"),
            "evento_ndmi_min": ev.get("ndmi_min"),
            "evento_ndmi_z_min": ev.get("ndmi_z_min"),
        })

    return {
        "caso_id": caso_id,
        "tipo_caso": tipo_caso,
        "titulo": titulo,
        "pregunta_decision": pregunta_decision,
        "fecha_generacion": fecha_proceso().isoformat(),
        "comuna": {
            "slug": comuna_resumen["slug"],
            "nombre": comuna_resumen["nombre"],
            "poblacion_aprox": comuna_resumen.get("poblacion_aprox"),
            "cobertura_arboles_comuna_pct": comuna_resumen.get("cobertura_arboles_comuna_pct"),
            "pct_vulnerabilidad_alta": comuna_resumen.get("pct_vulnerabilidad_alta"),
            "lst_verano_mediana_c": comuna_resumen.get("lst_verano_mediana_c"),
            "temp_max_periodo_c": comuna_resumen.get("temp_max_periodo_c"),
        },
        "comuna_control": comuna_control,
        "aire": aire,
        "sitio": {
            "site_id": sitio_props["site_id"],
            "nombre": sitio_props["nombre"],
            "estado": sitio_props.get("estado"),
            "confianza": sitio_props.get("confianza"),
            "fecha_ultima_obs": sitio_props.get("fecha_ultima_obs"),
            "centro": sitio_props.get("centro"),
            "osm_url": sitio_props.get("osm_url"),
            "imagenes": sitio_props.get("imagenes", []),
            "imagen_lst": sitio_props.get("imagen_lst"),
        },
        "senales": sitio_props.get("senales", []),
        "evento_calor": ev,
        "numeros": numeros,
        "constantes_permitidas": [0, 5, 100, 10, 20, 30, 60, 400, 5000, 6, 15, 45000, 70000, 2021, 2024],
        "intervenciones": intervs_full,
        "fondos_publicos": fondos_full,
    }


def _elegir_sitio_preferido(features: list[dict[str, Any]], criterio_fn) -> dict[str, Any] | None:
    """Prioriza sitios con nombre oficial e imágenes satelitales para casos insignia del pitch."""
    con_nombre_img = [f for f in features if f["properties"].get("con_nombre") and (f["properties"].get("imagenes") or f["properties"].get("imagen_lst"))]
    con_img = [f for f in features if f["properties"].get("imagenes") or f["properties"].get("imagen_lst")]
    pool = con_nombre_img or con_img or features
    if not pool:
        return None
    return max(pool, key=lambda f: criterio_fn(f["properties"]))["properties"]


def construir_paquete_cartera(
    scope_id: str,
    titulo: str,
    nombre_ambito: str,
    features_pool: list[dict[str, Any]],
    catalogo: dict[str, Any],
    n_top: int = 8,
) -> dict[str, Any]:
    """Construye el paquete verificable de los mayores casos donde invertir (para informe IA y archivos)."""
    ordenados = sorted(
        features_pool,
        key=lambda f: (
            1 if (f["properties"].get("con_nombre") and f["properties"].get("area_m2", 0) >= 3000) else 0,
            float(f["properties"].get("prioridad_satelital") or 0.0),
            float(f["properties"].get("prioridad_score") or 0.0),
        ),
        reverse=True,
    )
    elegidos: list[dict[str, Any]] = []
    vistos_base: set[str] = set()
    for f in ordenados:
        prop = f["properties"]
        clave_base = (
            f"{prop.get('comuna_slug', '')}:"
            f"{str(prop.get('nombre_base') or prop.get('nombre') or prop['site_id']).strip().lower()}"
        )
        if clave_base in vistos_base:
            continue
        vistos_base.add(clave_base)
        elegidos.append(prop)
        if len(elegidos) >= n_top:
            break
    if len(elegidos) < n_top:
        usados = {s["site_id"] for s in elegidos}
        for f in ordenados:
            if f["properties"]["site_id"] not in usados:
                elegidos.append(f["properties"])
            if len(elegidos) >= n_top:
                break

    cartera_sitios: list[dict[str, Any]] = []
    arb_min = 0
    arb_max = 0
    clp_min = 0
    clp_max = 0
    lst_vals: list[float] = []
    techos: list[float] = []

    for s in elegidos:
        amin = int(s.get("arboles_necesarios_min") or 0)
        amax = int(s.get("arboles_necesarios_max") or 0)
        cmin = int(s.get("costo_clp_min") or 0)
        cmax = int(s.get("costo_clp_max") or 0)
        arb_min += amin
        arb_max += amax
        clp_min += cmin
        clp_max += cmax
        if s.get("lst_verano_c") is not None:
            lst_vals.append(float(s["lst_verano_c"]))
        if s.get("pct_techo_calor_400m") is not None:
            techos.append(float(s["pct_techo_calor_400m"]))
        fondo_main = (s.get("fondos_sugeridos") or [{}])[0].get("nombre", "MINVU / PMU SUBDERE")
        cartera_sitios.append({
            "site_id": s["site_id"],
            "nombre": s["nombre"],
            "comuna": s["comuna"],
            "comuna_slug": s["comuna_slug"],
            "area_m2": s.get("area_m2"),
            "estado": s.get("estado"),
            "prioridad_satelital": s.get("prioridad_satelital"),
            "prioridad_score": s.get("prioridad_score"),
            "vulnerabilidad_termica": s.get("vulnerabilidad_termica"),
            "lst_verano_c": s.get("lst_verano_c"),
            "brecha_calor_vs_vitacura_c": s.get("brecha_calor_vs_vitacura_c"),
            "ndvi_actual": s.get("ndvi_actual"),
            "ndmi_actual": s.get("ndmi_actual"),
            "cobertura_arboles_400m_pct": s.get("cobertura_arboles_400m_pct"),
            "impermeable_400m_pct": s.get("impermeable_400m_pct"),
            "pct_techo_calor_400m": s.get("pct_techo_calor_400m"),
            "confianza_pct": s.get("confianza_pct"),
            "salud_vegetal_pct": s.get("salud_vegetal_pct"),
            "arboles_necesarios_min": amin,
            "arboles_necesarios_max": amax,
            "costo_clp_min": cmin,
            "costo_clp_max": cmax,
            "senales": s.get("senales", []),
            "fondo_sugerido": fondo_main,
            "imagenes": s.get("imagenes", []),
            "imagen_lst": s.get("imagen_lst"),
        })

    cartera_resumen = {
        "n_sitios_cartera": len(cartera_sitios),
        "arboles_min_cartera": arb_min,
        "arboles_max_cartera": arb_max,
        "costo_clp_min_cartera": clp_min,
        "costo_clp_max_cartera": clp_max,
        "lst_max_cartera_c": max(lst_vals) if lst_vals else None,
        "lst_media_cartera_c": redondear(sum(lst_vals) / len(lst_vals), 1) if lst_vals else None,
        "techo_calor_cartera_pct": redondear(sum(techos) / len(techos), 1) if techos else None,
    }

    return {
        "caso_id": f"inversion-{scope_id}",
        "tipo_caso": "Cartera ejecutiva de inversión",
        "titulo": titulo,
        "pregunta_decision": f"¿En qué parques y plazas de {nombre_ambito} conviene concentrar la inversión prioritaria según calor satelital y brecha de sombra?",
        "fecha_generacion": fecha_proceso().isoformat(),
        "comuna": {"slug": scope_id, "nombre": nombre_ambito},
        "sitio": {"site_id": "cartera", "nombre": nombre_ambito},
        "numeros": cartera_resumen,
        "cartera_resumen": cartera_resumen,
        "cartera_sitios": cartera_sitios,
        "constantes_permitidas": [0, 5, 100, 10, 20, 30, 50, 60, 400, 45000, 70000, 2021, 2024],
        "intervenciones": catalogo.get("intervenciones", []),
        "fondos_publicos": catalogo.get("fondos_publicos", []),
    }


def ejecutar_todas(comunas: list[dict[str, Any]], cfg: dict[str, Any]) -> None:
    """Genera los 3 casos del pitch, los informes Top 5 y las 5 carteras ejecutivas de inversión."""
    resumen = leer_json(WEB_DATA / "resumen.json")
    catalogo = mod_05.cargar_catalogo_intervenciones()
    res_idx = {c["slug"]: c for c in resumen.get("comunas", [])}

    sitios_por_comuna: dict[str, list[dict[str, Any]]] = {}
    todos_sitios: list[dict[str, Any]] = []
    for slug in res_idx:
        gj_path = dir_web(slug) / "sitios.geojson"
        if gj_path.exists():
            feats = leer_json(gj_path).get("features", [])
            sitios_por_comuna[slug] = feats
            todos_sitios.extend(feats)

    ctrl_vitacura = None
    if "vitacura" in res_idx:
        vc = res_idx["vitacura"]
        ctrl_vitacura = {
            "slug": "vitacura",
            "nombre": vc["nombre"],
            "cobertura_arboles_comuna_pct": vc.get("cobertura_arboles_comuna_pct"),
            "pct_vulnerabilidad_alta": vc.get("pct_vulnerabilidad_alta"),
            "lst_verano_mediana_c": vc.get("lst_verano_mediana_c"),
            "ndvi_medio": vc.get("ndvi_medio"),
        }

    casos_config = [
        {
            "slug": "cerro_navia",
            "caso_id": "caso-diagnostico-cerro-navia",
            "tipo": "Diagnóstico multi-satélite vs control",
            "titulo": "Cerro Navia vs Vitacura: isla de calor, déficit de sombra y techos vulnerables",
            "pregunta": "¿Dónde priorizar arborización en Cerro Navia combinando calor superficial Landsat, brecha arbórea y vivienda vulnerable?",
            "control": ctrl_vitacura,
            "score": lambda p: (p.get("prioridad_satelital") or 0.0, p.get("lst_verano_c") or 0.0, p.get("area_m2") or 0.0),
        },
        {
            "slug": "quilicura",
            "caso_id": "caso-evento-ola-calor-quilicura",
            "tipo": "Evento térmico + Landsat verano",
            "titulo": "Quilicura: respuesta vegetal alrededor del 29-ene-2026 y calor estival Landsat",
            "pregunta": "¿Qué parques con nombre en Quilicura registran mayor temperatura superficial e impacto tras el pico térmico estival?",
            "control": ctrl_vitacura,
            "score": lambda p: (
                -(min((p.get("evento_calor") or {}).get("ndvi_z_min") or 0.0, (p.get("evento_calor") or {}).get("ndmi_z_min") or 0.0)),
                p.get("lst_verano_c") or 0.0,
                p.get("prioridad_satelital") or 0.0,
            ),
        },
        {
            "slug": "san_miguel",
            "caso_id": "caso-oportunidad-san-miguel",
            "tipo": "Oportunidad de inversión y fondos",
            "titulo": "San Miguel: densificación impermeable y postulación rápida a fondos",
            "pregunta": "¿Qué parques urbanos de San Miguel ofrecen mejor retorno social y ambiental para postular a PMU SUBDERE / Espacios Públicos?",
            "control": ctrl_vitacura,
            "score": lambda p: (p.get("prioridad_satelital") or 0.0, p.get("brecha_dosel_puntos") or 0.0, p.get("area_m2") or 0.0),
        },
    ]

    casos_lista: list[dict[str, Any]] = []
    informes_mapa: dict[str, Any] = {}
    dir_casos_raw = RAW / "casos"
    dir_casos_web = WEB_DATA / "casos"
    dir_inf_web = WEB_DATA / "informes"
    dir_casos_raw.mkdir(parents=True, exist_ok=True)
    dir_casos_web.mkdir(parents=True, exist_ok=True)
    dir_inf_web.mkdir(parents=True, exist_ok=True)

    for cfg_caso in casos_config:
        slug = cfg_caso["slug"]
        if slug not in res_idx or not sitios_por_comuna.get(slug):
            continue
        sitio_sel = _elegir_sitio_preferido(sitios_por_comuna[slug], cfg_caso["score"])
        if not sitio_sel:
            continue
        paquete = construir_paquete_sitio(
            caso_id=cfg_caso["caso_id"],
            tipo_caso=cfg_caso["tipo"],
            titulo=cfg_caso["titulo"],
            pregunta_decision=cfg_caso["pregunta"],
            comuna_resumen=res_idx[slug],
            sitio_props=sitio_sel,
            catalogo=catalogo,
            comuna_control=cfg_caso["control"],
        )
        informe = mod_07.generar_informe_verificado(paquete)
        ok, errs = verificar_informe(informe, paquete)
        if not ok:
            raise RuntimeError(f"Verificación fallida en {cfg_caso['caso_id']}: {errs}")

        escribir_json(dir_casos_raw / f"{cfg_caso['caso_id']}.json", paquete)
        escribir_json(dir_casos_web / f"{cfg_caso['caso_id']}.json", paquete)
        escribir_json(dir_casos_raw / f"informe-{cfg_caso['caso_id']}.json", informe)
        escribir_json(dir_inf_web / f"informe-{cfg_caso['caso_id']}.json", informe)

        casos_lista.append(paquete)
        informes_mapa[cfg_caso["caso_id"]] = informe
        print(f"  [06] Caso verificado: {cfg_caso['caso_id']} -> sitio {sitio_sel['site_id']} ({sitio_sel['nombre']})")

    # Top 5 informes verificados por comuna
    for slug, feats in sitios_por_comuna.items():
        top5 = feats[:5]
        informes_top5: dict[str, Any] = {}
        for feat in top5:
            props = feat["properties"]
            cid = f"sitio-{slug}-{props['site_id']}"
            paq = construir_paquete_sitio(
                caso_id=cid,
                tipo_caso="Ficha prioritaria municipal",
                titulo=f"{props['nombre']} ({res_idx[slug]['nombre']})",
                pregunta_decision=f"¿Qué acción priorizar y verificar en terreno para {props['nombre']}?",
                comuna_resumen=res_idx[slug],
                sitio_props=props,
                catalogo=catalogo,
                comuna_control=ctrl_vitacura if slug != "vitacura" else None,
            )
            inf = mod_07.generar_informe_verificado(paq, intentar_llm=False)
            ok, errs = verificar_informe(inf, paq)
            if not ok:
                raise RuntimeError(f"Verificación Top 5 fallida en {cid}: {errs}")
            informes_top5[props["site_id"]] = {"paquete": paq, "informe": inf}
        escribir_js(dir_web(slug) / "informes_top5.js", f"informes_top5_{slug}", informes_top5)

    # Carteras ejecutivas de inversión (intercomunal + por cada comuna)
    carteras_inversion: dict[str, Any] = {}
    ambitos = [("intercomunal", "Gran Santiago (4 comunas analizadas)", todos_sitios)] + [
        (slug, res_idx[slug]["nombre"], feats) for slug, feats in sitios_por_comuna.items()
    ]
    for scope_id, nombre_amb, pool in ambitos:
        if not pool:
            continue
        paq_cart = construir_paquete_cartera(
            scope_id=scope_id,
            titulo=f"Dónde invertir primero — {nombre_amb}",
            nombre_ambito=nombre_amb,
            features_pool=pool,
            catalogo=catalogo,
            n_top=8,
        )
        inf_cart = mod_07.generar_informe_verificado(paq_cart)
        ok, errs = verificar_informe(inf_cart, paq_cart)
        if not ok:
            raise RuntimeError(f"Verificación cartera fallida en {scope_id}: {errs}")
        carteras_inversion[scope_id] = {"paquete": paq_cart, "informe": inf_cart}
        escribir_json(dir_casos_raw / f"inversion-{scope_id}.json", carteras_inversion[scope_id])
        print(f"  [06] Cartera inversión verificada: {scope_id} ({len(paq_cart['cartera_sitios'])} sitios)")

    escribir_json(WEB_DATA / "casos.json", casos_lista)
    escribir_js(WEB_DATA / "casos.js", "casos", casos_lista)
    escribir_json(WEB_DATA / "informes.json", informes_mapa)
    escribir_js(WEB_DATA / "informes.js", "informes", informes_mapa)
    escribir_json(WEB_DATA / "informes_inversion.json", carteras_inversion)
    escribir_js(WEB_DATA / "informes_inversion.js", "informes_inversion", carteras_inversion)
    escribir_js(WEB_DATA / "intervenciones.js", "catalogo", catalogo)


if __name__ == "__main__":
    cfg = cargar_config()
    ejecutar_todas(cfg["comunas"], cfg)
