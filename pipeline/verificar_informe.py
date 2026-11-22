"""Verificador determinístico de informes técnicos contra cifras verificadas y reglas de honestidad."""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from typing import Any

RE_FECHA_ISO = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
RE_NUMERO = re.compile(r"(?<![A-Za-z0-9_])[-+]?(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d+|\.\d+)?")
RE_PROHIBIDAS = [
    ("no_regar", re.compile(r"\bno\s+regar\b", re.IGNORECASE)),
    ("regar", re.compile(r"\bregar\b", re.IGNORECASE)),
    ("causo", re.compile(r"\bcaus[oó]\b", re.IGNORECASE)),
    ("provoco", re.compile(r"\bprovoc[oó]\b", re.IGNORECASE)),
    ("vidas_salvadas", re.compile(r"\bvidas\s+salvadas\b|\bsalva\s+vidas\b", re.IGNORECASE)),
    ("carbono_capturado", re.compile(r"\bcarbono\s+capturado\b|\bsecuestro\s+de\s+carbono\b", re.IGNORECASE)),
    ("retorno_financiero", re.compile(r"\bretorno\s+financiero\b", re.IGNORECASE)),
]

SECCIONES_REQUERIDAS = (
    "caso_id",
    "titulo",
    "resumen_ejecutivo",
    "hallazgos",
    "acciones_priorizadas",
    "fondos_recomendados",
    "limitaciones_y_verificacion",
)


def _es_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _recolectar_numeros(obj: Any, salida: list[float]) -> None:
    if _es_num(obj):
        val = float(obj)
        salida.append(val)
        salida.append(abs(val))
    elif isinstance(obj, dict):
        for v in obj.values():
            _recolectar_numeros(v, salida)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _recolectar_numeros(v, salida)


def _recolectar_fechas(obj: Any, salida: set[str]) -> None:
    if isinstance(obj, str):
        for m in RE_FECHA_ISO.findall(obj):
            salida.add(m)
            salida.add(m[:7])
            for parte in m.split("-"):
                salida.add(str(int(parte)))
    elif isinstance(obj, dict):
        for v in obj.values():
            _recolectar_fechas(v, salida)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _recolectar_fechas(v, salida)


def _parsear_token_numero(tok: str) -> float | None:
    s = tok.strip()
    if not s:
        return None
    if re.match(r"^[-+]?[1-9]\d{0,2}(?:\.\d{3})+(?:,\d+)?$", s):
        s = s.replace(".", "").replace(",", ".")
    elif "," in s and "." not in s:
        s = s.replace(",", ".")
    try:
        v = float(s)
        return v if math.isfinite(v) else None
    except ValueError:
        return None


