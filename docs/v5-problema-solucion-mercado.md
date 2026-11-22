# Pulmón Urbano v5 — Problema, solución y estudio de mercado

Nov 22, 2026 · Borrador para revisar. Todos los montos son **hipótesis (sin verificar)** hasta cotizarlos con un municipio. Fuentes al final. Las cifras de prensa y de comunicados oficiales no son presupuestos detallados.

---

## 1. Problema (reescrito)

**El Estado y las empresas financian obras en áreas verdes y espacios deportivos que muchas veces no encajan con el lugar ni con lo que quiere la gente, y nadie guarda ese dato para decidir mejor la próxima vez.**

Hay cuatro formas de fallar, todas con casos reales en Chile (sección 3.5):

1. **Obra equivocada para el lugar.** Pasto que necesita riego donde no hay agua ni plata para regar; infraestructura que nadie pidió.
2. **Obra construida pero sin uso.** Recintos terminados que no se reciben ni se abren, o parques que se abandonan y se vandalizan.
3. **Obra que se deteriora por falta de mantención.** Juegos infantiles que se rompen a los meses; espacios descuidados que la gente deja de usar.
4. **Decisión sin información.** Se elige con criterio político o técnico, sin saber qué prefiere el vecino ni qué condiciones tiene el sitio (sombra, humedad, calor).

Lo que falta no es solo plata: es una **base de datos comparable** que diga, lugar por lugar, qué condiciones tiene, qué quiere la gente y cuánto cuesta cada opción.

> Dato propio del documento v4 (a verificar): en Espacios Públicos 2022–2025, 117 de 289 iniciativas (40 %) no llegaron a pedir sus recursos.

## 2. Solución

**Pulmón Urbano es un mediador de datos: convierte las condiciones satelitales de cada área verde y la votación de los vecinos en una base de datos que dice dónde invertir y en qué.**

### Para el vecino (gratis)
- Elige su comuna y ve el mapa en bloques de color: verde (bien), amarillo (atención), rojo (necesita ayuda), gris (sin datos suficientes).
- Toca un bloque y ve **datos en palabras simples**: humedad de la vegetación, sombra, calor en verano, cuántas personas viven cerca.
- La IA propone entre 4 y 6 opciones de qué instalar, cada una con un **rango de costo**, más un campo **«Otro»** para escribir una idea propia.
- Vota sus 3 favoritas y responde: «¿lo usarías?» y «¿ayudarías a cuidarlo?».

### Base de datos
- Los votos se guardan por bloque, de forma anónima y sin mostrar resultados con pocos votos.
- Los votos se ajustan por edad y barrio con el Censo, y siempre se muestra cuánta gente votó.

### Para municipios, consultoras, constructoras y fundaciones (de pago, contacto con ventas)
- Tocan el mismo bloque y ven: votos por opción, inversión total estimada, representatividad y condiciones del sitio.
- La IA detalla el caso y lo exporta en un paso a Markdown o PDF.
- Quien paga no puede modificar los votos. El método es público.

### Qué cambia respecto de la app actual
La versión técnica (NDVI, LST, etc.) pasa a «modo Profesional». La pantalla principal es para vecinos.

## 3. Estudio de mercado

### 3.1 Cuánta plata se mueve

| Fuente | Cifra | Nota |
|---|---|---|
| MINVU, mantención de 22 parques urbanos RM (2026) | $26.725 M | Parquemet además tiene $32.099 M para inversión |
| Subdere, plazas con máquinas de ejercicio | 901 plazas, $39.509 M (2010–14 y 2018–20) | Promedio ≈ $44 M por plaza |
| Subdere, 2020 | 137 plazas, $7.660 M | Promedio ≈ $56 M por plaza |
| GORE RM, «Plan de árboles» | $1.998 M | No informa cuántos árboles |
| FPA (MMA), según v4 | 596 proyectos, $4.609 M (2022–25) | Promedio ≈ $7,7 M, pero v4 dice «hasta $6 M» por proyecto: **verificar** |

### 3.2 Cuánto cuesta construir (CLP millones, nominales, años 2013–2026 mezclados)

