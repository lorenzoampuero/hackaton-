"""Cliente de calidad del aire y clima para Pulmón Urbano.

Fuente primaria de MP2.5 / MP10: Red Oficial SINCA del Ministerio del Medio Ambiente (MMA),
extrayendo las lecturas oficiales de promedio móvil 24 h (usadas para el ICAP chileno).
Fuente complementaria de clima/suelo y respaldo atmosférico: Open-Meteo (gratis, sin API key).
Respaldo offline a prueba de fallas de Wi-Fi: data/processed/air_fallback.json.
"""

from __future__ import annotations

import html
import json
import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.scoring import CHILE_DS12_PM10_24H, CHILE_DS12_PM25_24H, WHO_PM10_24H, WHO_PM25_24H

SINCA_URL = "https://sinca.mma.gob.cl/index.php/json/listadomapa2k19/"
OPEN_METEO_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Mapeo transparente de cada comuna a su estación oficial SINCA más cercana
COMUNA_STATION_MAP: dict[str, dict[str, Any]] = {
    "santiago_centro": {
        "comuna_name": "Santiago Centro",
        "lat": -33.4569,
        "lon": -70.6560,
        "sinca_key": "D14",
        "station_fallback_name": "Parque O'Higgins (SINCA MMA)",
        "station_in_comuna": True,
    },
    "cerro_navia": {
        "comuna_name": "Cerro Navia",
        "lat": -33.4230,
        "lon": -70.7420,
        "sinca_key": "D18",
        "station_fallback_name": "Cerro Navia (SINCA MMA)",
        "station_in_comuna": True,
    },
    "estacion_central": {
        "comuna_name": "Estación Central",
        "lat": -33.4620,
        "lon": -70.7010,
        "sinca_key": "D35",
        "station_fallback_name": "Cerrillos II (SINCA MMA)",
        "station_in_comuna": False,
    },
}

_CACHE_TTL_SECONDS = 900  # 15 minutos
_air_cache: dict[str, tuple[float, dict[str, Any]]] = {}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(a)), 2)


def parse_sinca_strong_value(html_snippet: str) -> float | None:
    """Extrae el valor real publicado por SINCA dentro de <strong>XX &micro;g...</strong>.

    Importante: SINCA suma +10 al campo numérico c[1].v para graficar barras;
    el valor físico real en µg/m³ está dentro de la etiqueta <strong> de c[3].v.
    """
    if not html_snippet:
        return None
    text = html.unescape(html_snippet)
    match = re.search(r"<strong>\s*([0-9]+(?:[.,][0-9]+)?)", text)
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def parse_sinca_icap(html_snippet: str) -> int | None:
    if not html_snippet:
        return None
    text = html.unescape(html_snippet)
    match = re.search(r"</strong>\s*([0-9]+)\s*ICAP", text)
    return int(match.group(1)) if match else None


def _build_norm_comparison(pm25: float | None, pm10: float | None) -> dict[str, Any]:
    return {
        "pm25_vs_who_24h": {
            "limit": WHO_PM25_24H,
            "exceeds": (pm25 > WHO_PM25_24H) if pm25 is not None else None,
            "pct_of_limit": round((pm25 / WHO_PM25_24H) * 100.0, 1) if pm25 is not None else None,
        },
        "pm25_vs_chile_ds12_24h": {
            "limit": CHILE_DS12_PM25_24H,
            "exceeds": (pm25 > CHILE_DS12_PM25_24H) if pm25 is not None else None,
            "pct_of_limit": round((pm25 / CHILE_DS12_PM25_24H) * 100.0, 1) if pm25 is not None else None,
        },
        "pm10_vs_who_24h": {
            "limit": WHO_PM10_24H,
            "exceeds": (pm10 > WHO_PM10_24H) if pm10 is not None else None,
            "pct_of_limit": round((pm10 / WHO_PM10_24H) * 100.0, 1) if pm10 is not None else None,
        },
        "pm10_vs_chile_ds12_24h": {
            "limit": CHILE_DS12_PM10_24H,
            "exceeds": (pm10 > CHILE_DS12_PM10_24H) if pm10 is not None else None,
            "pct_of_limit": round((pm10 / CHILE_DS12_PM10_24H) * 100.0, 1) if pm10 is not None else None,
        },
    }


