"""Paso 08: datos simples para la vista del vecino.

Lee web/data/<slug>/sitios.geojson (paso 04/05) y el catálogo data/opciones_votacion.json y escribe:
  web/data/vecino/zonas.json        las comunas y cuántos sitios hay en cada color
  web/data/vecino/<slug>.json       cada sitio con su semáforo, 4 datos en palabras simples y las opciones
                                    de obra recomendadas (ordenadas) con la razón de cada una
  web/data/vecino/opciones.json     el catálogo de opciones con rangos de costo y ejemplos con fuente

Todo es determinístico: no hay IA ni cifras inventadas. El semáforo compara cada sitio con los demás
sitios escaneados (percentiles), así que dice 'mejor o peor que el resto', no 'bueno' en términos absolutos.
"""

from __future__ import annotations

import re
from bisect import bisect_left, bisect_right
from typing import Any

from shapely.geometry import mapping, shape

from pipeline.comun import RAIZ, WEB_DATA, escribir_json, leer_json

CATALOGO = RAIZ / "data" / "opciones_votacion.json"
SALIDA = WEB_DATA / "vecino"

UMBRAL_VERDE = 66.0       # índice de condiciones (0 a 100) desde aquí el sitio está en buen estado
UMBRAL_ROJO = 33.0        # bajo esto, necesita ayuda
PESOS = {"calor": 0.35, "sombra": 0.30, "ndvi": 0.20, "ndmi": 0.15}
OPCIONES_RECOMENDADAS = 5
TOLERANCIA_GEOMETRIA = 0.00002  # grados (≈ 2 m)


def _num(v: Any) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


class Percentil:
    """Posición (0 a 100) de un valor dentro de un conjunto; los empates cuentan a la mitad."""

    def __init__(self, valores: list[float]) -> None:
        self.orden = sorted(valores)

    def __call__(self, v: float) -> float:
        n = len(self.orden)
        if n < 2:
            return 50.0
        pos = (bisect_left(self.orden, v) + bisect_right(self.orden, v)) / 2.0
        return max(0.0, min(100.0, 100.0 * pos / n))


def referencias(todas: list[dict[str, Any]]) -> dict[str, Percentil]:
    claves = {"calor": "lst_verano_c", "sombra": "cobertura_arboles_400m_pct", "ndvi": "ndvi_actual", "ndmi": "ndmi_actual"}
    refs = {}
    for nombre, clave in claves.items():
        valores = [v for p in todas if (v := _num(p.get(clave))) is not None]
        refs[nombre] = Percentil(valores)
    return refs


def indice_condiciones(p: dict[str, Any], refs: dict[str, Percentil]) -> float | None:
    """0 a 100, más alto es mejor: menos calor, más sombra, más vegetación y más humedad en las hojas."""
    partes: dict[str, float] = {}
    if (v := _num(p.get("lst_verano_c"))) is not None:
        partes["calor"] = 100.0 - refs["calor"](v)
    if (v := _num(p.get("cobertura_arboles_400m_pct"))) is not None:
        partes["sombra"] = refs["sombra"](v)
    if (v := _num(p.get("ndvi_actual"))) is not None:
        partes["ndvi"] = refs["ndvi"](v)
    if (v := _num(p.get("ndmi_actual"))) is not None:
        partes["ndmi"] = refs["ndmi"](v)
    if len(partes) < 2:
        return None
    peso = sum(PESOS[k] for k in partes)
    return round(sum(PESOS[k] * partes[k] for k in partes) / peso, 1)


def _entero_cl(v: float) -> str:
    return f"{round(v):,}".replace(",", ".")


def _decimal_cl(v: float, dec: int = 1) -> str:
    return f"{v:.{dec}f}".replace(".", ",")


