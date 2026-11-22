"""Pruebas unitarias y de integración de extremo a extremo para Pulmón Urbano."""

from __future__ import annotations

import importlib
import json
from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pytest

from pipeline import s2
from pipeline.comun import RAW, WEB_DATA, cargar_config
from pipeline.verificar_informe import verificar_informe

mod_03b = importlib.import_module("pipeline.03b_cobertura_arboles")
mod_04 = importlib.import_module("pipeline.04_prioridad")
mod_05 = importlib.import_module("pipeline.05_senales")
mod_06 = importlib.import_module("pipeline.06_paquete_caso")
mod_07 = importlib.import_module("pipeline.07_informe_ia")


def test_s2_offset_pendiente_y_norm():
    banda = {"scale": 0.0001, "offset": -0.1}
    valido = np.ones((30, 30), dtype=bool)
    ya_restado = np.full((30, 30), 400, dtype=np.int16)
    sin_restar = np.full((30, 30), 1400, dtype=np.int16)

    assert s2.offset_pendiente(ya_restado, valido, banda) is False
    assert s2.offset_pendiente(sin_restar, valido, banda) is True
    assert s2.offset_pendiente(ya_restado[:10, :10], valido[:10, :10], banda) is None

    ndvi = s2.indice_normalizado(
        np.array([[0.6]], dtype=np.float32),
        np.array([[0.2]], dtype=np.float32),
        np.array([[True]]),
    )
    assert pytest.approx(float(ndvi[0, 0]), abs=1e-5) == 0.5


def test_brecha_dosel_calculo():
    cfg = cargar_config()
    # Entorno de 100.000 m² con 10% de árboles: brecha de 20 puntos = 20.000 m² = 2,0 ha
    res = mod_03b.brecha_dosel(100000.0, 10.0, cfg)
    assert res["brecha_dosel_puntos"] == 20.0
    assert res["brecha_dosel_ha"] == 2.0
    assert res["arboles_necesarios_min"] == 400  # 20.000 / 50
    assert res["arboles_necesarios_max"] == 1000  # 20.000 / 20
    assert res["costo_clp_min"] == 400 * 45000
    assert res["costo_clp_max"] == 1000 * 70000


def test_percentiles_y_vulnerabilidad():
    pcts = mod_04.percentiles_rango([10.0, 20.0, 30.0, None], invertir=False)
    assert pcts == [0.0, 50.0, 100.0, None]
    pcts_inv = mod_04.percentiles_rango([10.0, 20.0, 30.0], invertir=True)
    assert pcts_inv == [100.0, 50.0, 0.0]

    v = mod_04.calcular_vulnerabilidad(80.0, 60.0, 40.0, {"pct_60_mas": 0.4, "densidad": 0.3, "bajo_verde_per_capita": 0.3})
    assert v == 62.0


def test_agregar_series_mantiene_huecos():
    obs = [
        ["2025-11-10", 0.35, 0.05, 80, 5.0],
        # diciembre 2025 sin observaciones libres de nubes -> hueco obligatorio
        ["2026-01-29", 0.18, -0.09, 75, 0.0],
    ]
    escenas = [
        {"fecha": "2025-11-10", "nubes_escena_pct": 5.0},
        {"fecha": "2026-01-29", "nubes_escena_pct": 0.0},
    ]
    clima = [
        ["2025-11-10", 19.0, 26.0, 0.0],
        ["2025-12-15", 22.0, 30.0, 0.0],
        ["2026-01-29", 25.0, 36.2, 0.0],
    ]
    ser = mod_04.agregar_series(obs, escenas, clima, "2025-11-01", "2026-01-31")
    mensual = {r[0]: r for r in ser["mensual"]}
    assert mensual["2025-11"][2] == 0.35
    assert mensual["2025-12"][2] is None  # nunca interpolado
    assert mensual["2025-12"][3] is None
    assert mensual["2026-01"][2] == 0.18