| Tipo de obra | Casos | Rango | Promedio / mediana | Qué incluye |
|---|---|---|---|---|
| **Cancha de pasto sintético, comunitaria** | Melipilla 56 · Pelluhue 59 · Lo Espejo 154 | 56 – 154 | prom. ≈ 90 | 700–950 m²; algunas con cierre e iluminación |
| **Cancha sintética estándar FIFA** | Quillota 247 · Chillán Viejo 800 · Pedro Aguirre Cerda 890 | 247 – 890 | prom. ≈ 650 | 6.000 m²; cierre, luces, pavimento |
| **Multicancha** | Illapel 160+ · Cerro Placeres 175 · Valparaíso Andorra 299 | 160 – 299 | prom. ≈ 211 | Renovación o nueva (FRIL) |
| **Techado de multicancha** | Puerto Williams 488 | — | — | Un solo caso; sectorial MINVU |
| **Skatepark** (9 casos) | Ancud 18 · La Serena 50 · Freire 59 · Ñuble 60 · Viña 84 · Ovalle 107 · Macul 136 · La Calera 162 · Quilpué 193 | 18 – 193 | prom. 96,5 · mediana 84 | Los extremos: techado chico vs. hormigón con iluminación |
| **Plaza con juegos o máquinas** | Reposición 35 · Alto Jahuel 60 · Lago Ranco ≈68 · San Fernando 80 · Chañaral 92 | 35 – 92 | prom. ≈ 67 | Caso extremo: Buin 402 (446 m²) |
| **Renovación de plaza grande** | Arica 633 (3.600 m²) | — | ≈ $176.000 por m² (cálculo propio) | Renovación, no obra nueva |
| **Piscina semiolímpica nueva** | Villa Alemana ≈ 1.600 (fuente de baja confiabilidad) · Zapallar 3.748 (todo un complejo deportivo) | 1.600 – 3.748 | — | **Pocos datos: no se encontró un precio confiable de piscina nueva simple** |
| **Piscina, renovación** | Cauquenes 75 · Maipú ≈ 798 · Parque O'Higgins 1.550 | 75 – 1.550 | — | Filtros, climatización, camarines |
| **Árbol plantado** | — | — | — | **No se encontró precio unitario verificado.** El catálogo usa $45.000–$70.000 como hipótesis |

Lectura simple: una **plaza con juegos** cuesta unas decenas de millones; una **cancha** o **skatepark**, entre 50 y 200 millones; una **cancha FIFA** o **piscina**, de 600 millones hacia arriba.

### 3.3 Mantención y agua (lo que casi nadie considera al votar)

| Dato | Cifra | Año |
|---|---|---|
| Mantención de áreas verdes, Providencia | $2.962 por m² al año | 2017 |
| Mantención, rango nacional (CPP UC) | desde $350 (zona austral) hasta $3.417 (norte) por m² al año | ~2018 |
| Promedio nacional citado en v4 | $1.625 por m² al año | v4 |
| Riego en áreas verdes públicas | ≈ $4.000 M al año sobre 20 millones de m² ≈ **$200 por m² al año** (cálculo propio, orden de magnitud) | La Tercera |
| Mantención de piscinas (MINVU, dos piscinas) | $24 M en mantención y remodelación + $34 M en filtrado | 2018 |
| Reposición de juegos infantiles | $35 M en un caso | Subdere |

Regla práctica para la app: **el costo real de una obra es la inversión inicial más varios años de mantención.** Una plaza de 3.000 m² a $1.600 por m² cuesta cerca de $4,8 M al año solo en mantención.

### 3.4 Qué ha cambiado en el mercado
- El Parque Metropolitano anunció retirar **53.000 m²** de pasto («el que no cumple rentabilidad social»), con un déficit de agua cercano a 86 % entre sus dos fuentes.
- Prensa regional reporta parques de 16 comunas retirando pasto ornamental para ahorrar unos 300.000 litros diarios.
- Providencia reemplaza pasto en veredones por especies resistentes a la sequía.

### 3.5 Casos de fracaso documentados

