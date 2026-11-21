# Pulmón Urbano

**Hackatón de Urbanismo — Universidad de Chile / ie&t chile 2026**

Plataforma web cívica y abierta que traduce datasets satelitales reales de cobertura vegetal (**NDVI**), estrés hídrico/humedad (**NDMI**, Sentinel-2 L2A a 10 m) y contexto de calidad del aire (**MP2.5 / MP10**) en diagnósticos comprensibles y un **Informe Técnico-Ciudadano exportable en PDF**, listo para presentar ante municipalidades, Concejos Municipales o fondos públicos.

## Estado actual

- Especificación técnica y diseño del MVP: [`docs/superpowers/specs/2026-11-21-pulmon-urbano-mvp-design.md`](docs/superpowers/specs/2026-11-21-pulmon-urbano-mvp-design.md)
- Arquitectura elegida: **Opción A** — Pipeline Python (`uv`) para preprocesamiento Sentinel-2 + backend FastAPI + mapa interactivo Leaflet.js + generación de PDF en Python (ReportLab).
