# Pulmón Urbano v5 — Plan de Implementación, Impacto, Viabilidad, Supabase y Vercel

**Objetivo:** Convertir Pulmón Urbano en un MVP ejecutable, claro desde lejos ("wow factor" inmediato), escrito en lenguaje simple para municipios, consultoras e inmobiliarias, con fotografía aérea real + captura de foto de la misma página, asistente IA entrenado (preguntas frecuentes + análisis multimodal de imágenes/casos), tabla interactiva de 5 planes con restricción real en plan Gratis y activación instantánea `"Plan aceptado"` conectada a **Supabase** (`fommievafrgbyjuvnauy`), listo para desplegar en **Vercel**.

---

## 1. Evaluación de Impacto y Nivel "Wow" (Ciclo Construir → Medir → Aprender)

| Dimensión | Estado actual (v4) | Meta v5 | Métrica medible del ciclo |
| :--- | :--- | :--- | :--- |
| **Claridad desde 2 metros ("Wow")** | Mapa técnico con siglas (`NDVI`, `NDMI`, `LST`) y tarjetas repetidas | Franja ejecutiva superior legible al instante + lenguaje ciudadano y % de confianza visible (`94%`) | Tiempo para entender qué hace la app: **< 5 segundos** |
| **Construir (Build)** | Motor multi-satélite en 4 comunas (`542` parques) | Dedup de parques, vista aérea real Esri HD, captura de foto a Casos, Chat IA FAQ/foto, Supabase + Vercel | `5` fuentes oficiales + `3` tablas Supabase activas |
| **Medir (Measure)** | Sin registro de uso ni conversión | Contador de exportaciones gratis (`2 de 2`), clics en `"Activar Plan"` (`perfiles_planes`), preguntas IA (`consultas_ia`) y expedientes (`casos_guardados`) | Tasa de activación demo Free → Consultora + consultas por sesión |
| **Aprender (Learn)** | Diagnóstico estático por plantilla o JSON largo | Chat IA directo con contexto real de cada parque/comuna + validación fotográfica en terreno | Ahorro de **3 semanas de análisis GIS → 3 minutos** en toma de decisión |

### Cuantificación de la Solución (4 comunas activas, `542` sitios analizados)
- **Superficie monitoreada:** `542` parques y plazas reales (`108` Cerro Navia, `28` San Miguel, `197` Vitacura, `209` Quilicura) con `~518` escenas Sentinel-2 + `20` lecturas Landsat verano + `750` días clima ERA5 + Censo 2024 + WorldCover 2021 + Copernicus CAMS.
- **Brecha cuantificada a meta 30% de cobertura arbórea:**
  - **Cerro Navia:** `55.106 – 137.764` árboles estimados (`39,7 °C` verano · `5,2%` árboles · `83,7%` techos vulnerables).
  - **San Miguel:** `53.158 – 132.894` árboles estimados (`37,3 °C` verano · `2,4%` árboles).
  - **Quilicura:** `302.259 – 755.648` árboles estimados (`42,9 °C` verano · `3,5%` árboles).
  - **Vitacura (Comuna Control):** `0` brecha (`33,5%` árboles > `30%`, `34,9 °C`, muestra cómo el arbolado reduce hasta `8 °C` el calor superficial).

---

## 2. Tabla de Precios, Márgenes Unitarios y Competencia (Valores netos + IVA, `1 UF ≈ $41.280`)

| Plan | Precio (CLP / UF) | Qué ofrece | Costo unitario IA + DB + Hosting | Margen bruto estimado |
| :--- | :--- | :--- | :--- | :--- |
| **Gratis (Demo / Público)** | **$0** | Mapa público solo lectura, indicadores básicos, Top 5 y **2 exportaciones gratis** de datos. Sin IA en vivo. | ~$150 CLP/usuario activo | Adquisición (CAC orgánico) |
| **Pase por Proyecto** | **1,5 UF (~$62.000)** pago único | Acceso 15 días a 1 comuna/sitio, **1 informe IA verificado** y descarga completa (PDF, Word, CSV, GeoJSON). | ~$1.200 CLP/pase | **~98,1%** |
| **Profesional (Indep.)** | **1,5 UF/mes (~$62.000)** · Anual `1,2 UF` (`~$50.000`) | 1 usuario, 2 comunas, multicapa completo, **3 informes IA/mes**, exportación PDF/Word/CSV y Casos. | ~$2.400 CLP/mes | **~96,1%** |
| **Consultora ⭐ (Principal)** | **4,5 UF/mes (~$186.000)** · Anual `3,7 UF` (`~$153.000`) | Hasta 5 usuarios + lectores, 10 comunas, **15 informes IA/mes**, White-Label, GeoJSON/QGIS/Excel, historial 24m. | ~$8.500 CLP/mes | **~95,4%** |
| **Empresa (Multi-territ.)** | **9,5 UF/mes (~$392.000)** · Anual `7,8 UF` (`~$322.000`) | Usuarios ilimitados, hasta 35 comunas, IA ilimitada, White-Label + subdominio, módulo antes/después, API/GeoJSON. | ~$24.000 CLP/mes | **~93,9%** |