def datos_simples(p: dict[str, Any], refs: dict[str, Percentil]) -> dict[str, dict[str, str]]:
    """Cuatro datos en palabras simples: sombra, calor, vegetación y vecinos."""
    salida: dict[str, dict[str, str]] = {}
    cob = _num(p.get("cobertura_arboles_400m_pct"))
    if cob is not None:
        et = "Poca" if cob < 10 else "Regular" if cob < 20 else "Buena"
        salida["sombra"] = {"titulo": "Sombra", "etiqueta": et, "texto": f"{_decimal_cl(cob, 0)} % del entorno (400 m) tiene árboles"}
    lst = _num(p.get("lst_verano_c"))
    if lst is not None:
        rango = refs["calor"](lst)
        et = "Muy alto" if rango >= 75 else "Alto" if rango >= 50 else "Moderado"
        salida["calor"] = {"titulo": "Calor en verano", "etiqueta": et, "texto": f"{_decimal_cl(lst, 0)} °C; más que el {_decimal_cl(rango, 0)} % de los sitios escaneados"}
    ndvi, ndmi = _num(p.get("ndvi_actual")), _num(p.get("ndmi_actual"))
    if ndvi is not None:
        rango = refs["ndvi"](ndvi)
        et = "Seca" if rango < 25 else "Regular" if rango < 60 else "Verde"
        extra = ""
        if ndmi is not None:
            r2 = refs["ndmi"](ndmi)
            extra = " · hojas con " + ("poca" if r2 < 25 else "media" if r2 < 60 else "buena") + " humedad"
        salida["verde"] = {"titulo": "Vegetación", "etiqueta": et, "texto": f"Vigor {_decimal_cl(ndvi, 2)}{extra}"}
    pop = _num(p.get("pop_400m"))
    if pop is not None:
        mayores = _num(p.get("pct_60_mas_400m"))
        txt = f"{_entero_cl(pop)} personas a 400 m"
        if mayores is not None:
            txt += f" ({_decimal_cl(mayores, 0)} % de 60 años o más)"
        salida["vecinos"] = {"titulo": "Vecinos cerca", "etiqueta": "", "texto": txt}
    return salida


def resumen_frase(datos: dict[str, dict[str, str]], semaforo: str) -> str:
    problemas = []
    if datos.get("sombra", {}).get("etiqueta") == "Poca":
        problemas.append("poca sombra")
    if datos.get("calor", {}).get("etiqueta") in ("Alto", "Muy alto"):
        problemas.append("mucho calor en verano")
    if datos.get("verde", {}).get("etiqueta") == "Seca":
        problemas.append("la vegetación se ve seca")
    if semaforo == "verde":
        return "Está mejor que la mayoría de los sitios escaneados."
    if problemas:
        return "Tiene " + " y ".join(problemas[:2]).replace("Tiene la", "La") + "."
    return "Está en un punto medio frente a los demás sitios escaneados."


def nombre_limpio(p: dict[str, Any]) -> str:
    nombre = re.sub(r"\s*\([^)]*\bha\)", "", p.get("nombre") or "").strip()
    if not nombre or "sin nombre" in nombre.lower():
        return f"Área verde sin nombre ({p.get('tipo', 'plaza')})"
    return nombre


