# RE-VIDA — Plataforma Multi-Satélite y Cartera de Arbolado Municipal

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

## Vista del vecino y votación (nuevo)

- `web/vecino.html`: mapa grande para vecinos. Eligen su comuna (o entran con un QR: `vecino.html?zona=cerro_navia&sitio=<id>&qr=1`), tocan un punto, ven 4 datos en palabras simples y votan qué les gustaría que se construya (con un campo «Otro»).
- `web/institucion.html`: tablero para instituciones con gráficos (mapa de la demanda, lo que más piden, votos en el tiempo, quiénes votaron, necesidad y demanda, inversión aproximada), modo claro y oscuro, filtro por idea, vista en tabla de cada gráfico y exportación a Markdown o PDF. Los porcentajes se publican solo cuando la votación cierra. Incluye un índice de confianza por resultado (cantidad de votos, QR, edad declarada y detección de ráfagas), hallazgos automáticos, costo a 5 años (obra + mantención), fondos donde postular (según el catálogo interno), modo en vivo, comparador de las 4 comunas y exportación a GeoJSON y CSV.
- En la encuesta del vecino, «Otra idea» se reemplazó por un buscador (`/api/votacion/ideas`, datos en `data/ideas_busqueda.json`); por ahora lee un archivo y más adelante leerá una tabla de la base de datos.
- Los datos simples y las opciones recomendadas salen del paso 08 (`python -m pipeline.run --pasos 08`) y del catálogo `data/opciones_votacion.json` (cada rango de costo trae su fuente o dice «por cotizar»).
- Los votos se guardan en Supabase si existen las tablas (`supabase/migrations/20261122_votacion.sql`, se ejecuta una vez en tu proyecto) y, si no, en SQLite local (`data/votos_local.db`).
- `PULMON_ADMIN_TOKEN` (en `.env`) activa los botones de cerrar/abrir votaciones; `PULMON_MIN_VOTOS` fija el mínimo de votos para mostrar porcentajes (por defecto 10).
- `python -m app.votos --demo` crea una votación cerrada con votos SIMULADOS (marcados como demo) para mostrar cómo se ven los resultados.

## Despliegue en Vercel

Vercel no lee `.env`: las variables se cargan en el panel (Settings → Environment Variables).

- **Mínimo para una demostración con votos simulados:** `PULMON_DEMO_AUTO=1`. Crea sola la votación cerrada con votos SIMULADOS de cada comuna y una votación abierta de 14 días. Sin Supabase los votos viven en memoria de cada instancia y se pierden: sirve para mostrar, no para una votación real.
- **Para guardar votos de verdad:** `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY` y `SUPABASE_SECRET_KEY` (esta última, como variable sensible), y ejecutar antes los SQL de `supabase/migrations/` en tu proyecto.
- **Administración (cerrar y abrir votaciones):** `PULMON_ADMIN_TOKEN` con un texto largo y aleatorio; opcional `PULMON_VOTOS_SAL` (otro texto aleatorio para anonimizar los votos) y `PULMON_MIN_VOTOS`.
- **Informes con IA:** `OPENAI_API_KEY`, `OPENAI_BASE_URL` y `PULMON_LLM_MODEL`. Un informe tarda cerca de 40 s: el límite de tiempo de la función en el plan gratuito de Vercel puede cortarlo.
