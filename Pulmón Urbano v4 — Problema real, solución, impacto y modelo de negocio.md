# Pulmón Urbano v4 — Problema real, solución, impacto y modelo de negocio

Nov 21, 2026 · @Lorenzo

## Resumen en 30 segundos

**Pulmón Urbano convierte imágenes satelitales gratuitas en decisiones de dónde actuar primero, dónde invertir y qué proyecto postular, para que los municipios con menos verde dejen de perder plata y fondos.**

- **Problema:** las comunas con menos verde son las más calientes y las que menos pueden pagar agua y mantención. Además, muchos proyectos se caen antes de financiarse: en Espacios Públicos 2022–2025, 117 de 289 iniciativas (40 %) no llegaron a pedir sus recursos.
- **Solución:** software que mide vegetación y humedad de la vegetación por sitio (Sentinel-2, gratis), prioriza dónde actuar primero (rescatar, invertir, optimizar o monitorear) con su nivel de confianza, verifica contratos de mantención y entrega un expediente listo para postular.
- **Impacto referencial:** por cada 5.000 m² de césped reconvertido, 3.750–7.225 m³ de agua evitados al año y $2,4–4,6 M ahorrados.
- **Quién paga:** primero consultoras y mantenedoras (pago por proyecto); luego municipios, con un diagnóstico por encargo y, más adelante, una suscripción que cabe en Compra Ágil. Juntas de vecinos y ciudadanos ven la ficha gratis.

## El problema real

**El verde, el calor y el agua se reparten según ingreso, y las comunas pobres no logran convertir los fondos existentes en proyectos que se construyan y se mantengan.** Falta verde, pero el cuello de botella está en decidir, formular y sostener.

### Lo que muestran las láminas de ANID (verificado)

