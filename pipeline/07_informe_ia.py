"""Paso 07: Redacción de informes técnicos individuales y carteras de inversión con verificación estricta."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from pipeline.comun import cargar_env
from pipeline.verificar_informe import verificar_informe

ETIQUETA_IA = "Redactado con IA a partir de datos del sistema; debe revisarlo una persona antes de entregarlo."
ETIQUETA_PLANTILLA = (
    "Síntesis por plantilla (sin IA) a partir de datos del sistema; debe revisarla una persona antes de entregarla."
)
CAMPOS_NO_REDACTABLES = ("imagenes", "imagen_lst", "centro", "osm_url")
TIEMPO_MAX_LLM_S = 90.0

# Prompt del sistema (informe v4, sección «IA: prompts y verificación»), ajustado al esquema que usa la página.
INSTRUCCIONES_IA = """Eres un redactor técnico de informes de priorización de inversión en áreas verdes urbanas de Chile.
Recibes un JSON llamado PaqueteCaso. Redacta SOLO a partir de ese JSON.
Reglas:
1. No inventes ni calcules cifras: no sumes, restes, promedies ni redondees distinto. Nunca escribas subtotales calculados (por ejemplo, NO escribas "otros 7 sitios" ni "los 3 mejores" salvo que ese número exacto exista en paquete["numeros"]). Cada número del texto debe aparecer tal cual en el paquete (puedes usar coma decimal y punto de miles). Si un dato es nulo, escribe sin dato.
2. Elige intervenciones solo del campo intervenciones y fondos solo del campo fondos_publicos. Si ninguna aplica, dilo.
3. No uses lenguaje causal (causó, provocó). Usa: coincide con, se observa, es compatible con.
4. No des asesoría financiera, legal, médica ni de ingeniería. No prometas retornos, ahorros, salud ni carbono capturado. Nunca escribas ni niegues literalmente "regar", "no regar", "vidas salvadas", "carbono capturado" ni "retorno financiero" (tampoco escribas "sin retorno financiero").
5. Declara los límites: resolución de 10 a 20 m de Sentinel-2 y 30 m de Landsat 8/9, el NDMI mide humedad de la vegetación (hojas) y no del suelo, WorldCover es de 2021, y la confianza de cada dato.
6. Si la confianza es baja o hay menos de 6 observaciones, escribe: verificar en terreno.
7. Todo monto en CLP debe ir acompañado literalmente de hipótesis (sin verificar) (sin comillas dobles internas en el JSON).
8. Tono claro, conciso y formal, en español de Chile, para una persona que debe decidir. El resumen ejecutivo tiene 3 frases, hallazgos entre 3 y 5 puntos, y acciones_priorizadas entre 3 y 4 elementos.
9. Devuelve solo JSON válido sin comillas dobles sin escapar dentro de los valores de texto, con estas claves exactas:
   caso_id (igual al del paquete), titulo, resumen_ejecutivo,
   hallazgos (lista de frases: dónde invertir y por qué, con sus números),
   acciones_priorizadas (lista de objetos {nombre, cuando_aplica, detalle, rango_estimado}: cómo invertir),
   fondos_recomendados (lista de objetos {nombre, institucion, requisito}),
   plan_30_90_365 (lista de 3 objetos {plazo, accion} con plazo "30 días", "90 días" y "365 días": verificar en terreno, postular, medir línea base y re-medir),
   como_se_medira (lista de frases: línea base y re-medición a los 6 y 12 meses, mismo mes del año),
   limitaciones_y_verificacion (lista de frases)."""


def _plan_y_medicion(fondo: str | None, que: str) -> tuple[list[dict[str, str]], list[str]]:
    """Pasos a 30, 90 y 365 días y forma de medir el resultado (texto fijo, sin cifras calculadas)."""
    destino = f"al fondo «{fondo}»" if fondo else "a los fondos públicos compatibles"
    plan = [
        {
            "plazo": "30 días",
            "accion": f"Verificar en terreno {que} con fotografía georreferenciada y confirmar la cobertura arbórea "
            "de WorldCover 2021 antes de comprometer presupuesto.",
        },
        {
            "plazo": "90 días",
            "accion": f"Cubicar y cotizar las intervenciones elegidas del catálogo y preparar la postulación {destino}.",
        },
        {
            "plazo": "365 días",
            "accion": "Ejecutar la primera etapa y re-medir NDVI, NDMI y temperatura superficial en el mismo mes "
            "del año para comparar con la línea base de este informe.",
        },
    ]
    medicion = [
        "Línea base: NDVI y NDMI de Sentinel-2 y temperatura superficial estival de Landsat 8/9 registrados en este informe.",
        "Re-medición a los 6 y 12 meses, comparando siempre el mismo mes del año y exigiendo observaciones sin nubes.",
        "Con un sitio de control parecido se puede atribuir el cambio; sin control, la mejora solo se describe como coincidente con la intervención.",
    ]
    return plan, medicion


def _fmt_num(val: Any, dec: int = 1) -> str:
    if val is None:
        return "sin dato"
    if isinstance(val, int):
        return f"{val:,}".replace(",", ".")
    val_f = float(val)
    s = f"{val_f:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def construir_informe_plantilla(paquete: dict[str, Any]) -> dict[str, Any]:
    """Redacta un informe técnico completo usando exclusivamente cifras verificadas en `paquete`."""
    if paquete.get("cartera_sitios"):
        return construir_informe_inversion_cartera(paquete)

    num = paquete["numeros"]
    sitio = paquete["sitio"]
    comuna = paquete["comuna"]
    ctrl = paquete.get("comuna_control")
    ev = paquete.get("evento_calor") or {}
    senales = paquete.get("senales", [])
    intervs = paquete.get("intervenciones", [])
    fondos = paquete.get("fondos_publicos", [])

    area_ha = _fmt_num(num.get("area_ha"), 2)
    vuln = _fmt_num(num.get("vulnerabilidad"), 1)
    prio_sat = _fmt_num(num.get("prioridad_satelital"), 1)
    techo = _fmt_num(num.get("pct_techo_calor_400m"), 1)
    hacin = _fmt_num(num.get("pct_hacinamiento_400m"), 1)
    vp = _fmt_num(num.get("verde_per_capita_m2"), 2)
    pop = _fmt_num(num.get("pop_400m"), 0)

    ndvi_act = _fmt_num(num.get("ndvi_actual"), 3)
    ndvi_ref = _fmt_num(num.get("ndvi_ref"), 3)
    ndvi_z = _fmt_num(num.get("ndvi_z"), 2)
    ndmi_act = _fmt_num(num.get("ndmi_actual"), 3)
    ndmi_z = _fmt_num(num.get("ndmi_z"), 2)
    lst_c = _fmt_num(num.get("lst_verano_c"), 1)
    brecha_calor = _fmt_num(num.get("brecha_calor_vs_vitacura_c"), 1)
    cob_sitio = _fmt_num(num.get("cobertura_arboles_400m_pct"), 1)
    imp_sitio = _fmt_num(num.get("impermeable_400m_pct"), 1)
    brecha_pts = _fmt_num(num.get("brecha_dosel_puntos"), 1)
    arb_min = _fmt_num(num.get("arboles_necesarios_min"), 0)
    arb_max = _fmt_num(num.get("arboles_necesarios_max"), 0)
    costo_min = _fmt_num(num.get("costo_clp_min"), 0)
    costo_max = _fmt_num(num.get("costo_clp_max"), 0)
    fecha_ult = sitio.get("fecha_ultima_obs") or "fecha no disponible"

    tramo_calor = (
        f"Temperatura superficial estival Landsat 8/9 de {lst_c} °C (+{brecha_calor} °C sobre Vitacura). "
        if num.get("lst_verano_c") is not None
        else "Temperatura superficial Landsat pendiente para este sitio. "
    )
    tramo_censo = (
        f"Censo 2024 opcional en 400 m ({pop} habitantes): {techo}% de viviendas con techos de zinc/fibrocemento/precarios "
        f"y {hacin}% de hacinamiento (vulnerabilidad térmica {vuln}/100, {vp} m²/hab OSM)."
        if num.get("pct_techo_calor_400m") is not None
        else f"Entorno Censo 2024 en 400 m: {pop} habitantes y {vp} m²/hab OSM (vulnerabilidad {vuln}/100)."
    )

    resumen = (
        f"En {comuna['nombre']}, el sitio {sitio['nombre']} ({area_ha} ha) registra prioridad satelital de {prio_sat}/100. "
        f"{tramo_calor}"
        f"Su lectura Sentinel-2 más reciente ({fecha_ult}) muestra NDVI de {ndvi_act} (referencia {ndvi_ref}, z={ndvi_z}) "
        f"y NDMI de humedad de la vegetación (hojas) de {ndmi_act} (z={ndmi_z}), junto a cobertura arbórea WorldCover 2021 de {cob_sitio}%. "
        f"{tramo_censo}"
    )

    hallazgos: list[str] = [
        f"Vigor y humedad foliar Sentinel-2 (confianza {sitio.get('confianza', 'media')}, {_fmt_num(num.get('n_obs'), 0)} obs.): NDVI={ndvi_act} (z={ndvi_z}) y NDMI={ndmi_act} (z={ndmi_z}).",
        f"Cobertura y superficie WorldCover 2021 (400 m): {cob_sitio}% de árboles frente a la meta de 30% (brecha de {brecha_pts} puntos).",
        tramo_censo,
    ]
    if num.get("lst_verano_c") is not None:
        hallazgos.insert(
            0,
            f"Isla de calor superficial Landsat 8/9: {lst_c} °C en verano ({_fmt_num(num.get('lst_pico_c'), 1)} °C pico y {brecha_calor} °C sobre mediana de Vitacura).",
        )
    if num.get("impermeable_400m_pct") is not None:
        hallazgos.append(f"Superficie construida/impermeable en 400 m (WorldCover 2021): {imp_sitio}%.")
    if num.get("pm2_5_media") is not None:
        hallazgos.append(f"Calidad del aire comunal Copernicus CAMS (ventana reciente): PM2.5 medio {_fmt_num(num.get('pm2_5_media'), 1)} ug/m3.")

    if ctrl:
        hallazgos.append(
            f"Referencia frente a comuna control ({ctrl['nombre']}): cobertura arbórea comunal de "
            f"{_fmt_num(ctrl.get('cobertura_arboles_comuna_pct'), 1)}% frente a "
            f"{_fmt_num(num.get('cobertura_arboles_comuna_pct'), 1)}% en {comuna['nombre']}."
        )

    if ev and ev.get("fecha_min_ndvi"):
        temp_ev = _fmt_num(num.get("temp_max_evento_c") or num.get("temp_max_periodo_c"), 1)
        hallazgos.append(
            f"Ventana estival alrededor del pico de calor del {ev.get('fecha_pico_calor')} (temperatura máx. aire reanálisis ERA5 en la ventana: {temp_ev} °C): "
            f"coincide con NDVI mínimo de {_fmt_num(ev.get('ndvi_min'), 3)} (z={_fmt_num(ev.get('ndvi_z_min'), 2)} el {ev.get('fecha_min_ndvi')})."
        )

    if senales:
        hallazgos.append(f"Señales activas: {', '.join(senales)}.")

    acciones: list[dict[str, Any]] = []
    for i in intervs[:4]:
        item: dict[str, Any] = {
            "nombre": i["nombre"],
            "cuando_aplica": ", ".join(i.get("cuando_aplica", [])),
            "detalle": i["descripcion"],
            "etiqueta_costo": "hipótesis (sin verificar)",
        }
        if i.get("id") == "arborizacion_calles" and num.get("arboles_necesarios_min") is not None:
            item["rango_estimado"] = (
                f"Entre {arb_min} y {arb_max} árboles (CLP ${costo_min} a ${costo_max}, hipótesis (sin verificar))."
            )
        elif i.get("costo_rango_min_clp") and i.get("costo_rango_max_clp"):
            item["rango_estimado"] = (
                f"CLP ${_fmt_num(i['costo_rango_min_clp'], 0)} a ${_fmt_num(i['costo_rango_max_clp'], 0)} (hipótesis (sin verificar))."
            )
        acciones.append(item)

    if not acciones:
        acciones.append({
            "nombre": "Inspección en terreno y mantención operativa prioritaria",
            "cuando_aplica": "sin_senal",
            "detalle": "Verificar estado físico en terreno y capturar fotografía georreferenciada de respaldo.",
            "etiqueta_costo": "hipótesis (sin verificar)",
        })

    fondos_rec = [
        {"nombre": f["nombre"], "institucion": f["institucion"], "requisito": f["requisito_evidencia"]}
        for f in fondos[:3]
    ]

    limitaciones = [
        "El índice NDMI mide humedad de la vegetación en hojas (20 m) y no reemplaza sensores de humedad de suelo.",
        "La cobertura arbórea base corresponde a ESA WorldCover 2021 y debe confirmarse en terreno antes de licitar.",
        "La temperatura del aire y PM2.5 provienen de reanálisis ERA5 / CAMS vía Open-Meteo a escala comunal (CC BY 4.0 no comercial); el calor superficial Landsat 8/9 es compuesto estival a 30 m.",
        "Todos los montos de inversión en CLP son hipótesis (sin verificar) sujetas a cubicación municipal.",
        "Las alertas satelitales orientan la prioridad de visita en terreno; no atribuyen causalidad única ni prescriben decisiones sin inspección.",
    ]
    plan, medicion = _plan_y_medicion(fondos[0]["nombre"] if fondos else None, f"el sitio {sitio['nombre']}")

    return {
        "caso_id": paquete["caso_id"],
        "titulo": f"Informe técnico verificable — {sitio['nombre']} ({comuna['nombre']})",
        "pregunta_decision": paquete.get("pregunta_decision", ""),
        "resumen_ejecutivo": resumen,
        "hallazgos": hallazgos,
        "acciones_priorizadas": acciones,
        "fondos_recomendados": fondos_rec,
        "plan_30_90_365": plan,
        "como_se_medira": medicion,
        "limitaciones_y_verificacion": limitaciones,
        "etiqueta_ia": ETIQUETA_PLANTILLA,
        "origen_redaccion": "plantilla_deterministica",
        "verificado": True,
    }


def construir_informe_inversion_cartera(paquete: dict[str, Any]) -> dict[str, Any]:
    """Redacta informe ejecutivo IA determinístico con los mayores casos donde invertir."""
    cr = paquete["cartera_resumen"]
    cartera = paquete["cartera_sitios"]
    fondos = paquete.get("fondos_publicos", [])
    comuna = paquete["comuna"]

    arb_min = _fmt_num(cr.get("arboles_min_cartera"), 0)
    arb_max = _fmt_num(cr.get("arboles_max_cartera"), 0)
    clp_min = _fmt_num(cr.get("costo_clp_min_cartera"), 0)
    clp_max = _fmt_num(cr.get("costo_clp_max_cartera"), 0)
    lst_max = _fmt_num(cr.get("lst_max_cartera_c"), 1)
    n_sitios = _fmt_num(cr.get("n_sitios_cartera"), 0)

    lider = cartera[0]
    segundo = cartera[1] if len(cartera) > 1 else None

    resumen = (
        f"Cartera ejecutiva de inversión para {comuna['nombre']}: prioriza los {n_sitios} sitios con mayor "
        f"carga térmica superficial Landsat 8/9 (hasta {lst_max} °C en verano), brecha de dosel arbóreo WorldCover 2021 "
        f"y déficit de vigor vegetal Sentinel-2. Encabeza {lider['nombre']} ({lider['comuna']}, prioridad satelital "
        f"{_fmt_num(lider.get('prioridad_satelital'), 1)}/100, LST {_fmt_num(lider.get('lst_verano_c'), 1)} °C). "
        f"La cartera acumulada estima entre {arb_min} y {arb_max} árboles necesarios "
        f"(CLP ${clp_min} a ${clp_max}, hipótesis (sin verificar))."
    )

    hallazgos: list[str] = []
    for s in cartera[:5]:
        hallazgos.append(
            f"{s['nombre']} ({s['comuna']}): prioridad satelital {_fmt_num(s.get('prioridad_satelital'), 1)}/100, "
            f"calor superficial Landsat {_fmt_num(s.get('lst_verano_c'), 1)} °C, "
            f"cobertura arbórea WorldCover 2021 de {_fmt_num(s.get('cobertura_arboles_400m_pct'), 1)}% "
            f"y estimado de {_fmt_num(s.get('arboles_necesarios_min'), 0)} a {_fmt_num(s.get('arboles_necesarios_max'), 0)} árboles."
        )
    if segundo and cr.get("techo_calor_cartera_pct") is not None:
        hallazgos.append(
            f"Capa opcional Censo 2024 habitacional: promedio de {_fmt_num(cr.get('techo_calor_cartera_pct'), 1)}% de viviendas "
            f"con techos de zinc/fibrocemento/precarios en el entorno de 400 m de estos sitios."
        )

    acciones: list[dict[str, Any]] = []
    for s in cartera:
        acciones.append({
            "nombre": f"{s['nombre']} ({s['comuna']}) — Arborización, sombra y eficiencia hídrica",
            "site_id": s["site_id"],
            "comuna_slug": s["comuna_slug"],
            "cuando_aplica": ", ".join(s.get("senales", [])),
            "rango_estimado": (
                f"{_fmt_num(s.get('arboles_necesarios_min'), 0)} a {_fmt_num(s.get('arboles_necesarios_max'), 0)} árboles · "
                f"CLP ${_fmt_num(s.get('costo_clp_min'), 0)} a ${_fmt_num(s.get('costo_clp_max'), 0)} (hipótesis (sin verificar))."
            ),
            "detalle": (
                f"LST Landsat {_fmt_num(s.get('lst_verano_c'), 1)} °C · Dosel WorldCover 2021 {_fmt_num(s.get('cobertura_arboles_400m_pct'), 1)}% · "
                f"Fondo sugerido: {s.get('fondo_sugerido', 'MINVU / PMU SUBDERE')}."
            ),
            "etiqueta_costo": "hipótesis (sin verificar)",
        })

    fondos_rec = [
        {"nombre": f["nombre"], "institucion": f["institucion"], "requisito": f["requisito_evidencia"]}
        for f in fondos
    ]

    limitaciones = [
        "Todos los montos en CLP y rangos de árboles corresponden a hipótesis (sin verificar) basadas en copas de 20 a 50 m².",
        "La cobertura base de árboles proviene de ESA WorldCover 2021 (10 m) y requiere validación en terreno antes de formular bases.",
        "La prioridad combina Landsat 8/9 térmico, Sentinel-2 y WorldCover; el Censo 2024 térmico es opcional y auditable por separado.",
    ]
    plan, medicion = _plan_y_medicion(lider.get("fondo_sugerido"), "los sitios de la cartera, partiendo por los primeros del ranking,")

    return {
        "caso_id": paquete["caso_id"],
        "titulo": f"Cartera prioritaria de inversión — {comuna['nombre']}",
        "pregunta_decision": paquete.get("pregunta_decision", ""),
        "resumen_ejecutivo": resumen,
        "hallazgos": hallazgos,
        "acciones_priorizadas": acciones,
        "fondos_recomendados": fondos_rec,
        "plan_30_90_365": plan,
        "como_se_medira": medicion,
        "limitaciones_y_verificacion": limitaciones,
        "etiqueta_ia": ETIQUETA_PLANTILLA,
        "origen_redaccion": "sintesis_cartera_deterministica",
        "verificado": True,
    }


def proveedor_configurado() -> tuple[str, str] | None:
    """Devuelve (proveedor, modelo) según las claves del entorno o del archivo .env; None si no hay clave."""
    cargar_env()
    if (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip():
        return "gemini", os.environ.get("PULMON_GEMINI_MODEL", "gemini-2.5-flash")
    if os.environ.get("OPENAI_API_KEY", "").strip():
        base = os.environ.get("OPENAI_BASE_URL", "").lower()
        prov = "deepseek" if "deepseek" in base else "openai"
        return prov, os.environ.get("PULMON_LLM_MODEL", "gpt-4o-mini")
    return None


def _paquete_para_llm(obj: Any) -> Any:
    """Copia del paquete sin rutas de imagen ni coordenadas: no aportan a la redacción y gastan tokens."""
    if isinstance(obj, dict):
        return {k: _paquete_para_llm(v) for k, v in obj.items() if k not in CAMPOS_NO_REDACTABLES}
    if isinstance(obj, list):
        return [_paquete_para_llm(v) for v in obj]
    return obj


def construir_mensaje_ia(paquete: dict[str, Any], errores_previos: list[str] | None = None) -> str:
    """Mensaje del usuario para el modelo: el paquete y, si hubo rechazo, los errores a corregir."""
    mensaje = "PaqueteCaso:\n" + json.dumps(_paquete_para_llm(paquete), ensure_ascii=False)
    if errores_previos:
        mensaje += (
            "\n\nTu respuesta anterior fue RECHAZADA por el verificador automático. Corrige exactamente esto "
            "(si una cifra no tiene respaldo, elimínala del texto):\n- " + "\n- ".join(errores_previos[:15])
        )
    return mensaje


def _error_legible(exc: Exception) -> str:
    """Resume un fallo de la llamada sin exponer la clave (va en una cabecera, nunca en la URL)."""
    if isinstance(exc, httpx.HTTPStatusError):
        cuerpo = " ".join(exc.response.text.split())[:220]
        return f"HTTP {exc.response.status_code}: {cuerpo}"
    return f"{type(exc).__name__}: {str(exc)[:220]}"


def _json_de_texto(texto: str) -> Any:
    limpio = texto.strip()
    if limpio.startswith("```"):
        limpio = limpio.strip("`").strip()
        if limpio.lower().startswith("json"):
            limpio = limpio[4:]
    return json.loads(limpio)


def _llamar_llm(paquete: dict[str, Any], errores_previos: list[str] | None = None) -> tuple[Any, str | None]:
    """Pide la redacción al proveedor configurado. Devuelve (objeto, None) o (None, motivo del fallo)."""
    prov = proveedor_configurado()
    if prov is None:
        return None, "Sin clave de API configurada (GEMINI_API_KEY u OPENAI_API_KEY)."
    proveedor, modelo = prov
    mensaje = construir_mensaje_ia(paquete, errores_previos)
    try:
        if proveedor == "gemini":
            clave = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
            resp = httpx.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
                headers={"x-goog-api-key": clave},
                json={
                    "systemInstruction": {"parts": [{"text": INSTRUCCIONES_IA}]},
                    "contents": [{"role": "user", "parts": [{"text": mensaje}]}],
                    "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1},
                },
                timeout=TIEMPO_MAX_LLM_S,
            )
            resp.raise_for_status()
            texto = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        else:
            base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
            payload = {
                "model": modelo,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": INSTRUCCIONES_IA},
                    {"role": "user", "content": mensaje},
                ],
                "temperature": 0.1,
            }
            if proveedor == "deepseek":
                payload["reasoning_effort"] = os.environ.get("PULMON_DEEPSEEK_EFFORT", "low")
            resp = httpx.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY'].strip()}"},
                json=payload,
                timeout=TIEMPO_MAX_LLM_S,
            )
            resp.raise_for_status()
            texto = resp.json()["choices"][0]["message"]["content"]
        return _json_de_texto(texto), None
    except Exception as exc:  # noqa: BLE001 - cualquier fallo del proveedor termina en la plantilla
        return None, _error_legible(exc)


def _llamar_llm_opcional(paquete: dict[str, Any], errores_previos: list[str] | None = None) -> dict[str, Any] | None:
    """Compatibilidad: devuelve solo el objeto redactado (o None si la llamada falló)."""
    obj, _ = _llamar_llm(paquete, errores_previos)
    return obj if isinstance(obj, dict) else None


def generar_informe_verificado(paquete: dict[str, Any], intentar_llm: bool = True) -> dict[str, Any]:
    """Intenta redacción LLM hasta 2 veces si está configurada y cae a plantilla determinística verificada."""
    informe, diag = generar_informe_detallado(paquete, intentar_llm=intentar_llm)
    for intento in diag["intentos"]:
        if intento["resultado"] != "verificado":
            detalle = intento.get("detalle") or "; ".join(intento.get("errores", [])[:3])
            print(f"  [07] IA intento {intento['intento']} en {paquete.get('caso_id')}: {intento['resultado']} — {detalle}")
    return informe


def normalizar_informe(obj: Any, paquete: dict[str, Any]) -> dict[str, Any]:
    """Ajusta la forma de lo que devolvió un modelo; no toca el contenido que revisa el verificador."""
    if not isinstance(obj, dict):
        return {}
    inf = {k: v for k, v in obj.items() if k not in ("verificado", "origen_redaccion", "etiqueta_ia")}
    inf["caso_id"] = paquete.get("caso_id")
    inf["pregunta_decision"] = paquete.get("pregunta_decision", "")
    for campo in ("hallazgos", "limitaciones_y_verificacion", "como_se_medira"):
        valor = inf.get(campo)
        if isinstance(valor, str):
            valor = [valor]
        if isinstance(valor, list):
            inf[campo] = [str(v) for v in valor if v]
    for campo in ("acciones_priorizadas", "fondos_recomendados", "plan_30_90_365"):
        valor = inf.get(campo)
        if isinstance(valor, list):
            inf[campo] = [v if isinstance(v, dict) else {"nombre": str(v)} for v in valor if v]
    for accion in inf.get("acciones_priorizadas") or []:
        accion.setdefault("etiqueta_costo", "hipótesis (sin verificar)")
    return inf


def generar_informe_detallado(
    paquete: dict[str, Any], intentar_llm: bool = True, max_intentos: int = 2
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Redacta con IA (si hay clave) y verifica; si falla, usa la plantilla. Devuelve (informe, diagnóstico)."""
    prov = proveedor_configurado() if intentar_llm else None
    diag: dict[str, Any] = {
        "proveedor": prov[0] if prov else None,
        "modelo": prov[1] if prov else None,
        "intentos": [],
        "uso_plantilla": True,
    }
    if prov:
        errores: list[str] | None = None
        for n in range(1, max_intentos + 1):
            crudo, fallo = _llamar_llm(paquete, errores)
            if crudo is None:
                diag["intentos"].append({"intento": n, "resultado": "error_llamada", "detalle": fallo})
                break  # clave inválida, cuota o red: reintentar no ayuda
            candidato = normalizar_informe(crudo, paquete)
            ok, errores = verificar_informe(candidato, paquete)
            diag["intentos"].append(
                {"intento": n, "resultado": "verificado" if ok else "rechazado", "errores": errores[:15]}
            )
            if ok:
                candidato["origen_redaccion"] = f"{prov[0]}:{prov[1]}"
                candidato["etiqueta_ia"] = ETIQUETA_IA
                candidato["verificado"] = True
                diag["uso_plantilla"] = False
                return candidato, diag

    informe = construir_informe_plantilla(paquete)
    ok, errores_tpl = verificar_informe(informe, paquete)
    if not ok:
        raise ValueError(f"La plantilla determinística falló verificación en {paquete.get('caso_id')}: {errores_tpl}")
    informe["verificado"] = True
    return informe, diag