def _textos_de(obj: Any) -> list[str]:
    textos: list[str] = []
    if isinstance(obj, str):
        textos.append(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("caso_id", "origen_redaccion"):
                continue
            textos.extend(_textos_de(v))
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            textos.extend(_textos_de(v))
    return textos


def verificar_informe(informe: dict[str, Any], paquete: dict[str, Any]) -> tuple[bool, list[str]]:
    """Valida esquema, vocabulario honesto y respaldo numérico exacto del informe frente a paquete."""
    errores: list[str] = []

    if not isinstance(informe, dict):
        return False, ["El informe no es un diccionario JSON válido."]

    for campo in SECCIONES_REQUERIDAS:
        val = informe.get(campo)
        if not val:
            errores.append(f"Falta o está vacía la sección requerida '{campo}'.")

    if paquete.get("caso_id") and informe.get("caso_id") != paquete.get("caso_id"):
        errores.append(f"caso_id no coincide ({informe.get('caso_id')} != {paquete.get('caso_id')}).")

    # Universo de números y fechas autorizados desde el paquete
    permitidos: list[float] = []
    _recolectar_numeros(paquete.get("numeros", {}), permitidos)
    _recolectar_numeros(paquete.get("constantes_permitidas", []), permitidos)
    _recolectar_numeros(paquete.get("sitio", {}), permitidos)
    _recolectar_numeros(paquete.get("comuna", {}), permitidos)
    if paquete.get("comuna_control"):
        _recolectar_numeros(paquete["comuna_control"], permitidos)
    _recolectar_numeros(paquete.get("intervenciones", []), permitidos)
    _recolectar_numeros(paquete.get("fondos_publicos", []), permitidos)
    if paquete.get("evento_calor"):
        _recolectar_numeros(paquete["evento_calor"], permitidos)
    if paquete.get("cartera_sitios"):
        _recolectar_numeros(paquete["cartera_sitios"], permitidos)
    if paquete.get("cartera_resumen"):
        _recolectar_numeros(paquete["cartera_resumen"], permitidos)
    if paquete.get("aire"):
        _recolectar_numeros(paquete["aire"], permitidos)

    # Nombres de sitios OSM y títulos pueden contener números de calles, fechas históricas o IDs (ej. "Plaza 18 de Septiembre", OSM ID)
    textos_ref = [
        (paquete.get("sitio") or {}).get("nombre"),
        (paquete.get("comuna") or {}).get("nombre"),
        paquete.get("titulo"),
        paquete.get("pregunta_decision"),
    ] + [s.get("nombre") for s in paquete.get("cartera_sitios", []) if isinstance(s, dict)]
    for texto_ref in textos_ref:
        if isinstance(texto_ref, str):
            for tok in RE_NUMERO.findall(texto_ref):
                val = _parsear_token_numero(tok)
                if val is not None:
                    permitidos.append(val)
                    permitidos.append(abs(val))

    # Constantes estructurales universales permitidas del diseño (Sentinel 10/20m, Landsat 30m, buffer 400m, Censo 0-5/60+/2024, WorldCover 2021, meta 30%)
    # y plazos fijos del plan y de la re-medición (30, 90 y 365 días; 6 y 12 meses)
    for c in (0, 5, 6, 10, 12, 20, 30, 60, 90, 365, 400, 2021, 2024, 2025, 2026):
        permitidos.append(float(c))

    fechas_permitidas: set[str] = set()
    _recolectar_fechas(paquete, fechas_permitidas)

    todo_texto = "\n".join(_textos_de(informe))

    # Reglas de honestidad lingüística
    for nombre_regla, patron in RE_PROHIBIDAS:
        if patron.search(todo_texto):
            errores.append(f"Expresión prohibida detectada ({nombre_regla}).")

    # Si cita montos o CLP, debe quedar explícita la etiqueta hipótesis (sin verificar)
    if ("$" in todo_texto or "CLP" in todo_texto) and "hipótesis" not in todo_texto.lower():
        errores.append("Se mencionan montos sin la etiqueta obligatoria 'hipótesis (sin verificar)'.")

    # Validación numérica estricta de toda cifra presente en la narrativa
    texto_limpio = re.sub(r"\bSentinel-2\b|\bLandsat\s*8/9\b|\bPM2\.5\b|\bPM10\b|\bNO2\b|\bCC\s+BY\s+4\.0\b", " ", todo_texto)
    texto_sin_fechas = texto_limpio
    for f_str in RE_FECHA_ISO.findall(texto_limpio):
        if f_str not in fechas_permitidas:
            errores.append(f"Fecha no respaldada en el paquete: {f_str}.")
        texto_sin_fechas = texto_sin_fechas.replace(f_str, " ")

    # Evita falsos positivos con identificadores tipo 'Censo 2024', 'WorldCover 2021', 'NDVI', 'NDMI' ya cubiertos
    # y con números ordinales o rangos ya listados en permitidos
    for tok in RE_NUMERO.findall(texto_sin_fechas):
        val = _parsear_token_numero(tok)
        if val is None:
            continue
        ok = any(abs(val - p) <= max(0.05, abs(p) * 0.006) for p in permitidos)
        if not ok:
            errores.append(f"Cifra sin respaldo en paquete['numeros']: '{tok}' ({val}).")

    return len(errores) == 0, errores


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Uso: python -m pipeline.verificar_informe <informe.json> <paquete.json>", file=sys.stderr)
        return 2
    inf = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    paq = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    ok, errs = verificar_informe(inf, paq)
    if ok:
        print("INFORME_OK")
        return 0
    for e in errs:
        print(f"ERROR: {e}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