| Caso | Qué pasó | Tipo de falla |
|---|---|---|
| **Chile Nativo (Parquemet)** | El ministro habla de $14 mil millones desperdiciados; la constructora abandonó las obras; el sector está abandonado y vandalizado desde 2022 | Obra costosa que no se terminó |
| **Parque Mapocho Río (Cerro Navia–Quinta Normal, 52 ha)** | Problemas de seguridad; se separaron contratos de mantención y seguridad | Uso afectado por inseguridad |
| **Estadio de San Antonio** | Obra terminada, el municipio no aprobó la recepción final; Contraloría detectó fallas; deportistas entrenan en una cancha sin luz ni baños | Construida, sin uso |
| **Polideportivo de La Granja** | Obra adjudicada con conflicto de interés; recinto sin operar al momento del reportaje (2023) | Construida, sin uso |
| **Juegos infantiles en plazas** | Se instalan equipos de menor calidad que los especificados y se rompen a los 3 o 4 meses; muchos municipios no tienen inventario de lo que instalaron | Mantención y fiscalización |
| **Piscina del Parque Quinta Normal** | Reabierta tras años de cierre | Obra cerrada por años |
| **517 obras públicas sin terminar (Contraloría)** | Todos los sectores, última década | Obras detenidas (dato nacional) |
| **Infraestructura deportiva** | Más de 26.000 recintos públicos, pero 88 % reporta dificultad de acceso (citado en una nota de la Cámara) | Existe, pero no se usa |

### 3.6 Lo que NO encontré (y por qué importa)
- **Ningún caso documentado de «el vecino quería cancha y le construyeron piscina».** Es probable que pase, pero nadie lo mide. **Ese vacío es lo que llena Pulmón Urbano.**
- **Ningún caso específico de parque con pasto europeo que se secó** en una ciudad árida (Calama, Copiapó). Solo debate general sobre pasto y sequía. El Parque Oasis de Calama aparece como obra valorada.
- **Costo unitario verificado de un árbol plantado en Chile.**
- **Cifras de piscina nueva simple.**
- **Una tasa nacional de «obras verdes construidas que no se usan».**

Cómo llenar los vacíos: pedir por Transparencia a SERVIU, Subdere y municipios la lista de proyectos con ubicación, año y monto, y medir con satélite si el verde de esos sitios sube o se seca después de la obra.

## 4. Cómo se traduce en la app

Cada bloque recibe, en palabras simples:

| Dato técnico | Cómo se dice al vecino |
|---|---|
| NDVI | «Qué tan verde está» |
| NDMI | «Humedad de las hojas: baja» |
| Temperatura de superficie (Landsat) | «Calor en verano: más alto que el 80 % de la comuna» |
| Árboles en 400 m | «Poca sombra alrededor» |
| Censo | «Viven muchas personas mayores y niños cerca» |

Opciones y rangos que muestra la IA (siempre desde el catálogo, nunca inventadas):

| Nivel | Ejemplos | Rango referencial (hipótesis) |
|---|---|---|
| **Pequeño** (hasta ≈ $60 M) | Bancas con sombra, bebedero, 5–10 árboles, mejorar riego, reposición de juegos | $5 M – $60 M |
| **Mediano** ($60 M – $200 M) | Plaza con juegos y máquinas, skatepark chico, cancha comunitaria, jardín de lluvia | $60 M – $200 M |
| **Grande** ($200 M +) | Cancha FIFA, multicancha techada, rediseño completo de parque | $200 M – $900 M+ |
| **Piscina** | Renovación o construcción | $75 M – $3.700 M (muy variable) |

Cada opción muestra además: **costo de mantención por año** y **si el lugar tiene agua** («por verificar en terreno»).

## 5. Modelo de negocio
- **Gratis:** vecinos (ver, votar, ver resultados de su zona).
- **De pago, contacto con ventas:** municipios, consultoras, constructoras, fundaciones y empresas con responsabilidad social.
- **Regla de independencia:** los clientes no pueden editar votos; el método y los datos agregados son públicos.
- **Primeros clientes:** consultoras y fundaciones (compra más rápida que un municipio, que depende de Compra Ágil).

## 6. Riesgos y validación
1. **Quién vota:** los presupuestos participativos suelen tener participación baja y sesgada. Se corrige con Censo y con el número de votantes visible.
2. **Fraude:** un voto por persona; verificación por QR en el parque y ubicación.
3. **Datos personales:** guardar solo lo mínimo; consultar la ley chilena de datos personales.
4. **Un voto no es un presupuesto:** la opción más votada puede costar más que el fondo.
5. **Calidad de la app actual:** corregir antes cifras de árboles, textos con jerga y temperaturas atribuidas a la fecha equivocada.
6. **Piloto:** 5 parques, 1 comuna, 4 semanas. Medir votos por parque, tasa de finalización, representatividad y si un cliente acepta pagar.

