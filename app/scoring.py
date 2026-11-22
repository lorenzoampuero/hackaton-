"""Módulo único de verdad para fórmulas satelitales, Índice de Urgencia (IUS),
matriz diagnóstica de 4 estados y modelo paramétrico de intervención.

Todas las fórmulas aquí son 100% deterministas, transparentes y auditables
para respaldar tanto la interfaz web como el Informe PDF y la defensa Q&A.
"""

from __future__ import annotations

import math
from typing import Any

# Umbrales de la Matriz Diagnóstica (Santiago urbano, Sentinel-2 L2A)
NDVI_THRESHOLD = 0.20
NDMI_THRESHOLD = -0.05

# Pesos del Índice de Urgencia Socioambiental (IUS 0-100)
IUS_WEIGHT_VEG = 0.45   # Resolución 10 m (Sentinel-2 NDVI)
IUS_WEIGHT_HID = 0.35   # Resolución 10-20 m (Sentinel-2 NDMI)
IUS_WEIGHT_AIR = 0.20   # Contexto atmosférico 24h (SINCA MMA / respaldo cuenca)

# Referencias normativas (promedio móvil 24 horas)
WHO_PM25_24H = 15.0         # Guía OMS 2021 (24 h)
WHO_PM10_24H = 45.0         # Guía OMS 2021 (24 h)
CHILE_DS12_PM25_24H = 50.0  # Norma Primaria Chilena D.S. N° 12/2011 MMA (24 h)
CHILE_DS12_PM10_24H = 130.0 # Norma Primaria Chilena D.S. N° 12/2022 MMA (24 h)

# Parámetros hídricos referenciales (Región Metropolitana, clima mediterráneo semiárido)
GRASS_WATER_L_M2_YEAR = 1500
NATIVE_WATER_L_M2_YEAR = 400
WATER_SAVING_L_M2_YEAR = GRASS_WATER_L_M2_YEAR - NATIVE_WATER_L_M2_YEAR  # 1100 L/m2/año (~73.3%)
WATER_SAVING_PCT = round((WATER_SAVING_L_M2_YEAR / GRASS_WATER_L_M2_YEAR) * 100.0, 1)


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(value)))


def classify_ndvi(ndvi: float) -> dict[str, str]:
    if ndvi < 0.10:
        return {
            "level": "Déficit severo",
            "short": "Cemento / suelo desnudo",
            "color": "#c62828",
            "meaning": "Superficie dominada por asfalto, cemento, techos o tierra árida sin cobertura vegetal.",
        }
    if ndvi < 0.25:
        return {
            "level": "Vegetación muy escasa",
            "short": "Pasto seco / baja cobertura",
            "color": "#ef6c00",
            "meaning": "Cobertura vegetal muy limitada, pasto deteriorado o árboles aislados insuficientes para dar sombra.",
        }
    if ndvi < 0.45:
        return {
            "level": "Vegetación moderada",
            "short": "Arbolado disperso / plazas",
            "color": "#7cb342",
            "meaning": "Presencia relevante de arbolado urbano o plazas de tamaño medio en condición aceptable.",
        }
    return {
        "level": "Vegetación densa y sana",
        "short": "Parque consolidado",
        "color": "#1b5e20",
        "meaning": "Cobertura arbórea y vegetal vigorosa que entrega sombra, frescor y amortiguación microclimática.",
    }


def classify_ndmi(ndmi: float) -> dict[str, str]:
    if ndmi < -0.20:
        return {
            "level": "Sequedad severa",
            "short": "Suelo árido / sin humedad",
            "color": "#8d2c1f",
            "meaning": "Superficie extremadamente seca con nula retención hídrica y alta propensión a calor superficial.",
        }
    if ndmi < 0.0:
        return {
            "level": "Estrés hídrico alto",
            "short": "Déficit de humedad",
            "color": "#e65100",
            "meaning": "Falta de agua en vegetación o suelo superficial; mayor riesgo de marchitez y polvo resuspendido.",
        }
    if ndmi < 0.20:
        return {
            "level": "Humedad moderada",
            "short": "Hidratación aceptable",
            "color": "#0288d1",
            "meaning": "Balance hídrico moderado en la cubierta vegetal o superficie.",
        }
    return {
        "level": "Buena hidratación",
        "short": "Vegetación bien hidratada",
        "color": "#01579b",
        "meaning": "Alto contenido de humedad en follaje o suelo; condición típica de parques regados o cuerpos de agua.",
    }


