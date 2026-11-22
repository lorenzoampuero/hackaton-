"""Pruebas del paso 08: semáforo, datos simples y opciones recomendadas para la vista del vecino."""

from __future__ import annotations

import importlib
import json

import pytest

from pipeline.comun import RAIZ, WEB_DATA

mod_08 = importlib.import_module("pipeline.08_vecino")
CATALOGO = json.loads((RAIZ / "data" / "opciones_votacion.json").read_text(encoding="utf-8"))


def test_percentil_es_monotono_y_acotado():
    p = mod_08.Percentil([1.0, 2.0, 3.0, 4.0])
    assert p(0) == 0.0 and p(10) == 100.0
    assert p(1.0) < p(2.0) < p(3.0) < p(4.0)


def _sitio(**kw):
    base = {"area_m2": 3000, "lst_verano_c": 42.0, "cobertura_arboles_400m_pct": 1.0, "ndvi_actual": 0.2, "ndmi_actual": 0.0,
            "pop_400m": 9000, "pct_60_mas_400m": 25.0, "pct_infancia_0_5_400m": 7.5, "impermeable_400m_pct": 95.0, "vulnerabilidad": 80.0}
    base.update(kw)
    return base


def _refs():
    muestra = [_sitio(lst_verano_c=30 + i, cobertura_arboles_400m_pct=i * 3, ndvi_actual=0.1 + i / 20, ndmi_actual=-0.05 + i / 40) for i in range(20)]
    return mod_08.referencias(muestra)


def test_indice_peor_para_un_sitio_caliente_sin_sombra_y_seco():
    refs = _refs()
    malo = mod_08.indice_condiciones(_sitio(), refs)
    bueno = mod_08.indice_condiciones(_sitio(lst_verano_c=30, cobertura_arboles_400m_pct=60, ndvi_actual=1.0, ndmi_actual=0.5), refs)
    assert malo is not None and bueno is not None and malo < mod_08.UMBRAL_ROJO < mod_08.UMBRAL_VERDE < bueno


def test_sin_datos_suficientes_no_hay_indice():
    assert mod_08.indice_condiciones({"area_m2": 2000}, _refs()) is None


def test_datos_simples_usan_palabras_y_no_jerga():
    d = mod_08.datos_simples(_sitio(), _refs())
    assert d["sombra"]["etiqueta"] == "Poca"
    assert set(d) == {"sombra", "calor", "verde", "vecinos"}
    texto = json.dumps(d, ensure_ascii=False)
    for jerga in ("NDVI", "NDMI", "LST", "z-score"):
        assert jerga not in texto


def test_opciones_filtran_por_area_y_ordenan_por_condiciones():
    ranking = mod_08.puntuar_opciones(_sitio(area_m2=1000), CATALOGO["opciones"])
    ids = [o["id"] for o in ranking]
    assert "piscina" not in ids and "multicancha" in ids  # piscina pide 3.000 m²; multicancha 800 m²
    assert ranking[0]["id"] == "sombra_arboles"            # poca sombra manda
    assert all(a["score"] >= b["score"] for a, b in zip(ranking, ranking[1:]))
    assert all(o["razon"] for o in ranking)


def test_catalogo_no_inventa_costos():
    for o in CATALOGO["opciones"]:
        lo, hi = o["costo_min_M"], o["costo_max_M"]
        assert (lo is None) == (hi is None)
        if lo is not None:
            assert 0 < lo <= hi and o["costo_nota"]
        if o["costo_nota"].startswith("rango de obras similares"):
            assert o["ejemplos"], f"{o['id']} dice tener obras similares pero no cita ninguna"
        for ej in o["ejemplos"]:
            assert ej["url"].startswith("https://")


@pytest.mark.skipif(not (WEB_DATA / "vecino" / "zonas.json").exists(), reason="corre antes el paso 08")
def test_salida_para_las_cuatro_comunas():
    zonas = json.loads((WEB_DATA / "vecino" / "zonas.json").read_text(encoding="utf-8"))["zonas"]
    assert {z["slug"] for z in zonas} == {"cerro_navia", "san_miguel", "vitacura", "quilicura"}
    for z in zonas:
        datos = json.loads((WEB_DATA / "vecino" / f"{z['slug']}.json").read_text(encoding="utf-8"))
        assert len(datos["sitios"]) == z["n_sitios"] > 0
        s = datos["sitios"][0]
        assert s["semaforo"]["color"] in {"verde", "amarillo", "rojo", "gris"} and 1 <= len(s["opciones"]) <= 5
        assert s["geometria"]["type"] in {"Polygon", "MultiPolygon"}
