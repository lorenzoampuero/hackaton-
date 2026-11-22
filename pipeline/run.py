"""Orquestador del pipeline.

Ejemplos:
  uv run python -m pipeline.run                      # todo, para las comunas de config.yml
  uv run python -m pipeline.run --pasos 04,05,06     # solo recalcular prioridad, señales y casos
  uv run python -m pipeline.run --comunas quilicura  # solo una comuna (los pasos globales usan todas)
  uv run python -m pipeline.run --agregar "Renca"    # agrega una comuna a config.yml y la procesa
"""

from __future__ import annotations

import argparse
import importlib
import sys
import time
import traceback

from pipeline import comun

PASOS_POR_COMUNA = {
    "01": "01_parques_osm",
    "02": "02_sentinel2_indices",
    "02b": "02b_clima",
    "03": "03_censo_social",
    "03b": "03b_cobertura_arboles",
}
PASOS_GLOBALES = {
    "02c": "02c_satelites_extra",
    "04": "04_prioridad",
    "05": "05_senales",
    "06": "06_paquete_caso",
    "08": "08_vecino",
}
ORDEN = ["01", "02", "02b", "02c", "03", "03b", "04", "05", "06", "08"]


def agregar_comuna(nombre: str) -> str:
    slug = comun.slug_de(nombre)
    cfg = comun.cargar_config()
    if any(c["slug"] == slug for c in cfg["comunas"]):
        return slug
    texto = comun.RUTA_CONFIG.read_text(encoding="utf-8").rstrip("\n")
    comun.RUTA_CONFIG.write_text(f'{texto}\n  - {{slug: {slug}, nombre: "{nombre}"}}\n', encoding="utf-8")
    print(f"Comuna agregada a config.yml: {nombre} ({slug})")
    return slug


def main() -> int:
    ap = argparse.ArgumentParser(description="Pipeline de RE-VIDA")
    ap.add_argument("--pasos", default=",".join(ORDEN), help="lista separada por comas, p. ej. 01,02")
    ap.add_argument("--comunas", default="", help="slugs separados por comas; vacío = todas")
    ap.add_argument("--agregar", default="", help="nombre de una comuna nueva (tal como figura en OSM)")
    args = ap.parse_args()

    solo = [s for s in args.comunas.split(",") if s]
    if args.agregar:
        solo = [agregar_comuna(args.agregar)]
    cfg = comun.cargar_config()
    todas = cfg["comunas"]
    elegidas = [c for c in todas if not solo or c["slug"] in solo]
    if not elegidas:
        print(f"Ninguna comuna coincide con {solo}. Disponibles: {[c['slug'] for c in todas]}")
        return 2

    pedidos = [p.strip() for p in args.pasos.split(",") if p.strip()]
    desconocidos = [p for p in pedidos if p not in ORDEN]
    if desconocidos:
        print(f"Pasos desconocidos: {desconocidos}. Válidos: {ORDEN}")
        return 2

    fallas = 0
    for paso in [p for p in ORDEN if p in pedidos]:
        inicio = time.time()
        if paso in PASOS_POR_COMUNA:
            modulo = importlib.import_module(f"pipeline.{PASOS_POR_COMUNA[paso]}")
            for comuna in elegidas:
                print(f"[{paso}] {comuna['nombre']}…", flush=True)
                try:
                    modulo.ejecutar(comuna, cfg)
                except Exception:  # noqa: BLE001 - una comuna que falla no debe botar las demás
                    fallas += 1
                    print(f"  ERROR en paso {paso}, {comuna['nombre']}:\n{traceback.format_exc()}", flush=True)
        else:
            modulo = importlib.import_module(f"pipeline.{PASOS_GLOBALES[paso]}")
            print(f"[{paso}] todas las comunas con datos…", flush=True)
            try:
                modulo.ejecutar_todas(todas, cfg)
            except Exception:  # noqa: BLE001
                fallas += 1
                print(f"  ERROR en paso {paso}:\n{traceback.format_exc()}", flush=True)
        print(f"[{paso}] listo en {time.time() - inicio:.0f} s", flush=True)
    print("FIN_PIPELINE con errores" if fallas else "FIN_PIPELINE ok", flush=True)
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