def diagnose_cell(ndvi: float, ndmi: float) -> dict[str, Any]:
    """Clasifica un cuadrante en la Matriz Diagnóstica de 4 Estados (NDVI × NDMI)."""
    if ndvi < NDVI_THRESHOLD and ndmi < NDMI_THRESHOLD:
        return {
            "code": "CRITICAL_DESERT",
            "label": "Déficit Crítico (Desierto Urbano)",
            "short_label": "Déficit Crítico",
            "priority": 1,
            "color": "#c62828",
            "bg_color": "#fdecea",
            "summary": "Baja cobertura vegetal y alta sequedad superficial simultáneas.",
            "action_headline": "Prioridad 1: Arborización y creación de área verde nativa de bajo consumo hídrico",
        }
    if ndvi >= NDVI_THRESHOLD and ndmi < NDMI_THRESHOLD:
        return {
            "code": "WATER_STRESS",
            "label": "Área Verde en Estrés Hídrico",
            "short_label": "Estrés Hídrico",
            "priority": 2,
            "color": "#e65100",
            "bg_color": "#fff3e0",
            "summary": "Existe vegetación o pasto, pero sufre déficit severo de humedad.",
            "action_headline": "Prioridad 2: Reconversión de césped seco a especies nativas + mulch y riego eficiente",
        }
    if ndvi < NDVI_THRESHOLD and ndmi >= NDMI_THRESHOLD:
        return {
            "code": "UNCOVERED_MOIST",
            "label": "Superficie Húmeda sin Cobertura",
            "short_label": "Verificar Suelo",
            "priority": 3,
            "color": "#1565c0",
            "bg_color": "#e3f2fd",
            "summary": "Humedad o reflectancia compatible con sombra profunda, riego o cuerpo de agua, pero sin dosel vegetal.",
            "action_headline": "Verificación en terreno: confirmar uso de suelo (sombra/agua/sitio eriazo) antes de presupuestar",
        }
    is_optimal = ndvi >= 0.35 and ndmi >= 0.05
    return {
        "code": "HEALTHY_LUNG",
        "label": "Pulmón Sano (Óptimo)" if is_optimal else "Pulmón Sano (Referencia)",
        "short_label": "Pulmón Sano",
        "priority": 4,
        "color": "#1b5e20",
        "bg_color": "#e8f5e9",
        "summary": "Vegetación presente y adecuadamente hidratada que aporta sombra y confort térmico.",
        "action_headline": "Modo conservación: mantener eficiencia hídrica y usar como estándar comparativo comunal",
    }


def compute_ius(ndvi: float, ndmi: float, pm25_24h: float) -> dict[str, Any]:
    """Calcula el Índice de Urgencia Socioambiental (0 a 100) y su desglose exacto."""
    d_veg = _clip((0.45 - ndvi) / (0.45 - 0.05), 0.0, 1.0)
    d_hid = _clip((0.15 - ndmi) / (0.15 - (-0.25)), 0.0, 1.0)
    d_aire = _clip(pm25_24h / CHILE_DS12_PM25_24H, 0.0, 1.0)

    comp_veg = round(100.0 * IUS_WEIGHT_VEG * d_veg, 1)
    comp_hid = round(100.0 * IUS_WEIGHT_HID * d_hid, 1)
    comp_air = round(100.0 * IUS_WEIGHT_AIR * d_aire, 1)
    ius_total = round(min(100.0, comp_veg + comp_hid + comp_air), 1)

    if ius_total >= 75.0:
        urgency_level = "Crítica"
        urgency_color = "#b71c1c"
    elif ius_total >= 55.0:
        urgency_level = "Alta"
        urgency_color = "#e65100"
    elif ius_total >= 35.0:
        urgency_level = "Moderada"
        urgency_color = "#f9a825"
    else:
        urgency_level = "Baja"
        urgency_color = "#2e7d32"

    return {
        "ius_total": ius_total,
        "urgency_level": urgency_level,
        "urgency_color": urgency_color,
        "d_veg": round(d_veg, 3),
        "d_hid": round(d_hid, 3),
        "d_aire": round(d_aire, 3),
        "component_veg": comp_veg,
        "component_hid": comp_hid,
        "component_aire": comp_air,
        "ius_satellite_only": round(comp_veg + comp_hid, 1),
    }


