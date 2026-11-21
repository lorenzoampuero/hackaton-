# Diseño del MVP — Pulmón Urbano (Hackatón Urbanismo U. de Chile / ie&t chile 2026)

> **Estado:** Borrador para revisión y aprobación del equipo  
> **Enfoque seleccionado:** Opción A — Pipeline Python (Sentinel-2 real) + Backend FastAPI + Web interactiva (HTML/Leaflet.js) + Exportación PDF en Python  
> **Principio rector:** Rigor científico verificable, simplicidad operativa y trazabilidad total para defender cada decisión en el pitch y Q&A ante el jurado de la FCFM.

---

## 1. Intención, Problema y Posicionamiento (Criterios 01, 02 y 03 de la Rúbrica)

### El problema real
En el Gran Santiago existe una brecha marcada entre sectores con áreas verdes consolidadas e hidratadas y sectores densamente poblados con déficit vegetal, suelo seco y alta exposición a calor urbano y material particulado. Los datos satelitales y ambientales abiertos para medir esta brecha ya existen, pero están encerrados en herramientas técnicas (GIS, Google Earth Engine, APIs científicas) inaccesibles para dirigentes vecinales, concejales o municipalidades sin área GIS dedicada. Como resultado, cuando comunidades o autoridades locales piden mejorar una plaza o sector en un Concejo Municipal o reunión con el alcalde, llegan con argumentos subjetivos que pierden prioridad frente a otras demandas presupuestarias.

### Propuesta de valor (por qué NO es "otro mapa satelital más")
**Pulmón Urbano** es un **traductor de datos satelitales y ambientales abiertos a evidencia estructurada y accionable**. Permite a cualquier persona sin conocimientos de teledetección:
1. Visualizar en un mapa con barras de colores claras dónde falta vegetación (**NDVI**) y dónde hay estrés hídrico o sequedad (**NDMI**), junto al contexto de calidad del aire (**MP2.5 / MP10**) en zonas pobladas.
2. Entender en lenguaje simple qué significa cada índice en un cuadrante específico y compararlo objetivamente contra un sector sano de referencia.
3. Exportar en un clic un **Informe Técnico-Ciudadano en PDF**, trazable y con fuentes oficiales, listo para llevar a una reunión con el alcalde, Concejo Municipal o postulación a fondos públicos (FPA, GORE, PMU).

### Usuarios y sostenibilidad (Viabilidad — 20%)
* **Usuario activo principal:** Agentes de cambio territorial — dirigentes vecinales (Juntas de Vecinos), concejales, ONGs de urbanismo (p. ej. Fundación Mi Parque, Cultiva) y equipos técnicos de municipalidades con recursos limitados.
* **Beneficiario final:** Habitantes de zonas pobladas con déficit de áreas verdes, calor superficial y polvo.
* **Modelo de viabilidad (sin cobro forzado al vecino):** Herramienta de **Bien Público / Civic Tech gratuita** para la ciudadanía. Su costo de adquisición de datos es **\$0** (100% datasets públicos abiertos: ESA Copernicus Sentinel-2, Open-Meteo, OpenStreetMap). Se sostiene institucionalmente vía fondos públicos/universitarios (GORE, CORFO innovación social, universidades), alianzas con ONGs urbanas o convenios municipales de monitoreo periódico.

---

## 2. Alcance: Metas, No-Metas y Anti-Metas

