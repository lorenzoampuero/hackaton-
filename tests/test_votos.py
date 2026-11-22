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


def test_modo_vercel_ids_deterministicos_y_demo_automatica(tmp_path, monkeypatch):
    """En Vercel cada instancia tiene su propia memoria: el id de la época y la demo deben ser iguales en todas."""
    monkeypatch.setenv("PULMON_VOTOS_BACKEND", "local")
    monkeypatch.setenv("PULMON_DEMO_AUTO", "1")
    servidor = importlib.import_module("app.servidor")
    resultados = []
    for nombre in ("instancia_a.db", "instancia_b.db"):  # dos instancias que no comparten disco
        monkeypatch.setenv("PULMON_VOTOS_DB", str(tmp_path / nombre))
        votos._cache_almacen.update({"t": 0.0, "obj": None, "clave": None})
        votos._demo_listo.clear()
        c = TestClient(servidor.app)
        zonas = c.get("/api/votacion/zonas").json()["zonas"]
        ep = next(z for z in zonas if z["slug"] == "cerro_navia")["epoca"]
        assert ep["id"].startswith("auto-cerro_navia-") and ep["estado"] == "abierto"
        per = c.get("/api/votacion/periodos", params={"comuna": "cerro_navia"}).json()["periodos"]
        demo = next(p for p in per if p["demo"])
        assert demo["id"] == "demo-cerro_navia" and demo["estado"] == "cerrado"
        res = c.get("/api/votacion/resultados", params={"periodo_id": demo["id"]}).json()
        assert res["publicado"] and res["total_votos"] > 100
        resultados.append((ep["id"], demo["id"]))
    assert resultados[0] == resultados[1]


def test_buscador_devuelve_solo_coincidencias_sin_populares(cliente):
    r = cliente.get("/api/votacion/ideas", params={"q": "perros"}).json()
    assert r["resultados"][0]["id"] == "parque_perros"
    assert r["coincidencias"] == len(r["resultados"]) >= 1
    assert r["relleno"] is False
    assert not any(x["popular"] for x in r["resultados"])

    futbol = cliente.get("/api/votacion/ideas", params={"q": "fútbol"}).json()  # con tilde y sinónimo
    assert futbol["resultados"][0]["id"] == "cancha_comunitaria"
    assert futbol["relleno"] is False

    parecido = cliente.get("/api/votacion/ideas", params={"q": "pisina"}).json()  # parecido con error de tipeo
    assert any(x["id"] == "piscina" for x in parecido["resultados"])

    vacio = cliente.get("/api/votacion/ideas", params={"q": ""}).json()
    assert vacio["coincidencias"] == 0 and vacio["relleno"] is False and vacio["resultados"] == []

    corto = cliente.get("/api/votacion/ideas", params={"q": "a"}).json()
    assert corto["coincidencias"] == 0 and corto["relleno"] is False and corto["resultados"] == []

    sin_nada = cliente.get("/api/votacion/ideas", params={"q": "zzzzqqq"}).json()
    assert sin_nada["coincidencias"] == 0 and sin_nada["relleno"] is False and sin_nada["resultados"] == []


def test_se_puede_votar_por_una_idea_del_buscador_y_el_costo_no_se_inventa(cliente):
    ep, sitio = _epoca(cliente), _un_sitio()
    assert _votar(cliente, ep["id"], sitio["id"], "huerto_comunitario").status_code == 200
    ficha = cliente.get("/api/votacion/ideas", params={"q": "huerto"}).json()["resultados"][0]
    assert ficha["id"] == "huerto_comunitario" and ficha["costo_min_M"] is None and "cotizar" in ficha["costo_nota"]


def test_resultados_traen_participacion_sin_revelar_votos(cliente):
    ep, sitio = _epoca(cliente), _un_sitio()
    _votar(cliente, ep["id"], sitio["id"], "sombra_arboles", edad_rango="60_mas", via_qr=True)
    r = cliente.get("/api/votacion/resultados", params={"periodo_id": ep["id"]}).json()
    part = r["participacion"]
    assert part["total"] == 1 and part["via_qr"] == 1 and part["edades"]["60_mas"] == 1
    assert len(part["por_dia"]) == 1 and part["por_dia"][0]["votos"] == 1
    assert "sitios" not in r  # abierta: sigue sin publicar porcentajes


def test_confianza_detecta_rafagas_y_premia_votos_repartidos():
    from datetime import timedelta

    base = votos._ahora()
    rafaga = [{"site_id": "a", "opcion_id": "x", "via_qr": False, "edad_rango": None, "creado_en": votos._iso(base + timedelta(minutes=i))} for i in range(20)]
    c = votos.calcular_confianza(rafaga, 10)
    assert c["nivel"] == "baja" and c["rafaga_pct"] == 100.0 and any("una sola hora" in r for r in c["razones"])
    bueno = [{"site_id": "a", "opcion_id": "x", "via_qr": True, "edad_rango": "30_44", "creado_en": votos._iso(base + timedelta(hours=7 * i))} for i in range(60)]
    assert votos.calcular_confianza(bueno, 10)["nivel"] == "alta"
    assert votos.calcular_confianza([], 10)["nivel"] == "baja"
    pocos = votos.calcular_confianza(bueno[:4], 10)
    assert any("Pocos votos" in r for r in pocos["razones"])


def test_resultados_incluyen_confianza_sin_revelar_preferencias(cliente):
    ep, sitio = _epoca(cliente), _un_sitio()
    for i in range(4):
        _votar(cliente, ep["id"], sitio["id"], "sombra_arboles", disp=f"dispositivo-{i}-0123456789")
    r = cliente.get("/api/votacion/resultados", params={"periodo_id": ep["id"]}).json()
    assert r["publicado"] is False and "sitios" not in r
    assert sitio["id"] in r["confianza"] and r["confianza_global"]["n"] == 4
    assert "opcion_id" not in json.dumps(r["confianza"])


def test_votar_y_resultados_hidratan_periodo_auto_y_demo_en_instancia_fria(tmp_path, monkeypatch):
    monkeypatch.setenv("PULMON_VOTOS_BACKEND", "local")
    monkeypatch.setenv("PULMON_EPOCAS_AUTO", "1")
    monkeypatch.setenv("PULMON_DEMO_AUTO", "1")
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)
    servidor = importlib.import_module("app.servidor")
    pid_auto = votos.ventana_auto("cerro_navia")["id"]
    sitio = _un_sitio()

    def cliente_frio(db_name):
        monkeypatch.setenv("PULMON_VOTOS_DB", str(tmp_path / db_name))
        votos._cache_almacen.update({"t": 0.0, "obj": None, "clave": None})
        votos._demo_listo.clear()
        return TestClient(servidor.app)

    c1 = cliente_frio("fria_1.db")
    r_res = c1.get("/api/votacion/resultados", params={"periodo_id": pid_auto})
    assert r_res.status_code == 200 and r_res.json()["epoca"]["id"] == pid_auto

    c2 = cliente_frio("fria_2.db")
    r_vot = _votar(c2, pid_auto, sitio["id"], "sombra_arboles")
    assert r_vot.status_code == 200 and r_vot.json()["ok"] is True

    c3 = cliente_frio("fria_3.db")
    r_demo = c3.get("/api/votacion/resultados", params={"periodo_id": "demo-cerro_navia"})
    assert r_demo.status_code == 200 and r_demo.json()["publicado"] is True and r_demo.json()["total_votos"] > 100

    r_404 = c3.get("/api/votacion/resultados", params={"periodo_id": "no-existe-123"})
    assert r_404.status_code == 404 and "Esa votación no existe." in r_404.json()["detail"]