def compute_intervention(
    diagnostic_code: str,
    target_area_m2: int,
    ndvi: float,
    ndmi: float,
) -> dict[str, Any]:
    """Genera el plan paramétrico de intervención determinista según el estado del cuadrante."""
    area = max(100, min(5000, int(target_area_m2)))

    if diagnostic_code == "CRITICAL_DESERT":
        trees = math.ceil(area / 25.0)
        water_saved = area * WATER_SAVING_L_M2_YEAR
        cost_low = area * 18000
        cost_mid = area * 22000
        cost_high = area * 28000
        return {
            "mode": "creation",
            "mode_label": "Creación de Área Verde y Arborización Nativa",
            "budget_applicable": True,
            "target_area_m2": area,
            "recommended_trees": trees,
            "tree_density_rule": "1 árbol nativo cada 25 m² (estándar sombra urbana)",
            "water_grass_l_year": area * GRASS_WATER_L_M2_YEAR,
            "water_native_l_year": area * NATIVE_WATER_L_M2_YEAR,
            "water_saved_l_year": water_saved,
            "water_saving_pct": WATER_SAVING_PCT,
            "cost_clp_min": cost_low,
            "cost_clp_est": cost_mid,
            "cost_clp_max": cost_high,
            "unit_cost_note": "$22.000 CLP/m² estimado (rango $18.000–$28.000/m²: preparación de suelo, especies nativas, mulch y riego básico de establecimiento).",
            "species": [
                {"common": "Quillay", "scientific": "Quillaja saponaria", "role": "Árbol estructural perenne, muy resistente a sequía y polvo"},
                {"common": "Molle", "scientific": "Schinus latifolius", "role": "Dosel amplio de rápida sombra y bajo requerimiento hídrico"},
                {"common": "Algarrobo chileno", "scientific": "Neltuma chilensis", "role": "Alta tolerancia a calor urbano extremo y suelos pobres"},
                {"common": "Lavanda y Romero", "scientific": "Lavandula spp. / Salvia rosmarinus", "role": "Cubresuelos xerófitos que fijan polvo y evitan evaporación"},
            ],
            "actions": [
                f"Habilitar {area:,} m² de suelo permeable / plaza de bolsillo o bandejón arborizado.".replace(",", "."),
                f"Plantar aproximadamente {trees} árboles nativos de Chile central con tasa de establecimiento asistido durante los primeros 2 veranos.",
                "Incorporar cobertura orgánica (mulch/chipeado) y cubresuelos xerófitos en reemplazo de césped de alto consumo.",
                "Priorizar frentes de colegios, paraderos, veredas soleadas o sitios públicos subutilizados dentro del cuadrante.",
            ],
        }

    if diagnostic_code == "WATER_STRESS":
        trees = math.ceil(area / 40.0)
        water_saved = area * WATER_SAVING_L_M2_YEAR
        cost_low = area * 12000
        cost_mid = area * 16000
        cost_high = area * 20000
        return {
            "mode": "reconversion",
            "mode_label": "Reconversión Hídrica de Área Verde Existente",
            "budget_applicable": True,
            "target_area_m2": area,
            "recommended_trees": trees,
            "tree_density_rule": "1 árbol de refuerzo cada 40 m² sobre masa vegetal existente",
            "water_grass_l_year": area * GRASS_WATER_L_M2_YEAR,
            "water_native_l_year": area * NATIVE_WATER_L_M2_YEAR,
            "water_saved_l_year": water_saved,
            "water_saving_pct": WATER_SAVING_PCT,
            "cost_clp_min": cost_low,
            "cost_clp_est": cost_mid,
            "cost_clp_max": cost_high,
            "unit_cost_note": "$16.000 CLP/m² estimado (rango $12.000–$20.000/m²: retiro de pasto seco, cubresuelos xerófitos, mulch y ajuste de riego).",
            "species": [
                {"common": "Peumo", "scientific": "Cryptocarya alba", "role": "Follaje denso ideal para reforzar sombra en plazas existentes"},
                {"common": "Maitén", "scientific": "Maytenus boaria", "role": "Buen desempeño urbano en suelos con riego moderado"},
                {"common": "Quillay", "scientific": "Quillaja saponaria", "role": "Árbol nativo de respaldo con mínima demanda de agua"},
                {"common": "Doca / Lavanda", "scientific": "Carpobrotus aequilaterus / Lavandula spp.", "role": "Sustitución directa de césped seco de alto consumo"},
            ],
            "actions": [
                f"Reconvertir {area:,} m² de césped con estrés hídrico a pradera de bajo consumo y cubresuelos nativos.".replace(",", "."),
                f"Reforzar el dosel con {trees} árboles nativos para reducir la evaporación del suelo.",
                "Instalar riego tecnificado por goteo o reprogramar riego a horarios nocturnos + capa de mulch de 5–7 cm.",
                "Monitorear recuperación de NDMI en imágenes Sentinel-2 cada trimestre.",
            ],
        }

    if diagnostic_code == "UNCOVERED_MOIST":
        return {
            "mode": "verification",
            "mode_label": "Verificación de Uso de Suelo en Terreno",
            "budget_applicable": False,
            "target_area_m2": area,
            "recommended_trees": 0,
            "tree_density_rule": "Sujeto a verificación previa (no se presupuesta sin inspección en terreno)",
            "water_grass_l_year": 0,
            "water_native_l_year": 0,
            "water_saved_l_year": 0,
            "water_saving_pct": 0.0,
            "cost_clp_min": 0,
            "cost_clp_est": 0,
            "cost_clp_max": 0,
            "unit_cost_note": "No se asigna presupuesto automático hasta descartar cuerpo de agua, sombra profunda de edificios o infraestructura cerrada.",
            "species": [
                {"common": "Quillay / Maitén (condicional)", "scientific": "Quillaja saponaria / Maytenus boaria", "role": "Solo si se verifica suelo público apto para arborización"},
            ],
            "actions": [
                "Verificar en terreno o catastro municipal la causa de la señal (NDVI bajo + NDMI alto): puede corresponder a cuerpos de agua (p. ej. laguna o cauce), sombra densa de edificios en altura o suelo húmedo sin vegetación.",
                "Confirmar propiedad pública (BNUP / municipal) y ausencia de restricciones de servidumbre.",
                "Si existe espacio público despejado y soleado, re-evaluar como intervención de arborización nativa.",
            ],
        }

    # HEALTHY_LUNG
    return {
        "mode": "conservation",
        "mode_label": "Conservación y Estándar de Referencia",
        "budget_applicable": False,
        "target_area_m2": area,
        "recommended_trees": 0,
        "tree_density_rule": "No requiere nueva plantación masiva; foco en mantención eficiente",
        "water_grass_l_year": 0,
        "water_native_l_year": 0,
        "water_saved_l_year": 0,
        "water_saving_pct": 0.0,
        "cost_clp_min": 0,
        "cost_clp_est": 0,
        "cost_clp_max": 0,
        "unit_cost_note": "Cuadrante sano: no requiere presupuesto de creación, solo mantención hídrica eficiente.",
        "species": [
            {"common": "Mantención del patrimonio arbóreo existente", "scientific": "Especies consolidadas del parque/sector", "role": "Preservar cobertura y salud foliar actual"},
        ],
        "actions": [
            "Proteger la cobertura vegetal consolidada y evitar pavimentación o pérdida de permeabilidad del suelo.",
            "Auditar horarios y eficiencia de riego para mantener el NDMI en rango positivo sin desperdicio de agua.",
            "Utilizar las métricas de este cuadrante (NDVI y NDMI) como meta de referencia en informes para sectores con déficit de la comuna.",
        ],
    }