---

## 7. Cuánto cuesta operar, cuánto se gana y cuánto pagarían

Todo esto son **hipótesis para ajustar**. Cambia los números de las tablas y el resultado se recalcula con las mismas fórmulas.

### 7.1 Cuánto pagaría cada cliente (y por qué ese número)

| Cliente | Ancla del precio | Precio a probar |
|---|---|---|
| **Consultora o arquitecto paisajista** | El diseño cuesta 5–10 % de la obra (regla MINVU Espacios Públicos). Plaza de $60 M → diseño $3–6 M; una ficha de $250.000 es 4–8 % de eso | Ficha $150.000–$400.000, o paquete anual $4 M (≈15 fichas) |
| **Municipio mediano** | Tope de Compra Ágil: 100 UTM ≈ $7,24 M. Una herramienta genérica de participación parte en ≈ US$1.100–1.400 al año; nuestros datos valen más | Licencia por comuna $4–7 M al año (se usa $5,5 M) |
| **Fundación o empresa con RSE** | 1–3 % del monto del programa que financia. Programa de $200 M → $2–6 M | $6 M por programa |
| **GORE, SERVIU, ministerio** | MINVU tiene $26.725 M para mantener 22 parques; una licencia de $20–60 M es 0,07–0,22 % de eso | Licencia de datos ≈ $30 M al año (por licitación) |

### 7.2 Fórmulas

- **Ingresos** = Σ (clientes de cada tipo × precio anual).
- **Costo variable por informe** = costo de IA + cómputo. Se supone $1.000 por informe (por verificar con la factura real de DeepSeek). Es casi cero.
- **Costo de ventas** = 15 % de los ingresos (el modelo es contacto con ventas).
- **Costos fijos** = infraestructura, licencias de datos y legal ($13 M al año, supuesto) + personas (2 personas × $1,8 M al mes = $43 M al año, supuesto).
- **Resultado** = ingresos − variable − ventas − fijos.
- **Punto de equilibrio** = fijos ÷ (precio × 0,85). Con $56,2 M de fijos: **17 consultoras** (a $4 M) o **12 municipios** (a $5,5 M).
- **Costo de procesar una comuna:** en los registros de esta app tomó unos 16 minutos de cómputo por comuna (lectura de parques ≈ 11 min y satélite ≈ 5 min). Los datos satelitales son gratuitos, así que el costo es casi cero.
- **Atención con la licencia de Open-Meteo:** su API gratuita es solo para uso no comercial. Para vender hay que pasar a un plan comercial o cambiar de fuente.

### 7.3 Escenarios al segundo año (CLP millones por año)

| | Conservador | Base | Optimista |
|---|---|---|---|
| Consultoras ($4 M) | 8 | 20 | 40 |
| Municipios ($5,5 M) | 2 | 5 | 12 |
| Fundaciones/RSE ($6 M) | 1 | 3 | 6 |
| Licencias institucionales ($30 M) | 0 | 1 | 2 |
| **Ingresos** | **49** | **155,5** | **322** |
| Variable (IA y cómputo) | 0,2 | 0,6 | 1,3 |
| Ventas (15 %) | 7,3 | 23,3 | 48,3 |
| Fijos | 56,2 | 56,2 | 77,8 (3 personas) |
| **Resultado** | **−14,8** | **+75,3** | **+194,6** |
| Margen operacional | −30 % | 48 % | 60 % |

Lectura simple: casi todo el costo son personas, no tecnología. El margen bruto es altísimo, pero **solo hay ganancia si se llega a unos 17 consultoras o 12 municipios**.

Tamaño referencial del mercado municipal: si 40 comunas urbanas medianas (la meta de v4) pagaran $5,5 M, serían $220 M al año. Con 12 comunas son $66 M.

## 8. Base de datos de ejemplo (con datos reales de la app)

Archivo completo: [v5-base-de-datos-ejemplo.csv](v5-base-de-datos-ejemplo.csv) (111 parques de más de 5.000 m² con datos completos en las 4 comunas).