def puntuar_opciones(p: dict[str, Any], catalogo: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ordena las opciones del catálogo según las condiciones del sitio; cada una trae su razón."""
    area = _num(p.get("area_m2")) or 0.0
    cob = _num(p.get("cobertura_arboles_400m_pct"))
    lst = _num(p.get("lst_verano_c"))
    ndvi, ndmi = _num(p.get("ndvi_actual")), _num(p.get("ndmi_actual"))
    pop = _num(p.get("pop_400m")) or 0.0
    mayores = _num(p.get("pct_60_mas_400m"))
    ninos = _num(p.get("pct_infancia_0_5_400m"))
    imperm = _num(p.get("impermeable_400m_pct"))
    vuln = _num(p.get("vulnerabilidad"))
    seca = (ndvi is not None and ndvi < 0.29) or (ndmi is not None and ndmi < 0.03)
    calor = lst is not None and lst >= 40.0
    poca_sombra = cob is not None and cob < 10.0

    def r(score: float, razon: str) -> tuple[float, str]:
        return score, razon

    reglas: dict[str, tuple[float, str]] = {
        "sombra_arboles": r(90 if poca_sombra else 55 if (cob or 0) < 20 else 20,
                            f"Hay poca sombra: solo {_decimal_cl(cob or 0, 0)} % del entorno tiene árboles." if poca_sombra
                            else "La sombra es regular; más árboles ayudan en verano."),
        "bancas_bebedero": r(85 if (mayores or 0) >= 24.5 else 60 if (mayores or 0) >= 20.3 else 35,
                             f"El {_decimal_cl(mayores or 0, 0)} % de los vecinos tiene 60 años o más." if mayores is not None else "Sirve a todas las edades."),
        "juegos_infantiles": r(85 if (ninos or 0) >= 6.9 else 60 if (ninos or 0) >= 6.2 else 35,
                               f"El {_decimal_cl(ninos or 0, 0)} % de los vecinos tiene entre 0 y 5 años." if ninos is not None else "Sirve a las familias."),
        "jardin_infantil": r(80 if (ninos or 0) >= 6.9 else 45 if (ninos or 0) >= 6.2 else 25,
                             f"El {_decimal_cl(ninos or 0, 0)} % de los vecinos tiene entre 0 y 5 años." if ninos is not None else "Depende de cuántos niños viven cerca."),
        "maquinas_ejercicio": r(65 if area >= 2000 and pop >= 6000 else 40,
                                f"Viven {_entero_cl(pop)} personas a 400 m y el lugar mide {_entero_cl(area)} m²."),
        "cancha_comunitaria": r(75 if pop >= 8900 else 55 if pop >= 6183 else 30,
                                f"Viven {_entero_cl(pop)} personas a 400 m; el lugar mide {_entero_cl(area)} m²."),
        "multicancha": r(70 if (pop >= 8900 and area >= 3000) else 40,
                         f"Viven {_entero_cl(pop)} personas a 400 m; el lugar mide {_entero_cl(area)} m²."),
        "skatepark": r(55 if pop >= 6183 else 30, f"Viven {_entero_cl(pop)} personas a 400 m y hay {_entero_cl(area)} m² de espacio."),
        "plantas_nativas": r(85 if seca else 35,
                             "La vegetación se ve seca; plantas de poco riego aguantan mejor." if seca else "La vegetación está en buen estado hoy."),
        "riego_eficiente": r(70 if seca else 30,
                             "La vegetación se ve seca; un mejor riego ayuda a mantenerla." if seca else "La vegetación está en buen estado hoy."),
        "refugio_climatico": r(85 if (calor and (vuln or 0) >= 60) else 60 if calor else 25,
                               f"Hace calor en verano ({_decimal_cl(lst or 0, 0)} °C) y viven muchas personas expuestas." if calor else "El calor es moderado frente a otros sitios."),
        "jardin_lluvia": r(80 if (imperm or 0) >= 90.6 else 50 if (imperm or 0) >= 76.7 else 20,
                           f"El {_decimal_cl(imperm or 0, 0)} % del entorno es cemento o construcción." if imperm is not None else "Depende de cuánto cemento hay alrededor."),
        "iluminacion_seguridad": r(40, "No medimos seguridad con datos; los vecinos pueden decirlo con su voto."),
        "piscina": r(45 if (pop >= 10000 and area >= 5000) else 15,
                     f"Viven {_entero_cl(pop)} personas a 400 m y hay {_entero_cl(area)} m² de espacio."),
    }
    ranking = []
    for opcion in catalogo:
        if area < float(opcion.get("min_area_m2") or 0):
            continue
        score, razon = reglas.get(opcion["id"], (30, ""))
        ranking.append({"id": opcion["id"], "score": float(score), "razon": razon})
    ranking.sort(key=lambda o: -o["score"])
    return ranking


def construir_comuna(slug: str, todas: list[dict[str, Any]], refs: dict[str, Percentil], catalogo: list[dict[str, Any]]) -> dict[str, Any]:
    gj = leer_json(WEB_DATA / slug / "sitios.geojson")
    comuna = gj.get("comuna", {})
    sitios = []
    for feat in gj["features"]:
        p = feat["properties"]
        indice = indice_condiciones(p, refs)
        if indice is None:
            color, etiqueta = "gris", "Sin datos suficientes"
        elif indice >= UMBRAL_VERDE:
            color, etiqueta = "verde", "Buen estado"
        elif indice >= UMBRAL_ROJO:
            color, etiqueta = "amarillo", "Regular"
        else:
            color, etiqueta = "rojo", "Necesita ayuda"
        datos = datos_simples(p, refs)
        area = _num(p.get("area_m2")) or 0.0
        geom = shape(feat["geometry"]).simplify(TOLERANCIA_GEOMETRIA, preserve_topology=True)
        centro = p.get("centro") or list(shape(feat["geometry"]).representative_point().coords[0])
        sitios.append({
            "id": p["site_id"],
            "nombre": nombre_limpio(p),
            "tipo": p.get("tipo", "plaza"),
            "area_m2": round(area),
            "centro": [round(centro[0], 6), round(centro[1], 6)],
            "semaforo": {"color": color, "etiqueta": etiqueta, "indice": indice},
            "resumen": resumen_frase(datos, color) if indice is not None else "Faltan datos del satélite para este sitio.",
            "datos": datos,
            "poca_confianza": p.get("confianza") == "baja",
            "mantencion_M": [round(area * 1625 / 1e6, 1), round(area * 2962 / 1e6, 1)],
            "opciones": puntuar_opciones(p, catalogo)[:OPCIONES_RECOMENDADAS],
            "geometria": {"type": mapping(geom)["type"], "coordinates": _redondear(mapping(geom)["coordinates"])},
        })
    orden = {"rojo": 0, "amarillo": 1, "verde": 2, "gris": 3}
    sitios.sort(key=lambda s: (orden[s["semaforo"]["color"]], s["semaforo"]["indice"] or 0))
    return {
        "comuna": {
            "slug": slug,
            "nombre": comuna.get("nombre", slug),
            "centro": comuna.get("centro"),
            "bbox": comuna.get("bbox"),
        },
        "umbrales": {"verde": UMBRAL_VERDE, "rojo": UMBRAL_ROJO},
        "sitios": sitios,
    }


def _redondear(coords: Any) -> Any:
    if isinstance(coords, (list, tuple)):
        if coords and isinstance(coords[0], (int, float)):
            return [round(coords[0], 6), round(coords[1], 6)]
        return [_redondear(c) for c in coords]
    return coords


def ejecutar_todas(comunas: list[dict[str, Any]], cfg: dict[str, Any]) -> None:
    catalogo = leer_json(CATALOGO)
    todas: list[dict[str, Any]] = []
    for c in comunas:
        ruta = WEB_DATA / c["slug"] / "sitios.geojson"
        if ruta.exists():
            todas.extend(f["properties"] for f in leer_json(ruta)["features"])
    if not todas:
        raise RuntimeError("[08] No hay sitios.geojson: corre antes los pasos 04 y 05.")
    refs = referencias(todas)
    zonas = []
    for c in comunas:
        if not (WEB_DATA / c["slug"] / "sitios.geojson").exists():
            print(f"[08] Omitiendo {c['nombre']}: falta sitios.geojson")
            continue
        datos = construir_comuna(c["slug"], todas, refs, catalogo["opciones"])
        escribir_json(SALIDA / f"{c['slug']}.json", datos)
        conteo = {"rojo": 0, "amarillo": 0, "verde": 0, "gris": 0}
        for s in datos["sitios"]:
            conteo[s["semaforo"]["color"]] += 1
        zonas.append({**datos["comuna"], "n_sitios": len(datos["sitios"]), "semaforos": conteo})
        print(f"  [08] {c['nombre']}: {len(datos['sitios'])} sitios {conteo}")
    escribir_json(SALIDA / "zonas.json", {"zonas": zonas})
    publico = {k: v for k, v in catalogo.items() if k != "nota"}
    publico["nota"] = catalogo.get("nota", "")
    escribir_json(SALIDA / "opciones.json", publico)


if __name__ == "__main__":
    from pipeline.comun import cargar_config

    cfg = cargar_config()
    ejecutar_todas(cfg["comunas"], cfg)