def test_evaluar_senales_y_confianza():
    cfg = cargar_config()
    conf_baja, razones = mod_04.evaluar_confianza(2500.0, 4, 20, 15, cfg["confianza"])
    assert conf_baja == "baja"
    assert len(razones) >= 3

    cat = mod_05.cargar_catalogo_intervenciones()
    props = {
        "n_obs": 15,
        "ndvi_actual": 0.21,
        "ndvi_ref": 0.34,
        "ndvi_z": -1.8,
        "ndvi_delta_pct": -38.2,
        "ndmi_actual": -0.05,
        "ndmi_z": -1.7,
        "brecha_dosel_puntos": 24.0,
        "cobertura_arboles_400m_pct": 6.0,
        "vulnerabilidad": 78.0,
        "pct_60_mas_400m": 22.0,
        "arboles_necesarios_min": 500,
        "arboles_necesarios_max": 1200,
        "costo_clp_min": 22500000,
        "costo_clp_max": 84000000,
        "evento_calor": {"ndvi_z_min": -1.9, "ndmi_z_min": -1.6},
    }
    props["lst_verano_c"] = 39.4
    props["brecha_calor_vs_vitacura_c"] = 4.5
    props["pct_techo_calor_400m"] = 75.0
    res = mod_05.evaluar_senales_sitio(props, cfg, cat)
    assert set(res["senales"]) == {"veg_caida", "estres_hidrico", "brecha_dosel", "isla_calor", "calor_vulnerabilidad"}
    assert len(res["intervenciones_sugeridas"]) >= 3
    assert len(res["fondos_sugeridos"]) >= 2


def test_verificar_informe_estricto():
    paquete = {
        "caso_id": "test-caso",
        "tipo_caso": "Diagnostico",
        "titulo": "Sitio de prueba",
        "pregunta_decision": "¿Priorizar arborización?",
        "comuna": {"slug": "cerro_navia", "nombre": "Cerro Navia", "cobertura_arboles_comuna_pct": 5.2, "pct_vulnerabilidad_alta": 55.0},
        "comuna_control": {"nombre": "Vitacura", "cobertura_arboles_comuna_pct": 33.5, "pct_vulnerabilidad_alta": 12.0, "ndvi_medio": 0.42},
        "sitio": {"site_id": "cn-w1", "nombre": "Parque Test", "estado": "critico", "confianza": "alta", "fecha_ultima_obs": "2026-11-13"},
        "senales": ["brecha_dosel", "estres_hidrico"],
        "evento_calor": {"fecha_pico_calor": "2026-01-29", "fecha_min_ndvi": "2026-02-02", "ndvi_min": 0.21, "ndvi_z_min": -1.8},
        "numeros": {
            "area_ha": 1.2,
            "vulnerabilidad": 75.0,
            "pop_400m": 3200,
            "pct_60_mas_400m": 21.4,
            "densidad_hab_ha": 140.0,
            "verde_per_capita_m2": 3.5,
            "n_obs": 18,
            "ndvi_actual": 0.25,
            "ndvi_ref": 0.34,
            "ndvi_z": -1.6,
            "ndmi_actual": -0.02,
            "ndmi_z": -1.7,
            "cobertura_arboles_400m_pct": 6.2,
            "brecha_dosel_puntos": 23.8,
            "arboles_necesarios_min": 400,
            "arboles_necesarios_max": 900,
            "costo_clp_min": 18000000,
            "costo_clp_max": 63000000,
            "cobertura_arboles_comuna_pct": 5.2,
            "pct_vulnerabilidad_alta": 55.0,
            "temp_max_periodo_c": 36.1,
        },
        "constantes_permitidas": [0, 100, 30, 400, 60, 2021, 2024],
        "intervenciones": [
            {
                "id": "arborizacion_calles",
                "nombre": "Arborización en calles",
                "cuando_aplica": ["brecha_dosel"],
                "descripcion": "Plantación en veredas y entorno cercano.",
            }
        ],
        "fondos_publicos": [
            {"id": "fpa_mma", "nombre": "FPA MMA", "institucion": "MMA", "requisito_evidencia": "Línea base verificable."}
        ],
    }

    inf = mod_07.construir_informe_plantilla(paquete)
    ok, errs = verificar_informe(inf, paquete)
    assert ok, f"Errores inesperados: {errs}"

    # Rechaza cifra inventada
    inf_malo_num = dict(inf)
    inf_malo_num["resumen_ejecutivo"] = inf["resumen_ejecutivo"] + " Se observaron 999 hectáreas perdidas."
    ok_num, _ = verificar_informe(inf_malo_num, paquete)
    assert not ok_num

    # Rechaza expresión causal prohibida
    inf_malo_causal = dict(inf)
    inf_malo_causal["resumen_ejecutivo"] = inf["resumen_ejecutivo"] + " La falta de lluvia causó mortalidad total."
    ok_causal, _ = verificar_informe(inf_malo_causal, paquete)
    assert not ok_causal


