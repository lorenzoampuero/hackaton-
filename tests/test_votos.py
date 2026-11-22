"""Pruebas de la votación vecinal: épocas, votos, privacidad de resultados y administración."""

from __future__ import annotations

import importlib
import json
import sys
from datetime import timedelta
from pathlib import Path

import pytest
from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import votos  # noqa: E402
from pipeline.comun import WEB_DATA  # noqa: E402

DISP_A = "dispositivo-a-0123456789"
DISP_B = "dispositivo-b-0123456789"

pytestmark = pytest.mark.skipif(not (WEB_DATA / "vecino" / "zonas.json").exists(), reason="corre antes el paso 08")


@pytest.fixture()
def cliente(tmp_path, monkeypatch):
    monkeypatch.setenv("PULMON_VOTOS_BACKEND", "local")
    monkeypatch.setenv("PULMON_VOTOS_DB", str(tmp_path / "votos.db"))
    monkeypatch.setenv("PULMON_ADMIN_TOKEN", "token-de-prueba")
    monkeypatch.setenv("PULMON_MIN_VOTOS", "3")
    votos._cache_almacen.update({"t": 0.0, "obj": None, "clave": None})
    servidor = importlib.import_module("app.servidor")
    return TestClient(servidor.app)


def _un_sitio(slug="cerro_navia"):
    datos = json.loads((WEB_DATA / "vecino" / f"{slug}.json").read_text(encoding="utf-8"))
    return datos["sitios"][0]


def _epoca(cliente, slug="cerro_navia"):
    r = cliente.get("/api/votacion/zonas")
    assert r.status_code == 200
    return next(z for z in r.json()["zonas"] if z["slug"] == slug)["epoca"]


def _votar(cliente, epoca_id, site_id, opcion, disp=DISP_A, **extra):
    return cliente.post("/api/votacion/votar", json={"periodo_id": epoca_id, "site_id": site_id, "opcion_id": opcion, "dispositivo": disp, **extra})


def test_zonas_trae_las_cuatro_comunas_con_epoca_abierta(cliente):
    zonas = cliente.get("/api/votacion/zonas").json()["zonas"]
    assert {z["slug"] for z in zonas} == {"cerro_navia", "san_miguel", "vitacura", "quilicura"}
    assert all(z["epoca"]["estado"] == "abierto" and z["epoca"]["dias_restantes"] >= 1 for z in zonas)


def test_votar_una_vez_por_sitio_y_dispositivo(cliente):
    ep, sitio = _epoca(cliente), _un_sitio()
    assert _votar(cliente, ep["id"], sitio["id"], sitio["opciones"][0]["id"]).status_code == 200
    repetido = _votar(cliente, ep["id"], sitio["id"], sitio["opciones"][1]["id"])
    assert repetido.status_code == 409
    assert _votar(cliente, ep["id"], sitio["id"], sitio["opciones"][1]["id"], disp=DISP_B).status_code == 200
    mios = cliente.get("/api/votacion/mis-votos", params={"periodo_id": ep["id"], "dispositivo": DISP_A}).json()
    assert mios["sitios"] == [sitio["id"]]


def test_validaciones_de_voto(cliente):
    ep, sitio = _epoca(cliente), _un_sitio()
    assert _votar(cliente, ep["id"], sitio["id"], "opcion_que_no_existe").status_code == 422
    assert _votar(cliente, ep["id"], "sitio-inexistente", "sombra_arboles").status_code == 404
    assert _votar(cliente, ep["id"], sitio["id"], "otro").status_code == 422  # 'otro' exige texto
    assert _votar(cliente, ep["id"], sitio["id"], "sombra_arboles", edad_rango="mil_años").status_code == 422
    assert _votar(cliente, "no-existe", sitio["id"], "sombra_arboles").status_code == 404
    ok = _votar(cliente, ep["id"], sitio["id"], "otro", otro_texto="  Una   feria   vecinal  ")
    assert ok.status_code == 200


def test_resultados_ocultos_mientras_la_epoca_esta_abierta(cliente):
    ep, sitio = _epoca(cliente), _un_sitio()
    _votar(cliente, ep["id"], sitio["id"], "sombra_arboles")
    r = cliente.get("/api/votacion/resultados", params={"periodo_id": ep["id"]}).json()
    assert r["publicado"] is False
    assert r["votos_por_sitio"] == {sitio["id"]: 1}
    assert "sitios" not in r  # nada de porcentajes antes del cierre