def explain_cell_plain_spanish(cell: dict[str, Any], air: dict[str, Any]) -> str:
    """Redacta una explicación en lenguaje humano claro y verificable para el cuadrante."""
    ndvi = cell["ndvi_mean"]
    ndmi = cell["ndmi_mean"]
    arid_pct = round(cell["pct_arid_surface"])
    veg_pct = round(cell["pct_healthy_veg"])
    code = cell["diagnostic_code"]
    comuna = cell["comuna_name"]
    pm25 = air.get("pm25_24h")
    station = air.get("station_name", "estación de referencia")

    if code == "CRITICAL_DESERT":
        core = (
            f"El satélite detecta que un {arid_pct}% de este cuadrante en {comuna} corresponde a cemento, "
            f"techos o suelo árido sin vegetación (NDVI {ndvi:.2f}) y con fuerte sequedad superficial (NDMI {ndmi:.2f}). "
            f"Solo un {veg_pct}% presenta vegetación sana, lo que aumenta el calor local y el polvo en el entorno."
        )
    elif code == "WATER_STRESS":
        core = (
            f"Este cuadrante en {comuna} sí cuenta con vegetación o áreas verdes (NDVI {ndvi:.2f}, {veg_pct}% con cobertura), "
            f"pero muestra estrés hídrico marcado (NDMI {ndmi:.2f}). Es un candidato ideal para reconvertir pasto seco "
            f"a especies nativas tolerantes a sequía y ahorrar agua municipal."
        )
    elif code == "UNCOVERED_MOIST":
        core = (
            f"Este sector presenta baja vegetación visible (NDVI {ndvi:.2f}), pero humedad o reflectancia elevada (NDMI {ndmi:.2f}). "
            f"En tejido urbano denso esto suele deberse a sombras profundas de edificios, superficies húmedas o cuerpos de agua; "
            f"se recomienda validar el uso de suelo en terreno."
        )
    else:
        core = (
            f"Este cuadrante en {comuna} funciona como un pulmón urbano activo: combina buena cobertura vegetal "
            f"(NDVI {ndvi:.2f}, {veg_pct}% vegetación sana) con hidratación adecuada (NDMI {ndmi:.2f}), "
            f"sirviendo como estándar objetivo para comparar zonas con déficit."
        )

    if cell.get("is_non_residential"):
        core += (
            f" Nota territorial: OpenStreetMap marca este cuadrante con predominio de infraestructura o uso "
            f"{cell.get('land_use_label', 'no residencial')}, por lo que fue excluido del ranking Top 5 residencial."
        )

    if pm25 is not None:
        vs_oms = "sobre" if pm25 > WHO_PM25_24H else "bajo"
        core += (
            f" En calidad de aire (escala sectorial, estación {station}), el promedio móvil 24 h de MP2.5 es "
            f"{pm25:.1f} µg/m³ ({vs_oms} la guía OMS de {WHO_PM25_24H:.0f} µg/m³ y frente a la norma chilena de {CHILE_DS12_PM25_24H:.0f} µg/m³)."
        )

    return core