def test_integracion_web_data_completa():
    resumen_path = WEB_DATA / "resumen.json"
    if not resumen_path.exists():
        pytest.skip("Aún no se generan salidas en web/data/")

    def _no_nan(val):
        raise ValueError(f"Constante JSON inválida: {val}")

    resumen = json.loads(resumen_path.read_text(encoding="utf-8"), parse_constant=_no_nan)
    slugs = {c["slug"] for c in resumen["comunas"]}
    assert {"cerro_navia", "san_miguel", "vitacura", "quilicura"}.issubset(slugs)

    raiz_web = WEB_DATA.parent
    index_html = (raiz_web / "index.html").read_text(encoding="utf-8")
    assert "https://cdn" not in index_html
    assert "vendor/leaflet/leaflet.js" in index_html
    assert "vendor/chartjs/chart.umd.min.js" in index_html
    assert "vendor/docx/index.umd.js" in index_html

    for slug in ("cerro_navia", "san_miguel", "vitacura", "quilicura"):
        p2 = json.loads((RAW / slug / "paso02.json").read_text(encoding="utf-8"), parse_constant=_no_nan)
        assert "escenas_bandera_offset_contradicha" in p2

        gj = json.loads((WEB_DATA / slug / "sitios.geojson").read_text(encoding="utf-8"), parse_constant=_no_nan)
        assert len(gj["features"]) > 0
        assert (WEB_DATA / slug / "sitios.js").exists()
        assert (WEB_DATA / slug / "series.js").exists()
        assert (WEB_DATA / slug / "series.csv").exists()
        assert (WEB_DATA / slug / "informes_top5.js").exists()

        # Verifica que al menos los sitios con imágenes declaradas tengan archivos PNG reales no vacíos
        con_img = [f for f in gj["features"] if f["properties"].get("imagenes")]
        assert len(con_img) > 0, f"{slug} sin PNGs generados"
        for f in con_img[:5]:
            for im in f["properties"]["imagenes"]:
                for key in ("color", "ndvi"):
                    fp = raiz_web / im[key]
                    assert fp.exists() and fp.stat().st_size > 1000, f"PNG inválido: {fp}"
                if "ndmi" in im:
                    fp_ndmi = raiz_web / im["ndmi"]
                    assert fp_ndmi.exists() and fp_ndmi.stat().st_size > 1000, f"NDMI PNG inválido: {fp_ndmi}"
            if f["properties"].get("imagen_lst"):
                fp_lst = raiz_web / f["properties"]["imagen_lst"]
                assert fp_lst.exists() and fp_lst.stat().st_size > 1000, f"LST PNG inválido: {fp_lst}"

        p2c = json.loads((RAW / slug / "paso02c.json").read_text(encoding="utf-8"), parse_constant=_no_nan)
        assert p2c.get("comuna_lst_verano_c") is not None
        assert p2c.get("impermeable_comuna_pct") is not None
        assert p2c.get("pct_techo_calor_comuna") is not None
        assert (RAW / slug / "aire.json").exists()

    casos = json.loads((WEB_DATA / "casos.json").read_text(encoding="utf-8"), parse_constant=_no_nan)
    informes = json.loads((WEB_DATA / "informes.json").read_text(encoding="utf-8"), parse_constant=_no_nan)
    assert len(casos) == 3
    for caso in casos:
        cid = caso["caso_id"]
        assert cid in informes
        assert len(informes[cid].get("plan_30_90_365", [])) == 3
        assert len(informes[cid].get("como_se_medira", [])) >= 2
        ok, errs = verificar_informe(informes[cid], caso)
        assert ok, f"Caso {cid} falló verificación: {errs}"

    inv = json.loads((WEB_DATA / "informes_inversion.json").read_text(encoding="utf-8"), parse_constant=_no_nan)
    for scope in ("intercomunal", "cerro_navia", "san_miguel", "vitacura", "quilicura"):
        assert scope in inv
        assert len(inv[scope]["informe"].get("plan_30_90_365", [])) == 3
        ok, errs = verificar_informe(inv[scope]["informe"], inv[scope]["paquete"])
        assert ok, f"Cartera inversión {scope} falló verificación: {errs}"