**Add-ons opcionales:** Comuna extra `0,4 UF/mes` (~$16.500) · Pack 5 informes IA extra `0,5 UF` (~$20.600) · Módulo terrenos constructoras `+2 UF/mes` (~$82.560).

**Comparativa con competencia:** ArcGIS Online (`~$78.000/mes` sin análisis ambiental listo), Auravant Pro (`~$59 USD/mes` foco agrícola), TOCTOC Escala (`5 UF/mes`) / Círculo (`10 UF/mes`, foco inmobiliario), Felt Team (`$199–$249 USD/mes`), Deepblocks (`$500 USD/mes`).

---

## 3. Privacidad, Protección de Datos y Confiabilidad (%)

- **Cumplimiento legal (Ley 19.628 y nueva Ley 21.719 de Protección de Datos Personales en Chile):** No procesamos ni almacenamos RUT, direcciones personales ni datos individuales de vecinos. Las cifras habitacionales provienen exclusivamente de agregados estadísticos oficiales del Censo 2024 (entorno de 400 m).
- **Fotografías en terreno y capturas:** Las fotos que el usuario sube o captura se procesan bajo consentimiento explícito del proyecto y se almacenan únicamente en sus expedientes de proyecto (`casos_guardados` en Supabase).
- **Confiabilidad cuantificada (`93%–96%` por comuna):** Calculada transparentemente según porcentaje de observaciones satelitales libres de nubes, resolución del polígono (`>= 5.000 m²` vs sitios angostos) y coincidencia de 5 fuentes oficiales (Copernicus Sentinel-2, NASA/USGS Landsat 8-9, ESA WorldCover, Open-Meteo ERA5/CAMS e INE Censo 2024).

---

## 4. Variables de Entorno para Vercel y Supabase

En **Vercel → Project Settings → Environment Variables** (Production, Preview y Development):

- `OPENAI_API_KEY` = *(tu clave DeepSeek en `.env`, rota periódicamente en consola DeepSeek)*
- `OPENAI_BASE_URL` = `https://api.deepseek.com/v1`
- `PULMON_LLM_MODEL` = `deepseek-flash`
- `PULMON_DEEPSEEK_EFFORT` = `low`
- `SUPABASE_URL` = `https://fommievafrgbyjuvnauy.supabase.co`
- `SUPABASE_PUBLISHABLE_KEY` = `sb_publishable_jyoRcj8zhC5BuvLp48XO_A_WdsrT8S3`
- `SUPABASE_SECRET_KEY` = *(tu `sb_secret_...` privada, **nunca** con prefijo `NEXT_PUBLIC_`)*

En **Supabase (`fommievafrgbyjuvnauy`)**:
- Tablas creadas por migración: `public.perfiles_planes`, `public.casos_guardados`, `public.consultas_ia` con RLS habilitado y políticas demo listas.

---

## 5. Tareas de Implementación

- [ ] **Task 1:** Guardar este plan en `docs/superpowers/plans/2026-11-22-pulmon-urbano-v5-supabase-vercel.md`.
- [ ] **Task 2:** Agregar `confianza_pct`, `salud_vegetal_pct`, normalización de nombres duplicados/sin nombre en `pipeline/04_prioridad.py`, deduplicación de cartera en `pipeline/06_paquete_caso.py`, catálogo completo de 5 planes + márgenes + BML + privacidad en `data/catalogo_intervenciones.json`, y re-ejecutar pasos `04,05` + actualizar `informes_inversion.json` y `catalogo.js`.
- [ ] **Task 3:** Aplicar migración Supabase (`perfiles_planes`, `casos_guardados`, `consultas_ia`), actualizar `.env` / `.env.example`, y crear `api/index.py`, `vercel.json` y `requirements.txt`.
- [ ] **Task 4:** Extender `app/servidor.py` con endpoints Supabase (`/api/plan/actual`, `/api/plan/activar`, `/api/auth/login`, `/api/plan/consumir-exportacion`, `/api/casos`), chat multimodal entrenado (`/api/chat`) y estado ampliado (`/api/estado`).
- [ ] **Task 5:** Rediseñar UI frontal en `web/index.html`, `web/style.css` y `web/app.js`: Hero legible de lejos con `%` de confianza, lenguaje humano simple, vista aérea real Esri World Imagery + captura de foto del parque (`#btnCapturarFotoParque`), y pestañas `Resumen / Satélite / Evolución / Inversión / Informe` renovadas.
- [ ] **Task 6:** Construir el **Asistente IA con FAQ + Foto + Casos**, vista interactiva **Planes, Viabilidad y Privacidad** (5 planes, costes/márgenes/competencia, BML, privacidad, gating en `Gratis`, Login/Registro visual y activación `"Plan aceptado"` en Supabase).
- [ ] **Task 7:** Agregar pruebas `pytest` (confianza %, carteras sin duplicados, endpoints Supabase/Chat) y verificar de extremo a extremo en navegador en vivo (`1280×800` y `390×844`).