def test_cierre_publica_porcentajes_y_respeta_el_minimo(cliente):
    ep, sitio = _epoca(cliente), _un_sitio()
    otro_sitio = json.loads((WEB_DATA / "vecino" / "cerro_navia.json").read_text(encoding="utf-8"))["sitios"][1]
    for i, op in enumerate(["jardin_infantil", "jardin_infantil", "jardin_infantil", "sombra_arboles"]):
        assert _votar(cliente, ep["id"], sitio["id"], op, disp=f"dispositivo-{i}-0123456789").status_code == 200
    _votar(cliente, ep["id"], otro_sitio["id"], "sombra_arboles")  # un solo voto: bajo el mínimo
    sin_token = cliente.post("/api/votacion/admin/cerrar", json={"periodo_id": ep["id"]})
    assert sin_token.status_code == 401
    cerrar = cliente.post("/api/votacion/admin/cerrar", json={"periodo_id": ep["id"]}, headers={"X-Admin-Token": "token-de-prueba"})
    assert cerrar.status_code == 200 and cerrar.json()["epoca"]["estado"] == "cerrado"
    res = cliente.get("/api/votacion/resultados", params={"periodo_id": ep["id"]}).json()
    assert res["publicado"] is True
    ganador = res["sitios"][sitio["id"]]["opciones"][0]
    assert ganador == {"id": "jardin_infantil", "votos": 3, "pct": 75.0}
    assert res["sitios"][otro_sitio["id"]] == {"total": 1, "oculto": True}
    assert _votar(cliente, ep["id"], sitio["id"], "sombra_arboles", disp="dispositivo-nuevo-0123456789").status_code == 409


def test_admin_desactivado_sin_token_configurado(cliente, monkeypatch):
    monkeypatch.delenv("PULMON_ADMIN_TOKEN")
    ep = _epoca(cliente)
    r = cliente.post("/api/votacion/admin/cerrar", json={"periodo_id": ep["id"]}, headers={"X-Admin-Token": "lo-que-sea"})
    assert r.status_code == 403


def test_nueva_epoca_solo_si_la_anterior_cerro(cliente):
    ep = _epoca(cliente)
    h = {"X-Admin-Token": "token-de-prueba"}
    assert cliente.post("/api/votacion/admin/epocas", json={"comuna_slug": "cerro_navia", "nombre": "Votación 2", "dias": 7}, headers=h).status_code == 409
    cliente.post("/api/votacion/admin/cerrar", json={"periodo_id": ep["id"]}, headers=h)
    nueva = cliente.post("/api/votacion/admin/epocas", json={"comuna_slug": "cerro_navia", "nombre": "Votación 2", "dias": 7}, headers=h)
    assert nueva.status_code == 200 and nueva.json()["epoca"]["estado"] == "abierto"
    assert _epoca(cliente)["id"] == nueva.json()["epoca"]["id"]


def test_demo_queda_marcada_y_separada(cliente):
    alm = votos.obtener_almacen()
    demo = votos.sembrar_demo(alm, "cerro_navia", sitios=3, votos_por_sitio=12)
    assert demo["epoca"]["demo"] is True and demo["epoca"]["estado"] == "cerrado"
    assert _epoca(cliente)["demo"] is False  # la época real no es la demo
    res = cliente.get("/api/votacion/resultados", params={"periodo_id": demo["epoca"]["id"]}).json()
    assert res["publicado"] is True and res["epoca"]["demo"] is True


def test_calcular_resultados_porcentajes_suman_100():
    filas = [{"site_id": "a", "opcion_id": o, "otro_texto": None} for o in ["x", "x", "y", "z"]]
    res = votos.calcular_resultados(filas, 2)["a"]
    assert sum(o["pct"] for o in res["opciones"]) == pytest.approx(100.0)
    assert res["opciones"][0] == {"id": "x", "votos": 2, "pct": 50.0}


def test_estado_epoca_por_fechas():
    base = votos.nueva_epoca("cerro_navia", "x", dias=5)
    assert votos.estado_epoca(base) == "abierto"
    assert votos.estado_epoca(base, votos._parse(base["cierra_en"]) + timedelta(seconds=1)) == "cerrado"
    futura = votos.nueva_epoca("cerro_navia", "y", dias=5, abre=votos._ahora() + timedelta(days=2))
    assert votos.estado_epoca(futura) == "proximo"