**Cómo se calcula el «índice de condiciones» (0 a 100, más alto es mejor):** 35 % calor de verano (menos es mejor) + 30 % árboles en 400 m + 20 % vigor de la vegetación (NDVI) + 15 % humedad de las hojas (NDMI), comparando los parques entre sí. Grupos: **buenas** (66 o más), **medias** (33 a 66), **difíciles** (menos de 33).

**Cómo se estima la inversión:** buenas → nivel pequeño ($5–60 M); medias → mediano ($60–200 M); difíciles → mediano, o grande ($200–900 M) si el parque supera 15.000 m². La mantención por año = superficie × $1.625–$2.962 por m².

| Grupo | Lugar | Área m² | Calor verano | Árboles 400 m | Personas 400 m | Índice | Obra sugerida | Inversión | Mantención/año |
|---|---|---|---|---|---|---|---|---|---|
| Buenas | Vitacura, Plaza Vecinal #13 | 7.336 | 30,6 °C | 32,7 % | 571 | 90,5 | Mantener: bancas, bebedero | $5–60 M | $12–22 M |
| Buenas | Vitacura, Plaza Turquía | 11.885 | 32,7 °C | 41,5 % | 4.179 | 90,3 | Mantener: bancas, bebedero | $5–60 M | $19–35 M |
| Buenas | Vitacura, Plaza Vecinal #23 | 5.956 | 31,8 °C | 82,8 % | 1.640 | 88,5 | Mantener | $5–60 M | $10–18 M |
| Difíciles | Quilicura, Plaza Vecinal #1 | 13.185 | 42,3 °C | 2,1 % | 17.542 | 11,8 | Sombra intensiva + árboles + bebedero | $60–200 M | $21–39 M |
| Difíciles | Cerro Navia, Parque Javiera Carrera (Sector 3) | 6.824 | 40,1 °C | 0,7 % | 7.692 | 11,6 | Sombra intensiva + árboles + bebedero | $60–200 M | $11–20 M |
| Difíciles | Quilicura, Parque Teniente Merino | 8.947 | 42,3 °C | 0,9 % | 13.186 | 8,0 | Sombra intensiva + árboles + bebedero | $60–200 M | $15–27 M |
| Difíciles | Quilicura, Plaza Vecinal #7 | 6.830 | 42,9 °C | 0,5 % | 12.786 | 3,0 | Sombra intensiva + árboles + bebedero | $60–200 M | $11–20 M |

**Totales aproximados de la cartera de las 4 comunas (111 parques):** 34 con condiciones buenas (≈ $0,2–2,0 mil millones), 40 medias (≈ $2,4–8,0 mil millones) y 37 difíciles (≈ $3,2–12,3 mil millones). En conjunto, entre **$5,8 y $22,3 mil millones** (cálculo propio con las reglas de arriba).

