"""Paso 2b: lluvia y temperatura del aire diarias de la comuna (Open-Meteo, reanálisis).

Es un dato grueso, de referencia comunal: no distingue barrios ni mide temperatura de superficie.
Licencia: la API gratuita de Open-Meteo es solo para uso NO comercial (datos CC BY 4.0).
Salida: data/raw/<slug>/clima.json
"""

from __future__ import annotations

from datetime import timedelta

from pipeline import comun

URL = "https://archive-api.open-meteo.com/v1/archive"


def ejecutar(comuna: dict, cfg: dict) -> None:
    slug, nombre = comuna["slug"], comuna["nombre"]
    raw = comun.dir_raw(slug)
    lon, lat = comun.leer_json(raw / "paso01.json")["comuna"]["centro"]
    hoy = comun.fecha_proceso()
    meses = cfg["sentinel2"]["meses_historia"]
    total = hoy.year * 12 + (hoy.month - 1) - meses
    desde = hoy.replace(year=total // 12, month=total % 12 + 1, day=1)
    hasta = hoy - timedelta(days=1)
    datos = comun.pedir("GET", URL, params={
        "latitude": lat, "longitude": lon,
        "start_date": desde.isoformat(), "end_date": hasta.isoformat(),
        "daily": "temperature_2m_mean,temperature_2m_max,precipitation_sum",
        "timezone": "America/Santiago",
    }).json()
    diario = datos["daily"]
    dias = [
        [f, comun.redondear(tm, 1), comun.redondear(tx, 1), comun.redondear(ll, 1)]
        for f, tm, tx, ll in zip(
            diario["time"], diario["temperature_2m_mean"], diario["temperature_2m_max"], diario["precipitation_sum"]
        )
    ]
    comun.escribir_json(raw / "clima.json", {
        "fuente": "Open-Meteo, API histórica (reanálisis); aire, referencia comunal",
        "url": URL,
        "licencia": "CC BY 4.0; la API gratuita es solo para uso no comercial",
        "lat": datos.get("latitude", lat), "lon": datos.get("longitude", lon),
        "fecha_consulta": hoy.isoformat(),
        "columnas": ["fecha", "temp_media_c", "temp_max_c", "lluvia_mm"],
        "dias": dias,
    })
    con_dato = sum(1 for d in dias if d[1] is not None)
    print(f"  [02b] {nombre}: {con_dato} días con temperatura entre {desde} y {hasta}.")