def fetch_sinca_stations_sync(timeout: float = 5.0) -> dict[str, dict[str, Any]]:
    """Descarga y parsea las estaciones relevantes de la red SINCA (MMA Chile)."""
    with httpx.Client(timeout=timeout, headers={"User-Agent": "PulmonUrbanoHackathon/1.0"}) as client:
        resp = client.get(SINCA_URL)
        resp.raise_for_status()
        stations = resp.json()

    by_key: dict[str, dict[str, Any]] = {}
    for st in stations:
        key = str(st.get("key", ""))
        if not key:
            continue
        parsed: dict[str, Any] = {
            "key": key,
            "nombre": st.get("nombre", ""),
            "comuna": st.get("comuna", ""),
            "lat": float(st["latitud"]) if st.get("latitud") is not None else None,
            "lon": float(st["longitud"]) if st.get("longitud") is not None else None,
            "pm25_24h": None,
            "pm10_24h": None,
            "pm25_icap": None,
            "pm10_icap": None,
            "timestamp": None,
        }
        for rt in st.get("realtime") or []:
            code = rt.get("code")
            info = rt.get("info")
            rows = info.get("rows") if isinstance(info, dict) else None
            if not rows:
                continue
            cells = rows[0].get("c") or []
            if len(cells) < 4:
                continue
            ts = cells[0].get("v")
            tooltip = cells[3].get("v") or ""
            val = parse_sinca_strong_value(tooltip)
            icap = parse_sinca_icap(tooltip)
            if code == "PM25" and val is not None:
                parsed["pm25_24h"] = val
                parsed["pm25_icap"] = icap
                parsed["timestamp"] = ts
            elif code == "PM10" and val is not None:
                parsed["pm10_24h"] = val
                parsed["pm10_icap"] = icap
                if not parsed["timestamp"]:
                    parsed["timestamp"] = ts
        by_key[key] = parsed
    return by_key