- **Segregación:** alrededor del 62 % de las comunas sigue en niveles medio-bajo o bajo del Índice de Calidad de Vida Urbana (ICVU 2015–2025), y la brecha entre comunas aumentó ([The Clinic](https://www.theclinic.cl/2026/04/23/el-ranking-de-las-comunas-de-la-rm-con-mejor-calidad-de-vida-con-san-miguel-entre-las-mejores-junto-al-sector-oriente-revisa-aca-el-listado-completo/)).
- **Déficit de áreas verdes:** de las 20.864 ha proyectadas en el PRMS de 1994, solo se materializó el 7,3 %, con 3,7 m² por habitante ([El Dínamo, 16-nov-2026](https://www.eldinamo.cl/pais/2026/11/16/la-deuda-urbana-de-santiago-que-arrastra-hace-30-anos-lleva-el-73-de-las-areas-verdes-proyectadas-en-1994/)). Otro documento del MINVU RM habla de \~29.000 ha y \~10 % ejecutado: las cifras varían según el instrumento, así que cita la de tu profesional con su fuente.
- **Crisis climática:** contaminación, escasez hídrica y olas de calor. La lámina agrega que los estudios de riesgo datan de 1982; ese dato no lo pude verificar.

### Lo que verificamos nosotros

| Dato | Cifra | Fuente |
| --- | --- | --- |
| Verde desigual | Las 4 comunas más ricas tienen 32,2 % de la superficie de áreas verdes; las 4 más pobres, 4,1 % | [Reyes y Figueroa, EURE](https://www.redalyc.org/pdf/196/19615724004.pdf) |
| Calor | 29-ene-2026: 12 comunas sobre 42 °C de superficie; Quilicura sobre 43 °C; casi 8 °C de diferencia con Lo Barnechea | [Corporación Ciudades](https://eldesconcierto.cl/2026/03/04/comunas-mas-calurosas-se-concentran-en-santiago-poniente-identifican-77-zonas-frias-para-resguardarse-en-ellas) |
| Salud | 584 y 245 muertes en exceso en las olas de calor de 2017 y 2019 (total nacional); mayores de 65 los más afectados | [UC](https://www.uc.cl/noticias/estudio-uc-revela-que-580-muertes-en-un-solo-mes-son-atribuibles-a-olas-de-calor/) |
| Agua | 49,9 millones de m² de césped en el Gran Santiago (total; el 86,7 % es privado); su riego equivale al consumo diario de más de 4 millones de personas | [MINVU vía Pauta](https://www.pauta.cl/ciudad/riego-de-cesped-privado-en-la-rm-gasta-al-dia-el-agua-equivalente-al) |
| Mantención | $0 a $2.962 por m² al año; promedio nacional $1.625 | [CPP UC](https://politicaspublicas.uc.cl/web/content/uploads/2018/05/INFORME_Administracion-%C3%81reas-verdes-3.pdf) |
| Ejecución | Espacios Públicos 2022–2025: 289 iniciativas financiadas, solo 172 alcanzaron a solicitar los recursos | [Decreto 27 (BCN)](https://www.bcn.cl/leychile/navegar?idNorma=1222956) |

### Los tres cuellos de botella

1. **Mantención sin plata.** Construir un parque que no se puede mantener no sirve.
2. **Formular y ejecutar.** DIPRES describe proyectos que no responden a las necesidades de las personas y exceden costos. Aquí está el hueco que ataca el expediente.
3. **Decidir dónde y qué.** Arborizar o reconvertir césped, y en qué cuadra, hoy se decide con datos comunales o sin datos.

## Usuario, decisor y cliente

**El comprador final es el municipio, pero el primer cliente ideal es quien formula o ejecuta proyectos para él (consultoras y mantenedoras); ver la sección siguiente.** Los demás actores entran como usuarios o como segundo cliente.

| Rol | Quién | Qué necesita | ¿Paga? |
| --- | --- | --- | --- |
| Quien sufre | Vecinos de barrios con poco verde y mucho calor; mayores de 65 | Sombra, refugio y espacios seguros | No |
| Quien decide | SECPLAN, Dirección de Áreas Verdes o Medio Ambiente, concejo | Saber dónde invertir y cómo justificarlo | Sí, vía plan anual |
| Segundo cliente | Consultoras de diseño y empresas mantenedoras | Diagnóstico rápido y prueba de cumplimiento | Sí, por expediente |
| Cliente institucional | GORE, SEREMI, fundaciones | Línea base comparable y medición antes/después | Sí, observatorio |
| Usuario gratuito | Juntas de vecinos | Ficha de barrio en PDF para respaldar su postulación al FPA (hasta $6 M) | No |

## Cliente ideal y modelo de venta: B2B, B2G o B2B2G

**Con $0 y 1–2 personas conviene vender primero B2B (a consultoras y mantenedoras que trabajan para municipios) y llegar al B2G (municipios y gobiernos regionales) después, con casos que ya funcionen: un modelo B2B2G.** Una aclaración: B2G significa *business-to-government*, es decir, venderle al Estado; no es "governance".

| Camino | A quién | Ventaja | Problema | Encaje hoy (sin inversión) |
| --- | --- | --- | --- | --- |
| B2B | Consultoras de diseño, paisajismo y arquitectura; oficinas que formulan postulaciones; mantenedoras | Compra privada, sin licitación, decide una o dos personas, ciclo de semanas | No hay evidencia de que paguen; ticket pequeño ($250–400 mil por expediente); pueden copiarlo | **Alto** |
| B2G directo | Municipios (SECPLAN, Áreas Verdes) | Son el comprador final y quienes postulan a Espacios Públicos | Concejo y presupuesto; [Compra Ágil](https://www.chilecompra.cl/ley-compra-agil/) hasta 100 UTM (\~$7,24 M con la UTM de nov-2026 en $72.440), con al menos 3 cotizaciones y sin fraccionar; ciclo de meses; al menos un tercio de las comunas depende del Fondo Común Municipal ([DF](https://www.df.cl/regiones/un-tercio-de-las-comunas-de-chile-no-podria-financiar-su-operacion-si-no)) | Medio, a mediano plazo |
| B2G institucional | GORE, SEREMI, MINVU, BID, fundaciones, universidades | Tickets altos y datos comparables entre comunas | Exige credibilidad y casos previos; ciclo largo | Bajo hoy, alto después |
| Gratis para la sociedad civil | Juntas de vecinos, vecinos, prensa | Distribución y confianza | No genera ingresos | Alto, porque cuesta casi $0 |

### Por qué empezar por el B2B

1. **Quien paga captura el beneficio.** A una consultora le sirve armar rápido el diagnóstico y ganar más postulaciones. El ahorro de riego, en cambio, suele quedar en el contrato del contratista y no en el municipio (riesgo que marcó el revisor de mercado).
2. **Compra rápida y sin licitación.** Un contrato privado se cierra en semanas; una compra pública, en meses.
3. **Es un canal.** Una consultora que entrega nuestro informe con su marca nos abre sus municipios sin vender uno por uno (white label).
4. **Riesgo de conflicto de canal:** si además vendemos directo a sus clientes, la consultora puede verse amenazada. Se cuida con una regla clara: ella firma el informe y nosotros somos el proveedor de datos.

Todo esto es una hipótesis: todavía ninguna consultora ha dicho que pagaría.

### Cliente ideal

| Perfil | Descripción (hipótesis) | Por qué es buen cliente |
| --- | --- | --- |
| **#1 Consultora u oficina de proyectos** | De 2 a 15 personas; formula postulaciones (Espacios Públicos, PMU, FPA) o diseños de áreas verdes para municipios medianos | Pierde días armando diagnósticos, gana si la postulación sale y paga con su propio presupuesto |
| **#2 Municipio mediano** | Comuna urbana de \~80 mil a 300 mil habitantes, con equipo de SECPLAN que formula proyectos, vulnerabilidad media o alta, parques de más de 5.000 m² y estrés hídrico (zona central o norte); que ya postuló a fondos y perdió proyectos | Tiene el problema, puede pagar un servicio chico y es abierta a pilotos con universidades |
| **#3 Mantenedora** | Empresa con contrato municipal que necesita probar el antes y el después | Sirve solo si acepta transparentar sus resultados; se evalúa más adelante |
| **Se descarta por ahora** | Comunas muy ricas (ya tienen consultoras SIG), muy pequeñas o dependientes del Fondo Común, y las sin parques grandes (a 10 m no se miden bien) | La meta inicial son unas 30 a 50 comunas urbanas medianas (estimación del revisor de mercado, no es un dato) |

### Ficha para calificar a un cliente

Puntúa de 0 a 2 cada pregunta; si suma 8 o más de 12, vale la pena una reunión.

| # | Pregunta | 0 | 1 | 2 |
| --- | --- | --- | --- | --- |
| 1 | ¿Formula o ejecuta proyectos de áreas verdes cada año? | No | A veces | Sí, varios |
| 2 | ¿Ha perdido o retrasado proyectos por falta de diagnóstico o de datos? | No | No sabe | Sí |
| 3 | ¿Puede decidir o pagar sin licitación ni concejo? | No | Con trámite | Sí |
| 4 | ¿Tiene parques o zonas de más de 5.000 m²? | No | Pocos | Sí |
| 5 | ¿Hay estrés hídrico o alta vulnerabilidad social en su territorio? | No | Parcial | Sí |
| 6 | ¿Aceptaría un piloto y una carta de apoyo? | No | Tal vez | Sí |

### Cómo validarlo en 2 semanas

1. Hablar con **5 consultoras u oficinas** y **3 SECPLAN o Áreas Verdes**. Preguntas: ¿cuánto tiempo y plata gastan armando un diagnóstico?, ¿qué usan hoy?, ¿quién decide la compra?, ¿pagarían $300 mil por un expediente?
2. **Señal de éxito:** al menos 2 de las 5 consultoras aceptan probar con un proyecto real o dicen un precio.
3. **Señal de alarma:** todos piden que sea gratis; entonces el camino es el B2G institucional con fondos externos (GORE, fundaciones, BID) y no las ventas directas.

## Solución

**Un software que mide cada sitio con datos gratuitos y responde cuatro preguntas: dónde actuar primero, qué tipo de acción conviene, dónde invertir y si lo contratado se cumplió.** No planta ni riega: habilita a quien decide y vuelve a medir.

1. **Mapa por sitio** de vegetación (NDVI) y humedad de la vegetación (NDMI) con Sentinel-2, cada \~5 días en teoría (con nubes, menos), más clima público (Open-Meteo/ERA5).
2. **Semáforo de prioridad:** rescatar, invertir, optimizar o monitorear, con los umbrales y el nivel de confianza visibles.
3. **Alerta de pérdida:** un sitio cae frente a su historia o a sus vecinos.
4. **Verificación de contratos de mantención:** estado antes y después de cada sitio contratado.
5. **Expediente** listo para postular (Espacios Públicos, PMU, FPA) con costo, beneficiarios (Censo) y re-medición.

### Límites que hay que decir en voz alta

- **Plazas chicas.** A 10 m, una plaza de 1.000 m² son 10 píxeles. Las comunas de bajos ingresos tienen más áreas verdes pero más pequeñas, así que se trabaja por parques mayores a 5.000 m², arbolado o promedios por barrio.
- **“Humedad” es de la vegetación, no del suelo.** El NDMI mide agua en las hojas; la humedad real del suelo queda para la fase 2.
- **El calor es un proxy.** La capa de superficie caliente sale de Sentinel-2 (NDBI) y no mide temperatura. Los estudios de grados usan sensores térmicos de USGS/NASA.
- **Salud:** solo asociaciones con rango, nunca “vidas salvadas”.

## Mapa de prioridad: estrés hídrico × vulnerabilidad social

**El mapa no debe mostrar “riesgo” en general, sino dos preguntas distintas cruzadas: qué vegetación está sufriendo y quién está más expuesto.** Cada cuadrante pide una acción distinta, y esa es la diferencia con el mapa genérico que ya regalan otros.

| Cuadrante | Qué significa | Acción sugerida |
| --- | --- | --- |
| Vulnerabilidad alta y vegetación con estrés | Barrio expuesto cuyo poco verde se está secando | **Rescatar:** riego y cuidado ya, verificando en terreno |
| Vulnerabilidad alta y poco verde | Barrio expuesto sin nada que regar | **Invertir:** arborizar y armar el expediente de fondos |
| Vulnerabilidad baja y vegetación con estrés | Zona con recursos y verde bajo estrés | **Optimizar:** ajustar calendario de riego o reconvertir césped |
| Vulnerabilidad baja y vegetación sana | Sin urgencia | **Monitorear** |

Un barrio pobre sin pasto no aparece en un mapa solo de riego, y una plaza seca en una comuna de altos ingresos no merece prioridad pública. Cruzar los dos ejes evita ambos errores.

### Qué dice la industria

- **Ya existe y lo compran ciudades.** Palermo usa una herramienta de Planetek con datos satelitales abiertos y un índice de estrés de vegetación para optimizar riego ([Planetek](https://planetek.it/en/projects/sustainability_of_urban_green_spaces_in_palermo)). E2O.GREEN aplica teledetección a parques, canchas y campos de golf ([ESA](https://dragon3.esa.int/eogateway/success-story/tech-start-up-uses-satellite-data-to-boost-commercial-success)). Eso valida la demanda, pero también significa que no eres único.
- **Se vende la decisión, no la imagen.** Un piloto australiano calcula calendarios de riego según el presupuesto del concejo y el pronóstico de 7 días ([Pump Industry](https://www.pumpindustry.com.au/its-not-easy-being-green/)).
- **Hueco que sí existe:** esas soluciones son de consultora o enterprise. Un plan simple y barato para municipios chilenos medianos no lo vi.

### Reglas de diseño (por las debilidades del dato)

1. **Resolución:** los estudios de riego urbano advierten que las parcelas son pequeñas e irregulares y recomiendan imágenes de 1 m ([MDPI](https://www.mdpi.com/2071-1050/15/17/12676)), que en Chile no tenemos gratis. Con 10 a 20 m, trabajamos parques de más de 5.000 m² y promedios por barrio, y las plazas chicas salen marcadas “baja confianza”.
2. **Cada alerta lleva nivel de confianza** (alta, media o “verificar en terreno”). Un “no regar” equivocado mata árboles y cuesta políticamente.
3. **Del mapa a la orden:** cada top 5 trae acción, motivo y PDF para el concejo.
4. **Validar contra riego real:** comparar 3 a 5 parques de un municipio piloto con sus registros de riego o medidores. Esa validación es la ventaja que no se copia con un mapa.
5. **Pregunta de compra:** averiguar quién en el municipio puede cambiar el calendario de riego. Si riegan por contrato fijo, pesa más el módulo de verificación de contratos que el de riego.

## Casos: historial, señales e informes con IA

**Un “caso” es la historia con datos de un lugar: cómo cambiaron su vegetación, humedad y clima por intervalos de tiempo, qué señales aparecen y qué inversión justifica.** Sirve para mostrar evidencia a quien financia y es lo que el cliente se lleva exportado. También funciona como vitrina: los casos públicos muestran el producto sin regalar el expediente.

### Tipos de caso

| Tipo | Pregunta que responde | Datos | Ejemplo |
| --- | --- | --- | --- |
| Diagnóstico | ¿Cómo está este sitio y cómo ha cambiado? | Serie mensual de NDVI y NDMI, lluvia y temperatura del aire | Un parque grande, últimos 24 meses |
| Evento | ¿Qué pasó en una ola de calor o sequía y a quién afectó? | Serie alrededor de la fecha, más la capa social | La ola de calor del 29 de enero de 2026 (12 comunas con más de 42 °C de superficie, según Corporación Ciudades) |
| Intervención | ¿Mejoró después de actuar? | Antes y después, con un sitio de control parecido | Una reconversión o arborización con fecha conocida |
| Oportunidad de inversión | ¿Dónde y cuánto conviene invertir? | Brecha de dosel, costo estimado, beneficiarios (Censo) y fondos posibles | Un barrio con poco verde y alta vulnerabilidad |

Los casos de intervención solo se hacen con fechas y datos reales de lo que se hizo; no se inventan. Para el prototipo sirven los de diagnóstico y de evento, que usan solo datos públicos.

### Qué muestra la pantalla de un caso

- **Selector de intervalo:** semanal, mensual (por defecto) o estacional. El mensual usa la mediana de los píxeles válidos para reducir el ruido de las nubes.
- **Series:** nivel de vegetación (NDVI), humedad de la vegetación (NDMI), lluvia y temperatura del aire.
- **Marcas en el gráfico:** intervenciones, olas de calor y la última imagen válida.
- **Huecos por nubes visibles:** no se rellenan en silencio.
- **Comparaciones:** contra la propia historia del sitio (mismo mes de años anteriores) y contra un sitio de control parecido.
- **Señales** y, si corresponde, la **ficha de inversión**.
- **Botones de exportar** (ver más abajo).

### Sobre la temperatura (límite importante)

| Nivel | Qué es | Resolución | Cómo se rotula |
| --- | --- | --- | --- |
| Temperatura del aire | Dato de clima de Open-Meteo o ERA5 | Gruesa (comunal) | “Aire, referencia comunal”; revisar la licencia comercial |
| Proxy de calor | Superficie construida con NDBI de Sentinel-2 | 20 m | “Proxy de calor, no temperatura” |
| Temperatura de superficie real | Requiere sensor térmico; Landsat y ECOSTRESS vienen de NASA/USGS, que el proyecto excluyó | — | No se usa en el prototipo. Sentinel-3 (ESA) tiene una versión de \~1 km, muy gruesa para barrios; verificar si sirve |

Por eso el producto no promete “grados por barrio”: promete vegetación, humedad de la vegetación y un proxy de calor bien rotulado.

### Señales (reglas calculadas, no IA)

Las señales las calcula Python con reglas fijas. Los umbrales de abajo son ilustrativos y hay que calibrarlos con un piloto.

| Señal | Regla (hipótesis) | Lectura | Confianza |
| --- | --- | --- | --- |
| Vegetación en caída | NDVI mensual baja más de 15 % frente al mismo mes del año anterior, 2 meses seguidos | El sitio está peor que su normal | Alta si hay 3 o más años |
| Estrés hídrico | NDMI de hoy 1,5 desviaciones bajo su historia | Verificar riego en terreno | Media |
| Mejora tras intervención | NDVI sube más que el del sitio de control después de la fecha | Coincide con la intervención | Media; sin control no se afirma |
| Brecha de dosel | % de árboles bajo la meta de 30 % en un círculo de 400 m | Hay espacio para arborizar | Media; mapa de 2020/2021 |
| Calor con vulnerabilidad | Proxy de calor alto y mayor % de adultos mayores | Prioridad social | Media |
| Datos insuficientes | Menos de 6 observaciones válidas en el periodo | “Sin señal” | — |

### Informe con IA, con barandas

1. **Python calcula** las series y las señales; la IA no calcula nada.
2. Se arma un **paquete JSON** con los números, las fechas, las fuentes y la confianza.
3. El **modelo de lenguaje solo redacta** a partir de ese paquete, con una estructura fija: resumen, qué pasó, señales, límites, siguiente paso, y fuentes y fechas.
4. **Chequeo automático:** cada número del texto debe existir en el paquete; si no, el informe se rechaza.
5. **Revisión humana** antes de entregarlo a un cliente.

**Reglas del texto:** nunca decir “causó” (se dice “coincide con”), sin afirmaciones de salud, sin promesas de ahorro y siempre con los límites a la vista.

**Costo:** cada informe cuesta poco en llamadas a un modelo, pero no es cero (por confirmar). En el prototipo basta una plantilla de texto o un informe redactado por Claude a mano; la IA integrada se agrega cuando haya ingresos.

### Exportar fácil

| Salida | Contenido | Para qué |
| --- | --- | --- |
| CSV | Una fila por sitio e intervalo: sitio, fecha, NDVI, NDMI, píxeles válidos, lluvia, temperatura del aire, señales | Análisis propio en Excel |
| XLSX | Lo mismo, con una hoja de metodología | Equipos municipales |
| GeoJSON | Geometrías y atributos | Equipos SIG |
| JSON del caso | Paquete listo para que otra IA redacte un informe | Informes con IA |
| PDF | Informe de 1 a 2 páginas con gráficos y señales | Concejo y postulaciones |
| Paquete ZIP | Todo lo anterior más la ficha metodológica | Entrega a un cliente |

### Para conseguir inversión

Quien financia pide línea base, brecha cuantificada, beneficiarios, costo estimado y plan de re-medición. El caso de oportunidad de inversión los junta en una ficha. Los financistas realistas son públicos o filantrópicos (Espacios Públicos, FPA, PMU, GORE, fundaciones, BID); la ficha no promete retorno económico privado.

### Límites y riesgos

- **Estacionalidad y nubes:** comparar siempre el mismo mes y exigir un mínimo de observaciones.
- **Causalidad:** sin sitio de control, la mejora solo “coincide” con la intervención.
- **Resolución:** parques de más de 5.000 m²; las plazas chicas salen con baja confianza.
- **Licencias:** Open-Meteo gratis es no comercial; los mapas base y OSM piden atribución.
- **Privacidad:** los casos públicos usan solo sitios públicos y datos agregados.

### En el prototipo del hackathon

Una pestaña “Casos” con 2 casos precalculados (un diagnóstico y uno de evento), gráfico por intervalo, señales y botón de descarga en CSV, con informe por plantilla (IA opcional). Cuesta unas 1,5 a 2 horas extra. **Recomiendo priorizarla sobre los deslizadores de pesos,** porque muestra series de tiempo y exportación, que es lo que pide quien financia.

## Encaje con la metodología y los ODS

**Pulmón Urbano es el eslabón “Medir” del ciclo de la lámina “Emprendimiento ágil aplicado al urbanismo”**, y lo dice en su mismo lenguaje. El ciclo vuelve a empezar cada vez.

1. **Construir / Colectivo:** el municipio, la comunidad o una fundación interviene (plantar, reconvertir, mantener). Nosotros no hacemos esto.
2. **Medir:** nuestro producto. Diagnóstico antes, priorización y re-medición después, con la misma metodología.
3. **Aprender / Compartir:** informes abiertos y comparables entre barrios, que alimentan la siguiente decisión.

**ODS que cubre** (de la lámina): 11 Ciudades sostenibles, 13 Acción por el clima, 6 Agua limpia, 10 Reducción de desigualdades, 3 Salud y bienestar y 17 Alianzas.

### Dónde caes frente a los otros proyectos

Según la lámina de distribución temática, el 22,7 % de los proyectos es de cambio climático, el 13,3 % de parques urbanos y el 12,0 % de gestión hídrica. Tu idea toca los tres (48 %), así que es un tema concurrido. Te diferencias por el dato de barrio, el expediente de fondos y la verificación de contratos. Falta confirmar si esa lámina muestra los proyectos de esta edición.

## Impacto cuantificado

**El mayor ahorro no está en el agua sino en el acceso a fondos y en evitar proyectos caídos.** El agua es un argumento de apoyo.

| Qué ahorra | Cálculo | Resultado | Supuesto a validar |
| --- | --- | --- | --- |
| Agua (5.000 m² de césped reconvertido) | 0,75 a 1,445 m³ por m² × 5.000 m² | 3.750–7.225 m³ al año, el consumo anual de 60–115 personas (170 L al día) | Rango de 750 L (documento v3) a 1.445 L (césped de 1.700 L menos 85 %) |
| Dinero por agua | m³ evitados × $635 por m³ | $2,4–4,6 M al año | $635 por m³ es un cálculo mío a partir de \~$4.000 M de riego municipal |
| Mantención | El césped cuesta 65 % más que áreas sustentables | \~$640 por m² al año sobre el promedio de $1.625 | Cifra de prensa, a confirmar |
| Suscripción de $5 M | Evitar el 1 % de un contrato como el de Ñuñoa ($490 M) | $4,9 M: solo una referencia, sin holgura (hipótesis) | Hipótesis, no promesa |
| Fondos | Espacios Públicos admite hasta 30.000 UF por proyecto | \~$1.238 M (UF ≈ $41.280, aproximado) | UF vigente |
| Tiempo | Expediente en minutos en vez de semanas de equipo técnico | Sin dato público | Medir en las llamadas a SECPLAN |

### Brecha de dosel al 30 % en un círculo de 400 m (50,3 ha)

| Zona | Árboles hoy | Brecha | Árboles necesarios | Costo |
| --- | --- | --- | --- | --- |
| San Miguel | 2 % | 14 ha | 2.800–7.000 | $127–493 M |
| Beauchef | 18 % | 6 ha | 1.200–3.000 | $54–211 M |
| Vitacura | 27 % | 1,5 ha | 300–750 | $14–53 M |

Supuestos: copa de 20 a 50 m² por árbol y $45–70 mil por árbol (cifras del documento v3, sin verificar). El % de árboles es el sondeo de WorldCover.

**Advertencia:** si un xerojardín cuesta $25–60 mil por m², el agua sola tarda décadas en pagarlo. No vendas el ahorro de agua como el retorno principal.

**Métricas para el pitch y para el seguimiento:** m² intervenidos, personas a menos de 400 m (Censo), personas de 60+ en zonas críticas, agua evitada, pesos ahorrados y % de proyectos que llegan a financiamiento.

**Nota sobre el agua:** una lectura de la cifra MINVU (49,9 millones de m² y el consumo de 4 millones de personas) sugiere un riego del orden de 10 L por m² al día, bastante más que el rango del cuadro. No lo verifiqué en detalle; el cuadro queda conservador hasta medir con los registros de riego de un piloto.

## Modelo de negocio sin inversión

**Sin capital ni equipo, el modelo empieza como producto-servicio: se vende el resultado (diagnóstico y expediente) hecho con los mismos scripts, y el software se construye con el dinero que eso genere.** El plan gratuito es solo de lectura. Todos los precios son hipótesis a validar con las llamadas de la sección anterior.

### Escalera de oferta

| Escalón | Qué es | Para quién | Precio (hipótesis) | Tiempo mío por entrega |
| --- | --- | --- | --- | --- |
| 0. Ficha pública | Mapa y ficha de barrio, solo lectura; sin expediente ni descargas | Vecinos, juntas, prensa | $0 | Casi nada (página estática) |
| 1. Piloto acotado | 1 comuna, 3 parques, 30 días | Un municipio o una consultora | $0, a cambio de una carta de apoyo y de sus registros de riego | 20–30 h |
| 2. Expediente por proyecto | PDF de postulación con indicadores, línea base y marca del cliente | Consultoras, municipios | $250–400 mil | 3–6 h |
| 3. Diagnóstico por encargo | Comuna completa: prioridad, top 5, informe y ficha metodológica | Municipios, GORE, fundaciones | $0,8–2,5 M | 15–30 h |
| 4. Monitoreo anual | Actualización mensual, re-medición y alertas (cuando exista el software) | Municipios | $3–6 M al año | \~30 h al año por comuna |
| 5. Convenio institucional | Observatorio de varias comunas con línea base comparable | GORE, fundaciones, BID, universidades | $15–40 M | Alrededor de 100 h por convenio |

**Por qué así:** se cobra por proyecto y por comuna al año, que es lo que el cliente entiende y puede justificar. Los escalones 1 a 3 no necesitan software de producción y se pueden vender desde el primer mes.

### Freemium corregido

- **Gratis (solo lectura):** ficha de barrio en pantalla y comparación con un barrio de referencia. Sirve para mostrar el producto y ganar confianza.
- **De pago:** expediente, descargas (PDF, Excel, GeoJSON), comuna completa, top 5, re-medición y marca propia.
- **Por qué pagan:** porque el expediente y el diagnóstico ahorran semanas y respaldan una postulación. Dejar el expediente gratis (como estaba antes) regalaba el valor central.
- **Los usuarios gratuitos no son clientes:** su valor es la distribución y la credibilidad, no los ingresos.

### Tope de precio y compra pública

[Compra Ágil](https://www.chilecompra.cl/ley-compra-agil/) llega hasta 100 UTM, unos $7,24 M con la UTM de nov-2026 en $72.440 ([SII](https://www.sii.cl/valores_y_fechas/utm/utm2026.htm)), con al menos 3 cotizaciones, preferencia por MiPyme y proveedores locales, y sin fraccionar compras. Los escalones 2, 3 y 4 caben bajo ese tope; el 5 no.

### Escenario realista (hipótesis, no es un pronóstico)

Reemplaza al escenario anterior (\~$20 M, \~$112 M y \~$295 M), que suponía suscripciones tempranas que nadie ha validado.

| Año | Supuestos | Ingreso | Horas estimadas |
| --- | --- | --- | --- |
| 1 | 3 diagnósticos × $1,5 M + 6 expedientes × $0,3 M | \~$6,3 M | \~105 h |
| 2 | 8 diagnósticos × $1,5 M + 20 expedientes × $0,3 M + 4 monitoreos × $4 M + 1 convenio de $20 M | \~$54 M | \~460 h |
| 3 | 10 diagnósticos × $1,5 M + 40 expedientes × $0,3 M + 12 monitoreos × $4,5 M + 2 convenios × $25 M | \~$131 M | \~830 h |

**Cómo leerlo:**

- **Valor de la hora:** unos $60 mil por hora en un diagnóstico ($1,5 M en 25 h) y en un expediente ($300 mil en 5 h). Es una hipótesis: hay que medir las horas reales.
- **El año 1 es para validar, no para vivir de esto.** Los ingresos de ese año son más bien una prueba de que alguien paga.
- **El año 3 pide una persona dedicada** (\~830 h): se contrata solo con ingresos ya firmados.
- **Costos fijos:** dominio, mapa base y, si se cobra, el plan comercial del clima: del orden de $0,3 a 1 M al año (estimación mía, a confirmar).
- **Otras entradas posibles:** premios del hackathon, fondos de fomento (Corfo, ANID, GORE; confirmar qué convocatorias están vigentes) y convenios con universidades.

### Cuándo construir el software completo

Cuando haya al menos 3 clientes recurrentes que paguen el monitoreo o la re-medición. Hasta entonces, scripts, mapa estático y documentos hechos a mano.

### Riesgos de este modelo

1. **No hay comprador probado:** el revisor de mercado no halló ningún municipio chileno que pague por esto (puede ser falta de evidencia y no ausencia).
2. **El ahorro puede quedar en el contratista**, no en el municipio; por eso el primer cliente es quien formula o ejecuta proyectos.
3. **Competencia con sustitutos gratuitos** (ARClim del MMA, Barrios por el Clima, Google Tree Canopy); el diferencial debe ser el expediente de fondos y la re-medición.
4. **Open-Meteo gratis es solo no comercial:** para cobrar hay que cambiar de fuente o contratar su plan.

## Mercado, competencia, fondos y licitaciones

**No hay un producto chileno público que mida por barrio, arme el expediente y verifique contratos, pero Barrios por el Clima ya cubre parte del terreno y es más aliado que rival.**

### Competencia y referentes

| Referente | Qué hace | Cómo te diferencias |
| --- | --- | --- |
| [Barrios por el Clima](https://eldesconcierto.cl/2026/01/05/vecinos-de-lo-espejo-se-adaptan-al-cambio-climatico-mediante-alianza-que-aumenta-las-areas-verdes-con-innovacion-urbana) (Corporación Ciudades y fundaciones) | Análisis georreferenciado de calor; 77 “zonas frías” en 12 comunas; convenio con Lo Espejo | Cualquier comuna, expediente de fondos, verificación de contratos |
| [Tree Equity Score](https://www.treeequityscore.org/analyzer) (EE.UU.) | Puntaje público gratis y un “Analyzer” a medida con ciudades como Toronto | Mismo modelo (base gratis, versión con la ciudad), adaptado a Chile |
| [Google Tree Canopy Insights](https://blog.google/products-and-platforms/products/maps/how-5-cities-plan-use-tree-canopy-fight-climate-change/) | Dosel arbóreo para más de 100 ciudades | No prioriza ni arma expediente ni verifica contratos |

### Fondos que alimentan al cliente

- **FPA (MMA):** hasta $6 M por proyecto para organizaciones sin fines de lucro; 596 proyectos y $4.609 M entre 2022 y 2025.
- **Espacios Públicos (MINVU):** hasta 30.000 UF por proyecto; solo los municipios postulan; el llamado regular de 2025 cerró el 27 de junio, así que hay que confirmar la fecha del próximo (el tope incluye el diseño).
- **PMU (SUBDERE):** su guía privilegia el uso eficiente del agua. Es una guía de un plan anterior, hay que confirmar que sigue vigente.
- **Quiero mi Barrio:** $1.500 M por barrio en el concurso 2025.

### Licitaciones

**No encontré licitaciones abiertas que calcen con el producto.** Sí hay análogos que prueban que existe el presupuesto:

- Mantención y renovación de arbolado de Ñuñoa, ID 5482-127-LR25, presupuesto de $490 M.
- Mecanismo de monitoreo y verificación de la Estrategia Ciudades Verdes, adjudicado vía [UNGM](https://www.ungm.org/Public/ContractAward/157104).
- Licitación de imágenes satelitales del SII, que muestra que el Estado ya las compra.

Para monitorear en Mercado Público, busca “áreas verdes”, “arbolado”, “riego”, “teledetección”, “imágenes satelitales” e “inspección técnica”. Mercado Público tiene una API abierta.

## Pitch de 5 minutos, preguntas difíciles y qué falta validar

**El pitch cuenta una sola historia: el verde está mal repartido, los proyectos se caen en el camino y nosotros somos el paso “Medir” que lo corrige.**

1. **0:00–0:30, gancho:** “A 400 m a la redonda de Beauchef hay 18 % de árboles; en San Miguel, 2 %; en Vitacura, 27 %” (sondeo WorldCover).
2. **0:30–1:15, problema:** solo 7,3 % de las 20.864 ha proyectadas en 1994; 62 % de las comunas con calidad de vida medio-baja o baja; 117 de 289 proyectos no llegaron a pedir recursos.
3. **1:15–3:15, demo:** mapa por sitio, semáforo de riego, top 5, expediente en PDF.
4. **3:15–4:00, impacto y plata:** 5.000 m² reconvertidos y un diagnóstico de \~$1,5 M (hipótesis), que se cubre ahorrando el 0,3 % de un contrato de mantención de $490 M.
5. **4:00–4:30, metodología:** somos el “Medir” del ciclo Construir–Medir–Aprender.
6. **4:30–5:00, cierre:** pedimos un municipio piloto.

### Preguntas difíciles

| Pregunta | Respuesta corta |
| --- | --- |
| ¿Ya existe? | Barrios por el Clima mide calor en 12 comunas; nosotros damos expediente, contratos y re-medición a cualquier comuna. Somos complementarios. |
| ¿Quién paga y por qué? | El municipio, porque ya gasta en riego y mantención y puede acceder a fondos de hasta 30.000 UF. |
| ¿Resolución? | 10 m para NDVI y 20 m para NDMI; para plazas chicas, promedios por barrio. |
| ¿Las cifras son reales? | Cada fórmula tiene fuente, rango y supuesto visible; los precios son hipótesis. |
| ¿Mide temperatura? | No: la capa de calor es un proxy; la temperatura la miden sensores térmicos. |
| ¿Salud causal? | No: son asociaciones de meta-análisis con rango. |

### Qué falta validar

- [ ] 5 llamadas a SECPLAN, Áreas Verdes, consultoras o fundaciones: ¿dónde se cae un proyecto y cuántas horas toma el diagnóstico?
- [ ] Tarifa real del agua para riego municipal (usamos $635 por m³, cálculo propio).
- [ ] Qué cuenta la lámina de burbujas (16 sector público, 6 privado, 4 sociedad civil): no tiene título.
- [ ] Si la lámina de distribución temática es de esta edición.
- [ ] La cifra de “estudios de riesgo de 1982” de la lámina de ANID.
- [ ] Precios de los planes y umbral vigente de Compra Ágil.

## Resumen final y prototipo (MVP)

**Pulmón Urbano prioriza dónde actuar primero cruzando el estrés de la vegetación con la vulnerabilidad social, usando solo datos gratuitos.** Hoy se presenta como un prototipo web usable, sin hardware ni servidor, y se vende como servicio mientras no haya inversión.

### Resumen en una tabla

| Pregunta | Respuesta |
| --- | --- |
| Problema real | Verde, calor y agua mal repartidos por ingreso; 117 de 289 iniciativas de Espacios Públicos no llegaron a pedir recursos |
| Primer cliente | Consultoras y oficinas de proyectos que trabajan para municipios (B2B); después municipios y GORE (B2G): modelo B2B2G |
| Gratis | Ficha de barrio de solo lectura |
| Producto de hoy | Diagnóstico y expediente por encargo; el software llega con los ingresos |
| Precios (hipótesis) | Expediente $250–400 mil; diagnóstico $0,8–2,5 M; monitoreo $3–6 M al año |
| Ingresos (escenario) | \~$6 M año 1, \~$54 M año 2, \~$131 M año 3 |
| Impacto referencial | 5.000 m² reconvertidos: 3.750–7.225 m³ de agua al año ($2,4–4,6 M); proyectos de hasta 30.000 UF (\~$1.238 M) por desbloquear |
| Mayor riesgo | Aun no hay comprador validado; la resolución de 10–20 m deja fuera las plazas chicas |

### Prototipo del hackathon: qué hace

Una página web que se abre desde el celular o el computador, con datos reales de una comuna calculados antes con Python. **Es una demo funcional, no el producto final.**

| # | Función del prototipo | Para qué sirve en la demo |
| --- | --- | --- |
| 1 | Mapa con parques o barrios coloreados por cuadrante (rescatar, invertir, optimizar, monitorear), siempre con texto además del color | Se entiende la idea en 30 segundos |
| 2 | Interruptor de 3 capas: estrés de vegetación, vulnerabilidad social y prioridad combinada | Muestra por qué un solo mapa no basta |
| 3 | Clic en un sitio: ficha con NDVI, NDMI, fecha de la imagen, confianza, acción y un “por qué” en lenguaje simple | Transparencia del dato |
| 4 | Panel con el top 5 | Responde “dónde actúo primero” |
| 5 | Tres deslizadores de pesos (mayores de 65, densidad, poco verde) que recalculan el ranking en el navegador | Muestra que la decisión es ajustable y no una caja negra (opcional) |
| 6 | Selector entre dos fechas | Demuestra la re-medición antes y después (opcional) |
| 7 | Ventana “Cómo leer este mapa” con los límites (resolución, qué mide el NDMI) | Honestidad ante el jurado |
| 8 | Botón para imprimir o guardar la ficha en PDF y enlaces para bajar CSV y GeoJSON | Muestra la salida que un cliente se lleva |

**Pestaña “Casos” (opcional, \~1,5–2 h):** 2 casos precalculados con serie mensual, señales y descarga en CSV; ver “Casos: historial, señales e informes con IA”. Si el tiempo alcanza para una sola cosa extra, elegir esta.

### Cómo se construye sin servidor ni hardware

1. **Python en un computador, una sola vez** (notebook o script): baja imágenes Sentinel-2 y parques de OSM, calcula índices y cuadrantes, y escribe archivos GeoJSON y CSV.
2. **Una página HTML con Leaflet** lee esos archivos y dibuja todo; los deslizadores y el PDF se resuelven en el navegador.
3. **Se publica gratis** en GitHub Pages (o se abre local si falla internet). No hay base de datos, ni login, ni API propia.

### Plan de 6 a 7 horas con 2 personas

| Hora | Persona A (datos, Python) | Persona B (mapa y pitch) | Entregable |
| --- | --- | --- | --- |
| 0–1 | Elegir comuna; bajar parques de OSM y 1 a 3 escenas Sentinel-2 limpias (AWS Earth Search) | Esqueleto de Leaflet con datos de prueba | Datos y página base |
| 1–3 | NDVI y NDMI por parque (máscara SCL, offset de reflectancia); exportar GeoJSON | Capas, ficha y top 5 | Mapa con estrés de vegetación |
| 3–4 | Índice social con el Censo 2024 por manzana (mayores de 65, densidad), promediado por barrio | Leyenda, textos del “por qué” y ventana de límites | Capa social |
| 4–5 | Cruce de cuadrantes y confianza; exportar CSV y GeoJSON finales | Datos reales en la página; deslizadores o selector de fechas si hay tiempo | Prioridad combinada |
| 5–6 | Revisar cifras y fuentes de cada número | Pruebas en celular, impresión a PDF | Prototipo estable |
| 6–7 | Ensayo del pitch y 3 diapositivas | Ensayo del pitch y plan B | Demo lista |

**Si es una sola persona:** sin deslizadores ni selector de fechas; mapa, ficha, top 5 e impresión a PDF.

### Qué no incluye (y se dice así en el pitch)

- Sin servidor, login, base de datos, varias comunas ni pagos.
- Sin NDBI ni calor: el calor es solo un proxy y queda para la fase 2.
- Sin la instrucción “regar / no regar”: el prototipo prioriza estrés relativo y pide verificar en terreno hasta validar con registros de riego reales.
- Sin verificación de contratos ni alertas: se muestran como siguiente fase.

### Plan B si algo falla

- **No baja Sentinel-2:** quedarse con una sola escena y solo NDVI, y decirlo.
- **Falta el Censo por manzana:** usar el dato comunal o por zona y rotularlo como menos preciso.
- **Se cae internet:** abrir la página local y llevar capturas del mapa.
- **Datos preparados antes:** confirmar con la organización si se pueden llevar descargados; si no, bajarlos en la hora 0–1. Nunca presentar datos simulados como reales.

### Guion de la demo (5 minutos)

1. **Problema (30 s):** 7,3 % del verde proyectado, 62 % de comunas en calidad de vida media-baja o baja, 40 % de proyectos que no piden recursos.
2. **Mapa (90 s):** elegir un barrio, abrir la ficha y leer el “por qué” y la confianza.
3. **Ajuste (30 s):** mover un deslizador y ver cambiar el top 5.
4. **Modelo (90 s):** B2B2G, escalera de precios, primer cliente y valor de la hora.
5. **Cierre (60 s):** piloto gratuito de 30 días a cambio de una carta de apoyo y de los registros de riego.

### Cómo saber que funcionó

- El mapa carga rápido en un celular y se entiende en 30 segundos.
- Cada cifra tiene fuente y cada recomendación tiene motivo y confianza.
- Los límites se dicen antes de que el jurado los pregunte.

### Después del hackathon (primeros 30 días)

1. Hablar con 5 consultoras u oficinas y 3 SECPLAN o Áreas Verdes (ver “Cliente ideal”).
2. Ofrecer un piloto gratuito de 30 días a una comuna o consultora y pedir sus registros de riego.
3. Validar el modelo contra esos registros antes de prometer decisiones de riego.
4. Escribir a Barrios por el Clima, fundaciones y universidades como aliados.
5. Ajustar precios con lo que digan y recién entonces cobrar el primer expediente.

## Imágenes del lugar y ficha de inversión

**Para mostrarle un lugar a quien podría invertir, cada sitio tiene una galería con tres tipos de imagen (satélite propio, fotos del terreno y vistas externas) y una ficha de inversión con números, cada uno con fuente, fecha y confianza.** La idea nace de un CEO que dijo que esto le serviría para conseguir inversión. Es una buena señal de interés, pero no es una venta: falta saber quién es, qué inversión busca, en qué formato quiere la información y cuánto pagaría.

### Qué imagen se puede usar y para qué

| Fuente | Qué muestra | Licencia y límites | ¿Se puede poner en PDF, Word o correo? | Costo |
| --- | --- | --- | --- | --- |
| Sentinel-2 Satelite llamado Lemu propio (color real y NDVI) | Vista desde satélite a 10 m, con fecha exacta | Datos abiertos de Copernicus; citar la fuente | **Sí** | $0 |
| Fotos del cliente o de vecinos, con GPS | El terreno y sus detalles | Propias; pedir consentimiento y evitar rostros y patentes | **Sí** | $0 |
| Mapillary | Fotos a nivel de calle de la comunidad | Licencia CC BY-SA 4.0 (citar al autor y compartir igual); API con token gratuito; la cobertura es desigual ([Atlas](https://atlas.co/data-sources/mapillary/), [OSM Wiki](https://wiki.openstreetmap.org/wiki/Mapillary)) | Sí, con atribución y cuidando la condición de compartir igual | $0 |
| Google Maps, Street View y Map Tiles | Satélite de alta resolución y calle | Los términos prohíben exportar, extraer o guardar su contenido para usarlo fuera de sus servicios ([políticas de Map Tiles](https://developers.google.cn/maps/documentation/tile/policies?hl=en)); tope gratuito de 10.000 solicitudes al mes por cada SKU Essentials y de 100.000 en Map Tiles ([Google](https://developers.google.com/maps/billing-and-pricing/pricing-categories)); sobre el tope, unos $2 por 1.000 en Static Maps y $7 por 1.000 en Static Street View ([lista de precios](https://developers.google.com/maps/billing/pricing)); normalmente pide cuenta de facturación (verificar) | **No asumir.** Mostrarlo solo dentro de un visor de Google con su atribución; no pegarlo en documentos ni correos ni analizarlo con IA | $0 hasta el tope |
| OpenAerialMap (drones) | Imágenes abiertas donde existan | Cada imagen trae su propia licencia | Solo si es CC BY o más abierta | $0, cobertura incierta |

**Conclusión práctica:** no existe una fuente gratuita de alta resolución que se pueda exportar sin condiciones. Para el documento que va al inversionista se usan el satélite propio y las fotos propias o de Mapillary. Google queda como un visor interactivo opcional, con un enlace a Google Maps o Street View. Para el MVP **no hace falta Google**.

### Galería del sitio (pestaña “Imágenes”)

1. **Satélite propio:** color real y NDVI lado a lado, con un deslizador antes y después entre dos fechas válidas; muestra la fecha y el porcentaje de nubes.
2. **Fotos del terreno:** miniaturas con fecha, autor, licencia y distancia al sitio. El botón “Subir foto” deja la imagen en el navegador, lee su GPS y no la envía a ningún servidor.
3. **Vista externa:** enlaces “Abrir en Google Maps” y “Abrir Street View”, que se abren en Google y no se incrustan en los documentos.
4. **Observación asistida por IA (opcional):** para fotos propias o de Mapillary, la IA describe lo visible (pasto verde, seco o ausente; sombra; árboles; suelo desnudo; señales de abandono) con su confianza. Es cualitativa, se contrasta con el NDVI y nunca se aplica a imágenes de Google.

### Ficha de inversión (todo medible y con fuente)

| Indicador | Cómo se mide | Fuente | Confianza |
| --- | --- | --- | --- |
| Superficie del sitio (m²) | Geometría del polígono | OSM o dibujo del usuario | Alta |
| Nivel de vegetación (NDVI) y su tendencia | Mediana mensual y comparación con el mismo mes del año anterior | Sentinel-2 | Media (10 m) |
| Humedad de la vegetación (NDMI) | Puntaje z frente a su propia historia | Sentinel-2 | Media (20 m) |
| Cobertura de árboles en 400 m y brecha a la meta de 30 % | Porcentaje y hectáreas faltantes | ESA WorldCover (mapa de 2020/2021) | Media |
| Árboles necesarios (rango) | Brecha ÷ copa de 20 a 50 m² | Supuesto | Baja (hipótesis) |
| Costo estimado (rango) | Árboles × $45–70 mil | Supuesto sin verificar | Baja |
| Personas a menos de 400 m y mayores de 65 | Suma de zonas del Censo | INE, Censo 2024 | Media |
| Prioridad (cuadrante y puesto) | Cruce estrés × vulnerabilidad | Cálculo propio | Media |
| Fondos posibles | Reglas de elegibilidad | Espacios Públicos (hasta 30.000 UF, postulan municipios), FPA ($6 M, organizaciones), PMU (verificar) | Informativa |
| Plan de medición | Línea base y re-medición a los 6 y 12 meses | Propio | — |

**Si piden retorno económico (ROI):** el producto mide impacto ambiental y social; no calcula rentabilidad. Eso se dice de entrada.

### Segmento a validar: empresas

El comentario del CEO abre una hipótesis nueva: empresas con presupuesto de responsabilidad social o ESG, inmobiliarias e industrias que quieren invertir en áreas verdes o necesitan respaldar una decisión con evidencia visual y numérica. Antes de construir para ellas:

- **Preguntar al CEO:** ¿qué inversión busca y en qué etapa?, ¿quién decide?, ¿qué formato necesita (PDF, Word, presentación)?, ¿cuánto pagaría por un informe así?
- **Cuidar el *greenwashing*:** solo afirmaciones medidas y conservadoras, cada una con fuente. No se promete carbono capturado, porque no se mide.
- **Tratarlo como el cliente #1 (consultoras) o un cliente nuevo,** según lo que responda.

## Informe de inversión con IA y exportación

**El informe lo redacta una IA, pero solo con los números que calculó el sistema: dice dónde invertir, cómo y qué hacer, y se exporta a PDF, Word y correo.** No es asesoría financiera ni de ingeniería; es un borrador que una persona revisa antes de entregarlo.

### Qué contiene

1. **Resumen** de 3 frases.
2. **Dónde invertir:** el ranking del sitio o los sitios, con el motivo y los números que lo respaldan.
3. **Cómo invertir:** intervenciones elegidas del catálogo, con rango de costo, estado del costo y fondos posibles.
4. **Qué hacer:** pasos a 30, 90 y 365 días (verificar en terreno, postular, medir la línea base, re-medir).
5. **Evidencia:** señales, imágenes y series, con fuentes y fechas.
6. **Límites y confianza.**
7. **Cómo se medirá el resultado.**

### Catálogo de intervenciones (la IA elige de aquí, no inventa)

| Intervención | Cuándo aplica (regla) | Costo (estado) | Fondos posibles |
| --- | --- | --- | --- |
| Arborización de calles | Brecha de cobertura de árboles mayor a 10 puntos en 400 m y vulnerabilidad alta | $45–70 mil por árbol (hipótesis, sin verificar) | Espacios Públicos (municipio); FPA (organizaciones, hasta $6 M) |
| Reconversión de césped | Césped con estrés hídrico repetido en un sitio de más de 5.000 m² | $25–60 mil por m² (hipótesis, sin verificar) | Espacios Públicos; PMU (verificar) |
| Riego eficiente y control | Estrés hídrico con riego sospechado excesivo o insuficiente | Cotizar | Presupuesto municipal |
| Mantención y verificación | Vegetación en caída en un sitio con contrato | $0 a $2.962 por m² al año, promedio $1.625 (informe de 2018, desactualizado) | Presupuesto municipal |
| Sombra y refugios | Calor con vulnerabilidad alta y poco espacio verde posible | Cotizar | Espacios Públicos; Quiero mi Barrio si el barrio está seleccionado |
| Medición y línea base | Siempre | Cotizar | Incluida en el expediente |

El catálogo vive en un archivo (`intervenciones.json`) que se puede editar sin tocar el código, y cada costo lleva su estado (hipótesis, verificado o cotizar).

### Barandas de la IA

- **Solo redacta:** no calcula ni agrega cifras; cada número del texto debe estar en el paquete de datos.
- **Verificación automática:** un script compara los números del informe con los del paquete; si alguno no existe, el informe se rechaza y se regenera.
- **Sin causalidad:** “coincide con” y “se observa”, nunca “causó”.
- **Sin promesas** de ahorro, salud, retorno ni carbono.
- **Con límites a la vista:** resolución, qué mide el NDMI, proxy de calor y confianza de cada dato.
- **Con revisión humana** y una etiqueta visible: “Redactado con IA a partir de datos del sistema; revisado por una persona”.

### Exportar a documento y correo

| Formato | En el MVP (sin servidor) | Después |
| --- | --- | --- |
| PDF | Impresión del navegador con estilos de impresión | WeasyPrint en un servidor, con marca del cliente |
| Word (.docx) | Librería `docx` en el navegador, editable | Plantilla con marca (white label) |
| Correo | Botón “Abrir correo” (mailto con asunto, resumen corto y enlace; el PDF se adjunta a mano) y botón “Copiar como correo” | Envío real con una función en la nube y un proveedor de correo, con dominio propio (SPF y DKIM) y consentimiento de los destinatarios |
| CSV, XLSX, GeoJSON y JSON del caso | Descarga directa de los archivos ya calculados | Igual, con hoja de metodología |

Un enlace mailto admite pocos caracteres, por eso solo lleva un resumen corto; el informe completo va en el PDF adjunto.

### Cómo corre la IA sin servidor

| Modo | Cómo funciona | Cuándo |
| --- | --- | --- |
| A. Pre-generado (MVP) | Los informes de los 2 o 3 casos de la demo se generan antes con el modelo y se guardan como JSON; la página los muestra con la etiqueta de IA | Hackathon |
| B. Con proxy mínimo | Una función en la nube guarda la llave de la API, limita el uso y devuelve el informe; el costo por informe es bajo pero no es cero | Piloto |
| C. El usuario lleva su JSON | Descarga el JSON del caso y lo pega en su propio asistente de IA | Alternativa sin costo para nosotros |

La llave de la API nunca se pone en el navegador.

### Riesgos

- **Alucinación:** se controla con la verificación automática y la revisión humana.
- **Que suene a asesoría de inversión:** se evita con el texto de descargo y limitándose al catálogo.
- **Greenwashing:** solo afirmaciones medidas, con fuente y rango.
- **Correos y datos personales:** no guardar correos en el MVP; en la fase de envío real, pedir consentimiento y revisar la Ley 21.719.

## Evaluación de terrenos para compra y construcción (segundo cliente)

**El mismo motor sirve para ayudar a constructoras, inmobiliarias y fondos a descartar terrenos con señales de humedad, relieve o vegetación problemáticos antes de pagar estudios o promesas de compra, y a encontrar zonas con mejor entorno.** Surge de un problema contado por el equipo: al comprar terrenos, estas empresas no encuentran terrenos en buen estado (muy húmedos, con mala vegetación o mal relieve). Es una hipótesis de cliente, **no validada**: falta hablar con al menos una constructora o inmobiliaria.

### Qué promete y qué no

- **Sí:** un **pre-filtro de descarte** con semáforo por señal (verde, amarillo, rojo), imágenes de satélite con fecha y un informe redactado con IA, para decidir qué terrenos vale la pena estudiar.
- **No:** no dice que un terreno es “apto para construir”, no evalúa la **estructura ni la calidad del suelo** (eso exige mecánica de suelos en terreno), no revisa normativa ni títulos. El lenguaje es siempre “señales a verificar”.

### Qué se mide (todo gratis y sin NASA)

| Señal | Cómo se mide | Fuente (verificar vigencia) | Confianza |
| --- | --- | --- | --- |
| Humedad de la vegetación y su recurrencia | NDMI mensual y cuántos meses del año queda sobre el umbral | Sentinel-2 | Media |
| Agua en superficie o anegamiento | Índice MNDWI de Sentinel-2 y retrodispersión baja del radar Sentinel-1 (ve a través de nubes), en inviernos y tras lluvias | Sentinel-2 y Sentinel-1 | Media (el radar necesita filtrado; verificar en terreno) |
| Pendiente y relieve | Pendiente en % y rango de altura del terreno | Modelo de elevación Copernicus de 30 m (poco detalle para lotes chicos) | Baja a media |
| Cercanía a cauces | Distancia a ríos y esteros | OpenStreetMap | Media |
| Vegetación densa o humedal | Porcentaje de árboles y matorral en el polígono y su historia | ESA WorldCover y NDVI | Media |
| Intervención reciente (relleno o remoción) | Cambio brusco de NDVI entre meses | Sentinel-2 | Baja |
| Capas públicas de riesgo y humedales | Cruce con zonas de inundación, humedales urbanos y napa, si existen en formato descargable | Fuentes chilenas públicas (MMA, SENAPRED, DGA, IDE Chile): **confirmar existencia y licencia antes de prometer** | Informativa |
| Entorno más grato | Porcentaje de árboles en 400 m, parques a menos de 400 m, pendiente suave | OSM y WorldCover | Media |

### Escaneo de zonas (cómo se encuentran terrenos candidatos)

1. El usuario elige una zona (comuna o polígono dibujado).
2. El sistema la divide en celdas de 100 m y marca como candidatas las que tengan baja ocupación (sin edificios en OSM y con clases de suelo desnudo, pasto o matorral en WorldCover).
3. Calcula las señales de la tabla para cada celda candidata y asigna el semáforo.
4. Entrega un ranking de las mejores celdas y un mapa con imágenes de satélite con fecha.
5. El usuario puede también pegar o dibujar un terreno concreto para evaluarlo.

El escaneo **no identifica propietarios ni precios**; solo señala dónde mirar.

### Semáforo y puntaje (valores iniciales, hipótesis)

- **Rojo** si hay agua o anegamiento detectados en más de 2 inviernos o más de 15 % del área, o pendiente mayor a 20 %, o el terreno toca un cauce o humedal.
- **Amarillo** si hay humedad recurrente moderada, pendiente entre 10 y 20 % o vegetación densa que podría tener restricciones.
- **Verde** si no hay señales de lo anterior.
- **Resultado global:** “pasa el pre-filtro” (sin rojos), “revisar” (con amarillos) o “descartar por ahora” (con algún rojo). Los umbrales viven en `config.yml` y deben calibrarse con un experto antes de usarse con clientes.

### Informe de pre-evaluación con IA

Misma tubería y mismas barandas que el informe de inversión: la IA solo redacta con números calculados. Contenido: resumen, tabla de semáforo con valores y fuentes, imágenes de satélite (verano e invierno), qué verificar en terreno (mecánica de suelos, topografía, napa, normativa), límites y confianza. Se exporta igual: PDF, Word, CSV, GeoJSON y correo.

### Cliente y negocio (por validar)

- **Quién compra:** constructoras, inmobiliarias, corredores de terrenos y fondos de inversión; el ciclo de venta es más corto que el de un municipio.
- **Qué se les ahorra:** estudios o promesas de compra sobre terrenos que se podían descartar antes. El ahorro por cliente **no está cuantificado**: hay que preguntar cuánto cuesta hoy su estudio inicial y cuántos terrenos descartan.
- **Precio:** por terreno o por zona escaneada; se define después de la conversación con una empresa, tomando como ancla el costo de lo que reemplaza (cotizar).
- **Competencia a investigar:** consultores geotécnicos y topográficos, corredores, y plataformas de datos territoriales y de imágenes satelitales.

### Preguntas para validar con una constructora o inmobiliaria

1. ¿Cómo descartan hoy un terreno antes de comprar y cuánto tiempo y dinero cuesta?
2. ¿Cuántos terrenos revisan al año y cuántos descartan por humedad, relieve o vegetación?
3. ¿Qué información les falta al inicio y en qué formato la quieren (PDF, Word, mapa)?
4. ¿Quién decide y quién paga?
5. ¿Pagarían por un pre-filtro así? ¿Cuánto, por terreno o por zona?

### Riesgos

- **Responsabilidad:** un informe equivocado puede costar una mala compra. Se mitiga con lenguaje de señales, límites visibles, revisión humana y descargo.
- **Resolución:** 10 a 30 m no sirve para lotes muy pequeños; fijar un tamaño mínimo (por ejemplo 2.000 m²).
- **Datos públicos chilenos:** algunas capas pueden no estar en formato usable; en ese caso se enlazan, no se prometen.
- **Dispersar el equipo:** para la demo de hoy es un **caso de uso adicional del mismo motor**, no un segundo producto.

## Diseño final del producto

**Pulmón Urbano ayuda a decidir dónde actuar primero en áreas verdes y terrenos, usando solo imágenes de satélite y datos gratuitos, y entrega un informe listo para decidir o conseguir inversión.** Esta sección cierra el diseño: lo que contiene el producto, lo que queda fuera y lo que sigue sin validar.

### Para quién y qué obtiene

| Usuario | Qué obtiene | Estado |
| --- | --- | --- |
| Consultoras y oficinas de proyectos (cliente inicial) | Ranking de sitios, ficha con imágenes e informe para sus proyectos | Hipótesis, por validar |
| Municipios (SECPLAN, áreas verdes) | Prioridad de dónde invertir y verificar, e informe para postular a fondos | Hipótesis, por validar |
| Constructoras e inmobiliarias | Pre-filtro de terrenos con semáforo (humedad, relieve, vegetación) | Hipótesis, sin hablar con una empresa |
| Inversionistas y empresas (comentario de un CEO) | Imágenes de satélite y cifras con fuente para respaldar una inversión | Interés declarado, no es una venta |

### Datos y satélites: solo gratuitos

| Se usa | Para qué | Costo |
| --- | --- | --- |
| Sentinel-2 (Copernicus) | Imágenes de color real, vegetación (NDVI), humedad (NDMI), agua (MNDWI) | $0 |
| Sentinel-1 (Copernicus, radar) | Agua en superficie con nubes; opcional | $0 |
| Modelo de elevación Copernicus de 30 m | Pendiente y relieve | $0 |
| ESA WorldCover | Cobertura de árboles, pasto y suelo desnudo | $0 |
| OpenStreetMap | Parques, cauces y edificios | $0 |
| Censo 2024 (INE) | Población y adultos mayores por zona | $0 |
| Open-Meteo o ERA5 | Lluvia y temperatura del aire (Open-Meteo gratis solo para uso no comercial) | $0 |
| Mapillary y fotos propias | Fotos del terreno | $0 |

**Quedan fuera:** NASA y USGS (Landsat, ECOSTRESS), imágenes de Google en documentos, y todo satélite pagado o por acuerdo (incluido Lemu Nge, que parece comercial y no tiene datos abiertos confirmados). Si más adelante hay un cliente que lo justifique, se evalúa como mejora aparte.

### Un solo flujo, cinco pasos

1. **Elegir** una zona (comuna o polígono) o un sitio.
2. **Escanear:** el sistema calcula las señales de cada sitio o celda candidata.
3. **Priorizar:** ranking con cuadrantes (parques) o semáforo (terrenos).
4. **Ver la evidencia:** ficha con imágenes de satélite con fecha, serie por intervalos, fotos y ficha de inversión.
5. **Decidir y exportar:** informe redactado con IA a partir de números calculados; PDF, Word, CSV, GeoJSON y correo.

### Pantallas (una sola página, cinco pestañas)

- **Mapa:** sitios coloreados, capas y ranking.
- **Ficha del sitio:** resumen, imágenes, serie, inversión e informe.
- **Casos:** diagnóstico, evento, intervención y oportunidad de inversión.
- **Terrenos:** escaneo de zona y semáforo.
- **Cómo leer este mapa:** límites y fuentes, siempre accesible.

### Qué entra en cada etapa

| Etapa | Contenido |
| --- | --- |
| Hackathon (obligatorio) | Mapa con ranking, ficha, imágenes de satélite con fecha, serie, informe de IA pre-generado y exportar a PDF y CSV |
| Si sobra tiempo | Terrenos con semáforo, Word, correo, fotos propias o de Mapillary |
| Después del hackathon | Proxy de IA, envío real de correo, varias comunas, login, marca blanca, validación con clientes |

### Decisiones cerradas

- Sitio estático, sin servidor ni base de datos ni login; costo $0.
- Solo datos reales; si faltan, “sin dato” o rotulado como ejemplo.
- Cada cifra con fuente, fecha y confianza.
- La IA solo redacta con números calculados y lo verifica un script; lleva etiqueta y revisión humana.
- Lenguaje de “prioridad” y “verificar en terreno”: nunca “riego”, “apto”, retornos, salud ni carbono.
- El motor es uno solo; parques y terrenos son casos de uso del mismo motor.

### Sigue sin validar

- Que los clientes paguen y cuánto; ninguna cifra de ahorro está comprobada con un cliente.
- Los umbrales del ranking y del semáforo: son hipótesis para calibrar con expertos.
- Disponibilidad y licencia de algunas fuentes (Censo por manzana, capas de riesgo chilenas, colecciones de Sentinel-1 y del modelo de elevación).
- Los costos por árbol y por m².

### Cómo se juzga la demo

- Se ve un caso real completo, del mapa al informe, sin fallar.
- Cada número se puede rastrear a su fuente.
- Los límites se dicen antes de que los pregunten.

## Especificación de construcción del MVP (para Fable)

**Esta sección es una instrucción para el modelo que construye el prototipo (Fable). Léela completa antes de escribir código; el resto del documento da el contexto y las razones de cada decisión.**

### 1. Contexto en cinco líneas

- **Qué es:** un mapa de decisión que cruza el estrés de la vegetación (Sentinel-2) con la vulnerabilidad social (Censo 2024) para priorizar dónde actuar primero en áreas verdes urbanas de Chile.
- **Quién lo usa:** consultoras y oficinas de proyectos (cliente inicial), municipios, y empresas o inversionistas que quieren evidencia visual y numérica.
- **Qué entrega:** mapa, ficha por sitio, casos con series por intervalos, galería de imágenes, ficha de inversión, informe redactado con IA y exportación (PDF, Word, CSV, GeoJSON, correo).
- **Contexto del evento:** hackathon de 6 a 7 horas el 21 y 22 de noviembre de 2026, equipo de 1 o 2 personas, sin dinero y sin hardware.
- **Secciones de apoyo de este documento:** “Mapa de prioridad”, “Casos”, “Imágenes del lugar”, “Informe de inversión con IA” y “Datos y APIs externas”.

### 2. Restricciones obligatorias

- Sitio **estático en español de Chile**: sin servidor, sin base de datos y sin login. Los números usan punto para miles y coma para decimales; la plata, en pesos chilenos.
- **Costo $0:** solo fuentes gratuitas. Cualquier servicio que pida tarjeta o pago queda fuera del camino principal.
- **Datos reales de una comuna.** Nunca mostrar datos simulados como si fueran reales; si algo falta, mostrar “sin dato” o rotularlo como ejemplo.
- **Cada cifra lleva fuente, fecha y confianza.**
- **Honestidad del dato:** resolución de 10 a 20 m; el NDMI mide humedad de la vegetación; el calor es un proxy; nunca decir “regar” o “no regar”, sino “prioridad” y “verificar en terreno”.
- **Funciona en celular**, carga rápido y usa color más texto (accesibilidad).
- **Sin llaves secretas en el navegador.** La IA corre antes de la demo (modo A) o detrás de un proxy (después).
- **Licencias:** atribuir Copernicus, OpenStreetMap, INE, ESA WorldCover y Mapillary. **No guardar ni exportar imágenes de Google, ni analizarlas con IA.**

### 3. Antes de empezar, confirma con la persona (máximo 5 preguntas)

1. ¿Qué comuna y qué sitios? *Por defecto:* una comuna del poniente o sur de Santiago con parques de más de 5.000 m² y vulnerabilidad media o alta.
2. ¿Se pueden llevar datos descargados antes del hackathon? *Por defecto:* no, se bajan en la primera hora.
3. ¿Hay fotos propias del lugar y se usará Google? *Por defecto:* sin Google; satélite propio, fotos propias y Mapillary.
4. ¿Hay acceso a un modelo de IA para generar los informes ahora? *Por defecto:* sí, modo A (pre-generados); si no, plantilla de texto.
5. ¿Para quién es la demo y qué formato prefiere (PDF, Word, presentación)? *Por defecto:* PDF.

Si no hay respuesta, usa los valores por defecto y dígalo en el README.

### 4. Estructura de archivos

```
pulmon-urbano-prototipo/
  README.md                    # cómo correr, decisiones tomadas, atribuciones
  config.yml                   # umbrales y pesos (ver sección 7)
  data/
    raw/                       # descargas (no se publican)
    processed/
      sitios.geojson
      series.csv
      imagenes/<site_id>/<fecha>_color.png y <fecha>_ndvi.png
      casos/caso-<id>.json     # PaqueteCaso
      informes/informe-<id>.json
      intervenciones.json      # catálogo editable
    fotos/<site_id>/foto-01.jpg  y fotos.json
  pipeline/
    01_parques_osm.py
    02_sentinel2_indices.py
    03_censo_social.py
    04_prioridad.py
    05_senales.py
    06_paquete_caso.py
    07_informe_ia.py           # opcional, se corre antes de la demo
    08_fotos_mapillary.py      # opcional
    verificar_informe.py       # compara números del informe con el paquete
    requirements.txt
  web/
    index.html
    app.js
    style.css
    vendor/                    # Leaflet, gráfico y docx copiados (funciona sin internet)
  tests/
```

### 5. Contratos de datos (tipos en notación simple)

```
Sitio {
  site_id: texto
  nombre: texto
  tipo: parque | plaza | barrio | bandejon
  comuna: texto
  area_m2: numero
  geometria: poligono GeoJSON
  ndvi_ultimo: numero (-1 a 1)
  ndmi_ultimo: numero (-1 a 1)
  ndvi_tendencia_pct: numero o nulo      # frente al mismo mes del año anterior
  estres_z: numero o nulo                # NDMI frente a su historia o a sus pares
  estado_vegetacion: estres | poco_verde | sano
  vulnerabilidad: 0 a 100
  pop_400m: entero
  pct_65_mas_400m: numero
  cobertura_arboles_400m_pct: numero
  brecha_dosel_ha: numero
  arboles_necesarios_min: entero
  arboles_necesarios_max: entero
  cuadrante: rescatar | invertir | optimizar | monitorear
  ranking: entero
  confianza: alta | media | baja
  ultima_imagen_valida: fecha
  pixeles_validos: entero
}

FilaSerie (series.csv) {
  site_id, fecha_inicio, intervalo (semanal | mensual | estacional),
  ndvi_mediana, ndmi_mediana, pixeles_validos, nubes_pct,
  lluvia_mm, temp_aire_media_c, senal
}

Senal {
  id: veg_caida | estres_hidrico | mejora_vs_control | brecha_dosel | calor_vulnerabilidad | sin_senal
  etiqueta: texto
  valor: numero
  umbral: numero
  confianza: alta | media | baja
  base: texto corto con la regla aplicada
}

ObservacionFoto {
  pasto: verde | mixto | seco | ausente | no_visible
  sombra: baja | media | alta | no_visible
  arboles: ninguno | jovenes | adultos | no_visible
  suelo_desnudo: si | no | no_visible
  riego_visible: si | no | no_visible
  senales_de_abandono: lista corta de texto
  confianza: alta | media | baja
}

Foto {
  foto_id, archivo, fuente: propia | mapillary | otra,
  licencia, autor, fecha, lat, lon, distancia_al_sitio_m,
  observacion: ObservacionFoto o nulo
}

PaqueteCaso {
  caso_id, tipo: diagnostico | evento | intervencion | oportunidad
  sitio: Sitio
  periodo: { desde, hasta, intervalo }
  senales: lista de Senal
  serie_resumen: lista de { fecha, ndvi, ndmi, lluvia_mm, temp_aire_c }
  imagenes_satelite: lista de { fecha, archivo_color, archivo_ndvi, nubes_pct }
  fotos: lista de Foto
  catalogo_intervenciones: lista de Intervencion
  fondos: lista de { nombre, quien_postula, tope, nota }
  fuentes: lista de { nombre, url, fecha_consulta }
  limites: lista de texto
  numeros: lista de { id, valor, unidad, fuente }   # base para verificar el informe
}

Informe {
  titulo, resumen (3 frases),
  donde_invertir: lista de { site_id, motivo, numeros_usados }
  como_invertir: lista de { intervencion_id, por_que, costo_rango_clp, estado_costo, fondos }
  que_hacer: { dias_30, dias_90, dias_365 }  # listas de texto
  evidencia: lista de { texto, fuente, fecha }
  limites: lista de texto
  descargo: texto
  numeros_usados: lista de ids
}
```

### 6. Pipeline paso a paso

1. **`01_parques_osm.py`:** bajar parques, plazas y áreas verdes de la comuna desde OpenStreetMap (por ejemplo con `osmnx` u Overpass). Quedarse con los de más de 1.000 m² y marcar como confianza baja los menores de 5.000 m². Calcular áreas en EPSG:32719 (UTM 19S) y guardar en WGS84.
2. **`02_sentinel2_indices.py`:** buscar escenas Sentinel-2 L2A con `pystac-client` en AWS Earth Search (`https://earth-search.aws.element84.com/v1`, colección `sentinel-2-l2a`; assets `red`, `green`, `blue`, `nir`, `nir08`, `swir16`, `scl`; verificar el endpoint vigente). Rango: 24 meses si alcanza, si no 12. Aplicar el `scale` y el `offset` de los metadatos de cada asset (las escenas posteriores a 2022 traen un offset de reflectancia). Enmascarar con SCL los valores 0, 1, 3, 8, 9, 10 y 11. Calcular NDVI = (nir − red) / (nir + red) y NDMI = (nir08 − swir16) / (nir08 + swir16). Recortar cada sitio **achicando 10 m hacia adentro** para evitar el borde, tomar la mediana de los píxeles válidos y contar cuántos hubo; si hay menos de 5 píxeles válidos, el valor es nulo. Hacer un **compuesto mensual** (mediana de las observaciones válidas del mes) y guardar `series.csv`. Guardar para cada sitio dos imágenes PNG de color real y NDVI de la fecha válida más reciente y de la misma época del año anterior, con escala fija.
3. **Clima:** lluvia y temperatura media del aire por mes para la comuna (Open-Meteo, que es gratis solo para uso no comercial, o ERA5), rotulada “aire, referencia comunal”.
4. **`03_censo_social.py`:** unir la cartografía de manzanas del Censo 2024 (INE) con población total y de 65 años o más. Para el círculo de 400 m de cada sitio, ponderar por área de intersección y obtener `pop_400m` y `pct_65_mas_400m`. Calcular el verde per cápita (m² de áreas verdes de OSM en el círculo ÷ población). La vulnerabilidad es el promedio ponderado de los percentiles de adultos mayores, densidad y bajo verde per cápita (pesos en `config.yml`), llevado a 0 a 100. Si el dato por manzana no está disponible, usar zona o distrito y rotularlo “menos preciso”.
5. **Cobertura de árboles:** con ESA WorldCover 10 m, calcular el porcentaje de clase 10 (árboles) en el círculo de 400 m. La brecha a 30 % en hectáreas es el máximo entre 0 y (0,30 × área del círculo − área de árboles). Los árboles necesarios van de brecha ÷ 50 m² a brecha ÷ 20 m² por árbol. Costo estimado: mínimo × $45.000 y máximo × $70.000, rotulado “hipótesis”.
6. **`04_prioridad.py`:** definir `estado_vegetacion` y el `cuadrante` con las reglas de la sección 7 y ordenar el `ranking`. Con menos de 3 años de historia, calcular `estres_z` frente a los demás sitios en el mismo mes y decirlo en el campo `base`.
7. **`05_senales.py`:** calcular las señales de la sección “Casos” con los umbrales de `config.yml`. Con menos de 6 observaciones válidas en el periodo, la señal es `sin_senal`.
8. **`06_paquete_caso.py`:** armar un `PaqueteCaso` por caso, con la lista `numeros` (cada cifra con un id, valor, unidad y fuente).
9. **Fotos:** copiar las fotos propias a `data/fotos/<site_id>/` con su `fotos.json`. Si hay token de Mapillary, `08_fotos_mapillary.py` busca fotos por el recuadro del sitio, descarga una copia local y guarda autor y licencia (CC BY-SA 4.0); verificar la documentación vigente de la API.
10. **`07_informe_ia.py` (opcional, antes de la demo):** llama al modelo con el prompt de la sección 10, valida con `verificar_informe.py` y guarda `informe-<id>.json`.

### 7. Reglas de negocio (`config.yml`, valores iniciales)

```
umbral_vulnerabilidad_alta: 60
umbral_estres_z: -1.0
percentil_poco_verde: 25
pesos_vulnerabilidad:
  pct_65_mas: 0.4
  densidad: 0.3
  bajo_verde_per_capita: 0.3
confianza:
  area_minima_m2: 5000
  observaciones_minimas: 6
  antiguedad_maxima_dias: 15
senales:
  veg_caida_pct: -15        # NDVI mensual frente al mismo mes del año anterior, 2 meses seguidos
  estres_hidrico_z: -1.5
  brecha_dosel_puntos: 10   # puntos bajo la meta de 30 %
```

**Cuadrante:**

- vulnerabilidad alta (60 o más) y `estres` → **rescatar**
- vulnerabilidad alta y `poco_verde` → **invertir**
- vulnerabilidad baja y `estres` → **optimizar**
- todo lo demás → **monitorear** (si hay vulnerabilidad alta y vegetación sana, escribirlo en el motivo)

**Confianza baja** si el sitio tiene menos de 5.000 m², menos de 6 observaciones válidas o una última imagen válida de más de 15 días.

**Orden del ranking:** primero por cuadrante (rescatar, invertir, optimizar, monitorear), luego por vulnerabilidad de mayor a menor y luego por |estrés z|.

### 8. Interfaz (una sola página)

- **Mapa Leaflet** con los sitios coloreados por cuadrante y con el nombre del cuadrante escrito en la leyenda. Mapa base con atribución visible (para producción, un proveedor con plan).
- **Interruptor de capas:** estrés de vegetación, vulnerabilidad social y prioridad combinada.
- **Panel de ranking** con el top 5; al hacer clic, el mapa vuela al sitio.
- **Ficha del sitio con pestañas:** Resumen, Imágenes, Serie, Inversión e Informe.
  - *Resumen:* cuadrante, ranking, confianza, “por qué” en lenguaje simple y fecha de la última imagen válida.
  - *Imágenes:* color real y NDVI lado a lado con deslizador antes y después; fotos con atribución; “Subir foto” (queda en el navegador y lee el GPS); enlaces a Google Maps y Street View que se abren en Google.
  - *Serie:* gráfico con selector de intervalo (semanal, mensual por defecto, estacional), huecos por nubes visibles, marcas de eventos y las señales.
  - *Inversión:* la ficha cuantificada con fuente y confianza por fila.
  - *Informe:* el texto de la IA con la etiqueta de IA y los botones de exportar.
- **Galería de casos:** 2 o 3 tarjetas (un diagnóstico, un evento y, si hay datos, una oportunidad de inversión).
- **Ventana “Cómo leer este mapa”** con los límites, siempre accesible.
- **Accesibilidad:** color más texto, contraste suficiente, navegación con teclado y textos alternativos.

### 9. Exportar (en el navegador)

- **PDF:** estilos `@media print` para la ficha y el informe; el usuario guarda como PDF desde el diálogo de impresión.
- **Word:** biblioteca `docx` copiada en `vendor/`, con título, resumen, cuadros y gráficos como imagen.
- **CSV, GeoJSON y JSON del caso:** enlaces a los archivos ya generados.
- **Correo:** botón “Abrir correo” con `mailto:` (asunto, resumen corto de menos de 1.800 caracteres y enlace al caso; el PDF se adjunta a mano) y botón “Copiar como correo” (HTML al portapapeles con `navigator.clipboard.write`).
- **No guardar correos ni datos personales** en el MVP.

### 10. IA: prompts y verificación

**Prompt del sistema para el informe** (la entrada es un `PaqueteCaso` en JSON y la salida es un `Informe` en JSON):

```
Eres un redactor técnico de informes de priorización de inversión en áreas verdes urbanas de Chile.
Recibes un JSON llamado PaqueteCaso. Redacta SOLO a partir de ese JSON.
Reglas:
1. No inventes ni calcules cifras. Cada número del texto debe aparecer en el campo numeros del JSON; lista sus ids en numeros_usados.
2. Elige intervenciones solo del campo catalogo_intervenciones. Si ninguna aplica, dilo.
3. No uses lenguaje causal (causó, provocó). Usa: coincide con, se observa, es compatible con.
4. No des asesoría financiera, legal, médica ni de ingeniería. No prometas retornos, ahorros, salud ni carbono capturado.
5. Declara los límites: resolución de 10 a 20 m, el NDMI mide humedad de la vegetación, el calor es un proxy y la confianza de cada dato.
6. Si la confianza es baja o hay menos de 6 observaciones, escribe: verificar en terreno.
7. Cuando un costo sea hipótesis, di que es hipótesis.
8. Tono claro y formal, en español de Chile, para una persona que debe decidir.
9. Devuelve solo JSON válido con el esquema Informe.
```

**Prompt para observar una foto** (solo fotos propias o de Mapillary; nunca imágenes de Google):

```
Describe solo lo visible en esta foto de un espacio público urbano. Devuelve JSON con los campos: pasto (verde, mixto, seco, ausente, no_visible), sombra (baja, media, alta, no_visible), arboles (ninguno, jovenes, adultos, no_visible), suelo_desnudo (si, no, no_visible), riego_visible (si, no, no_visible), senales_de_abandono (lista corta) y confianza (alta, media, baja). No estimes cifras ni causas. Si algo no se ve, escribe no_visible.
```

**Verificación (`verificar_informe.py`):** extraer todos los números del informe (normalizando la coma decimal y el punto de miles), compararlos con los valores de `numeros` del paquete (se permiten años y fechas del paquete). Si alguno no aparece, rechazar y regenerar hasta 2 veces; si sigue fallando, usar el texto de plantilla sin IA.

**Plantilla sin IA:** un informe armado con frases fijas y los números del paquete, para que el flujo funcione aunque no haya modelo.

### 11. Orden de trabajo y prioridades

| Bloque | Qué | Tiempo (2 personas) | Prioridad |
| --- | --- | --- | --- |
| M0 | Preguntas, elegir comuna, estructura y parques de OSM | 0–1 h | P0 |
| M1 | Índices Sentinel-2, series, Censo, cuadrantes | 1–3 h | P0 |
| M2 | Mapa, ficha, ranking y ventana de límites (en paralelo con M1) | 1–3 h | P0 |
| M3 | Casos: series por intervalo, señales, imágenes de satélite antes y después, CSV | 3–4,5 h | P1 |
| M4 | Ficha de inversión, informe pre-generado, PDF, Word y correo | 4,5–6 h | P1 |
| M5 | Fotos propias o de Mapillary y observación con IA | 6–6,5 h | P2 |
| M6 | Pruebas en celular, plan B y ensayo del pitch | 6,5–7 h | P0 |
| Después | Proxy de IA, envío real de correo, visor de Google, varias comunas, login | — | P3 |

**Si el tiempo se acaba, cortar de abajo hacia arriba:** primero M5, luego el Word y luego el selector de fechas. Nunca cortar M6.

### 12. Criterios de aceptación

- [ ] El mapa abre en un celular en menos de 5 segundos con datos reales de la comuna elegida.
- [ ] Cada sitio muestra cuadrante, ranking, confianza, “por qué” y la fecha de la última imagen válida.
- [ ] Cada cifra visible tiene fuente, fecha y confianza.
- [ ] La serie permite cambiar de intervalo y muestra los huecos por nubes sin rellenarlos.
- [ ] Las imágenes de satélite tienen fecha y atribución, y no hay imágenes de Google en archivos exportados.
- [ ] El informe pasa `verificar_informe.py` o usa la plantilla, y lleva la etiqueta de IA.
- [ ] El PDF, el Word y el CSV se descargan y se abren bien.
- [ ] El botón de correo abre el cliente de correo con asunto y resumen cortos.
- [ ] Los límites son visibles antes de que alguien pregunte.
- [ ] El README explica cómo regenerar los datos, qué se decidió por defecto y las atribuciones.

### 13. Qué no hacer

- No crear servidor, base de datos ni login.
- No mostrar datos simulados sin rotularlos.
- No guardar, exportar ni analizar con IA imágenes de Google.
- No poner llaves de API en el código del navegador.
- No decir “regar” o “no regar”, ni prometer ahorros, retornos, salud o carbono.
- No usar NASA ni sensores térmicos; el calor es un proxy.
- No ampliar el alcance: una comuna, dos o tres casos.

### 14. Módulo opcional: Evaluación de terrenos (prioridad P2)

**Constrúyelo solo después de que M0 a M4 funcionen. Reutiliza el mismo pipeline, la misma interfaz y el mismo informe; no es un segundo producto.** El contexto y los límites están en la sección “Evaluación de terrenos para compra y construcción”.

**Reglas del módulo**

- Nunca escribir “apto para construir” ni evaluar estructura o suelo. El resultado es solo `pasa_prefiltro`, `revisar` o `descartar_por_ahora`, siempre con “verificar en terreno”.
- Cada señal lleva valor, umbral, fuente y confianza, igual que las del caso urbano.
- Tamaño mínimo del terreno: 2.000 m²; por debajo, confianza baja.

**Archivos nuevos**

```
pipeline/
  09_terrenos_candidatos.py    # celdas de 100 m sin edificios (OSM) y con suelo desnudo, pasto o matorral (WorldCover)
  10_senales_terreno.py        # humedad recurrente, agua, pendiente, cauces, vegetación, entorno
  11_paquete_terreno.py        # PaqueteTerreno por candidato
data/processed/terrenos.geojson
data/processed/informes/informe-terreno-<id>.json
web: pestaña “Terrenos” (mapa con semáforo, ranking, ficha, informe)
```

**Contrato de datos**

```
Terreno {
  terreno_id, geometria, area_m2, origen: celda_escaneo | dibujado,
  senales: lista de SenalTerreno,
  semaforo_global: pasa_prefiltro | revisar | descartar_por_ahora,
  confianza: alta | media | baja,
  imagenes: lista de { fecha, estacion: verano | invierno, archivo_color, archivo_ndvi }
}

SenalTerreno {
  id: humedad_recurrente | agua_superficie | pendiente | cauce_cercano |
      vegetacion_densa | intervencion_reciente | entorno,
  valor, unidad, umbral_amarillo, umbral_rojo,
  color: verde | amarillo | rojo,
  fuente, confianza
}
```

**Pasos**

1. **Candidatos:** dividir la zona elegida en celdas de 100 m en EPSG:32719; descartar celdas con edificios de OSM o clases de WorldCover de construido o agua; conservar suelo desnudo, pasto y matorral. Limitar a 200 celdas para la demo.
2. **Humedad recurrente:** a partir de la serie mensual de NDMI, contar los meses de los últimos 24 con valor sobre el percentil 80 de la zona.
3. **Agua en superficie:** MNDWI = (verde − swir16) / (verde + swir16) en Sentinel-2 con máscara SCL; si hay tiempo, Sentinel-1 (colección `sentinel-1-grd` en el mismo catálogo STAC; verificar), calibrar y filtrar el ruido, y marcar como agua los píxeles con retrodispersión baja en invierno. Si el radar no está disponible, usar solo MNDWI y rebajar la confianza.
4. **Pendiente:** modelo de elevación Copernicus de 30 m (colección `cop-dem-glo-30` en Earth Search; verificar), pendiente en % con numpy; rango de altura dentro del terreno.
5. **Cauces y vegetación:** distancia a `waterway` de OSM y porcentaje de árboles y matorral de WorldCover.
6. **Intervención reciente:** caída o salto de NDVI mayor a 0,3 entre dos meses seguidos.
7. **Entorno:** porcentaje de árboles en 400 m y cantidad de parques de OSM a menos de 400 m.
8. **Capas públicas de riesgo:** solo si se encuentran en formato descargable y con licencia clara; si no, mostrar un enlace y no una señal.
9. **Semáforo global:** rojo en cualquier señal de agua, pendiente o cauce → `descartar_por_ahora`; amarillo → `revisar`; sin rojos ni amarillos → `pasa_prefiltro`.

**Valores iniciales en `config.yml` (hipótesis, a calibrar con un experto)**

```
terreno:
  area_minima_m2: 2000
  celda_m: 100
  max_celdas_demo: 200
  pendiente_amarillo_pct: 10
  pendiente_rojo_pct: 20
  agua_rojo_pct_area: 15
  humedad_recurrente_meses_amarillo: 4
  salto_ndvi_intervencion: 0.3
```

**Interfaz:** pestaña “Terrenos” con mapa de semáforo, ranking de las mejores celdas, ficha con las señales y las imágenes de satélite de verano e invierno, y el informe con la misma etiqueta de IA y los mismos botones de exportar.

**Prompt del informe:** el mismo de la sección 10, con tres cambios: el esquema de entrada es `Terreno`, la lista de verificaciones obligatorias incluye mecánica de suelos, topografía, napa y normativa, y se agrega la regla “nunca afirmes que el terreno es apto para construir”.

**Criterios de aceptación del módulo**

- [ ] Una zona se escanea y devuelve un ranking de celdas con semáforo en menos de 3 minutos.
- [ ] Cada señal tiene valor, umbral, fuente y confianza.
- [ ] Ningún texto dice “apto” ni afirma algo sobre estructura o suelo.
- [ ] El informe pasa `verificar_informe.py` y se exporta a PDF.
- [ ] Las imágenes de verano e invierno tienen fecha y atribución.

**Si falta tiempo:** mostrar solo humedad (NDMI y MNDWI), pendiente y vegetación, con un ejemplo de 3 a 5 terrenos.

## Proyecto técnico: visión general y arquitectura

**Alcance:** esta parte describe el producto a largo plazo. El prototipo del hackathon es mucho más pequeño (sin servidor, base de datos ni login; ver “Resumen final y prototipo”), y el producto completo se construye solo cuando haya ingresos.

**La arquitectura tiene cinco capas simples: datos públicos entran, un pipeline en Python calcula índices por sitio, una base de datos geográfica los guarda por cliente, una API los sirve y la interfaz o los documentos los entregan.** Para el hackathon se usa una versión mínima de cada capa; el resto es el camino de crecimiento.

| Capa | Qué hace | Tecnología propuesta | En el hackathon |
| --- | --- | --- | --- |
| 1. Fuentes | Imágenes, clima, límites, censo | Sentinel-2, Open-Meteo, OSM, Censo 2024, WorldCover | Sí, pocas |
| 2. Pipeline | Descarga, limpia nubes, calcula NDVI, NDMI y índices | Python, rasterio, geopandas | Sí |
| 3. Datos | Guarda sitios, métricas y resultados por cliente | PostgreSQL + PostGIS | Archivo GeoPackage |
| 4. API | Sirve mapas, rankings y reportes | FastAPI | Sí |
| 5. Entrega | Mapa web, PDF, Excel, GeoJSON, marca del cliente | Leaflet o MapLibre, WeasyPrint | Mapa + PDF |

```
Fuentes públicas → Pipeline Python → PostGIS → API FastAPI → Mapa web / PDF / Excel / API
  (Sentinel-2,        (NDVI, NDMI,     (sitios,    (por cliente,   (con la marca
   clima, OSM,         índices,        métricas,  con login)      de cada municipio)
   Censo)              prioridad)       reportes)
```

**Principios de diseño:**

- **Reproducible:** cada resultado guarda la fecha de la imagen, la versión del método y los parámetros usados.
- **Datos gratuitos primero:** cero hardware y cero licencias de datos.
- **Un cliente = una configuración:** comuna, umbrales, pesos y marca viven en datos, no en código.
- **Honestidad del dato:** cada celda lleva un campo de confianza.

## Funciones del producto

**Las funciones se ordenan en tres paquetes: ver, decidir y probar.** Cada una se mapea a un plan del modelo freemium.

| # | Función | Qué hace el usuario | Plan | MVP |
| --- | --- | --- | --- | --- |
| 1 | Ficha de sitio o barrio | Dibuja o elige un polígono y ve NDVI, NDMI, tendencia y confianza | Vecino (1 polígono) | Sí |
| 2 | Comparador | Compara su sitio contra un barrio sano de referencia | Vecino | Parcial |
| 3 | Mapa de prioridad | Ve el cruce estrés hídrico × vulnerabilidad social con 4 cuadrantes | Municipio | Sí |
| 4 | Top 5 de acciones | Recibe una lista “rescatar / invertir / optimizar / monitorear” con motivo y confianza | Municipio | Sí |
| 5 | Semáforo de riego | Ve por sitio una sugerencia de riego o “verificar” con el clima de los próximos días, solo después de validar con registros de riego reales | Municipio | Fase 2 |
| 6 | Alertas de pérdida | Recibe aviso cuando un sitio cae frente a su propia historia o a sus vecinos | Municipio | Fase 2 |
| 7 | Verificación de contratos | Carga un contrato con sitios y fechas y ve el estado antes y después | Municipio | Fase 2 |
| 8 | Expediente de postulación | Genera el PDF para Espacios Públicos, FPA o PMU con indicadores | Municipio y Consultora | Sí (versión corta) |
| 9 | Exportar datos | Baja CSV, XLSX, GeoJSON o GeoPackage | Municipio | Sí |
| 10 | Re-medición | Repite el diagnóstico tras una intervención y muestra la diferencia | Municipio y Observatorio | Fase 2 |
| 11 | Marca propia | Logo, colores y dominio del cliente | Consultora y Observatorio | Fase 3 |
| 12 | Tablero multi-comuna | Compara muchas comunas con series históricas | Observatorio | Fase 3 |
| 13 | Casos con historial y señales | Ve la evolución de un sitio por intervalos (vegetación, humedad, lluvia, temperatura del aire, proxy de calor) y descarga el paquete de datos | Municipio y Consultora | Parcial (2 casos) |
| 14 | Informe con IA | Genera un informe redactado a partir de las señales calculadas, revisado por una persona | Consultora y Municipio | Plantilla; IA después |

### Historias de usuario críticas

1. Como **SECPLAN**, quiero ver en un mapa los 5 sitios que debo atender primero y por qué, para justificarlo ante el concejo.
2. Como **jefa de Áreas Verdes**, quiero saber si un parque está peor que hace 30 días, para enviar a la cuadrilla antes de que mueran las plantas.
3. Como **presidente de una junta de vecinos**, quiero un PDF con datos de mi barrio, para armar mi postulación al FPA.
4. Como **consultora**, quiero exportar el diagnóstico con mi marca, para entregarlo a mi cliente.
5. Como **GORE u observatorio**, quiero comparar comunas con la misma metodología, para repartir fondos con criterio.

## Datos y APIs externas

**Todo el dato sale de fuentes públicas y gratuitas, pero “gratis” no siempre significa “se puede usar en un producto de pago”.** Antes de cobrar, hay que revisar la licencia de cada una; las marcadas con ⚠ son las que reviso primero.

| Fuente | Qué aporta | Cómo se accede | Límites y licencia (verificar) |
| --- | --- | --- | --- |
| Sentinel-2 L2A (Copernicus) | Bandas B04, B08, B8A, B11; máscara de nubes SCL; cada \~5 días en teoría, menos con nubes; aplicar el offset de reflectancia posterior a 2022 | API STAC con `pystac-client` en Copernicus Data Space, AWS Earth Search o Microsoft Planetary Computer | Datos abiertos; revisar límites de descarga y atribución de cada proveedor |
| ESA WorldCover 10 m | Cobertura (árbol, pasto, construido) | Archivos GeoTIFF por mosaico | Licencia abierta CC BY 4.0; mapa de 2020/2021, no se actualiza solo |
| Open-Meteo ⚠ | Temperatura, lluvia y evapotranspiración de referencia, histórico y pronóstico | API REST sin llave | Su plan gratuito es para uso **no comercial**; para un producto pagado hay que contratar el plan comercial o usar otra fuente |
| OpenStreetMap ⚠ | Parques, árboles, calles, límites | Overpass API o descarga por región (Geofabrik) | Licencia ODbL: atribuir siempre; solo las bases de datos derivadas se comparten, no los mapas ni los PDF |
| Censo 2024 (INE) | Población, mayores de 65, densidad, por zona o manzana | Descarga de bases y cartografía | Verificar el nivel de desagregación realmente publicado |
| Límites comunales (BCN o INE) | Geometría de comunas y regiones | Descarga | Verificar actualización |
| SINCA (MMA) | Calidad del aire por estación | Descarga o scraping autorizado | Opcional; solo contexto |
| DGA y Meteochile | Estaciones meteorológicas locales para validar el clima | Descarga | Opcional; sirve para validar Open-Meteo |
| API de Mercado Público (ChileCompra) | Licitaciones y órdenes de compra | API con ticket | Requiere solicitar clave; para el módulo de licitaciones |
| Mapa base | Calles y fondos para el mapa web | Tiles de OSM, MapTiler, Carto u otros | ⚠ Los tiles públicos de OSM tienen política de uso limitada; en producción usar un proveedor con plan |

### Fórmulas base (Sentinel-2)

| Índice | Fórmula | Qué mide | Resolución |
| --- | --- | --- | --- |
| NDVI | (B08 − B04) / (B08 + B04) | Vigor de la vegetación | 10 m |
| NDMI | (B8A − B11) / (B8A + B11) | Agua en las hojas | 20 m |
| NDBI | (B11 − B08) / (B11 + B08) | Superficie construida; proxy de calor, no temperatura | 20 m |

Las nubes se descartan con la banda SCL, y cada polígono guarda cuántos píxeles válidos quedaron para calcular la confianza.

**Nota:** el producto no usa NASA ni sensores térmicos; el calor es un proxy y se rotula así.

## Base de datos

**PostgreSQL con la extensión PostGIS guarda geometrías y series de tiempo; en el hackathon basta un archivo GeoPackage con las mismas tablas.** Cada fila de negocio lleva `tenant_id` para separar a los clientes.

| Tabla | Para qué sirve | Campos principales |
| --- | --- | --- |
| `tenants` | Un cliente (municipio, consultora, observatorio) | id, nombre, plan, comuna(s), config de marca, pesos y umbrales |
| `users` | Personas con acceso | id, tenant\_id, correo, rol (admin, lector) |
| `sites` | Parques, plazas, bandejones, polígonos dibujados | id, tenant\_id, geometría, tipo, área m², fuente (OSM o usuario) |
| `site_metrics` | Un valor por sitio y fecha | site\_id, fecha, ndvi, ndmi, ndbi, píxeles válidos, % nubes, confianza |
| `weather_daily` | Clima por comuna o celda | fecha, lluvia mm, temp máx/mín, ET0 |
| `social_zones` | Zonas del Censo | geometría, población, % 65+, densidad, índice social |
| `priority_runs` | Cada cálculo del ranking | id, tenant\_id, fecha, versión del método, parámetros (JSON) |
| `priority_items` | Resultado por sitio en un cálculo | run\_id, site\_id, cuadrante, puntaje, acción, confianza, motivo |
| `contracts` | Contratos de mantención | id, tenant\_id, proveedor, monto, fechas, sitios incluidos |
| `interventions` | Lo que se hizo y cuándo | site\_id, tipo, fecha, costo, contrato opcional |
| `reports` | PDF y planillas generados | id, tenant\_id, tipo, ruta, hash, versión, fecha |
| `audit_log` | Quién hizo qué | usuario, acción, fecha |

**Reglas:**

- **Aislamiento:** políticas de seguridad por fila (Row Level Security de Postgres) para que un municipio nunca vea los datos de otro.
- **Índices:** índice espacial GiST sobre las geometrías y compuesto (site\_id, fecha) sobre las métricas.
- **Rasters:** no se guardan en la base; se guardan como COG (GeoTIFF optimizado) en almacenamiento de archivos y la base apunta a ellos.
- **Migraciones:** Alembic, para evolucionar el esquema sin perder datos.

**Correcciones tras la revisión:** `tenant_id` también en `site_metrics` y `priority_items`; separar los sitios de OSM (compartidos) de los dibujados por usuarios (privados); agregar una tabla `scenes` con huella por escena; y no correr el programador de tareas dentro de la API (usar un cron o un contenedor aparte).

## Backend en Python

**Python con `uv` para dependencias, un pipeline que corre por lotes y una API FastAPI que solo lee resultados ya calculados.** Así el mapa responde rápido y el cálculo pesado no se hace al abrir la página.

### Librerías

| Tarea | Librería |
| --- | --- |
| Buscar y leer imágenes | `pystac-client`, `odc-stac` o `stackstac`, `rasterio`, `rioxarray` |
| Geometrías y espacial | `geopandas`, `shapely`, `pyproj` |
| Cálculo | `numpy`, `pandas`, `scipy` |
| API | `fastapi`, `pydantic`, `uvicorn` |
| Base de datos | `SQLAlchemy`, `GeoAlchemy2`, `psycopg`, `alembic` |
| Tareas programadas | `APScheduler` al inicio; Prefect o Celery si crece |
| Documentos | `Jinja2`, `WeasyPrint`, `openpyxl`, `python-docx` |
| Mapas estáticos para PDF | `matplotlib`, `contextily` (con mapa base de uso permitido) |
| Calidad | `pytest`, `ruff` |

### Pipeline (cada noche o cada 5 días)

1. **Buscar escenas** nuevas de Sentinel-2 sobre las comunas activas con `pystac-client`.
2. **Filtrar nubes** con la banda SCL y descartar escenas con demasiadas.
3. **Calcular NDVI, NDMI y NDBI** y recortar por cada sitio, guardando la mediana y los píxeles válidos.
4. **Traer el clima** de la comuna (lluvia de los últimos 7 días y pronóstico).
5. **Calcular el índice de estrés hídrico** de cada sitio.
6. **Calcular el índice social** de cada zona.
7. **Cruzar y armar el ranking**, guardando `priority_run` y `priority_items`.
8. **Generar alertas** si un sitio cae frente a su historia.

### Índices (hipótesis para calibrar con el piloto)

- **Estrés hídrico del sitio:** diferencia entre el NDMI actual y el NDMI típico de ese sitio en el mismo mes de años anteriores, dividida por la variación normal (un puntaje z). Un sitio con puntaje muy negativo está peor de lo normal para la época.
- **Vulnerabilidad social de la zona:** promedio ponderado y normalizado de % de mayores de 65, densidad de población, poco verde por habitante y superficie construida (NDBI). Los pesos viven en la configuración de cada cliente.
- **Cuadrante y acción:** se cruzan los dos índices con umbrales editables y salen “rescatar, invertir, optimizar o monitorear”.
- **Confianza:** baja si el sitio mide menos de \~5.000 m², si hay pocos píxeles válidos o si la última imagen sin nubes tiene más de \~15 días.

### Estructura de carpetas

```
pulmon-urbano/
  pyproject.toml          # uv
  app/
    main.py               # FastAPI
    api/                  # rutas: sitios, prioridad, reportes
    core/                 # config, seguridad, tenants
    db/                   # modelos y migraciones (alembic)
    pipeline/
      stac.py             # búsqueda y lectura de Sentinel-2
      indices.py          # NDVI, NDMI, NDBI y máscara de nubes
      weather.py          # clima
      social.py           # índice social desde el Censo
      priority.py         # cuadrantes, puntaje, acción, confianza
    reports/
      templates/          # HTML por cliente (marca)
      pdf.py              # PDF de una página y expediente
      export.py           # CSV, XLSX, GeoJSON, GeoPackage
  tests/
  data/                   # caché local (no se sube)
```

### Endpoints principales

| Método y ruta | Qué hace |
| --- | --- |
| `GET /sites` | Lista los sitios del cliente |
| `POST /sites` | Crea un sitio dibujado |
| `GET /sites/{id}/metrics` | Serie de NDVI, NDMI y confianza |
| `GET /priority/latest` | Ranking y cuadrantes del último cálculo |
| `GET /priority/{run_id}` | Un cálculo anterior, para re-medir |
| `POST /reports/onepager` | Genera el PDF de una página |
| `POST /reports/expediente` | Genera el expediente de postulación |
| `GET /export/{formato}` | CSV, XLSX o GeoJSON |
| `GET /tenant/branding` | Logo y colores del cliente |

## Frontend y mapa

**Una sola pantalla de mapa con panel lateral: es lo que el municipio ve a diario y lo que se muestra en el pitch.** Para el hackathon, HTML con Leaflet servido por FastAPI; después se puede pasar a MapLibre o a un framework si hace falta.

| Elemento | Qué muestra |
| --- | --- |
| Mapa | Sitios coloreados por cuadrante, con interruptor de capas (estrés hídrico, vulnerabilidad social, prioridad) |
| Panel de ranking | Top 5 con acción, motivo y confianza; al hacer clic, vuela al sitio |
| Ficha del sitio | NDVI y NDMI en el tiempo, comparación con su historia, fecha de la última imagen válida |
| Selector de fecha | Para ver el estado antes y después de una intervención |
| Botones | Descargar PDF de 1 página, expediente, CSV o GeoJSON |
| Aviso de límites | Texto fijo: resolución de 10 a 20 m, NDMI mide hojas, calor es proxy |

**Decisiones de diseño:**

- **Un semáforo que no exagera:** colores acompañados de texto (“verificar en terreno”) para accesibilidad y para no sobrepasar la confianza del dato.
- **Mapa de baja carga:** las capas se sirven como GeoJSON simplificado o teselas vectoriales; los rasters se muestran como imagen recortada por zona, no la escena completa.
- **Celular primero para vecinos:** la ficha de barrio debe verse bien en el teléfono.
- **Alternativa rápida:** si el tiempo aprieta, un tablero en Streamlit con `folium` entrega lo mismo en menos horas, pero con menos control de marca.

## Exportar documentos

**Los documentos son lo que el cliente lleva al concejo o adjunta a una postulación; por eso son parte del producto y no un extra.** Se generan desde plantillas HTML con `Jinja2` y se convierten a PDF con `WeasyPrint`.

| Documento | Contenido | Formato | Para quién |
| --- | --- | --- | --- |
| Ficha de 1 página | Mapa del sitio o barrio, 3 indicadores, comparación con barrio de referencia, fecha de la imagen, nota de límites | PDF | Vecinos, concejales |
| Informe de prioridad | Top 5, cuadrantes, acción y confianza de cada sitio, metodología | PDF | SECPLAN |
| Expediente de postulación | Diagnóstico, antecedentes, beneficiarios (Censo), indicadores de línea base y plan de re-medición | PDF y Word editable | Municipios, juntas de vecinos, consultoras |
| Informe antes y después | Dos fechas, diferencia por sitio, qué contrato o intervención las separa | PDF | Verificación de contratos |
| Planilla de datos | Una fila por sitio con índices, cuadrante, acción y confianza | XLSX y CSV | Análisis propio |
| Capas geográficas | Sitios y zonas con atributos | GeoJSON y GeoPackage | Equipos SIG |
| Mapa en imagen | Captura del mapa con leyenda | PNG | Presentaciones |

### Garantías de confianza en cada documento

- **Ficha metodológica:** fórmulas, fuentes, fechas de imágenes y versión del método.
- **Aviso de límites:** resolución, qué mide el NDMI y que el calor es proxy.
- **Identificador y huella (hash):** cada reporte queda en la tabla `reports` para poder reproducirlo.
- **Atribución de datos:** Copernicus, OpenStreetMap, INE y los demás, según cada licencia.

**Cuidado con el formato oficial:** los programas (Espacios Públicos, FPA, PMU) tienen sus propios formularios y anexos. Nuestro expediente es un **adjunto de respaldo**; antes de prometer que sirve en la postulación, hay que confirmar los requisitos del llamado vigente con quien postula.

## White label y multi-cliente

**White label significa que la consultora o el municipio ve el producto con su propio nombre, logo y colores; es lo que justifica el plan Consultora y parte del plan Observatorio.** Técnicamente es una sola aplicación con muchos clientes (multi-tenant), donde cada uno tiene su propia configuración.

| Qué se personaliza | Cómo se hace | Plan |
| --- | --- | --- |
| Nombre, logo y colores | Campos en `tenants`; el frontend usa variables CSS y la API entrega `/tenant/branding` | Consultora, Observatorio |
| Plantillas de PDF y Word | Una plantilla Jinja2 base con cabecera, pie y portada que leen logo y colores del cliente | Consultora, Observatorio |
| Dominio propio | Subdominio por cliente (por ejemplo `comuna.pulmonurbano.cl`) y, después, dominio propio con certificado automático | Observatorio |
| Geografía | Qué comunas o regiones ve cada cliente | Todos |
| Pesos y umbrales | Configuración JSON por cliente (qué pesa más: adultos mayores, densidad, verde) | Municipio y arriba |
| Idioma y textos | Textos en archivos de traducción | Opcional |
| Marca de la plataforma | “Con tecnología de Pulmón Urbano” visible en los planes gratuito y Municipio; oculta en Consultora si así se pacta | Consultora |

### Aislamiento entre clientes

- **`tenant_id` en toda tabla de negocio** y seguridad por fila en PostgreSQL.
- **Archivos separados por cliente** en el almacenamiento (una carpeta por `tenant_id`).
- **Roles:** administrador del cliente y lector; el equipo propio tiene un rol aparte con auditoría.

### Por qué importa para el negocio

- **Canal de distribución:** una consultora que entrega nuestros expedientes con su marca nos lleva a sus municipios sin que tengamos que vender uno por uno.
- **Riesgo:** si el cliente oculta nuestra marca, perdemos visibilidad. La compensación es el precio (el plan sube) y que los datos y la metodología sigan siendo nuestros.
- **Se construye después del piloto:** para el hackathon basta una plantilla con logo y color configurables; el multi-cliente completo es fase 3.

## Despliegue, costos, seguridad y fases

**El costo de datos es cero; el costo real es el servidor, el tiempo del equipo y las ventas.** Los montos de abajo son órdenes de magnitud míos, para calibrar con cotizaciones reales.

### Despliegue

- **Hackathon:** todo en un computador o en un servidor pequeño con Docker; datos en un GeoPackage y los PDF en una carpeta.
- **Piloto:** un servidor virtual con Docker Compose (API, PostgreSQL con PostGIS, tarea programada) y almacenamiento de archivos para los COG y los reportes. Respaldos diarios de la base.
- **Crecimiento:** base de datos administrada, trabajos en cola y CDN para el mapa, solo cuando haya clientes que lo justifiquen.

### Costos y qué los mueve

| Partida | Hackathon | Piloto (3 municipios) | Qué la mueve |
| --- | --- | --- | --- |
| Datos satelitales y OSM | $0 | $0 | Revisar límites de descarga |
| Clima | $0 | Posible plan comercial de Open-Meteo | Licencia comercial |
| Servidor y base | $0 (local) | Del orden de decenas de dólares al mes | Número de comunas y frecuencia de cálculo |
| Almacenamiento | $0 | Bajo, crece con las imágenes guardadas | Cuántos COG se conservan |
| Mapa base | $0 | Plan gratuito de proveedor o propio | Visitas al mapa |
| Dominio y correo | Opcional | Bajo |  |
| Tiempo del equipo | Sin costo de caja | El costo dominante | Validación y ventas |

### Seguridad y privacidad

- **Sin datos personales por diseño:** los sitios y el Censo son agregados; solo se guardan cuentas de usuario (correo y rol).
- **Cuentas:** login con contraseña segura o enlace por correo, y roles por cliente.
- **Cifrado** en tránsito (HTTPS) y respaldos protegidos.
- **Ley de datos personales:** la Ley 21.719 cambia las reglas en Chile; revisar su vigencia y qué aplica a las cuentas de usuario antes de salir a vender.
- **Responsabilidad por el dato:** cada resultado dice su confianza y fecha; los términos de uso aclaran que es apoyo a la decisión y no reemplaza la inspección en terreno.

### Fases

| Fase | Cuándo | Qué se construye | Señal para pasar a la siguiente |
| --- | --- | --- | --- |
| 0. Hackathon | 21–22 nov | Una comuna, dos capas, ranking, PDF de 1 página | Pitch claro y demo que funciona |
| 1. Validación | Primeros 30 días | 5 llamadas, un municipio piloto, comparación con registros de riego | Un municipio acepta probar |
| 2. Piloto | Meses 2–4 | Base PostGIS, login, semáforo de riego, alertas, expediente completo | Un municipio paga o compromete compra |
| 3. Producto | Meses 5–12 | Verificación de contratos, re-medición, white label, tablero multi-comuna | Tres municipios y una consultora pagando |
| 4. Escala | Año 2 | Observatorio regional, integración con Mercado Público, alianzas | Plan Observatorio contratado |

### Riesgos técnicos

| Riesgo | Qué pasa | Mitigación |
| --- | --- | --- |
| Nubes frecuentes | Pocas imágenes válidas en invierno | Mostrar la última imagen válida y su antigüedad; baja la confianza |
| Resolución de 10–20 m | Plazas chicas mal medidas | Trabajar por parques y promedios por barrio; marcar “baja confianza” |
| NDMI mal interpretado | Se confunde sequía con otra cosa | Validar contra riego real; decir “verificar en terreno” |
| Licencias de datos | Un proveedor prohibe el uso comercial | Revisar antes de cobrar; tener una fuente alternativa por dato |
| Dependencia de una API | Una fuente cambia o cae | Caché local y datos históricos propios |

## Evaluación independiente y correcciones

**Tres revisores independientes (mercado, técnica y negocio/jurado) calificaron el proyecto como viable para el hackathon, pero todavía sin validación comercial.** Sus notas son opinión; los hechos que verificaron están con fuente.

| Revisor | Nota | En una línea |
| --- | --- | --- |
| Mercado y clientes | 4/10 | Hay presupuesto en áreas verdes, pero no se encontró ningún municipio chileno que pague por esto |
| Viabilidad técnica | 6/10 | Stack razonable; el NDMI no prueba demanda de riego y el MVP de 7 h es ajustado |
| Jurado (promedio) | 6/10 | Problema 7, solución 6, impacto 5, negocio 5, viabilidad 6, pitch 7 |

**Lectura del jurado:** el jurado lo financiaría solo como pre-semilla pequeña y condicionada a validar con clientes.

### Qué se cambió por esta revisión

- **Promesa:** de “regar / no regar” a **priorización de estrés relativo**, con nivel de confianza y verificación en terreno.
- **Cliente inicial:** de municipios a consultoras y oficinas de proyectos (B2B), con el B2G después.
- **Freemium:** el plan gratuito es de solo lectura y ya no incluye expediente.
- **Ingresos:** de \~$20 M, \~$112 M y \~$295 M a \~$6 M, \~$54 M y \~$131 M, con horas de trabajo por entrega.
- **MVP:** de API y base de datos a un prototipo web estático, sin servidor.
- **Cifras corregidas:** 100 UTM ≈ $7,24 M; 30.000 UF ≈ $1.238 M; el llamado regular de 2025 cerró el 27 de junio; muertes por calor son nacionales; el césped de 49,9 millones de m² es total y 86,7 % privado; ODbL solo obliga a compartir bases derivadas; el ahorro de agua se unificó en 3.750–7.225 m³.
- **Técnica:** el offset de reflectancia de Sentinel-2 posterior a 2022, `tenant_id` en todas las tablas y el programador de tareas fuera de la API.

### Sigue sin verificarse

- Las 289 y 172 iniciativas del Decreto 27 y el 32,2 % frente al 4,1 % de áreas verdes por comuna (fuentes no accesibles para los revisores).
- El costo de mantención de $0 a $2.962 por m² (informe de 2018, desactualizado) y los $45–70 mil por árbol.
- El contrato de Ñuñoa de $490 M (plazo y alcance) y cuánto del gasto en riego queda en el contratista.
- Los $635 por m³ de agua, que es un cálculo propio, y el consumo de riego por m².
- Los precios de consultoras, diagnósticos y observatorios: son hipótesis sin respaldo.
- Si el expediente sirve en los formularios oficiales de Espacios Públicos, FPA y PMU.

### Las 3 preguntas más duras del jurado

1. **¿Quién dijo que pagaría?** Hoy nadie; la respuesta es el plan de validación de 2 semanas y el piloto gratuito.
2. **¿Por qué el municipio no usa lo gratis?** Porque el producto entrega un expediente y una priorización hechos, y no un mapa suelto como ARClim o Google Tree Canopy.
3. **¿Cómo ahorra dinero?** Un diagnóstico de \~$1,5 M se cubre ahorrando el 0,3 % de un contrato de $490 M, pero esa referencia no está probada y se dice como hipótesis.

## Fuentes

Las cifras vienen de resultados de búsqueda del 21-nov-2026, no de páginas abiertas completas: confirma las que vayas a decir en voz alta. Los cálculos propios están marcados como supuestos.

- [ICVU 2015–2025 (The Clinic)](https://www.theclinic.cl/2026/04/23/el-ranking-de-las-comunas-de-la-rm-con-mejor-calidad-de-vida-con-san-miguel-entre-las-mejores-junto-al-sector-oriente-revisa-aca-el-listado-completo/)
- [PRMS 1994, 7,3 % (El Dínamo)](https://www.eldinamo.cl/pais/2026/11/16/la-deuda-urbana-de-santiago-que-arrastra-hace-30-anos-lleva-el-73-de-las-areas-verdes-proyectadas-en-1994/)
- [Áreas verdes en Santiago (Reyes y Figueroa, EURE)](https://www.redalyc.org/pdf/196/19615724004.pdf)
- [Zonas frías y calor (Corporación Ciudades)](https://eldesconcierto.cl/2026/03/04/comunas-mas-calurosas-se-concentran-en-santiago-poniente-identifican-77-zonas-frias-para-resguardarse-en-ellas)
- [Muertes por olas de calor (UC)](https://www.uc.cl/noticias/estudio-uc-revela-que-580-muertes-en-un-solo-mes-son-atribuibles-a-olas-de-calor/)
- [Agua, Césped y Ciudad (MINVU vía Pauta)](https://www.pauta.cl/ciudad/riego-de-cesped-privado-en-la-rm-gasta-al-dia-el-agua-equivalente-al)
- [Gasto municipal en riego (La Tercera)](https://www.latercera.com/pulso/noticia/rediseno-plazas-parques-urbanos-ante-la-sequia/866014/)
- [Costos de mantención (CPP UC)](https://politicaspublicas.uc.cl/web/content/uploads/2018/05/INFORME_Administracion-%C3%81reas-verdes-3.pdf)
- [Decreto 27, Espacios Públicos (BCN)](https://www.bcn.cl/leychile/navegar?idNorma=1222956)
- [Compra Ágil hasta 100 UTM (ChileCompra)](https://www.chilecompra.cl/?p=49146)
- [Tree Equity Score Analyzer](https://www.treeequityscore.org/analyzer)
- [Tree Canopy Insights (Google)](https://blog.google/products-and-platforms/products/maps/how-5-cities-plan-use-tree-canopy-fight-climate-change/)
- [Monitoreo Estrategia Ciudades Verdes (UNGM)](https://www.ungm.org/Public/ContractAward/157104)
- [Barrios por el Clima, Lo Espejo (El Desconcierto)](https://eldesconcierto.cl/2026/01/05/vecinos-de-lo-espejo-se-adaptan-al-cambio-climatico-mediante-alianza-que-aumenta-las-areas-verdes-con-innovacion-urbana)