### Metas del MVP (qué DEBE hacer impecablemente en la demo)
1. **Ingesta real de datos satelitales Sentinel-2 L2A** (Microsoft Planetary Computer STAC API, gratis y sin API key) para **3 sectores contrastantes de Santiago** *(decisión propuesta por defecto; editable por el equipo)*:
   * **Santiago Centro / Parque O'Higgins** (referencia cercana a Beauchef, mezcla de parque consolidado y trama urbana densa).
   * **Cerro Navia** (comuna con alto contraste socioambiental y vulnerabilidad histórica en calidad del aire y áreas verdes).
   * **Estación Central** (alta densificación urbana, zonas con baja cobertura vegetal y contraste claro con Parque O'Higgins).
2. **Mapa interactivo fluido con barras de colores claras** con 3 capas intercambiables:
   * **NDVI** (cobertura y vigor vegetal, escala rojo → naranjo → amarillo → verde).
   * **NDMI** (humedad vegetal / estrés hídrico, escala café/rojo → naranjo → celeste → azul).
   * **Índice de Urgencia Socioambiental — IUS (0–100)** (escala verde → amarillo → rojo), más marcadores automáticos del **Top 5 de cuadrantes críticos** por comuna.
3. **Panel explicativo transparente** al hacer clic en cualquier cuadrante:
   * Muestra los valores exactos (NDVI medio, NDMI medio, % de superficie árida/sin vegetación, IUS 0–100), la categoría en la **Matriz de 4 Diagnósticos**, y una explicación clara en español cotidiano de *qué ve el satélite* y *por qué importa*.
   * Muestra el contexto comunal de calidad del aire (**MP2.5, MP10** y clima/humedad del suelo desde Open-Meteo, comparado contra Guía OMS y Norma Chilena D.S. 12).
4. **Comparador objetivo (Zona Crítica vs. Referencia Sana):**
   * Permite comparar el cuadrante seleccionado lado a lado contra un cuadrante de referencia consolidado (por defecto, la zona vegetada del **Parque O'Higgins**) mostrando la brecha exacta en NDVI, NDMI y urgencia.
5. **Simulador paramétrico simple + Exportador de Informe PDF (2 páginas):**
   * Permite ajustar una superficie objetivo de intervención (por defecto `600 m²`, ajustable entre `100 m²` y `5.000 m²` para representar desde una esquina/bandejón hasta una plaza vecinal), calcula de forma determinista el ahorro hídrico anual y un presupuesto referencial paramétrico, sugiere especies nativas de Chile central según el diagnóstico, y genera un **PDF descargable de 2 páginas** listo para presentar en una junta municipal.
6. **Transparencia y respaldo para Q&A integrado:**
   * Modal/sección **"Metodología y Fuentes"** visible en la app y resumida en la página 2 del PDF, mostrando la fecha exacta de la imagen Sentinel-2, el ID de escena, porcentaje de nubes, fórmulas exactas, pesos del índice y limitaciones declaradas.
   * Documento complementario `docs/QNA_DEFENSA.md` con respuestas técnicas detalladas a las preguntas críticas más probables del jurado FCFM.

### No-Metas (explícitamente fuera del MVP)
* **Sin capa cualitativa / emocional ni encuestas vecinales** (descartado por decisión del equipo para mantener el foco 100% en datos medibles, explicación clara y exportación).
* **Sin cobertura nacional ni descarga satelital en vivo durante el pitch** (se preprocesan las 3 comunas una sola vez para carga instantánea).
* **Sin chatbot ni generación de cifras con LLM** (todas las cifras, diagnósticos y recomendaciones son 100% deterministas y auditables; cero riesgo de alucinación ante el jurado).
* **Sin cuentas de usuario, login ni base de datos transaccional.**

### Anti-Metas (qué haría fracasar el proyecto aunque funcione técnicamente)
* Depender del Wi-Fi del auditorio para que el mapa o el PDF funcionen.
* Sugerir que Open-Meteo mide MP2.5 calle por calle (falta de rigor científico).
* Afirmar que arborizar 600 m² elimina el MP2.5 invernal de la cuenca de Santiago.
* Mostrar números de ahorro de agua o presupuesto sin fórmula visible ni supuestos declarados.

---

## 3. Enfoques Considerados y Elección

| Opción | Descripción | Trade-offs | Estado |
| :--- | :--- | :--- | :--- |
| **A. Python (Sentinel-2) + FastAPI + HTML/Leaflet.js + PDF ReportLab** | Preprocesamiento satelital en Python (`uv`), backend ligero en FastAPI, mapa interactivo Leaflet sin Node.js, PDF profesional generado en Python. | Máxima fluidez en el pitch, PDF consistente y auditable, no requiere Node.js. Requiere un frontend pequeño en HTML/CSS/JS limpio. | **Seleccionada por el equipo** |
| **B. 100% Python (Streamlit + Folium)** | Toda la UI en un script Streamlit. | Fácil si solo se toca Python, pero los clics en Folium recargan la página y el acabado visual se ve más a prototipo rápido. | Descartada |
| **C. Pipeline offline + HTML estático + PDF vía navegador** | Sitio estático puro sin backend. | Fácil de hostear gratis, pero la exportación a PDF varía según navegador y complica futuras extensiones del lado servidor. | Descartada |

---

## 4. Restricciones Técnicas y Operativas

* **Entorno local verificado:** macOS con `Python` y **`uv`** instalados; **sin Node.js/npm**. Todo el proyecto debe correr limpiamente con `uv` (usando Python 3.11 o 3.12 gestionado por `uv`).
* **Datos 100% gratuitos y sin credenciales de pago:**
  * Satélite: **Microsoft Planetary Computer STAC API** (`https://planetarycomputer.microsoft.com/api/stac/v1`), colección `sentinel-2-l2a` (firmada con `planetary_computer.sign_inplace`, no requiere cuenta ni token).
  * Aire y clima: **Open-Meteo Air Quality API** (`https://air-quality-api.open-meteo.com/v1/air-quality`) y **Open-Meteo Weather API** (`https://api.open-meteo.com/v1/forecast`), sin API key.
  * Mapa base: tiles públicos de **OpenStreetMap / CartoDB Positron** (con degradación elegante si no hay internet: los polígonos GeoJSON de la grilla igual se renderizan completos sobre fondo limpio).
* **Resiliencia en vivo (Pitch-proof):**
  * Los GeoJSON preprocesados viven en `data/processed/` y cargan en `< 300 ms` desde el disco local.
  * Las consultas a Open-Meteo tienen timeout corto (`3.0 s`), caché en memoria (`15 min`) y **fallback automático** a `data/processed/air_fallback.json` (generado durante el setup con lecturas reales fechadas), indicando explícitamente en la UI/PDF si el dato es `En vivo` o `Respaldo local (<fecha>)`.

---

## 5. Trasfondo Científico, Fórmulas y Metodología (Base para la Defensa)

Cada cálculo del sistema vive en un único módulo compartido (`app/scoring.py`) para garantizar coherencia absoluta entre los datos preprocesados, la interfaz web y el PDF exportado.

### 5.1 Fuente Satelital e Índices Espectrales
* **Fuente:** Sentinel-2 Level-2A (reflectancia de superficie corregida atmosféricamente, ESA Copernicus).
* **Selección de escena:** Se busca la escena más reciente sobre Santiago (`bbox` que cubre las 3 comunas) dentro de los últimos 90 días con `eo:cloud_cover < 10%` (ampliable a 180 días si hubiera nubosidad persistente). Se guarda exactamente `scene_id`, `acquisition_date` y `cloud_cover_pct` en `data/processed/metadata.json`.
* **Manejo de bandas y escala Sentinel-2 L2A:** Las bandas `B04` (Rojo, 665 nm, 10 m), `B08` (NIR, 842 nm, 10 m) y `B11` (SWIR-1, 1610 nm, 20 m) vienen en enteros escalados (`DN`). En Sentinel-2 L2A post-enero 2022 (Baseline 04.00+), la reflectancia de superficie incluye un offset radiométrico (`-1000`, escala `/ 10000`, esto es `SR = (DN - 1000) / 10000` si la escena tiene offset; en la práctica leemos el `raster:bands` metadata o `BOA_ADD_OFFSET` de STAC para aplicar la conversión exacta y acotar `SR` a `[0.0001, 1.0]`, enmascarando píxeles sin datos y nubes/sombras con la banda `SCL` — conservando clases válidas de superficie: vegetación `4`, suelo desnudo `5`, agua `6`, no clasificado/urbano `7` si aplica, excluyendo `0, 1, 3, 8, 9, 10` de nodata/nubes/sombras).
  * *Nota de ingeniería importante:* Verificar con `SCL` real en el recorte de Santiago que las zonas urbanas densas (techos/asfalto, que en Sentinel-2 L2A suelen clasificarse en `5` *not_vegetated* y ocasionalmente `7` *unclassified*) queden **incluidas** y solo se excluyan `0` (no data), `1` (saturated/defective), `3` (cloud shadows), `8` (cloud medium), `9` (cloud high), `10` (thin cirrus).
* **Remuestreo de B11:** `B11` (20 m) se remuestrea bilinealmente a la grilla exacta de `B08` (10 m) antes de calcular NDMI.
* **Fórmulas exactas:**
  * **NDVI (cobertura y vigor vegetal):**
    $$\text{NDVI} = \frac{B08 - B04}{B08 + B04}$$
  * **NDMI (humedad vegetal y estrés hídrico superficial):**
    $$\text{NDMI} = \frac{B08 - B11}{B08 + B11}$$

### 5.2 Unidad de Análisis Espacial: Grilla Regular de 200 m × 200 m
* **Decisión:** Dividir cada área de estudio en una grilla cuadrada regular de **200 m × 200 m** (en proyección métrica UTM 19S, `EPSG:32719`, reproyectada a `EPSG:4326` para GeoJSON/Leaflet).
* **Trasfondo defendible:**
  * Cada celda cubre `40.000 m²` (aprox. 4 manzanas urbanas) y promedia hasta **400 píxeles Sentinel-2 de 10 m**.
  * Evita el ruido de un solo píxel (un techo brillante o un camión), mantiene resolución suficiente para distinguir plazas, parques y barrios críticos, y produce un total manejable (~350–600 celdas en total entre las 3 zonas de estudio) para renderizado instantáneo en el navegador.
* **Áreas de estudio (Bounding Boxes precisos en WGS84, verificados en Santiago):**
  * **Santiago Centro / Parque O'Higgins:** `[-70.678, -33.474, -70.638, -33.434]` (~3.7 km × 4.4 km; incluye Parque O'Higgins, Beauchef/FCFM, Barrio República, Santiago Centro y Parque Forestal/Almagro).
  * **Cerro Navia:** `[-70.768, -33.438, -70.718, -33.404]` (~4.6 km × 3.8 km; núcleo residencial principal de Cerro Navia, incluyendo sectores de alto déficit y contraste con Parque Mapocho Río / borde poniente).
  * **Estación Central:** `[-70.722, -33.474, -70.678, -33.444]` (~4.1 km × 3.3 km; eje Alameda, sector residencial denso de Estación Central y contraste con Quinta Normal/parques cercanos).
  * *Descarte de celdas vacías:* Celdas con `< 60%` de píxeles válidos se descartan.
* **Estadísticas almacenadas por celda:**
  * `cell_id` (p. ej. `CN-042`), `comuna`, `center_lat`, `center_lon`, `area_m2` (`40000`)
  * `ndvi_mean`, `ndvi_median`, `ndvi_p10`, `ndvi_p90`
  * `ndmi_mean`, `ndmi_median`
  * `pct_arid_surface` (% de píxeles con `NDVI < 0.15`)
  * `pct_healthy_veg` (% de píxeles con `NDVI >= 0.30`)
  * `diagnostic_code` y `diagnostic_label` (Matriz de 4 Estados)
  * `ius_base_satellite` (componente satelital 0–80 precalculado, que se combina con el componente de aire 0–20 para obtener el `ius_total` 0–100)
  * `is_top_critical` (`true` para las 5 celdas con mayor urgencia en cada comuna, asegurando además un mínimo de separación espacial o ranking limpio) y `is_reference` (`true` para la celda de referencia sana seleccionada en Parque O'Higgins).

### 5.3 Escalas de Interpretación y Matriz de 4 Diagnósticos

**Rangos interpretativos (para barras de color y texto explicativo):**
* **NDVI:**
  * `< 0.10`: Cemento, asfalto o tierra desnuda (déficit severo)
  * `0.10 – 0.25`: Vegetación muy escasa o pasto deteriorado
  * `0.25 – 0.45`: Vegetación moderada / arbolado disperso
  * `> 0.45`: Vegetación densa y vigorosa (parque consolidado)
* **NDMI:**
  * `< -0.20`: Sequedad severa / suelo árido
  * `-0.20 – 0.00`: Estrés hídrico alto
  * `0.00 – 0.20`: Humedad moderada
  * `> 0.20`: Buena hidratación vegetal

**Matriz diagnóstica de 4 estados (cruce NDVI × NDMI):**
* Umbrales de corte en zona urbana de Santiago: `NDVI_THRESHOLD = 0.20` y `NDMI_THRESHOLD = -0.05`.
  1. **`CRITICAL_DESERT` — Déficit Crítico ("Desierto Urbano"):** `NDVI < 0.20` y `NDMI < -0.05`. Dominio de superficies impermeables o tierra seca sin vegetación. *Prioridad 1:* creación de sombra, arborización y suelos permeables con especies nativas de bajo consumo hídrico.
  2. **`WATER_STRESS` — Área Verde en Estrés Hídrico:** `NDVI >= 0.20` y `NDMI < -0.05`. Existe masa vegetal o césped, pero bajo déficit de humedad. *Prioridad 2:* reconversión de pasto tradicional a cubierta nativa/xerófita y optimización de riego para evitar degradación y ahorrar agua municipal.
  3. **`UNCOVERED_MOIST` — Superficie Húmeda sin Cobertura Arbórea:** `NDVI < 0.20` y `NDMI >= -0.05`. Suelo con humedad presente, sombra o cuerpo de agua, pero sin dosel vegetal suficiente. *Acción:* evaluar uso de suelo y potencial de forestación/cobertura vegetal rápida.
  4. **`HEALTHY_LUNG` — Pulmón Sano (Referencia):** `NDVI >= 0.20` y `NDMI >= -0.05`. Cobertura vegetal presente e hidratada (sub-etiqueta *Óptimo* si `NDVI >= 0.35` y `NDMI >= 0.05`). *Acción:* conservación, mantención hídrica eficiente y uso como referencia comparativa.

### 5.4 Índice de Urgencia Socioambiental (IUS, 0 a 100)
Fórmula 100% transparente y acotada a `[0, 100]`:
$$D_{\text{veg}} = \text{clip}\!\left(\frac{0.45 - \text{NDVI}}{0.45 - 0.05},\; 0,\; 1\right)$$
$$D_{\text{hid}} = \text{clip}\!\left(\frac{0.15 - \text{NDMI}}{0.15 - (-0.25)},\; 0,\; 1\right)$$
$$D_{\text{aire}} = \text{clip}\!\left(\frac{\text{MP}_{2.5}}{50.0},\; 0,\; 1\right)$$
$$\text{IUS} = \text{round}\!\left(100 \times (0.45\,D_{\text{veg}} + 0.35\,D_{\text{hid}} + 0.20\,D_{\text{aire}}),\; 1\right)$$

* **Justificación de los pesos (clave para preguntas del jurado):**
  * **80% en variables satelitales de 10 m** (45% NDVI + 35% NDMI) porque son las únicas con resolución intra-urbana real capaz de distinguir una plaza o barrio de otro dentro de la misma comuna.
  * **20% en exposición atmosférica comunal (`MP2.5` normalizado contra 50 µg/m³ de la Norma Primaria Chilena D.S. 12/2011 MMA)** porque representa el contexto sanitario de escala sectorial (Open-Meteo CAMS); eleva la urgencia de comunas con peor aire sin fingir diferencias calle por calle que el dato de aire no tiene.
* **Referencias regulatorias visibles en UI y PDF:**
  * **Guía OMS 2021 (24 h):** MP2.5 = `15 µg/m³`, MP10 = `45 µg/m³`.
  * **Norma Primaria Chilena (24 h):** MP2.5 = `50 µg/m³` (D.S. N° 12/2011 MMA), MP10 = `130 µg/m³` (D.S. N° 12/2022 MMA).

### 5.5 Modelo Paramétrico de Intervención (Determinista y Auditable)
Cuando el usuario selecciona un cuadrante y una superficie intervenible $A$ (en $\text{m}^2$, por defecto `600 m²`, editable entre `100` y `5.000 m²`):
* **Ahorro hídrico anual (reconversión/diseño nativo vs. césped convencional en clima mediterráneo de Santiago):**
  * Consumo referencial césped tradicional Santiago: `1.500 L/m²/año`.
  * Consumo referencial paisajismo nativo / xerófito establecido (Chile central): `400 L/m²/año`.
  * **Ahorro neto:** $\text{Ahorro (L/año)} = A \times (1500 - 400) = 1100 \times A$ (**73,3% de ahorro hídrico**).
* **Densidad arbórea sugerida:** `1 árbol nativo cada 25 m²` en zonas de Déficit Crítico ($\lceil A / 25 \rceil$ árboles) o `1 cada 40 m²` en reforzamiento de Áreas Verdes en Estrés Hídrico.
* **Presupuesto referencial de anteproyecto (CLP):**
  * Rango transparente: `\$22.000 CLP/m²` estimado central (rango `\$18.000 – \$28.000 CLP/m²`) considerando preparación de suelo, especies nativas, mulch retenedor de humedad y riego básico de establecimiento. Etiquetado explícitamente como *estimación paramétrica referencial para anteproyecto*.
* **Catálogo curado de especies nativas de Chile central (según diagnóstico):**
  * *Déficit Crítico / Alta sequedad:* Quillay (*Quillaja saponaria*), Molle (*Schinus latifolius*), Algarrobo chileno (*Neltuma chilensis*), Espino (*Vachellia caven*), cubresuelos xerófitos (lavanda, romero, doca).
  * *Estrés Hídrico en área verde existente:* Peumo (*Cryptocarya alba*), Maitén (*Maytenus boaria*), Quillay, reemplazo parcial de césped por praderas de bajo consumo hídrico y cobertura mulch.
* **Alcance honesto del impacto sobre aire y microclima (siempre impreso en el informe):**
  * Declara expresamente que la intervención reduce **polvo resuspendido local (MP10)**, amortigua la **isla de calor superficial** y recorta significativamente el **consumo municipal de agua de riego**, pero **no elimina por sí sola episodios estructurales de MP2.5 de cuenca invernal**, complementando planes de descontaminación (PPDA).

---

## 6. Experiencia de Usuario y Flujo del Pitch (Interfaz Web)

```
+-----------------------------------------------------------------------------------+
| [Logo] PULMON URBANO  | Comuna: [Santiago Centro v] [Cerro Navia] [Est. Central]  |
| Evidencia satelital   | [i Metodologia y Fuentes]         [Satelite: YYYY-MM-DD]  |
+-----------------------------------------------------------------------------------+
|                                          |  PANEL DE ANALISIS (35% ancho)         |
|   MAPA INTERACTIVO (Leaflet, 65% ancho)  |  ------------------------------------  |
|                                          |  [1. Diagnostico] [2. Comparar] [3.PDF]|
|   Selector capa:                         |                                        |
|   (o) Urgencia (IUS)                     |  Cuadrante: CN-042 · Cerro Navia       |
|   ( ) Vegetacion (NDVI)                  |  Estado: [ROJO] Deficit Critico        |
|   ( ) Humedad (NDMI)                     |  Indice de Urgencia: 81 / 100          |
|                                          |                                        |
|   [Grilla 200x200m coloreada]            |  NDVI: 0.09  [==--------] Muy bajo     |
|   [Pins Top 5 Zonas Criticas]            |  NDMI: -0.19 [==--------] Sequedad     |
|   [Pin Referencia Parque O'Higgins]      |  Aire comuna: MP2.5 18 ug/m3 (En vivo) |
|                                          |                                        |
|   +----------------------------------+   |  Que significa esto en simple:         |
|   | Escala continua + rangos claros  |   |  "84% de esta cuadra es cemento/tierra |
|   | [Bajo] ======> [Medio] ==> [Alto]|   |   seca sin sombra ni vegetacion..."    |
|   +----------------------------------+   |                                        |
|                                          |  [Comparar con Parque O'Higgins ->]    |
|                                          |  [Preparar y Exportar Informe PDF ->]  |
+------------------------------------------+----------------------------------------+
```

### Flujo exacto de 3 minutos para la demo en vivo
1. **Contexto inmediato (30 s):** Abrir la web en **Cerro Navia** (o **Estación Central**), mostrar las 3 capas con sus barras de colores (NDVI, NDMI, IUS) y los **Top 5 puntos críticos** detectados automáticamente.
2. **Explicación humana + Comparación (60 s):** Hacer clic en el punto crítico #1 → el panel traduce los números en lenguaje claro → pestaña **Comparar** muestra lado a lado la brecha objetiva frente al cuadrante sano de referencia del **Parque O'Higgins** (junto a Beauchef).
3. **Acción y Entrega (60 s):** Pestaña **Informe PDF** → ajustar los `m²` de intervención (ej. `600 m²`), ver el cálculo instantáneo y transparente de ahorro de agua y especies nativas → clic en **"Exportar Informe PDF"** → abrir el PDF generado de 2 páginas listo para llevar a una junta con el alcalde o Concejo Municipal.
4. **Respaldo de rigor (30 s / Q&A):** Abrir el modal **"Metodología y Fuentes"** si el jurado pregunta por fórmulas, fecha de imagen Sentinel-2 o resolución de MP2.5.

---

## 7. Estructura del Informe PDF Exportable (2 Páginas, Carta)

Generado server-side en Python con **ReportLab** (+ gráficos nítidos generados en memoria con `matplotlib` en alta resolución `150–200 DPI`):

* **Página 1 — Resumen Ejecutivo para Presentación Municipal / Ciudadana:**
  * Encabezado institucional limpio ("Informe Técnico-Ciudadano de Diagnóstico Socioambiental — Pulmón Urbano"), fecha de emisión, comuna, ID de cuadrante y coordenadas exactas (`lat, lon`).
  * Tarjeta destacada de **Índice de Urgencia (0–100)** y **Categoría Diagnóstica (Matriz NDVI × NDMI)**.
  * **Tabla comparativa clave:** Cuadrante Evaluado vs. Zona de Referencia Sana (Parque O'Higgins) — NDVI, NDMI, % superficie árida, % vegetación sana, IUS y brecha numérica.
  * **Gráfico comparativo limpio** (barras horizontales lado a lado: NDVI, NDMI e IUS de la zona evaluada vs. referencia) + **mini-mapa / ubicación espacial de la grilla** mostrando la posición del cuadrante en su comuna.
  * **Explicación en lenguaje claro:** 1 párrafo directo que un alcalde, concejal o vecino entiende en 15 segundos, más caja de **Contexto de Calidad de Aire Comunal** (MP2.5, MP10 y comparación con Guía OMS y Norma Chilena D.S. 12).
* **Página 2 — Propuesta de Intervención y Ficha de Trazabilidad Técnica:**
  * **Acción recomendada** para la categoría diagnóstica + **superficie objetivo (`m²`)** y parámetros resultantes: ahorro hídrico anual estimado (`L/año` y `%` vs. césped convencional), número referencial de árboles nativos, presupuesto referencial de anteproyecto (`CLP`) y paleta de especies nativas recomendadas de Chile central.
  * **Alcances y limitaciones (honestidad técnica):** aclaración explícita sobre escala espacial del satélite (10 m) vs. aire comunal, y rol real de la vegetación urbana (polvo MP10, isla de calor, ahorro hídrico; no reemplaza medidas estructurales de cuenca para MP2.5 invernal).
  * **Ficha Metodológica y Fuentes Verificables:** Satélite Sentinel-2 L2A (ESA Copernicus / Microsoft Planetary Computer), `scene_id`, fecha exacta de captura y `%` de nubes, fórmulas exactas de NDVI, NDMI e IUS, fuente de aire (Open-Meteo / estado en vivo o respaldo fechado) y referencia normativa chilena.

---

## 8. Arquitectura de Código y Endpoints (Opción A)

```text
/Users/mirenchu/Downloads/hackaton /
├── pyproject.toml                  # Dependencias gestionadas con uv (Python 3.12)
├── docs/
│   ├── superpowers/specs/
│   │   └── 2026-11-21-pulmon-urbano-mvp-design.md
│   └── QNA_DEFENSA.md              # Guía detallada de defensa técnica y preguntas del jurado
├── scripts/
│   └── fetch_satellite_data.py     # Pipeline reproducible: Sentinel-2 STAC -> GeoJSON + metadata + fallback aire
├── data/
│   └── processed/
│       ├── santiago_centro.geojson
│       ├── cerro_navia.geojson
│       ├── estacion_central.geojson
│       ├── metadata.json           # Fecha captura Sentinel-2, scene_id, nubes, celda referencia, resumen comunal
│       └── air_fallback.json       # Lecturas reales fechadas de Open-Meteo por comuna (respaldo offline)
├── app/
│   ├── __init__.py
│   ├── scoring.py                  # Fórmulas NDVI/NDMI/IUS, matriz 4 estados, cálculos hídricos/agronómicos
│   ├── air_quality.py              # Cliente Open-Meteo (Air + Weather) con caché 15m y fallback local
│   ├── pdf_generator.py            # Generador PDF 2 páginas (ReportLab + gráficos matplotlib)
│   └── main.py                     # Servidor FastAPI + archivos estáticos
└── static/
    ├── index.html                  # UI principal (Leaflet.js + modal Metodología + panel 3 pestañas)
    ├── styles.css                  # Diseño limpio, sobrio, alto contraste y legible en proyector
    └── app.js                      # Lógica de mapa, barras de color, comparador, simulador y descarga PDF
```

### Contrato de Endpoints FastAPI
* `GET /` → Sirve `static/index.html`.
* `GET /api/overview` → Devuelve `metadata.json` (info satelital, listado de comunas con centroides y resúmenes estadísticos, y datos completos de la celda de referencia sana en Parque O'Higgins).
* `GET /api/comunas/{slug}/grid` → Devuelve el GeoJSON de la comuna (`santiago_centro`, `cerro_navia`, `estacion_central`) enriquecido con el `ius_total` recalculado usando la lectura actual (o respaldo) de aire comunal, más el ranking Top 5 crítico.
* `GET /api/comunas/{slug}/air` → Devuelve lecturas actuales de Open-Meteo (`pm2_5`, `pm10`, `no2`, `dust`, `temperature_2m`, `soil_moisture`), comparativa con norma OMS/Chile y bandera `source_mode` (`"live"` o `"cached_fallback"` con timestamp).
* `GET /api/methodology` → Devuelve el JSON estructurado de fórmulas, umbrales, pesos, fuentes y limitaciones para renderizar el modal "Metodología y Fuentes".
* `POST /api/report/pdf` → Recibe `{ "comuna": str, "cell_id": str, "target_area_m2": int, "custom_title": str | null }` y retorna `application/pdf` listo para descarga directa (`Content-Disposition: attachment; filename="informe_pulmon_urbano_<cell_id>.pdf"`).

---

## 9. Decisiones Dejadas al Constructor (Builder)

* Diseño visual detallado (tipografía, espaciado, paleta exacta de CSS) asegurando alto contraste para verse bien en el proyector del auditorio.
* Elección de librería de mapas base tile layer (CartoDB Positron recomendado por su fondo neutro que deja destacar la barra de colores satelital, con fallback a OpenStreetMap).
* Disposición fina de márgenes y estilos de tablas en ReportLab dentro de la estructura fija de 2 páginas.
* Cobertura de pruebas unitarias para `app/scoring.py` (verificando bordes de NDVI/NDMI, matriz de 4 estados, IUS 0–100 y cálculos hídricos) y prueba de integración que valide que `POST /api/report/pdf` produce un archivo PDF válido no vacío.