def fetch_open_meteo_weather_sync(lat: float, lon: float, timeout: float = 4.0) -> dict[str, Any]:
    """Consulta clima actual y humedad de suelo desde Open-Meteo Weather API."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m",
        "hourly": "soil_moisture_0_to_1cm,et0_fao_evapotranspiration",
        "past_hours": 24,
        "forecast_hours": 1,
        "timezone": "America/Santiago",
    }
    with httpx.Client(timeout=timeout) as client:
        resp = client.get(OPEN_METEO_WEATHER_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    current = data.get("current") or {}
    hourly = data.get("hourly") or {}
    soil_vals = [v for v in (hourly.get("soil_moisture_0_to_1cm") or []) if v is not None]
    et0_vals = [v for v in (hourly.get("et0_fao_evapotranspiration") or []) if v is not None]
    return {
        "temperature_c": current.get("temperature_2m"),
        "relative_humidity_pct": current.get("relative_humidity_2m"),
        "soil_moisture_m3m3": round(soil_vals[-1], 3) if soil_vals else None,
        "evapotranspiration_24h_mm": round(sum(et0_vals[-24:]), 2) if et0_vals else None,
        "weather_timestamp": current.get("time"),
    }


def fetch_open_meteo_aq_24h_sync(lat: float, lon: float, timeout: float = 4.0) -> dict[str, Any]:
    """Respaldo atmosférico de 24 h desde Open-Meteo Air Quality (CAMS ~40 km)."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "pm2_5,pm10,nitrogen_dioxide,dust",
        "past_hours": 24,
        "forecast_hours": 1,
        "timezone": "America/Santiago",
    }
    with httpx.Client(timeout=timeout) as client:
        resp = client.get(OPEN_METEO_AQ_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    hourly = data.get("hourly") or {}
    pm25_list = [v for v in (hourly.get("pm2_5") or []) if v is not None]
    pm10_list = [v for v in (hourly.get("pm10") or []) if v is not None]
    times = hourly.get("time") or []
    return {
        "pm25_24h": round(sum(pm25_list[-24:]) / len(pm25_list[-24:]), 1) if pm25_list else None,
        "pm10_24h": round(sum(pm10_list[-24:]) / len(pm10_list[-24:]), 1) if pm10_list else None,
        "timestamp": times[-1] if times else None,
    }


def fetch_all_comunas_air_snapshot() -> dict[str, dict[str, Any]]:
    """Construye el snapshot real de aire + clima para todas las comunas (usado en setup y fallback)."""
    now_iso = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    try:
        sinca = fetch_sinca_stations_sync(timeout=8.0)
    except Exception:
        sinca = {}

    result: dict[str, dict[str, Any]] = {}
    for slug, cfg in COMUNA_STATION_MAP.items():
        lat, lon = cfg["lat"], cfg["lon"]
        st = sinca.get(cfg["sinca_key"])

        weather: dict[str, Any] = {}
        try:
            weather = fetch_open_meteo_weather_sync(lat, lon, timeout=5.0)
        except Exception:
            weather = {
                "temperature_c": None,
                "relative_humidity_pct": None,
                "soil_moisture_m3m3": None,
                "evapotranspiration_24h_mm": None,
                "weather_timestamp": None,
            }

        if st and st.get("pm25_24h") is not None:
            dist_km = _haversine_km(lat, lon, st["lat"], st["lon"]) if st.get("lat") else 0.0
            pm25 = st["pm25_24h"]
            pm10 = st["pm10_24h"]
            result[slug] = {
                "comuna": slug,
                "comuna_name": cfg["comuna_name"],
                "pm25_24h": pm25,
                "pm10_24h": pm10,
                "pm25_icap": st.get("pm25_icap"),
                "pm10_icap": st.get("pm10_icap"),
                "station_name": f"{st['nombre']} (SINCA {st['key']})",
                "station_comuna": st["comuna"],
                "station_distance_km": dist_km,
                "station_in_comuna": cfg["station_in_comuna"],
                "scale_note": (
                    f"Estación oficial SINCA dentro de la comuna ({dist_km} km del centroide)."
                    if cfg["station_in_comuna"]
                    else f"Estación oficial SINCA más cercana ubicada en {st['comuna']} ({dist_km} km del centroide); contexto sectorial, no calle por calle."
                ),
                "source_label": "Red Oficial SINCA (MMA Chile) — Promedio móvil 24 h",
                "source_mode": "live_sinca",
                "timestamp": st.get("timestamp") or now_iso,
                "fetched_at": now_iso,
                "weather": weather,
                "norms": _build_norm_comparison(pm25, pm10),
            }
        else:
            aq_fb = fetch_open_meteo_aq_24h_sync(lat, lon, timeout=5.0)
            pm25 = aq_fb.get("pm25_24h") or 12.0
            pm10 = aq_fb.get("pm10_24h") or 28.0
            result[slug] = {
                "comuna": slug,
                "comuna_name": cfg["comuna_name"],
                "pm25_24h": pm25,
                "pm10_24h": pm10,
                "pm25_icap": None,
                "pm10_icap": None,
                "station_name": "Open-Meteo CAMS (Cuenca Santiago)",
                "station_comuna": "Región Metropolitana",
                "station_distance_km": None,
                "station_in_comuna": False,
                "scale_note": "Respaldo atmosférico de cuenca (~40 km, promedio 24 h Open-Meteo CAMS).",
                "source_label": "Open-Meteo Air Quality (Respaldo cuenca 24 h)",
                "source_mode": "live_open_meteo_fallback",
                "timestamp": aq_fb.get("timestamp") or now_iso,
                "fetched_at": now_iso,
                "weather": weather,
                "norms": _build_norm_comparison(pm25, pm10),
            }
    return result


def get_comuna_air_quality(slug: str, fallback_path: Path) -> dict[str, Any]:
    """Obtiene calidad de aire y clima en vivo con caché 15m y fallback local infalible."""
    now = time.time()
    cached = _air_cache.get(slug)
    if cached and (now - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1]

    cfg = COMUNA_STATION_MAP.get(slug)
    if not cfg:
        raise ValueError(f"Comuna desconocida: {slug}")

    # Intenta lectura en vivo (SINCA + Open-Meteo Weather) con timeout breve
    try:
        sinca = fetch_sinca_stations_sync(timeout=3.5)
        st = sinca.get(cfg["sinca_key"])
        if st and st.get("pm25_24h") is not None:
            try:
                weather = fetch_open_meteo_weather_sync(cfg["lat"], cfg["lon"], timeout=2.5)
            except Exception:
                weather = {}
            dist_km = _haversine_km(cfg["lat"], cfg["lon"], st["lat"], st["lon"]) if st.get("lat") else 0.0
            pm25 = st["pm25_24h"]
            pm10 = st["pm10_24h"]
            payload = {
                "comuna": slug,
                "comuna_name": cfg["comuna_name"],
                "pm25_24h": pm25,
                "pm10_24h": pm10,
                "pm25_icap": st.get("pm25_icap"),
                "pm10_icap": st.get("pm10_icap"),
                "station_name": f"{st['nombre']} (SINCA {st['key']})",
                "station_comuna": st["comuna"],
                "station_distance_km": dist_km,
                "station_in_comuna": cfg["station_in_comuna"],
                "scale_note": (
                    f"Estación oficial SINCA dentro de la comuna ({dist_km} km del centroide)."
                    if cfg["station_in_comuna"]
                    else f"Estación oficial SINCA más cercana ubicada en {st['comuna']} ({dist_km} km del centroide); escala sectorial."
                ),
                "source_label": "Red Oficial SINCA (MMA Chile) — En vivo (promedio móvil 24 h)",
                "source_mode": "live_sinca",
                "timestamp": st.get("timestamp"),
                "fetched_at": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M"),
                "weather": weather,
                "norms": _build_norm_comparison(pm25, pm10),
            }
            _air_cache[slug] = (now, payload)
            return payload
    except Exception:
        pass

    # Fallback local offline fechado (inmune a caídas de Wi-Fi en el pitch)
    if fallback_path.exists():
        fb_all = json.loads(fallback_path.read_text(encoding="utf-8"))
        if slug in fb_all:
            payload = dict(fb_all[slug])
            payload["source_mode"] = "cached_fallback"
            ts = payload.get("timestamp") or payload.get("fetched_at") or "snapshot local"
            payload["source_label"] = f"Respaldo local SINCA ({ts})"
            _air_cache[slug] = (now, payload)
            return payload

    # Último recurso determinista si ni siquiera existe el archivo
    return {
        "comuna": slug,
        "comuna_name": cfg["comuna_name"],
        "pm25_24h": 10.0,
        "pm10_24h": 30.0,
        "pm25_icap": 20,
        "pm10_icap": 23,
        "station_name": cfg["station_fallback_name"],
        "station_comuna": cfg["comuna_name"],
        "station_distance_km": 0.0,
        "station_in_comuna": cfg["station_in_comuna"],
        "scale_note": "Valor referencial de respaldo por indisponibilidad de red.",
        "source_label": "Respaldo referencial offline",
        "source_mode": "offline_default",
        "timestamp": "offline",
        "fetched_at": "offline",
        "weather": {},
        "norms": _build_norm_comparison(10.0, 30.0),
    }