def test_html_js_ids_sincronizados():
    import re

    raiz_web = WEB_DATA.parent
    html = (raiz_web / "index.html").read_text(encoding="utf-8")
    js = (raiz_web / "app.js").read_text(encoding="utf-8")
    html_ids = set(re.findall(r'\bid="([^"]+)"', html))
    js_created_ids = set(re.findall(r'\bid="([^"]+)"', js))
    js_get_ids = set(re.findall(r'getElementById\("([^"]+)"\)', js))
    faltantes = sorted(js_get_ids - html_ids - js_created_ids)
    assert not faltantes, f"IDs referenciados por app.js faltantes en index.html: {faltantes}"


def test_kpi_arboles_comuna_y_vitacura_cero():
    resumen_path = WEB_DATA / "resumen.json"
    if not resumen_path.exists():
        pytest.skip("Aún no se genera web/data/resumen.json")
    resumen = json.loads(resumen_path.read_text(encoding="utf-8"))
    cfg = cargar_config()
    por_slug = {c["slug"]: c for c in resumen["comunas"]}
    assert por_slug["vitacura"]["arboles_necesarios_min_total"] == 0
    assert por_slug["vitacura"]["arboles_necesarios_max_total"] == 0
    for slug in ("cerro_navia", "san_miguel", "quilicura"):
        c = por_slug[slug]
        esperado = mod_03b.brecha_dosel(float(c["area_km2"]) * 1e6, float(c["cobertura_arboles_comuna_pct"]), cfg)
        assert c["arboles_necesarios_min_total"] == esperado["arboles_necesarios_min"]
        assert c["arboles_necesarios_max_total"] == esperado["arboles_necesarios_max"]


def test_z_scores_acotados_y_temp_evento():
    resumen_path = WEB_DATA / "resumen.json"
    if not resumen_path.exists():
        pytest.skip("Aún no existen GeoJSON en web/data/")
    for slug in ("cerro_navia", "san_miguel", "vitacura", "quilicura"):
        gj = json.loads((WEB_DATA / slug / "sitios.geojson").read_text(encoding="utf-8"))
        con_temp_ev = 0
        for feat in gj["features"]:
            p = feat["properties"]
            for k in ("ndvi_z", "ndmi_z"):
                if p.get(k) is not None:
                    assert abs(p[k]) <= 4.0, f"{slug} {p['site_id']} {k}={p[k]} excede ±4.0"
            ev = p.get("evento_calor") or {}
            if ev:
                if ev.get("temp_max_evento_c") is not None:
                    con_temp_ev += 1
                    assert 20.0 <= ev["temp_max_evento_c"] <= 48.0
                for k in ("ndvi_z_min", "ndmi_z_min"):
                    if ev.get(k) is not None:
                        assert abs(ev[k]) <= 4.0, f"{slug} {p['site_id']} ev.{k}={ev[k]} excede ±4.0"
        assert con_temp_ev > 0, f"{slug} sin temp_max_evento_c en ventana estival"


def test_02c_usa_clave_sentinel2():
    src = (ROOT / "pipeline" / "02c_satelites_extra.py").read_text(encoding="utf-8")
    assert 'cfg["sentinel"]' not in src
    assert 'cfg["sentinel2"]' in src


def test_servidor_api_estado_y_error():
    from fastapi.testclient import TestClient
    from app import servidor

    client = TestClient(servidor.app)
    resp = client.get("/api/estado")
    assert resp.status_code == 200
    body = resp.json()
    assert body["servidor"] is True
    assert "ia_disponible" in body

    resp_404 = client.post("/api/informe", json={"ambito": "comuna_inexistente"})
    assert resp_404.status_code == 404