def get_methodology_payload(metadata: dict[str, Any]) -> dict[str, Any]:
    """Estructura completa de trazabilidad científica para el modal UI y defensa Q&A."""
    sat = metadata.get("satellite", {})
    return {
        "satellite": {
            "mission": "Copernicus Sentinel-2 Level-2A (ESA — Reflectancia de Superficie BOA)",
            "catalog": "Microsoft Planetary Computer STAC API (gratis, sin API key, sin NASA Earthdata)",
            "scene_id": sat.get("scene_id", "N/A"),
            "acquisition_date": sat.get("acquisition_date", "N/A"),
            "cloud_cover_pct": sat.get("cloud_cover_pct", "N/A"),
            "resolution": "10 m nativo (B04 Rojo 665 nm, B08 NIR 842 nm); B11 SWIR-1 1610 nm (20 m remuestreado bilinealmente a 10 m)",
            "grid_unit": "Grilla métrica regular de 200 m × 200 m (EPSG:32719 UTM 19S, ~400 píxeles de 10 m por celda) recortada a límites oficiales comunales (OpenStreetMap).",
            "cloud_mask": "Banda SCL (Scene Classification Layer): se excluyen píxeles sin datos (0), saturados (1), sombras de nube (3) y nubes/cirros (8, 9, 10); se conservan superficies urbanas y vegetación.",
        },
        "formulas": [
            {
                "name": "NDVI — Índice de Vegetación de Diferencia Normalizada",
                "formula": "NDVI = (B08 - B04) / (B08 + B04)",
                "meaning": "Mide densidad y vigor fotosintético. La clorofila absorbe luz roja (B04) y refleja infrarrojo cercano (B08). Valores < 0,10 indican cemento/tierra; > 0,45 parques consolidados.",
            },
            {
                "name": "NDMI — Índice de Humedad de Diferencia Normalizada",
                "formula": "NDMI = (B08 - B11) / (B08 + B11)",
                "meaning": "Mide contenido de agua foliar y estrés hídrico superficial. El agua absorbe infrarrojo de onda corta (B11). Valores negativos indican sequedad/estrés; positivos buena hidratación.",
            },
            {
                "name": "IUS — Índice de Urgencia Socioambiental (0 a 100)",
                "formula": "IUS = 100 × (0,45 · D_veg + 0,35 · D_hid + 0,20 · D_aire)",
                "meaning": "80% proviene de variables satelitales a 10 m (45% déficit vegetal + 35% estrés hídrico) que discriminan cuadra por cuadra; 20% refleja exposición atmosférica comunal 24 h (MP2.5 / 50 µg/m³ según D.S. 12 MMA).",
            },
        ],
        "air_quality": {
            "primary_source": "Red Oficial SINCA — Ministerio del Medio Ambiente de Chile (promedio móvil 24 h por estación acreditada).",
            "weather_and_fallback": "Open-Meteo Weather API (temperatura, humedad relativa, humedad del suelo, evapotranspiración) y Open-Meteo Air Quality (respaldo atmosférico de cuenca ~40 km) + respaldo local fechado si falla internet.",
            "norms": {
                "who_2021_24h": {"pm25": WHO_PM25_24H, "pm10": WHO_PM10_24H},
                "chile_ds12_24h": {"pm25": CHILE_DS12_PM25_24H, "pm10": CHILE_DS12_PM10_24H},
            },
        },
        "land_use_filter": (
            "Las alertas 'Top 5 Crítico' excluyen cuadrantes donde más del 40% corresponde a infraestructura "
            "industrial, ferroviaria o autopistas según OpenStreetMap (aunque siguen visibles en el mapa con su etiqueta) "
            "para asegurar que la priorización apunte a sectores poblados realmente intervenibles."
        ),
        "agronomic_assumptions": {
            "grass_water_l_m2_year": GRASS_WATER_L_M2_YEAR,
            "native_water_l_m2_year": NATIVE_WATER_L_M2_YEAR,
            "water_saving_l_m2_year": WATER_SAVING_L_M2_YEAR,
            "water_saving_pct": WATER_SAVING_PCT,
            "budget_note": "Costos referenciales paramétricos para anteproyecto municipal ($18.000–$28.000 CLP/m² creación; $12.000–$20.000 CLP/m² reconversión).",
        },
        "honest_limitations": [
            "Escala espacial del aire: Sentinel-2 mide vegetación y humedad a 10 m (escala plaza/manzana), mientras MP2.5/MP10 proviene de estaciones fijas SINCA (escala comunal/sectorial). No afirmamos medir MP2.5 calle por calle.",
            "Alcance físico sobre contaminación: la arborización y cobertura vegetal nativa reducen polvo resuspendido local (MP10), bajan temperatura superficial y ahorran ~73% de agua vs. césped, pero no eliminan por sí solas episodios estructurales de MP2.5 invernal de toda la cuenca de Santiago.",
            "Verificación en terreno: antes de licitar obra física, la municipalidad debe confirmar propiedad pública (BNUP), redes subterráneas y accesibilidad del cuadrante priorizado.",
        ],
    }