**Cuidados al leer la tabla:**
- El índice mide las condiciones del lugar, no la necesidad social. Un parque con malas condiciones pero casi sin vecinos alrededor (por ejemplo, Quilicura #13, con 6 personas en 400 m) no es prioridad.
- Los parques de Vitacura tienen buenas condiciones y baja vulnerabilidad: sirven como comparación, no como destino de fondos públicos.
- Muchas lecturas tienen confianza baja. Hay que verificar en terreno antes de decidir.
- Los rangos de inversión son hipótesis (sin verificar), tomados del estudio de mercado de la sección 3.

## Fuentes
- Canchas: [Subdere – Lo Espejo $154 M](https://www.subdere.gov.cl/node/83521) · [G5 Noticias – Quillota $247 M](https://g5noticias.cl/2026/10/15/municipalidad-de-quillota-invertira-247-millones-en-nuevo-espacio-deportivo-y-recreativo-para-la-villa-agustin-avezon/) · [Subdere – Pedro Aguirre Cerda $890 M](https://www.subdere.gov.cl/node/84266) · [Subdere – Pelluhue](https://www.subdere.gov.cl/node/83442) · [Subdere – Melipilla](https://www.subdere.gov.cl/node/81902)
- Skateparks: [Subdere – Ancud](https://www.subdere.gov.cl/node/75760) · [Subdere – La Serena](https://www.subdere.gov.cl/node/75814) · [Subdere – Freire](https://www.subdere.gov.cl/node/81542) · [The Clinic – Macul](https://www.theclinic.cl/2024/08/07/gobierno-de-santiago-inaugura-remodelacion-de-skatepark-en-macul/) · [G5 Noticias – La Calera](https://g5noticias.cl/2026/08/06/la-calera-contara-con-moderno-bowl-park/)
- Plazas y juegos: [Subdere – 900 plazas](https://www.subdere.gov.cl/node/81713) · [Subdere – 137 plazas 2020](https://www.subdere.gov.cl/node/81041) · [Subdere – Chañaral](https://www.subdere.gov.cl/node/84895)
- Multicanchas: [G5 Noticias – Andorra](https://g5noticias.cl/2026/09/30/cerca-de-300-millones-permitiran-renovar-la-multicancha-andorra-fortaleciendo-el-deporte-en-el-cerro-san-roque/) · [G5 Noticias – El Tordo](https://g5noticias.cl/2025/10/13/multicancha-el-tordo-en-cerro-placeres-contara-con-completo-mejoramiento/)
- Piscinas: [The Clinic – Parque O'Higgins $1.550 M](https://www.theclinic.cl/2026/06/20/reabren-piscina-olimpica-temperada-del-parque-ohiggins-tras-inversion-de-1-550-millones-y-con-descuentos-de-hasta-un-34-para-vecinos-de-santiago-mira-los-detalles/) · [Subdere – Cauquenes](https://www.subdere.gov.cl/node/83212) · [MINVU – Antilén y Tupahue 2018](https://www.minvu.gob.cl/noticia/con-una-inversion-de-58-millones-en-mejoras-de-antilen-y-tupahue-minvu-inaugura-temporada-de-piscinas/) · [CNN Chile – Quinta Normal](https://www.cnnchile.com/servicios/reabren-piscina-del-parque-quinta-normal-tras-anos-de-cierre-revisa-los-horarios-y-como-asistir-este-verano/)
- Parques: [MINVU – Parque Catrico](https://www.minvu.gob.cl/noticia/ministro-cristian-monckeberg-inaugura-parque-urbano-catrico-en-valdivia/) · [MINVU – Arica](https://www.minvu.gob.cl/noticia/ministro-felipe-ward-inaugura-obras-de-renovacion-de-plazas-del-sector-ampliacion-chile-de-arica-que-benefician-a-mas-de-5-mil-vecinos/)
- Mantención y agua: [CPP UC – informe áreas verdes](https://politicaspublicas.uc.cl/web/content/uploads/2018/05/INFORME_Administracion-%C3%81reas-verdes-3.pdf) · [La Tercera – rediseño ante la sequía](https://www.latercera.com/pulso/noticia/rediseno-plazas-parques-urbanos-ante-la-sequia/866014/) · [CNN Chile – 53.000 m² de pasto](https://www.cnnchile.com/pais/parque-metropolitano-5sacara-53-mil-metros-pasto-ahorrar-agua/)
- Fracasos: [The Clinic – Minvu y red de parques](https://www.theclinic.cl/2026/04/06/minvu-enfrenta-falencias-en-red-de-parques-urbanos-y-apuesta-por-reforzar-seguridad-mapocho-rio-y-parque-cerrillos-mientras-busca-reimpulsar-chile-nativo/) · [El Desconcierto – juegos que se rompen](https://eldesconcierto.cl/hoja-ruta/residuos-exceso-juegos-infantiles-plazas-se-rompen-los-meses-vacios-licitaciones-publicas-n5463397) · [Chilevisión – La Granja y San Antonio](https://www.chilevision.cl/noticias/reportajes/a-fondo/en-la-granja-y-san-antonio-millonarios-recintos-deportivos-sin-usar-frustran-a-talentos-locales/amp/) · [Cooperativa – 517 obras sin terminar](https://cooperativa.cl/noticias/pais/obras-publicas/contraloria-mas-de-517-obras-publicas-quedaron-sin-terminar-en-la/2025-11-18/144427.html)
- Participación: [Stanford – participación en presupuestos participativos](https://engineering.stanford.edu/news/how-do-you-give-voters-greater-voice-their-local-governments)
