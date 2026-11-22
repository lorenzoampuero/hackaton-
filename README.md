# Pulmón Urbano — Plataforma Multi-Satélite y Cartera de Arbolado Municipal

Plataforma cívica y municipal de priorización territorial de **calor superficial, arborización urbana, vigor vegetal y vulnerabilidad habitacional** para el Gran Santiago, construida sobre datos públicos y reproducibles.

## Comunas incluidas en el prototipo

- **Cerro Navia** (alta exposición térmica + 83,9% techos de zinc/fibrocemento/precarios)
- **San Miguel** (densificación urbana y baja área verde por habitante)
- **Vitacura** (comuna control con 33,5% de cobertura arbórea y 34,9 °C de mediana estival Landsat)
- **Quilicura** (isla de calor estival de 42,9 °C y estrés en torno al `2026-01-29`)

## Fuentes multi-satélite y territoriales

- **NASA / USGS Landsat 8 & 9 Collection 2 L2 (`lwir11` / `qa_pixel` vía Planetary Computer):** temperatura superficial terrestre estival real (`LST °C` a 30 m) y recortes térmicos infrarrojos.
- **Copernicus Sentinel-2 L2A (AWS Earth Search STAC):** `NDVI`, `SAVI`, `NDWI`, `BSI` (10 m) y `NDMI` (*humedad de la vegetación en hojas* a 20 m), con corrección automática del offset BOA por píxeles ([`pipeline/s2.py`](pipeline/s2.py)) y recuperación adaptativa de plazas angostas.
- **ESA WorldCover 2021 (`10 m`, `CC BY 4.0`):** desglose de cobertura arbórea frente a superficie construida/impermeable (`cemento`) y suelo desnudo para calcular brecha hacia la meta de `30%`.
- **Copernicus CAMS vía Open-Meteo Air Quality (`CC BY 4.0` no comercial):** concentración comunal de `PM2.5`, `PM10`, `NO₂` y radiación `UV` máxima, junto a temperatura del aire diaria y precipitación.
- **OpenStreetMap (`ODbL`):** geometrías de parques y plazas urbanas (`>= 1.000 m²`).
- **INE Censo 2024 por manzana (capa opcional):** techos de zinc/fibrocemento/precarios, hacinamiento, infancia `0–5`, población `60+` y densidad. El ranking principal es **100% satelital biofísico**, permitiendo activar la capa habitacional del Censo bajo control del usuario.

## Vistas principales del visor web

1. **Mapa satelital:** 5 capas temáticas (`Prioridad satelital integrada`, `Isla de calor Landsat °C`, `NDVI / SAVI`, `NDMI hojas`, `Censo térmico opcional`), conmutador de mapa base (`Mapa claro`, `Satélite HD`, `Calles`), selector *Solo satélites vs + Censo térmico*, ficha de 5 pestañas con comparador visual antes/después multi-satélite y gráficos sin interpolación en nubes.
2. **Informe IA de Inversión:** cartera priorizada de los mejores parques donde invertir (`Gran Santiago` o por comuna), con verificación determinística de cifras y soporte opcional para redacción en vivo con Gemini u OpenAI.
3. **Casos y Archivos:** repositorio de casos insignia, carteras ejecutivas, Top 5 comunales, importador `.json`, notas de inspección en terreno y exportaciones en Word (`.docx`), PDF, CSV, GeoJSON y JSON.

## Comandos principales

```bash
# Ejecutar enriquecimiento multi-satélite (02c) y generar todas las salidas web (04, 05, 06)
.venv/bin/python -m pipeline.run --pasos 02c,04,05,06

# Agregar una nueva comuna
.venv/bin/python -m pipeline.run --agregar "La Pintana"

# Ejecutar pruebas unitarias y de integración
.venv/bin/pytest -v

# Levantar servidor local
python3 -m http.server 8765 -d web
```

## Límites honestos

- **NDMI** mide humedad foliar en hojas (20 m), no humedad directa del suelo.
- **Open-Meteo** se utiliza bajo licencia `CC BY 4.0` no comercial (para uso comercial se requiere plan comercial o red oficial DMC).
- Los costos en CLP y planes **B2B2G / Compra Ágil** corresponden a **hipótesis (sin verificar)**.
