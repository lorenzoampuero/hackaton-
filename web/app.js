(function () {
  "use strict";

  const PU = window.PU_DATOS || {};
  const LS_KEY_CASOS = "pulmon_urbano_casos_guardados_v1";

  const ETIQ_ESTADO = {
    critico: "Crítico",
    prioritario: "Prioritario",
    vigilar: "Vigilar",
    estable: "Estable",
    sin_datos: "Sin datos",
  };

  const COLOR_ESTADO = {
    critico: "#b91c1c",
    prioritario: "#ea580c",
    vigilar: "#ca8a04",
    estable: "#15803d",
    sin_datos: "#64748b",
  };

  const ETIQ_SENAL = {
    isla_calor: "Isla de calor Landsat (≥ 36,5 °C)",
    veg_caida: "Caída vigor vegetal (NDVI)",
    estres_hidrico: "Estrés hídrico hojas (NDMI)",
    brecha_dosel: "Brecha de dosel (< 20%)",
    calor_vulnerabilidad: "Exposición vivienda y sombra",
    sin_senal: "Sin alerta activa",
  };

  const BASEMAPS = {
    claro: {
      url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      attr: "&copy; OpenStreetMap",
      className: "tile-claro",
    },
    satelite: {
      url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      attr: "Tiles &copy; Esri, Maxar, Earthstar Geographics",
      className: "",
    },
    osm: {
      url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      attr: "&copy; OpenStreetMap",
      className: "",
    },
  };

  const state = {
    vista: "mapa",
    comunaSlug: null,
    capa: "prioridad",
    basemap: "claro",
    modoRanking: "satelital", // 'satelital' | 'mixto'
    ocultarPequenos: false,
    senalFiltro: "todas",
    busqueda: "",
    pesosCenso: { techo: 40, hacin: 30, bajo_verde: 30 },
    comunaCache: {},
    sitioActivoId: null,
    tabActiva: "resumen",
    granularidad: "mensual",
    ambitoIA: "intercomunal",
    informeIACustom: {}, // scope -> informe redactado con IA y aprobado por el verificador del servidor
    informeSitioCustom: {}, // `${slug}:${siteId}` -> informe individual redactado con IA
    iaEstado: null, // respuesta de api/estado; null si la página se abrió sin el servidor local
    casoArchivoSelId: null,
    filtroTipoCaso: "todos",
    filtroComunaCaso: "todas",
    busquedaCaso: "",
    chartInstance: null,
    compareChartInstance: null,
    map: null,
    tileLayer: null,
    layerLimite: null,
    layerSitios: null,
    poligonosPorId: {},
  };

  function esc(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function fmtNum(val, dec = 1) {
    if (val === null || val === undefined || Number.isNaN(Number(val))) return "s/d";
    return new Intl.NumberFormat("es-CL", {
      minimumFractionDigits: dec,
      maximumFractionDigits: dec,
    }).format(Number(val));
  }

  function fmtInt(val) {
    if (val === null || val === undefined || Number.isNaN(Number(val))) return "s/d";
    return new Intl.NumberFormat("es-CL", { maximumFractionDigits: 0 }).format(Math.round(Number(val)));
  }

  function fmtClp(val) {
    if (val === null || val === undefined || Number.isNaN(Number(val))) return "s/d";
    return "$" + fmtInt(val) + " CLP";
  }

  function fmtClpCorto(val) {
    if (val === null || val === undefined || Number.isNaN(Number(val))) return "s/d";
    const n = Number(val);
    if (Math.abs(n) >= 1e6) return "$" + fmtInt(Math.round(n / 1e6)) + "M";
    return "$" + fmtInt(n);
  }

  function leerCasosGuardados() {
    try {
      const raw = window.localStorage.getItem(LS_KEY_CASOS);
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch (_e) {
      return [];
    }
  }

  function guardarCasosGuardados(lista) {
    try {
      window.localStorage.setItem(LS_KEY_CASOS, JSON.stringify(lista));
    } catch (_e) {
      // ignora si modo privado bloquea localStorage
    }
    actualizarContadorCasos();
  }

  function cargarScript(src) {
    return new Promise((resolve, reject) => {
      const existing = document.querySelector(`script[data-pu-src="${src}"]`);
      if (existing && existing.dataset.loaded === "1") {
        resolve();
        return;
      }
      const s = document.createElement("script");
      s.src = src;
      s.async = true;
      s.dataset.puSrc = src;
      s.onload = () => {
        s.dataset.loaded = "1";
        resolve();
      };
      s.onerror = () => reject(new Error("No se pudo cargar " + src));
      document.body.appendChild(s);
    });
  }

  async function cargarJsonConFallback(url, claveGlobal, scriptSrc) {
    if (PU[claveGlobal]) return PU[claveGlobal];
    if (url && window.location.protocol !== "file:") {
      try {
        const resp = await fetch(url);
        if (resp.ok) {
          const data = await resp.json();
          PU[claveGlobal] = data;
          return data;
        }
      } catch (_err) {
        // continúa a carga vía <script>
      }
    }
    await cargarScript(scriptSrc);
    if (!PU[claveGlobal]) throw new Error("Datos vacíos para " + claveGlobal);
    return PU[claveGlobal];
  }

  async function cargarComuna(slug) {
    if (state.comunaCache[slug]) return state.comunaCache[slug];

    const [geojson, limite, series] = await Promise.all([
      cargarJsonConFallback(`data/${slug}/sitios.geojson`, `sitios_${slug}`, `data/${slug}/sitios.js`),
      cargarJsonConFallback(`data/${slug}/limite.geojson`, `limite_${slug}`, `data/${slug}/limite.js`),
      cargarJsonConFallback(null, `series_${slug}`, `data/${slug}/series.js`),
    ]);

    let informesTop5 = {};
    try {
      informesTop5 = await cargarJsonConFallback(null, `informes_top5_${slug}`, `data/${slug}/informes_top5.js`);
    } catch (_err) {
      informesTop5 = {};
    }

    const pack = { geojson, limite, series, informesTop5 };
    state.comunaCache[slug] = pack;
    return pack;
  }

  function calcVulnCensoDinamica(p) {
    const w1 = state.pesosCenso.techo;
    const w2 = state.pesosCenso.hacin;
    const w3 = state.pesosCenso.bajo_verde;
    const pares = [
      [p.p_techo_calor, w1],
      [p.p_hacinamiento, w2],
      [p.p_bajo_verde, w3],
    ];
    let num = 0;
    let den = 0;
    for (const [val, w] of pares) {
      if (val !== null && val !== undefined && Number.isFinite(val) && w > 0) {
        num += val * w;
        den += w;
      }
    }
    if (den <= 0) return p.vulnerabilidad_termica ?? p.vulnerabilidad ?? 0;
    return Math.round((num / den) * 10) / 10;
  }

  function calcPrioridadActual(p) {
    const sat = p.prioridad_satelital ?? 0;
    if (state.modoRanking === "satelital") return Math.round(sat * 10) / 10;
    const vc = calcVulnCensoDinamica(p);
    return Math.round((0.70 * sat + 0.30 * vc) * 10) / 10;
  }

  function getSitiosFiltrados() {
    const pack = state.comunaCache[state.comunaSlug];
    if (!pack) return [];
    const term = state.busqueda.trim().toLowerCase();
    return pack.geojson.features.filter((f) => {
      const p = f.properties;
      if (state.ocultarPequenos && (p.area_m2 || 0) < 5000) return false;
      if (state.senalFiltro !== "todas" && !(p.senales || []).includes(state.senalFiltro)) return false;
      if (term) {
        const hay = `${p.nombre || ""} ${p.site_id || ""}`.toLowerCase();
        if (!hay.includes(term)) return false;
      }
      return true;
    });
  }

  function colorParaSitio(p) {
    if (state.capa === "prioridad") {
      const pr = calcPrioridadActual(p);
      if (pr >= 75) return "#b91c1c";
      if (pr >= 60) return "#ea580c";
      if (pr >= 45) return "#ca8a04";
      if (pr >= 28) return "#65a30d";
      return "#15803d";
    }
    if (state.capa === "calor") {
      const t = p.lst_verano_c;
      if (t === null || t === undefined) return "#94a3b8";
      if (t >= 42) return "#991b1b";
      if (t >= 39) return "#ea580c";
      if (t >= 36) return "#eab308";
      if (t >= 33) return "#65a30d";
      return "#0284c7";
    }
    if (state.capa === "ndvi") {
      const n = p.ndvi_actual;
      if (n === null || n === undefined) return "#94a3b8";
      if (n < 0.2) return "#b45309";
      if (n < 0.3) return "#eab308";
      if (n < 0.45) return "#65a30d";
      if (n < 0.6) return "#16a34a";
      return "#14532d";
    }
    if (state.capa === "ndmi") {
      const m = p.ndmi_actual;
      if (m === null || m === undefined) return "#94a3b8";
      if (m < -0.1) return "#b45309";
      if (m < 0.0) return "#eab308";
      if (m < 0.12) return "#38bdf8";
      return "#0f766e";
    }
    // censo térmico
    const v = calcVulnCensoDinamica(p);
    if (v >= 80) return "#991b1b";
    if (v >= 60) return "#ea580c";
    if (v >= 40) return "#eab308";
    if (v >= 20) return "#84cc16";
    return "#15803d";
  }

  function initMap() {
    state.map = L.map("map", { zoomControl: true }).setView([-33.44, -70.68], 13);
    aplicarBasemap(state.basemap);
  }

  function aplicarBasemap(clave) {
    state.basemap = clave;
    if (!state.map) return;
    if (state.tileLayer) state.map.removeLayer(state.tileLayer);
    const bm = BASEMAPS[clave] || BASEMAPS.claro;
    state.tileLayer = L.tileLayer(bm.url, {
      attribution: bm.attr,
      maxZoom: 19,
      className: bm.className || "",
    }).addTo(state.map);
    document.querySelectorAll(".bm-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.basemap === clave);
    });
  }

  function renderLeyenda() {
    const box = document.getElementById("mapLegend");
    let title = "";
    let items = [];
    if (state.capa === "prioridad") {
      title = state.modoRanking === "satelital" ? "Prioridad satelital integrada" : "Prioridad (Satélites + Censo térmico)";
      items = [
        ["#b91c1c", "≥ 75 (muy alta — intervención urgente)"],
        ["#ea580c", "60 – 74 (alta — priorizar inversión)"],
        ["#ca8a04", "45 – 59 (media — vigilar)"],
        ["#65a30d", "28 – 44 (moderada-baja)"],
        ["#15803d", "< 28 (condición favorable)"],
      ];
    } else if (state.capa === "calor") {
      title = "Temperatura superficial verano (Landsat 8/9)";
      items = [
        ["#991b1b", "≥ 42,0 °C (isla de calor extrema)"],
        ["#ea580c", "39,0 – 41,9 °C (calor severo)"],
        ["#eab308", "36,0 – 38,9 °C (cálido)"],
        ["#65a30d", "33,0 – 35,9 °C (moderado)"],
        ["#0284c7", "< 33,0 °C (fresco relativo)"],
      ];
    } else if (state.capa === "ndvi") {
      title = "Vigor vegetal actual (Sentinel-2 NDVI)";
      items = [
        ["#b45309", "< 0,20 (suelo o vegetación escasa)"],
        ["#eab308", "0,20 – 0,29 (vigor bajo)"],
        ["#65a30d", "0,30 – 0,44 (vigor medio)"],
        ["#16a34a", "0,45 – 0,59 (vigor alto)"],
        ["#14532d", "≥ 0,60 (dosel denso sano)"],
      ];
    } else if (state.capa === "ndmi") {
      title = "Humedad de la vegetación / hojas (NDMI)";
      items = [
        ["#b45309", "< -0,10 (estrés hídrico foliar alto)"],
        ["#eab308", "-0,10 – -0,01 (humedad foliar baja)"],
        ["#38bdf8", "0,00 – 0,11 (humedad foliar moderada)"],
        ["#0f766e", "≥ 0,12 (hojas bien hidratadas)"],
      ];
    } else {
      title = "Vulnerabilidad habitacional térmica (Censo 2024)";
      items = [
        ["#991b1b", "≥ 80 (alta carga techos zinc/hacinamiento)"],
        ["#ea580c", "60 – 79 (alta)"],
        ["#eab308", "40 – 59 (media)"],
        ["#84cc16", "20 – 39 (moderada-baja)"],
        ["#15803d", "< 20 (baja)"],
      ];
    }
    box.innerHTML =
      `<div class="legend-title">${esc(title)}</div>` +
      items
        .map(([col, lbl]) => `<div class="legend-item"><span class="legend-swatch" style="background:${col}"></span><span>${esc(lbl)}</span></div>`)
        .join("");
  }

  function renderKpis(slug) {
    const r = (PU.resumen?.comunas || []).find((c) => c.slug === slug);
    const vit = (PU.resumen?.comunas || []).find((c) => c.slug === "vitacura");
    if (!r) return;

    const deltaVit =
      r.lst_verano_mediana_c != null && vit?.lst_verano_mediana_c != null
        ? r.lst_verano_mediana_c - vit.lst_verano_mediana_c
        : null;

    document.getElementById("kpiLst").textContent = r.lst_verano_mediana_c != null ? `${fmtNum(r.lst_verano_mediana_c, 1)} °C` : "s/d";
    document.getElementById("kpiLstNota").textContent =
      deltaVit != null && slug !== "vitacura"
        ? `${deltaVit >= 0 ? "+" : ""}${fmtNum(deltaVit, 1)} °C vs Vitacura (${fmtNum(vit.lst_verano_mediana_c, 1)} °C)`
        : "Comuna referencia estival (5 escenas)";

    document.getElementById("kpiDosel").textContent = `${fmtNum(r.cobertura_arboles_comuna_pct, 1)}% · ${fmtNum(r.impermeable_comuna_pct, 1)}%`;
    document.getElementById("kpiDoselNota").textContent = `Árboles vs construido/cemento`;

    document.getElementById("kpiSitios").textContent = `${fmtInt(r.n_sitios_con_ndvi ?? r.n_sitios)} / ${fmtInt(r.n_sitios)}`;
    document.getElementById("kpiSitiosNota").textContent = `${fmtInt(r.n_sitios_imagen)} parques con PNG HD + térmico`;

    const aire = r.aire || {};
    document.getElementById("kpiAire").textContent = aire.pm2_5_media != null ? `${fmtNum(aire.pm2_5_media, 1)} µg/m³` : "s/d";
    document.getElementById("kpiAireNota").textContent = aire.uv_max != null ? `UV máx ${fmtNum(aire.uv_max, 1)} · NO₂ ${fmtNum(aire.no2_media, 1)}` : "CAMS 30 días";

    document.getElementById("kpiArboles").textContent =
      r.arboles_necesarios_min_total === 0 && r.arboles_necesarios_max_total === 0
        ? "0 (meta 30% cumplida)"
        : `${fmtInt(r.arboles_necesarios_min_total)} – ${fmtInt(r.arboles_necesarios_max_total)}`;
    document.getElementById("top5ComunaNombre").textContent = r.nombre;
  }

  function renderMapa(fitBounds = false) {
    const pack = state.comunaCache[state.comunaSlug];
    if (!pack || !state.map) return;

    if (state.layerLimite) state.map.removeLayer(state.layerLimite);
    if (state.layerSitios) state.map.removeLayer(state.layerSitios);
    state.poligonosPorId = {};

    const esSat = state.basemap === "satelite";
    state.layerLimite = L.geoJSON(pack.limite, {
      style: {
        color: esSat ? "#facc15" : "#14532d",
        weight: 2.3,
        dashArray: "6 4",
        fillOpacity: 0.02,
        fillColor: "#14532d",
      },
      interactive: false,
    }).addTo(state.map);

    const filtrados = getSitiosFiltrados();
    document.getElementById("estadoFiltroResumen").textContent = `${filtrados.length} de ${pack.geojson.features.length} sitios`;

    state.layerSitios = L.geoJSON(
      { type: "FeatureCollection", features: filtrados },
      {
        style: (feat) => {
          const p = feat.properties;
          const esSel = p.site_id === state.sitioActivoId;
          return {
            color: esSel ? "#ffffff" : esSat ? "#e2e8f0" : "#1e293b",
            weight: esSel ? 3.2 : 1.1,
            fillColor: colorParaSitio(p),
            fillOpacity: esSel ? 0.92 : 0.76,
          };
        },
        onEachFeature: (feat, layer) => {
          const p = feat.properties;
          state.poligonosPorId[p.site_id] = layer;
          layer.bindTooltip(
            `<strong>${esc(p.nombre)}</strong><br>` +
              `Prioridad: ${fmtNum(calcPrioridadActual(p), 1)}/100 · LST: ${fmtNum(p.lst_verano_c, 1)} °C<br>` +
              `NDVI: ${fmtNum(p.ndvi_actual, 3)} · Dosel 2021: ${fmtNum(p.cobertura_arboles_400m_pct, 1)}%`,
            { sticky: true }
          );
          layer.on("click", () => abrirSitio(p.site_id));
        },
      }
    ).addTo(state.map);

    if (fitBounds && state.layerLimite) {
      const b = state.layerLimite.getBounds();
      if (b.isValid()) state.map.fitBounds(b, { padding: [18, 18] });
    }
    renderLeyenda();
  }

  function renderTop5() {
    const list = document.getElementById("listaTop5");
    const filtrados = getSitiosFiltrados().slice();
    filtrados.sort((a, b) => {
      const pa = calcPrioridadActual(a.properties);
      const pb = calcPrioridadActual(b.properties);
      if (pb !== pa) return pb - pa;
      return (b.properties.lst_verano_c || 0) - (a.properties.lst_verano_c || 0);
    });

    const top5 = filtrados.slice(0, 5);
    if (!top5.length) {
      list.innerHTML = `<li class="hint">Sin sitios que coincidan con los filtros actuales.</li>`;
      return;
    }

    list.innerHTML = top5
      .map((f, idx) => {
        const p = f.properties;
        const pr = calcPrioridadActual(p);
        const selClass = p.site_id === state.sitioActivoId ? "selected" : "";
        return `
          <li>
            <button type="button" class="top5-card ${selClass}" data-site-id="${esc(p.site_id)}">
              <div class="top5-head">
                <span class="top5-name">#${idx + 1} ${esc(p.nombre)}</span>
                <span class="badge badge-${esc(p.estado)}">${esc(ETIQ_ESTADO[p.estado] || p.estado)}</span>
              </div>
              <div class="top5-meta tabular">
                <span>Prio: <strong>${fmtNum(pr, 1)}</strong></span>
                <span>LST: <strong>${fmtNum(p.lst_verano_c, 1)} °C</strong></span>
                <span>Dosel: <strong>${fmtNum(p.cobertura_arboles_400m_pct, 1)}%</strong></span>
                <span>NDVI: <strong>${fmtNum(p.ndvi_actual, 2)}</strong></span>
              </div>
            </button>
          </li>
        `;
      })
      .join("");

    list.querySelectorAll(".top5-card").forEach((btn) => {
      btn.addEventListener("click", () => {
        const sid = btn.dataset.siteId;
        const layer = state.poligonosPorId[sid];
        if (layer && state.map) {
          state.map.fitBounds(layer.getBounds(), { maxZoom: 16, padding: [36, 36] });
        }
        abrirSitio(sid);
        document.getElementById("sidebar").classList.remove("open");
      });
    });
  }

  function refrescarVistaMapa() {
    renderMapa(false);
    renderTop5();
    if (state.sitioActivoId) renderDrawerActual();
  }

  function obtenerFeature(siteId) {
    const pack = state.comunaCache[state.comunaSlug];
    if (!pack) return null;
    return pack.geojson.features.find((f) => f.properties.site_id === siteId) || null;
  }

  function construirPaqueteYInformeSitio(feat) {
    const p = feat.properties;
    const pack = state.comunaCache[state.comunaSlug];
    const r = (PU.resumen?.comunas || []).find((c) => c.slug === state.comunaSlug) || {};
    const pre = pack?.informesTop5?.[p.site_id];
    if (pre && state.modoRanking === "mixto" && state.pesosCenso.techo === 40 && state.pesosCenso.hacin === 30) {
      return { paquete: pre.paquete, informe: pre.informe, esPreVerificado: true };
    }

    const cat = PU.catalogo || { intervenciones: [], fondos_publicos: [] };
    const areaHa = (p.area_m2 || 0) / 10000;
    const prAct = calcPrioridadActual(p);
    const paquete = {
      caso_id: `sitio-${state.comunaSlug}-${p.site_id}`,
      sitio: { site_id: p.site_id, nombre: p.nombre, comuna: p.comuna, estado: p.estado, confianza: p.confianza, imagenes: p.imagenes, imagen_lst: p.imagen_lst },
      comuna: { slug: state.comunaSlug, nombre: p.comuna },
      numeros: {
        area_ha: Math.round(areaHa * 100) / 100,
        prioridad_actual: prAct,
        lst_verano_c: p.lst_verano_c,
        lst_pico_c: p.lst_pico_c,
        brecha_calor_vs_vitacura_c: p.brecha_calor_vs_vitacura_c,
        ndvi_actual: p.ndvi_actual,
        savi_actual: p.savi_actual,
        ndmi_actual: p.ndmi_actual,
        cobertura_arboles_400m_pct: p.cobertura_arboles_400m_pct,
        impermeable_400m_pct: p.impermeable_400m_pct,
        pct_techo_calor_400m: p.pct_techo_calor_400m,
        pct_hacinamiento_400m: p.pct_hacinamiento_400m,
        arboles_necesarios_min: p.arboles_necesarios_min,
        arboles_necesarios_max: p.arboles_necesarios_max,
        costo_clp_min: p.costo_clp_min,
        costo_clp_max: p.costo_clp_max,
      },
    };

    const acciones = (p.intervenciones_sugeridas || []).map((iv) => ({
      nombre: iv.nombre,
      etiqueta_costo: "hipótesis (sin verificar)",
      detalle:
        iv.id === "arborizacion_calles" && p.arboles_necesarios_min != null
          ? `Rango estimado de ${fmtInt(p.arboles_necesarios_min)} a ${fmtInt(p.arboles_necesarios_max)} árboles (${fmtClp(p.costo_clp_min)} a ${fmtClp(p.costo_clp_max)}, hipótesis (sin verificar)).`
          : `Rango de referencia ${fmtClp(iv.costo_min_clp)} a ${fmtClp(iv.costo_max_clp)} (hipótesis (sin verificar)).`,
    }));

    const informe = {
      caso_id: paquete.caso_id,
      titulo: `Informe multi-satélite — ${p.nombre} (${p.comuna})`,
      resumen_ejecutivo:
        `El sitio ${p.nombre} (${fmtNum(areaHa, 2)} ha) en ${p.comuna} registra prioridad de ${fmtNum(prAct, 1)}/100 ` +
        `y temperatura superficial estival Landsat 8/9 de ${fmtNum(p.lst_verano_c, 1)} °C (+${fmtNum(p.brecha_calor_vs_vitacura_c, 1)} °C frente a Vitacura). ` +
        `Sentinel-2 (${p.fecha_ultima_obs || "s/d"}) reporta NDVI=${fmtNum(p.ndvi_actual, 3)}, SAVI=${fmtNum(p.savi_actual, 3)} y NDMI foliar=${fmtNum(p.ndmi_actual, 3)}. ` +
        `En 400 m (WorldCover 2021) presenta ${fmtNum(p.cobertura_arboles_400m_pct, 1)}% de árboles y ${fmtNum(p.impermeable_400m_pct, 1)}% de superficie impermeable.`,
      hallazgos: [
        `Calor superficial Landsat 8/9: ${fmtNum(p.lst_verano_c, 1)} °C en el sitio y ${fmtNum(p.lst_entorno_400m_c, 1)} °C en entorno 400 m (pico ${fmtNum(p.lst_pico_c, 1)} °C).`,
        `Brecha de dosel WorldCover 2021: ${fmtNum(p.cobertura_arboles_400m_pct, 1)}% vs meta 30% (falta estimada de ${fmtInt(p.arboles_necesarios_min)}–${fmtInt(p.arboles_necesarios_max)} árboles).`,
        `Censo 2024 opcional en 400 m: ${fmtNum(p.pct_techo_calor_400m, 1)}% techos zinc/fibrocemento/precarios, ${fmtNum(p.pct_hacinamiento_400m, 1)}% hacinamiento y ${fmtNum(p.verde_per_capita_m2, 2)} m²/hab OSM.`,
        `Calidad del aire comunal CAMS: PM2.5 ${fmtNum(r.aire?.pm2_5_media, 1)} µg/m³ · UV máx ${fmtNum(r.aire?.uv_max, 1)}.`,
      ],
      acciones_priorizadas: acciones.length ? acciones : [{ nombre: "Verificación en terreno", etiqueta_costo: "hipótesis (sin verificar)", detalle: "Inspección de campo con fotografía georreferenciada." }],
      fondos_recomendados: (p.fondos_sugeridos || []).map((f) => {
        const full = (cat.fondos_publicos || []).find((x) => x.id === f.id);
        return { nombre: f.nombre, institucion: f.institucion, requisito: full?.requisito_evidencia || "Diagnóstico territorial cuantitativo." };
      }),
      limitaciones_y_verificacion: [
        "NDMI mide humedad foliar de la vegetación (hojas), no humedad directa del suelo.",
        "Landsat 8/9 entrega temperatura superficial estival a 30 m; WorldCover corresponde a 2021.",
        "Todos los montos en CLP corresponden a hipótesis (sin verificar).",
      ],
      origen_redaccion: "sintesis_verificada_navegador",
      verificado: true,
    };
    return { paquete, informe, esPreVerificado: Boolean(pre) };
  }

  function abrirSitio(siteId, tabDestino = null) {
    state.sitioActivoId = siteId;
    if (tabDestino) state.tabActiva = tabDestino;
    document.getElementById("siteDrawer").classList.remove("hidden");
    renderMapa(false);
    renderTop5();
    renderDrawerActual();
  }

  function guardarSitioEnCasos(feat) {
    const { paquete, informe } = construirPaqueteYInformeSitio(feat);
    const guardados = leerCasosGuardados();
    const id = `guardado-${state.comunaSlug}-${feat.properties.site_id}`;
    const existe = guardados.find((x) => x.id === id);
    const registro = {
      id,
      grupo: "guardado",
      tipoLabel: "Caso guardado",
      titulo: `${feat.properties.nombre} (${feat.properties.comuna})`,
      comunaSlug: state.comunaSlug,
      siteId: feat.properties.site_id,
      fecha: new Date().toISOString().slice(0, 10),
      nota: existe?.nota || "",
      paquete,
      informe,
    };
    const filtrados = guardados.filter((x) => x.id !== id);
    filtrados.unshift(registro);
    guardarCasosGuardados(filtrados);
    if (state.vista === "casos") renderListaCasos();
    return registro;
  }

  function renderDrawerActual() {
    const feat = obtenerFeature(state.sitioActivoId);
    if (!feat) return;
    const p = feat.properties;

    document.getElementById("drawerTitle").textContent = p.nombre;
    document.getElementById("drawerSub").textContent =
      `${p.comuna} · ${fmtNum((p.area_m2 || 0) / 10000, 2)} ha (${fmtInt(p.area_m2)} m²) · Ranking #${p.ranking_comuna || "—"}`;

    document.getElementById("drawerBadges").innerHTML = `
      <span class="badge badge-${esc(p.estado)}">${esc(ETIQ_ESTADO[p.estado] || p.estado)}</span>
      <span class="badge badge-calor">LST ${fmtNum(p.lst_verano_c, 1)} °C</span>
      <span class="badge badge-${esc(p.confianza)}">Confianza: ${esc(p.confianza)}</span>
    `;

    const guardados = leerCasosGuardados();
    const yaGuardado = guardados.some((x) => x.id === `guardado-${state.comunaSlug}-${p.site_id}`);
    const btnG = document.getElementById("btnGuardarCasoSitio");
    btnG.textContent = yaGuardado ? "En Casos ✓" : "Guardar caso";

    document.querySelectorAll(".tab-btn").forEach((b) => {
      const active = b.dataset.tab === state.tabActiva;
      b.classList.toggle("active", active);
      b.setAttribute("aria-selected", active ? "true" : "false");
    });
    document.querySelectorAll(".tab-pane").forEach((pane) => {
      pane.classList.toggle("active", pane.id === `tab-${state.tabActiva}`);
    });

    if (state.tabActiva === "resumen") renderTabResumen(p);
    else if (state.tabActiva === "imagenes") renderTabImagenes(p);
    else if (state.tabActiva === "serie") renderTabSerie(p);
    else if (state.tabActiva === "inversion") renderTabInversion(p);
    else if (state.tabActiva === "informe") renderTabInforme(feat);
  }

  function renderTabResumen(p) {
    const el = document.getElementById("tab-resumen");
    const lat = p.centro?.[1];
    const lon = p.centro?.[0];
    const urlMaps = lat && lon ? `https://www.google.com/maps/search/?api=1&query=${lat},${lon}` : "#";
    const urlSv = lat && lon ? `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${lat},${lon}` : "#";

    const detHtml = (p.senales_detalle || [])
      .map((d) => `<li><strong>${esc(d.etiqueta)}:</strong> ${esc(d.evidencia)}</li>`)
      .join("");

    el.innerHTML = `
      <div class="metrics-grid tabular">
        <div class="metric-box">
          <small>Isla de calor Landsat 8/9 (30 m)</small>
          <strong>${fmtNum(p.lst_verano_c, 1)} °C · Pico ${fmtNum(p.lst_pico_c, 1)} °C</strong>
          <div class="hint" style="margin:2px 0 0;">${p.brecha_calor_vs_vitacura_c != null ? `${p.brecha_calor_vs_vitacura_c >= 0 ? "+" : ""}${fmtNum(p.brecha_calor_vs_vitacura_c, 1)} °C vs Vitacura` : "Verano 2025-26"}</div>
        </div>
        <div class="metric-box">
          <small>Sentinel-2 vigor &amp; suelo ajustado</small>
          <strong>NDVI ${fmtNum(p.ndvi_actual, 3)} · SAVI ${fmtNum(p.savi_actual, 3)}</strong>
          <div class="hint" style="margin:2px 0 0;">z=${fmtNum(p.ndvi_z, 2)} · BSI suelo=${fmtNum(p.bsi_actual, 3)}</div>
        </div>
        <div class="metric-box">
          <small>Humedad vegetación / hojas (NDMI)</small>
          <strong>${fmtNum(p.ndmi_actual, 3)} (z=${fmtNum(p.ndmi_z, 2)})</strong>
          <div class="hint" style="margin:2px 0 0;">No mide humedad directa de suelo</div>
        </div>
        <div class="metric-box">
          <small>Superficie WorldCover 2021 (400 m)</small>
          <strong>${fmtNum(p.cobertura_arboles_400m_pct, 1)}% árboles · ${fmtNum(p.impermeable_400m_pct, 1)}% cemento</strong>
          <div class="hint" style="margin:2px 0 0;">Brecha dosel: ${fmtNum(p.brecha_dosel_puntos, 1)} pts bajo 30%</div>
        </div>
      </div>

      <div class="callout">
        <strong>Censo 2024 habitacional en 400 m (capa opcional · ${fmtInt(p.viviendas_400m)} viviendas / ${fmtInt(p.pop_400m)} hab):</strong><br>
        Techos zinc/fibrocemento/precarios: <strong>${fmtNum(p.pct_techo_calor_400m, 1)}%</strong> ·
        Hacinamiento: <strong>${fmtNum(p.pct_hacinamiento_400m, 1)}%</strong> ·
        Verde cercano OSM: <strong>${fmtNum(p.verde_per_capita_m2, 2)} m²/hab</strong> ·
        60+ años: ${fmtNum(p.pct_60_mas_400m, 1)}% · 0–5 años: ${fmtNum(p.pct_infancia_0_5_400m, 1)}%.
      </div>

      <div class="callout callout-warn">
        <strong>Señales detectadas (${esc(p.fecha_ultima_obs || "sin lectura Sentinel")}):</strong>
        <ul style="margin:5px 0 0 18px;padding:0;">${detHtml || "<li>Sin detalles.</li>"}</ul>
        <div class="hint" style="margin:6px 0 0;">${esc((p.razones_confianza || []).join(" · "))}</div>
      </div>

      <div class="link-row">
        <a class="ext-link" href="${esc(urlMaps)}" target="_blank" rel="noopener noreferrer">Abrir en Google Maps ↗</a>
        <a class="ext-link" href="${esc(urlSv)}" target="_blank" rel="noopener noreferrer">Abrir Street View ↗</a>
        ${p.osm_url ? `<a class="ext-link" href="${esc(p.osm_url)}" target="_blank" rel="noopener noreferrer">Ver polígono OSM ↗</a>` : ""}
      </div>
    `;
  }

  function leerExifGps(buffer) {
    try {
      const view = new DataView(buffer);
      if (view.getUint16(0, false) !== 0xffd8) return null;
      let offset = 2;
      while (offset < view.byteLength) {
        const marker = view.getUint16(offset, false);
        offset += 2;
        if (marker === 0xffe1) {
          const header = String.fromCharCode(
            view.getUint8(offset + 2),
            view.getUint8(offset + 3),
            view.getUint8(offset + 4),
            view.getUint8(offset + 5)
          );
          if (header !== "Exif") return null;
          const tiffStart = offset + 8;
          const little = view.getUint16(tiffStart, false) === 0x4949;
          const get16 = (o) => view.getUint16(o, little);
          const get32 = (o) => view.getUint32(o, little);
          const firstIfd = tiffStart + get32(tiffStart + 4);
          const entries = get16(firstIfd);
          let gpsOffset = null;
          for (let i = 0; i < entries; i++) {
            const ent = firstIfd + 2 + i * 12;
            if (get16(ent) === 0x8825) {
              gpsOffset = tiffStart + get32(ent + 8);
              break;
            }
          }
          if (!gpsOffset) return null;
          const gpsEntries = get16(gpsOffset);
          const readRat = (off) => get32(off) / (get32(off + 4) || 1);
          const tags = {};
          for (let i = 0; i < gpsEntries; i++) {
            const ent = gpsOffset + 2 + i * 12;
            const tag = get16(ent);
            const count = get32(ent + 4);
            const valOff = tiffStart + get32(ent + 8);
            if (tag === 1 || tag === 3) tags[tag] = String.fromCharCode(view.getUint8(ent + 8));
            else if ((tag === 2 || tag === 4) && count >= 3) {
              tags[tag] = readRat(valOff) + readRat(valOff + 8) / 60 + readRat(valOff + 16) / 3600;
            }
          }
          if (tags[2] != null && tags[4] != null) {
            return {
              lat: tags[1] === "S" ? -tags[2] : tags[2],
              lon: tags[3] === "W" ? -tags[4] : tags[4],
            };
          }
          return null;
        }
        if ((marker & 0xff00) !== 0xff00) break;
        offset += view.getUint16(offset, false);
      }
    } catch (_e) {
      return null;
    }
    return null;
  }

  function distanciaMetros(lat1, lon1, lat2, lon2) {
    const R = 6371000;
    const toRad = (x) => (x * Math.PI) / 180;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  function renderTabImagenes(p) {
    const el = document.getElementById("tab-imagenes");
    const imgs = p.imagenes || [];
    const imgLst = p.imagen_lst;

    if (!imgs.length && !imgLst) {
      el.innerHTML = `
        <div class="callout callout-warn">
          <strong>Parque bajo 5.000 m&sup2; (${fmtInt(p.area_m2)} m&sup2;).</strong><br>
          Los recortes visuales 480×480 se generan desde 5.000 m² para mantener escala interpretable; las lecturas numéricas Landsat/Sentinel ya están calculadas en Resumen.
        </div>
        <div class="upload-box">
          <strong>Subir foto de terreno (lectura EXIF GPS local):</strong><br>
          <input type="file" id="inputFotoTerreno" accept="image/jpeg,image/png,image/webp" style="margin-top:6px;">
          <div id="fotoTerrenoResultado"></div>
        </div>
      `;
    } else {
      const ult = imgs.length - 1;
      const CAPAS = {
        color: { nombre: "Color natural", fuente: "Sentinel-2, 10 m" },
        ndvi: {
          nombre: "NDVI (vigor vegetal)",
          fuente: "Sentinel-2, 10 m",
          rampa: "#7f3b08 0%, #d8b365 17.6%, #fee08b 31.8%, #a6d96a 47.1%, #1a9850 70.6%, #004529 100%",
          etiquetas: ["-0,05 sin vegetación", "0,35", "0,80 dosel denso"],
        },
        ndmi: {
          nombre: "NDMI (humedad de hojas)",
          fuente: "Sentinel-2, 20 m",
          rampa: "#8c510a 0%, #d8b365 24.3%, #f5f5f5 42.9%, #80cdc1 64.3%, #01665e 100%",
          etiquetas: ["-0,25 hojas secas", "0,05", "0,45 follaje hidratado"],
        },
        lst: {
          nombre: "Térmico superficial (°C)",
          fuente: "Landsat 8/9, 30 m",
          rampa: "#2c7bb6 0%, #80cdc1 27.8%, #fee08b 50%, #f46d43 72.2%, #a50026 100%",
          etiquetas: ["26 °C más fresco", "35 °C", "44 °C o más"],
        },
      };
      const claves = [];
      if (imgs.length) claves.push("color", "ndvi");
      if (imgs.some((im) => im.ndmi)) claves.push("ndmi");
      if (imgLst) claves.push("lst");

      const sel = { vista: "lado", mIzq: claves[0], mDer: claves[1] || claves[0], fIzq: Math.max(ult, 0), fDer: Math.max(ult, 0) };
      const presets = [];
      if (imgs.length) presets.push({ nombre: "Color y NDVI", v: { vista: "lado", mIzq: "color", mDer: "ndvi", fIzq: ult, fDer: ult } });
      if (imgs.length > 1) presets.push({ nombre: `Antes y después (${imgs[0].fecha} → ${imgs[ult].fecha})`, v: { vista: "cortina", mIzq: "ndvi", mDer: "ndvi", fIzq: 0, fDer: ult } });
      if (imgs.length && imgLst) presets.push({ nombre: "Vegetación y calor", v: { vista: "cortina", mIzq: "ndvi", mDer: "lst", fIzq: ult, fDer: ult } });

      const optCapas = claves.map((k) => `<option value="${k}">${esc(CAPAS[k].nombre)}</option>`).join("");
      const optFechas = imgs.map((im, i) => `<option value="${i}">${esc(im.fecha)}</option>`).join("");
      const urlCapa = (modo, idx) => (modo === "lst" ? imgLst : (imgs[idx] || {})[modo]) || "";
      const rotulo = (modo, idx) =>
        modo === "lst" ? `${CAPAS.lst.nombre} · verano 2025-26` : `${CAPAS[modo].nombre} · ${imgs[idx]?.fecha || "s/f"}`;

      el.innerHTML = `
        <div class="preset-row" role="group" aria-label="Comparaciones rápidas">
          ${presets.map((pr, i) => `<button type="button" class="chip" data-preset="${i}">${esc(pr.nombre)}</button>`).join("")}
        </div>
        <div class="compare-controls">
          <label><span>Imagen izquierda</span><select id="selModoIzq">${optCapas}</select></label>
          <label><span>Imagen derecha</span><select id="selModoDer">${optCapas}</select></label>
          <label><span>Fecha izquierda</span><select id="selFechaIzq">${optFechas}</select></label>
          <label><span>Fecha derecha</span><select id="selFechaDer">${optFechas}</select></label>
        </div>
        <div class="segmented seg-vista" role="group" aria-label="Modo de comparación">
          <button type="button" class="seg-btn" data-vista="lado">Lado a lado</button>
          <button type="button" class="seg-btn" data-vista="cortina">Cortina deslizante</button>
        </div>
        <div id="imgEscenario"></div>
        <div id="leyendaRampaImg" class="ramp-bar-wrap"></div>
        <p class="hint">
          El contorno blanco es el polígono del sitio (OpenStreetMap) y todas las capas usan el mismo encuadre.
          Sentinel-2: contiene datos modificados de Copernicus Sentinel, en escenas casi sin nubes sobre la comuna.
          Térmico: mediana de escenas de verano de Landsat 8/9 (USGS/NASA); con píxeles de 30 m orienta, no delimita.
        </p>
        <div class="upload-box">
          <strong>Validar en terreno con una foto propia (se lee su GPS aquí; no se sube a ningún servidor):</strong><br>
          <input type="file" id="inputFotoTerreno" accept="image/jpeg,image/png,image/webp" style="margin-top:6px;">
          <div id="fotoTerrenoResultado"></div>
        </div>
      `;
      const pintar = () => {
        const a = { src: urlCapa(sel.mIzq, sel.fIzq), txt: rotulo(sel.mIzq, sel.fIzq) };
        const b = { src: urlCapa(sel.mDer, sel.fDer), txt: rotulo(sel.mDer, sel.fDer) };
        document.getElementById("selModoIzq").value = sel.mIzq;
        document.getElementById("selModoDer").value = sel.mDer;
        const fIzq = document.getElementById("selFechaIzq");
        const fDer = document.getElementById("selFechaDer");
        fIzq.value = String(sel.fIzq);
        fDer.value = String(sel.fDer);
        fIzq.disabled = sel.mIzq === "lst" || !imgs.length;
        fDer.disabled = sel.mDer === "lst" || !imgs.length;
        el.querySelectorAll("[data-vista]").forEach((bt) => bt.classList.toggle("active", bt.dataset.vista === sel.vista));

        const escenario = document.getElementById("imgEscenario");
        if (sel.vista === "lado") {
          escenario.innerHTML = `<div class="img-pair">${[a, b]
            .map((x) => `<figure class="img-fig"><img src="${esc(x.src)}" alt="${esc(x.txt)}"><figcaption>${esc(x.txt)}</figcaption></figure>`)
            .join("")}</div>`;
        } else {
          escenario.innerHTML = `
            <div class="compare-stage">
              <img src="${esc(b.src)}" alt="${esc(b.txt)}">
              <div class="compare-overlay" id="imgOverlayIzq" style="clip-path: inset(0 50% 0 0);"><img src="${esc(a.src)}" alt="${esc(a.txt)}"></div>
              <div class="compare-divider" id="imgDivider" style="left: 50%;"></div>
              <span class="img-tag">${esc(a.txt)}</span>
              <span class="img-tag img-tag-der">${esc(b.txt)}</span>
            </div>
            <input type="range" class="compare-range" id="rangeCortina" min="0" max="100" value="50" aria-label="Mover la cortina entre la imagen izquierda y la derecha">`;
          document.getElementById("rangeCortina").addEventListener("input", (e) => {
            const pct = Number(e.target.value);
            document.getElementById("imgOverlayIzq").style.clipPath = `inset(0 ${100 - pct}% 0 0)`;
            document.getElementById("imgDivider").style.left = `${pct}%`;
          });
        }

        document.getElementById("leyendaRampaImg").innerHTML = [...new Set([sel.mIzq, sel.mDer])]
          .filter((k) => CAPAS[k].rampa)
          .map(
            (k) => `
            <div class="ramp-title">${esc(CAPAS[k].nombre)} · ${esc(CAPAS[k].fuente)}</div>
            <div class="ramp-bar" style="background: linear-gradient(90deg, ${CAPAS[k].rampa});"></div>
            <div class="ramp-labels">${CAPAS[k].etiquetas.map((t) => `<span>${esc(t)}</span>`).join("")}</div>`
          )
          .join("");
      };

      el.querySelectorAll("[data-preset]").forEach((bt) =>
        bt.addEventListener("click", () => {
          Object.assign(sel, presets[Number(bt.dataset.preset)].v);
          pintar();
        })
      );
      el.querySelectorAll("[data-vista]").forEach((bt) =>
        bt.addEventListener("click", () => {
          sel.vista = bt.dataset.vista;
          pintar();
        })
      );
      [["selModoIzq", "mIzq"], ["selModoDer", "mDer"]].forEach(([id, k]) =>
        document.getElementById(id).addEventListener("change", (e) => {
          sel[k] = e.target.value;
          pintar();
        })
      );
      [["selFechaIzq", "fIzq"], ["selFechaDer", "fDer"]].forEach(([id, k]) =>
        document.getElementById(id).addEventListener("change", (e) => {
          sel[k] = Number(e.target.value);
          pintar();
        })
      );
      pintar();
    }

    document.getElementById("inputFotoTerreno")?.addEventListener("change", async (ev) => {
      const file = ev.target.files?.[0];
      if (!file) return;
      const out = document.getElementById("fotoTerrenoResultado");
      const urlObj = URL.createObjectURL(file);
      const gps = leerExifGps(await file.arrayBuffer());
      let gpsHtml = "No se detectaron coordenadas EXIF en esta foto.";
      if (gps && p.centro) {
        const dist = distanciaMetros(gps.lat, gps.lon, p.centro[1], p.centro[0]);
        gpsHtml = `GPS EXIF: ${gps.lat.toFixed(5)}, ${gps.lon.toFixed(5)} · Distancia al centro: <strong>${fmtInt(dist)} m</strong>.`;
      }
      out.innerHTML = `
        <div class="photo-preview">
          <img src="${urlObj}" alt="Foto terreno">
          <div><strong>${esc(file.name)}</strong><div class="hint">${gpsHtml}</div></div>
        </div>`;
    });
  }

  function renderTabSerie(p) {
    const el = document.getElementById("tab-serie");
    const pack = state.comunaCache[state.comunaSlug];
    const sSitio = pack?.series?.sitios?.[p.site_id];
    if (!sSitio) {
      el.innerHTML = `<p class="hint">Sin serie histórica disponible para este sitio.</p>`;
      return;
    }

    const granOpts = [
      ["semanal", "Semanal"],
      ["mensual", "Mensual"],
      ["estacional", "Estacional"],
    ];
    const ev = p.evento_calor;
    const evHtml = ev
      ? `<div class="callout">
          <strong>Ventana evento térmico (${esc(ev.fecha_pico_calor)}):</strong>
          NDVI mín. <strong>${fmtNum(ev.ndvi_min, 3)}</strong> (z=${fmtNum(ev.ndvi_z_min, 2)}, ${esc(ev.fecha_min_ndvi)}) ·
          NDMI hojas mín. <strong>${fmtNum(ev.ndmi_min, 3)}</strong> (z=${fmtNum(ev.ndmi_z_min, 2)}).
        </div>`
      : "";

    el.innerHTML = `
      <div class="chart-toolbar">
        <div class="gran-btns">
          ${granOpts.map(([k, lbl]) => `<button type="button" class="gran-btn ${state.granularidad === k ? "active" : ""}" data-gran="${k}">${lbl}</button>`).join("")}
        </div>
        <span class="hint" style="margin:0;">Huecos = períodos nubosos sin interpolación.</span>
      </div>
      <div class="chart-wrap"><canvas id="canvasSerie"></canvas></div>
      ${evHtml}
      <p class="hint">Eje izquierdo: NDVI / NDMI. Eje derecho (°C): temperatura máx. del aire de reanálisis ERA5 (Open-Meteo, CC BY 4.0 no comercial). Barras azules: lluvia ERA5 acumulada (escala independiente).</p>
    `;

    el.querySelectorAll(".gran-btn").forEach((b) => {
      b.addEventListener("click", () => {
        state.granularidad = b.dataset.gran;
        renderTabSerie(p);
      });
    });

    const rows = sSitio[state.granularidad] || [];
    const labels = rows.map((r) => r[0]);
    const ndviArr = rows.map((r) => r[2]);
    const ndmiArr = rows.map((r) => r[3]);
    const tmaxArr = rows.map((r) => r[6]);
    const rainArr = rows.map((r) => r[7]);

    const idxCalor = rows.findIndex((r) => {
      if (state.granularidad === "mensual") return r[0] === "2026-01";
      if (state.granularidad === "estacional") return r[0] === "2026-Verano";
      return r[1] >= "2026-01-26" && r[1] <= "2026-02-02";
    });

    if (state.chartInstance) {
      state.chartInstance.destroy();
      state.chartInstance = null;
    }

    const markerPlugin = {
      id: "calorMarker",
      afterDraw(chart) {
        if (idxCalor < 0) return;
        const xMeta = chart.getDatasetMeta(0)?.data?.[idxCalor];
        if (!xMeta) return;
        const { ctx, chartArea } = chart;
        ctx.save();
        ctx.beginPath();
        ctx.setLineDash([5, 4]);
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = "#b91c1c";
        ctx.moveTo(xMeta.x, chartArea.top);
        ctx.lineTo(xMeta.x, chartArea.bottom);
        ctx.stroke();
        ctx.fillStyle = "#b91c1c";
        ctx.font = "bold 10px sans-serif";
        ctx.fillText("Calor 29-ene-26", Math.min(xMeta.x + 4, chartArea.right - 85), chartArea.top + 12);
        ctx.restore();
      },
    };

    const ctx = document.getElementById("canvasSerie").getContext("2d");
    state.chartInstance = new window.Chart(ctx, {
      data: {
        labels,
        datasets: [
          {
            type: "line",
            label: "NDVI (vigor)",
            data: ndviArr,
            borderColor: "#15803d",
            spanGaps: false,
            yAxisID: "yIdx",
            tension: 0.2,
            pointRadius: state.granularidad === "semanal" ? 2 : 3.5,
          },
          {
            type: "line",
            label: "NDMI (humedad hojas)",
            data: ndmiArr,
            borderColor: "#0284c7",
            spanGaps: false,
            yAxisID: "yIdx",
            tension: 0.2,
            pointRadius: state.granularidad === "semanal" ? 2 : 3.5,
          },
          {
            type: "line",
            label: "T° máx aire (°C)",
            data: tmaxArr,
            borderColor: "#ea580c",
            borderDash: [4, 3],
            spanGaps: true,
            yAxisID: "yTemp",
            pointRadius: 0,
            borderWidth: 2,
          },
          {
            type: "bar",
            label: "Lluvia (mm)",
            data: rainArr,
            backgroundColor: "rgba(56, 189, 248, 0.25)",
            yAxisID: "yRain",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        scales: {
          yIdx: {
            type: "linear",
            position: "left",
            min: -0.3,
            max: 0.85,
            title: { display: true, text: "NDVI / NDMI" },
          },
          yTemp: {
            type: "linear",
            position: "right",
            min: 5,
            max: 45,
            grid: { drawOnChartArea: false },
            title: { display: true, text: "T° aire (°C)" },
          },
          yRain: {
            type: "linear",
            position: "right",
            display: false,
            min: 0,
            suggestedMax: 280,
          },
        },
        plugins: {
          legend: { position: "bottom", labels: { boxWidth: 11, font: { size: 10 } } },
        },
      },
      plugins: [markerPlugin],
    });
  }

  function renderTabInversion(p) {
    const el = document.getElementById("tab-inversion");
    const intervs = p.intervenciones_sugeridas || [];
    const fondos = p.fondos_sugeridos || [];
    const fondosFull = Object.fromEntries((PU.catalogo?.fondos_publicos || []).map((f) => [f.id, f]));

    el.innerHTML = `
      <div class="callout">
        <strong>Brecha del entorno de 400 m (no solo de la plaza — ESA WorldCover 2021):</strong>
        Árboles <strong>${fmtNum(p.cobertura_arboles_400m_pct, 1)}%</strong> · Construido/cemento <strong>${fmtNum(p.impermeable_400m_pct, 1)}%</strong> ·
        Brecha a meta 30%: <strong>${fmtNum(p.brecha_dosel_puntos, 1)} pts</strong> (${fmtNum(p.brecha_dosel_ha, 2)} ha en radio 400 m).
      </div>
      <table class="data-table tabular">
        <thead><tr><th>Concepto (entorno 400 m)</th><th>Estimación</th><th>Etiqueta</th></tr></thead>
        <tbody>
          <tr><td>Árboles requeridos (copa 20–50 m²)</td><td><strong>${fmtInt(p.arboles_necesarios_min)} – ${fmtInt(p.arboles_necesarios_max)}</strong></td><td>WorldCover 2021 + meta 30%</td></tr>
          <tr><td>Presupuesto arbolado ($45–70 mil c/u)</td><td><strong>${fmtClp(p.costo_clp_min)} – ${fmtClp(p.costo_clp_max)}</strong></td><td><span class="badge badge-hipotesis">hipótesis (sin verificar)</span></td></tr>
        </tbody>
      </table>
      <h3>Intervenciones priorizadas</h3>
      ${intervs
        .map(
          (i) => `<div class="surface-card">
            <div style="display:flex;justify-content:space-between;gap:8px;align-items:flex-start;">
              <strong>${esc(i.nombre)}</strong>
              <span class="badge badge-hipotesis">${esc(i.etiqueta_costo || "hipótesis (sin verificar)")}</span>
            </div>
            <div class="hint" style="margin:4px 0 0;">Unidad: ${esc(i.unidad)} · Rango: ${fmtClp(i.costo_min_clp)} – ${fmtClp(i.costo_max_clp)}</div>
          </div>`
        )
        .join("")}
      <h3>Fondos públicos compatibles</h3>
      ${fondos
        .map((f) => `<div class="surface-card"><strong>${esc(f.nombre)}</strong> <span class="hint">(${esc(f.institucion)})</span>
          <div class="hint" style="margin:4px 0 0;">Requisito: ${esc((fondosFull[f.id] || {}).requisito_evidencia || "Ficha territorial cuantitativa.")}</div></div>`)
        .join("")}
    `;
  }

  function descargarBlob(blob, nombreArchivo) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = nombreArchivo;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      URL.revokeObjectURL(a.href);
      a.remove();
    }, 300);
  }

  async function descargarWordInforme(informe, metaFilas, filename) {
    if (!window.docx) {
      alert("Librería Word (.docx) no disponible.");
      return;
    }
    const { Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType } = window.docx;
    const mkP = (txt, heading = null) =>
      new Paragraph({ heading: heading || undefined, spacing: { after: 110 }, children: [new TextRun(String(txt))] });

    const tabla = new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      rows: metaFilas.map(
        ([k, v]) =>
          new TableRow({
            children: [new TableCell({ children: [mkP(k)] }), new TableCell({ children: [mkP(v)] })],
          })
      ),
    });

    const doc = new Document({
      sections: [
        {
          children: [
            mkP(informe.titulo, HeadingLevel.HEADING_1),
            mkP(textoEtiquetaIA(informe)),
            mkP(informe.resumen_ejecutivo),
            mkP("Resumen cuantificado", HeadingLevel.HEADING_2),
            tabla,
            mkP("Hallazgos verificados", HeadingLevel.HEADING_2),
            ...(informe.hallazgos || []).map((h) => mkP("• " + h)),
            mkP("Acciones e inversión priorizada (hipótesis sin verificar)", HeadingLevel.HEADING_2),
            ...(informe.acciones_priorizadas || []).map((a) => mkP(`• ${a.nombre}: ${a.rango_estimado || a.detalle || ""}`)),
            mkP("Fondos públicos sugeridos", HeadingLevel.HEADING_2),
            ...(informe.fondos_recomendados || []).map((f) => mkP(`• ${f.nombre} (${f.institucion}): ${f.requisito || ""}`)),
            ...((informe.plan_30_90_365 || []).length ? [mkP("Qué hacer: pasos a 30, 90 y 365 días", HeadingLevel.HEADING_2)] : []),
            ...(informe.plan_30_90_365 || []).map((pp) => mkP(`• ${pp.plazo || ""}: ${pp.accion || ""}`)),
            ...((informe.como_se_medira || []).length ? [mkP("Cómo se medirá el resultado", HeadingLevel.HEADING_2)] : []),
            ...(informe.como_se_medira || []).map((m) => mkP("• " + m)),
            mkP("Límites metodológicos", HeadingLevel.HEADING_2),
            ...(informe.limitaciones_y_verificacion || []).map((l) => mkP("• " + l)),
          ],
        },
      ],
    });
    descargarBlob(await Packer.toBlob(doc), filename);
  }

  function etiquetaOrigen(informe) {
    const m = String(informe.origen_redaccion || "").match(/^(gemini|openai|deepseek):(.+)$/);
    return m ? `Redactado con IA (${m[2]}) · cifras verificadas` : "Síntesis por plantilla · cifras verificadas";
  }

  function textoEtiquetaIA(informe) {
    return informe.etiqueta_ia || "Síntesis a partir de datos del sistema; debe revisarla una persona antes de entregarla.";
  }

  function htmlPlan(informe) {
    const plan = informe.plan_30_90_365 || [];
    if (!plan.length) return "";
    return `<ol class="plan-pasos">${plan
      .map((p) => `<li><span class="plan-plazo">${esc(p.plazo || p.nombre || "")}</span><span>${esc(p.accion || p.detalle || "")}</span></li>`)
      .join("")}</ol>`;
  }

  function renderHtmlInforme(informe) {
    const medicion = informe.como_se_medira || [];
    return `
      <h3 style="margin-bottom:6px;">${esc(informe.titulo)}</h3>
      <p class="informe-etiqueta">${esc(textoEtiquetaIA(informe))}</p>
      <p>${esc(informe.resumen_ejecutivo)}</p>
      <h4>Dónde invertir: hallazgos</h4>
      <ul>${(informe.hallazgos || []).map((h) => `<li>${esc(h)}</li>`).join("")}</ul>
      <h4>Cómo invertir: acciones del catálogo</h4>
      <ul>${(informe.acciones_priorizadas || [])
        .map((a) => `<li><strong>${esc(a.nombre)}:</strong> ${esc([a.detalle, a.rango_estimado].filter(Boolean).join(" "))}</li>`)
        .join("")}</ul>
      <h4>Fondos públicos compatibles</h4>
      <ul>${(informe.fondos_recomendados || []).map((f) => `<li><strong>${esc(f.nombre)}</strong> (${esc(f.institucion)}): ${esc(f.requisito || "")}</li>`).join("")}</ul>
      ${htmlPlan(informe) ? `<h4>Qué hacer: pasos a 30, 90 y 365 días</h4>${htmlPlan(informe)}` : ""}
      ${medicion.length ? `<h4>Cómo se medirá el resultado</h4><ul>${medicion.map((m) => `<li>${esc(m)}</li>`).join("")}</ul>` : ""}
      <h4>Límites y verificación</h4>
      <ul>${(informe.limitaciones_y_verificacion || []).map((l) => `<li>${esc(l)}</li>`).join("")}</ul>
    `;
  }

  function renderTabInforme(feat) {
    const p = feat.properties;
    const el = document.getElementById("tab-informe");
    const claveSitio = `${state.comunaSlug}:${p.site_id}`;
    const iaCustom = state.informeSitioCustom[claveSitio];
    const base = construirPaqueteYInformeSitio(feat);
    const paquete = base.paquete;
    const informe = iaCustom || base.informe;
    const esPreVerificado = base.esPreVerificado;
    const puedeIA = Boolean(state.iaEstado && state.iaEstado.ia_disponible);

    el.innerHTML = `
      <div class="export-bar">
        ${puedeIA ? `<button type="button" class="btn btn-primary" id="btnSitioIA">Redactar con IA (${esc(state.iaEstado.modelo)})</button>` : ""}
        <button type="button" class="btn ${puedeIA ? "btn-quiet" : "btn-primary"}" id="btnPrintPdf">Imprimir / PDF</button>
        <button type="button" class="btn btn-quiet" id="btnDocx">Word (.docx)</button>
        <button type="button" class="btn btn-quiet" id="btnCsvSitio">CSV serie</button>
        <button type="button" class="btn btn-quiet" id="btnGeojsonSitio">GeoJSON</button>
        <button type="button" class="btn btn-quiet" id="btnJsonPaquete">JSON caso</button>
        <button type="button" class="btn btn-quiet" id="btnMailto">Correo</button>
      </div>
      <div style="margin-bottom:8px;">
        <span class="badge ${iaCustom ? "badge-ia" : "badge-verificado"}">${iaCustom || esPreVerificado ? esc(etiquetaOrigen(informe)) : "Síntesis con cifras verificadas del sitio"}</span>
      </div>
      <p class="hint" id="estadoSitioIA" style="margin:0 0 8px;"></p>
      <article id="informePreview" style="font-size:0.85rem;line-height:1.5;">${renderHtmlInforme(informe)}</article>
    `;

    document.getElementById("btnSitioIA")?.addEventListener("click", async () => {
      const btn = document.getElementById("btnSitioIA");
      const st = document.getElementById("estadoSitioIA");
      btn.disabled = true;
      st.textContent = "Redactando informe del parque con IA verificada…";
      try {
        const resp = await fetch("api/informe", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ comuna_slug: state.comunaSlug, site_id: p.site_id }),
        });
        const j = await resp.json().catch(() => ({}));
        if (!resp.ok) throw new Error(j.detail || "HTTP " + resp.status);
        state.informeSitioCustom[claveSitio] = j.informe;
        renderTabInforme(feat);
      } catch (err) {
        st.textContent = "No se pudo redactar con IA: " + err.message;
        btn.disabled = false;
      }
    });

    document.getElementById("btnPrintPdf").addEventListener("click", () => {
      document.getElementById("printArea").innerHTML = document.getElementById("informePreview").innerHTML;
      window.print();
    });
    document.getElementById("btnDocx").addEventListener("click", () => {
      descargarWordInforme(
        informe,
        [
          ["Sitio / Comuna", `${p.nombre} — ${p.comuna}`],
          ["LST Verano Landsat", `${fmtNum(p.lst_verano_c, 1)} °C (+${fmtNum(p.brecha_calor_vs_vitacura_c, 1)} °C vs Vitacura)`],
          ["Sentinel-2 NDVI / SAVI / NDMI", `${fmtNum(p.ndvi_actual, 3)} / ${fmtNum(p.savi_actual, 3)} / ${fmtNum(p.ndmi_actual, 3)}`],
          ["WorldCover árboles / cemento", `${fmtNum(p.cobertura_arboles_400m_pct, 1)}% / ${fmtNum(p.impermeable_400m_pct, 1)}%`],
          ["Censo 2024 techos zinc / hacin.", `${fmtNum(p.pct_techo_calor_400m, 1)}% / ${fmtNum(p.pct_hacinamiento_400m, 1)}%`],
          ["Presupuesto (hipótesis)", `${fmtInt(p.arboles_necesarios_min)}–${fmtInt(p.arboles_necesarios_max)} árboles (${fmtClp(p.costo_clp_min)}–${fmtClp(p.costo_clp_max)})`],
        ],
        `informe_${state.comunaSlug}_${p.site_id}.docx`
      );
    });
    document.getElementById("btnCsvSitio").addEventListener("click", () => {
      const sSitio = state.comunaCache[state.comunaSlug]?.series?.sitios?.[p.site_id]?.mensual || [];
      const header = "granularidad,site_id,sitio,periodo,fecha_inicio,ndvi,ndmi,pixeles_validos,nubes_escena_pct,temp_max_c,lluvia_mm\n";
      const rows = sSitio
        .map((r) => ["mensual", p.site_id, `"${(p.nombre || "").replace(/"/g, '""')}"`, r[0], r[1], r[2] ?? "", r[3] ?? "", r[4] ?? "", r[5] ?? "", r[6] ?? "", r[7] ?? ""].join(","))
        .join("\n");
      descargarBlob(new Blob([header + rows], { type: "text/csv;charset=utf-8" }), `serie_${state.comunaSlug}_${p.site_id}.csv`);
    });
    document.getElementById("btnGeojsonSitio").addEventListener("click", () => {
      descargarBlob(new Blob([JSON.stringify({ type: "FeatureCollection", features: [feat] }, null, 2)], { type: "application/geo+json" }), `sitio_${state.comunaSlug}_${p.site_id}.geojson`);
    });
    document.getElementById("btnJsonPaquete").addEventListener("click", () => {
      descargarBlob(new Blob([JSON.stringify({ paquete, informe }, null, 2)], { type: "application/json" }), `caso_${state.comunaSlug}_${p.site_id}.json`);
    });
    document.getElementById("btnMailto").addEventListener("click", () => {
      const asunto = encodeURIComponent(informe.titulo);
      const cuerpo = encodeURIComponent(`${informe.resumen_ejecutivo}\n\n(Montos: hipótesis sin verificar)`);
      window.location.href = `mailto:?subject=${asunto}&body=${cuerpo}`;
    });
  }

  // =========================================================================
  // VISTA 2: INFORME IA DE INVERSIÓN
  // =========================================================================
  // La clave de la API nunca está en el navegador: la guarda el servidor local (app/servidor.py),
  // que redacta y verifica. Sin servidor, la página muestra la síntesis por plantilla ya verificada.
  async function consultarEstadoIA() {
    if (window.location.protocol === "file:") return null;
    try {
      const resp = await fetch("api/estado");
      if (!resp.ok) return null;
      const j = await resp.json();
      return j && j.servidor ? j : null;
    } catch (_e) {
      return null;
    }
  }

  async function actualizarPanelIA() {
    const msg = document.getElementById("estadoIAVivo");
    const btn = document.getElementById("btnGenerarIAVivo");
    const est = await consultarEstadoIA();
    state.iaEstado = est;
    btn.disabled = !(est && est.ia_disponible);
    if (!est) {
      msg.textContent =
        "Se muestra la síntesis por plantilla, ya verificada. Para redactar con IA abre la página con el servidor local " +
        "(.venv/bin/uvicorn app.servidor:app --port 8765) y pon la clave en el archivo .env; la clave no se escribe en el navegador.";
    } else if (!est.ia_disponible) {
      msg.textContent = "Servidor local activo, pero falta la clave: copia .env.example como .env, pon tu clave y reinicia el servidor.";
    } else {
      msg.textContent = `IA disponible (${est.modelo}). La clave queda en el servidor y cada texto pasa por el verificador de cifras antes de mostrarse.`;
    }
    document.getElementById("btnRestaurarIA").classList.toggle("hidden", !state.informeIACustom[state.ambitoIA]);
  }

  async function generarConIAAmbiente(scope) {
    const msg = document.getElementById("estadoIAVivo");
    const btn = document.getElementById("btnGenerarIAVivo");
    btn.disabled = true;
    msg.textContent = "Redactando con IA sobre las cifras de la cartera y verificando cada número…";
    try {
      const resp = await fetch("api/informe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ambito: scope }),
      });
      const j = await resp.json().catch(() => ({}));
      if (!resp.ok) throw new Error(j.detail || "HTTP " + resp.status);
      const diag = j.diagnostico || {};
      if (diag.uso_plantilla) {
        const ultimo = (diag.intentos || []).slice(-1)[0] || {};
        const motivo = ultimo.detalle || (ultimo.errores || []).slice(0, 2).join(" ") || "sin detalle";
        msg.textContent =
          (ultimo.resultado === "rechazado"
            ? "El verificador rechazó el texto de la IA; se mantiene la síntesis por plantilla. Motivo: "
            : "No se pudo llamar a la IA; se mantiene la síntesis por plantilla. Motivo: ") + motivo;
      } else {
        state.informeIACustom[scope] = j.informe;
        msg.textContent = `Texto redactado con IA (${diag.modelo}) y aprobado por el verificador de cifras en el intento ${(diag.intentos || []).length}. Revísalo antes de entregarlo.`;
        renderVistaInformeIA();
      }
    } catch (err) {
      msg.textContent = "No se pudo redactar con IA (" + err.message + "). Se mantiene la síntesis por plantilla.";
    }
    btn.disabled = !(state.iaEstado && state.iaEstado.ia_disponible);
    document.getElementById("btnRestaurarIA").classList.toggle("hidden", !state.informeIACustom[scope]);
  }

  function enlazarPanelIA() {
    document.getElementById("btnRestaurarIA").addEventListener("click", () => {
      delete state.informeIACustom[state.ambitoIA];
      renderVistaInformeIA();
      actualizarPanelIA();
    });
    document.getElementById("btnCopiarPaqueteIA").addEventListener("click", async () => {
      const bundle = (PU.informes_inversion || {})[state.ambitoIA];
      if (!bundle) return;
      const texto = JSON.stringify(bundle.paquete, null, 2);
      const msg = document.getElementById("estadoIAVivo");
      try {
        await navigator.clipboard.writeText(texto);
        msg.textContent = "Datos de la cartera copiados: pégalos en tu propio asistente de IA. Ese texto no pasa por nuestro verificador.";
      } catch (_e) {
        descargarBlob(new Blob([texto], { type: "application/json" }), `paquete_${state.ambitoIA}.json`);
        msg.textContent = "Datos de la cartera descargados como JSON para usarlos en tu propio asistente de IA.";
      }
    });
  }

  function renderVistaInformeIA() {
    const scope = state.ambitoIA;
    const bundle = (PU.informes_inversion || {})[scope];
    const cont = document.getElementById("contenidoInformeIA");
    if (!bundle) {
      cont.innerHTML = `<p class="hint">Aún no hay cartera generada para este ámbito.</p>`;
      return;
    }

    const paq = bundle.paquete;
    const inf = state.informeIACustom[scope] || bundle.informe;
    const cr = paq.cartera_resumen || {};
    const sitios = paq.cartera_sitios || [];

    cont.innerHTML = `
      <div class="portfolio-kpis tabular">
        <div class="kpi-card">
          <span class="kpi-label">Sitios prioritarios en cartera</span>
          <strong class="kpi-val">${fmtInt(cr.n_sitios_cartera)} sitios</strong>
          <span class="kpi-note">${esc(paq.comuna.nombre)}</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">Calor estival máx. / medio Landsat</span>
          <strong class="kpi-val">${fmtNum(cr.lst_max_cartera_c, 1)} °C / ${fmtNum(cr.lst_media_cartera_c, 1)} °C</strong>
          <span class="kpi-note">5 escenas verano 2025-26</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">Árboles estimados cartera</span>
          <strong class="kpi-val">${fmtInt(cr.arboles_min_cartera)} – ${fmtInt(cr.arboles_max_cartera)}</strong>
          <span class="kpi-note">Meta mínima 30% WorldCover 2021</span>
        </div>
        <div class="kpi-card" title="${esc(fmtClp(cr.costo_clp_min_cartera))} – ${esc(fmtClp(cr.costo_clp_max_cartera))}">
          <span class="kpi-label">Presupuesto estimado cartera</span>
          <strong class="kpi-val">${fmtClpCorto(cr.costo_clp_min_cartera)} – ${fmtClpCorto(cr.costo_clp_max_cartera)} CLP</strong>
          <span class="badge badge-hipotesis" style="margin-top:3px;">hipótesis (sin verificar)</span>
        </div>
      </div>

      <div class="surface-card">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px;">
          <h3 style="margin:0;">${esc(inf.titulo)}</h3>
          <span class="badge ${state.informeIACustom[scope] || /^deepseek|^gemini|^openai|^llm/i.test(inf.origen_redaccion || "") ? "badge-ia" : "badge-verificado"}">${esc(etiquetaOrigen(inf))}</span>
        </div>
        <p class="informe-etiqueta">${esc(textoEtiquetaIA(inf))}</p>
        <p style="font-size:0.9rem;line-height:1.55;max-width:78ch;">${esc(inf.resumen_ejecutivo)}</p>
      </div>

      <div class="surface-card" style="overflow-x:auto;">
        <h3>Mayores casos donde invertir primero</h3>
        <table class="exec-table tabular">
          <thead>
            <tr>
              <th>Parque y comuna</th>
              <th class="num-col">Prioridad</th>
              <th class="num-col">Calor verano</th>
              <th>Árboles / Cemento (400 m)</th>
              <th class="num-col">Techos zinc</th>
              <th class="num-col">Arbolado y fondo</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            ${sitios
              .map((s, i) => {
                const prio = Math.max(0, Math.min(100, Number(s.prioridad_satelital || 0)));
                const arb = Math.max(0, Math.min(100, Number(s.cobertura_arboles_400m_pct || 0)));
                const cem = Math.max(0, Math.min(100 - arb, Number(s.impermeable_400m_pct || 0)));
                const esMuyCalido = Number(s.lst_verano_c || 0) >= 40;
                return `
              <tr>
                <td>
                  <div class="park-cell">
                    <span class="rank-num">${i + 1}</span>
                    <div>
                      <strong>${esc(s.nombre)}</strong>
                      <span class="park-sub">${esc(s.comuna)} · ${fmtNum((s.area_m2 || 0) / 10000, 2)} ha</span>
                    </div>
                  </div>
                </td>
                <td class="num-col prio-cell">
                  <strong>${fmtNum(prio, 1)}</strong><span class="hint" style="margin:0;">/100</span>
                  <div class="micro-bar"><div class="micro-bar-fill" style="width:${prio.toFixed(0)}%;"></div></div>
                </td>
                <td class="num-col">
                  <span class="heat-pill ${esMuyCalido ? "" : "heat-pill-mild"}">${fmtNum(s.lst_verano_c, 1)} °C</span>
                </td>
                <td>
                  <span><strong>${fmtNum(arb, 1)}%</strong> árb · ${fmtNum(s.impermeable_400m_pct, 1)}% cem</span>
                  <div class="stack-bar" title="Árboles ${fmtNum(arb, 1)}% vs Cemento ${fmtNum(s.impermeable_400m_pct, 1)}%">
                    <div class="stack-tree" style="width:${arb.toFixed(1)}%;"></div>
                    <div class="stack-cement" style="width:${cem.toFixed(1)}%;"></div>
                  </div>
                </td>
                <td class="num-col">${fmtNum(s.pct_techo_calor_400m, 1)}%</td>
                <td class="num-col">
                  <strong>${fmtInt(s.arboles_necesarios_min)} – ${fmtInt(s.arboles_necesarios_max)}</strong>
                  <span class="fund-tag">${esc(s.fondo_sugerido)}</span>
                </td>
                <td class="num-col">
                  <button type="button" class="btn btn-quiet btn-ir-mapa-cartera" data-slug="${esc(s.comuna_slug)}" data-site="${esc(s.site_id)}" style="white-space:nowrap;">Ver en mapa →</button>
                </td>
              </tr>`;
              })
              .join("")}
          </tbody>
        </table>
      </div>

      <div class="cards-grid">
        <div class="surface-card">
          <h4>Hallazgos clave</h4>
          <ul style="padding-left:18px;font-size:0.84rem;line-height:1.48;">
            ${(inf.hallazgos || []).map((h) => `<li>${esc(h)}</li>`).join("")}
          </ul>
        </div>
        <div class="surface-card">
          <h4>Fondos recomendados</h4>
          <ul style="padding-left:18px;font-size:0.84rem;line-height:1.48;">
            ${(inf.fondos_recomendados || []).map((f) => `<li><strong>${esc(f.nombre)}:</strong> ${esc(f.requisito || "")}</li>`).join("")}
          </ul>
        </div>
        ${
          htmlPlan(inf)
            ? `<div class="surface-card"><h4>Qué hacer: pasos a 30, 90 y 365 días</h4>${htmlPlan(inf)}</div>`
            : ""
        }
        ${
          (inf.como_se_medira || []).length
            ? `<div class="surface-card"><h4>Cómo se medirá el resultado</h4>
                <ul style="padding-left:18px;font-size:0.84rem;line-height:1.48;">${inf.como_se_medira.map((m) => `<li>${esc(m)}</li>`).join("")}</ul></div>`
            : ""
        }
        <div class="surface-card">
          <h4>Límites y verificación</h4>
          <ul style="padding-left:18px;font-size:0.82rem;line-height:1.48;color:var(--muted);">
            ${(inf.limitaciones_y_verificacion || []).map((l) => `<li>${esc(l)}</li>`).join("")}
          </ul>
        </div>
      </div>
    `;

    cont.querySelectorAll(".btn-ir-mapa-cartera").forEach((b) => {
      b.addEventListener("click", async () => {
        cambiarVista("mapa");
        await seleccionarComuna(b.dataset.slug);
        abrirSitio(b.dataset.site, "resumen");
        const lyr = state.poligonosPorId[b.dataset.site];
        if (lyr && state.map) state.map.fitBounds(lyr.getBounds(), { maxZoom: 16, padding: [36, 36] });
      });
    });
  }

  // =========================================================================
  // VISTA 3: CASOS Y ARCHIVOS
  // =========================================================================
  function recopilarTodosExpedientes() {
    const items = [];
    for (const c of PU.casos || []) {
      const inf = (PU.informes || {})[c.caso_id];
      items.push({
        id: c.caso_id,
        grupo: "pitch",
        tipoLabel: "Caso del pitch",
        titulo: c.titulo,
        comunaSlug: c.comuna.slug,
        siteId: c.sitio.site_id,
        fecha: c.fecha_generacion || "2026-11-22",
        paquete: c,
        informe: inf,
      });
    }
    for (const [scope, bundle] of Object.entries(PU.informes_inversion || {})) {
      items.push({
        id: bundle.paquete.caso_id,
        grupo: "cartera",
        tipoLabel: "Cartera de inversión",
        titulo: bundle.paquete.titulo,
        comunaSlug: scope === "intercomunal" ? "cerro_navia" : scope,
        siteId: null,
        fecha: bundle.paquete.fecha_generacion || "2026-11-22",
        paquete: bundle.paquete,
        informe: bundle.informe,
      });
    }
    for (const g of leerCasosGuardados()) {
      items.push(g);
    }
    // Agrega Top 5 pre-verificados de comunas ya cacheadas
    for (const [slug, pack] of Object.entries(state.comunaCache)) {
      for (const [sid, entry] of Object.entries(pack.informesTop5 || {})) {
        items.push({
          id: entry.paquete.caso_id,
          grupo: "top5",
          tipoLabel: "Top 5 comunal",
          titulo: entry.paquete.titulo,
          comunaSlug: slug,
          siteId: sid,
          fecha: entry.paquete.fecha_generacion || "2026-11-22",
          paquete: entry.paquete,
          informe: entry.informe,
        });
      }
    }
    return items;
  }

  function actualizarContadorCasos() {
    const el = document.getElementById("navCasosCount");
    if (el) el.textContent = String(recopilarTodosExpedientes().length);
  }

  function renderListaCasos() {
    const todos = recopilarTodosExpedientes();
    actualizarContadorCasos();

    const q = state.busquedaCaso.trim().toLowerCase();
    const filtrados = todos.filter((it) => {
      if (state.filtroTipoCaso !== "todos" && it.grupo !== state.filtroTipoCaso) return false;
      if (state.filtroComunaCaso !== "todas") {
        const esIntercomunal = it.id === "inversion-intercomunal";
        if (!esIntercomunal && it.comunaSlug !== state.filtroComunaCaso) return false;
      }
      if (q) {
        const hay = `${it.titulo} ${it.tipoLabel} ${it.comunaSlug} ${it.siteId || ""}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });

    const box = document.getElementById("listaCasosArchivo");
    if (!filtrados.length) {
      box.innerHTML = `<p class="hint">Sin expedientes que coincidan con el filtro.</p>`;
      return;
    }

    if (!state.casoArchivoSelId || !filtrados.some((x) => x.id === state.casoArchivoSelId)) {
      state.casoArchivoSelId = filtrados[0].id;
    }

    box.innerHTML = filtrados
      .map(
        (it) => `
        <button type="button" class="case-list-item ${it.id === state.casoArchivoSelId ? "selected" : ""}" data-case-id="${esc(it.id)}">
          <div style="display:flex;justify-content:space-between;gap:6px;margin-bottom:3px;">
            <span class="badge ${it.grupo === "guardado" ? "badge-prioritario" : "badge-verificado"}">${esc(it.tipoLabel)}</span>
            <span class="hint" style="margin:0;">${esc(it.fecha)}</span>
          </div>
          <strong style="font-size:0.84rem;display:block;">${esc(it.titulo)}</strong>
        </button>`
      )
      .join("");

    box.querySelectorAll(".case-list-item").forEach((b) => {
      b.addEventListener("click", () => {
        state.casoArchivoSelId = b.dataset.caseId;
        renderListaCasos();
      });
    });

    const activo = filtrados.find((x) => x.id === state.casoArchivoSelId) || filtrados[0];
    renderDetalleCasoArchivo(activo);
  }

  function renderDetalleCasoArchivo(item) {
    const visor = document.getElementById("visorCasoArchivo");
    if (!item) return;
    const paq = item.paquete || {};
    const inf = item.informe || {};
    const sitio = paq.sitio || {};
    const imgs = sitio.imagenes || [];
    const ultImg = imgs[imgs.length - 1];

    const thumbs = [];
    if (sitio.imagen_lst) thumbs.push([sitio.imagen_lst, "Térmico Landsat (°C)"]);
    if (ultImg?.ndvi) thumbs.push([ultImg.ndvi, `NDVI HD (${ultImg.fecha})`]);
    if (ultImg?.ndmi) thumbs.push([ultImg.ndmi, `NDMI Hojas (${ultImg.fecha})`]);
    if (ultImg?.color) thumbs.push([ultImg.color, `Color natural (${ultImg.fecha})`]);

    visor.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;flex-wrap:wrap;margin-bottom:10px;">
        <div>
          <span class="badge badge-verificado">${esc(item.tipoLabel)}</span>
          <span class="badge badge-alta">${esc(item.fecha)}</span>
          <h3 style="margin:6px 0 2px;">${esc(item.titulo)}</h3>
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          ${item.siteId ? `<button type="button" class="btn btn-primary" id="btnAbrirCasoMapa">Abrir en Mapa satelital</button>` : ""}
          <button type="button" class="btn btn-quiet" id="btnArchivoDocx">Word (.docx)</button>
          <button type="button" class="btn btn-quiet" id="btnArchivoPdf">PDF</button>
          <button type="button" class="btn btn-quiet" id="btnArchivoJson">JSON</button>
          ${item.grupo === "guardado" ? `<button type="button" class="btn btn-quiet" id="btnEliminarCasoGuardado" style="color:var(--critico);">Eliminar</button>` : ""}
        </div>
      </div>

      ${
        thumbs.length
          ? `<div class="thumb-strip">
              ${thumbs
                .map(([src, lbl]) => `<div class="thumb-card"><img src="${esc(src)}" alt="${esc(lbl)}"><span>${esc(lbl)}</span></div>`)
                .join("")}
            </div>`
          : ""
      }

      ${
        item.grupo === "guardado"
          ? `<div class="surface-card">
              <label for="txtNotaCaso" style="font-size:0.8rem;font-weight:700;display:block;margin-bottom:5px;">Nota de inspección en terreno (guardada en este navegador):</label>
              <textarea id="txtNotaCaso" class="notes-textarea" placeholder="Escribe observaciones municipales, verificación de riego, especies presentes…">${esc(item.nota || "")}</textarea>
              <button type="button" class="btn btn-outline-primary" id="btnGuardarNotaCaso">Guardar nota</button>
            </div>`
          : ""
      }

      <div id="archivoInformeCuerpo" style="font-size:0.88rem;line-height:1.5;">
        ${inf.titulo ? renderHtmlInforme(inf) : `<pre style="font-size:0.75rem;overflow:auto;">${esc(JSON.stringify(paq, null, 2))}</pre>`}
      </div>
    `;

    document.getElementById("btnAbrirCasoMapa")?.addEventListener("click", async () => {
      cambiarVista("mapa");
      await seleccionarComuna(item.comunaSlug);
      abrirSitio(item.siteId, "informe");
      const lyr = state.poligonosPorId[item.siteId];
      if (lyr && state.map) state.map.fitBounds(lyr.getBounds(), { maxZoom: 16, padding: [36, 36] });
    });

    document.getElementById("btnArchivoDocx")?.addEventListener("click", () => {
      descargarWordInforme(
        inf,
        [
          ["Expediente", item.titulo],
          ["Tipo", item.tipoLabel],
          ["Fecha", item.fecha],
        ],
        `${item.id}.docx`
      );
    });
    document.getElementById("btnArchivoPdf")?.addEventListener("click", () => {
      document.getElementById("printArea").innerHTML = document.getElementById("archivoInformeCuerpo").innerHTML;
      window.print();
    });
    document.getElementById("btnArchivoJson")?.addEventListener("click", () => {
      descargarBlob(new Blob([JSON.stringify(item, null, 2)], { type: "application/json" }), `${item.id}.json`);
    });
    document.getElementById("btnGuardarNotaCaso")?.addEventListener("click", () => {
      const nota = document.getElementById("txtNotaCaso").value;
      const lista = leerCasosGuardados().map((g) => (g.id === item.id ? { ...g, nota } : g));
      guardarCasosGuardados(lista);
      item.nota = nota;
      alert("Nota guardada en Casos y Archivos.");
    });
    document.getElementById("btnEliminarCasoGuardado")?.addEventListener("click", () => {
      const lista = leerCasosGuardados().filter((g) => g.id !== item.id);
      guardarCasosGuardados(lista);
      state.casoArchivoSelId = null;
      renderListaCasos();
    });
  }

  // =========================================================================
  // MODALES COMPLEMENTARIOS Y NAVEGACIÓN PRINCIPAL
  // =========================================================================
  function abrirModal(titulo, html) {
    document.getElementById("modalTitle").textContent = titulo;
    document.getElementById("modalContent").innerHTML = html;
    document.getElementById("modalBackdrop").classList.remove("hidden");
  }

  function mostrarModalComparar() {
    const comunas = PU.resumen?.comunas || [];
    const filas = comunas
      .map(
        (c) => `
        <tr>
          <td><strong>${esc(c.nombre)}</strong></td>
          <td><strong>${fmtNum(c.lst_verano_mediana_c, 1)} °C</strong></td>
          <td>${fmtNum(c.cobertura_arboles_comuna_pct, 1)}% / ${fmtNum(c.impermeable_comuna_pct, 1)}%</td>
          <td><strong>${fmtNum(c.pct_techo_calor_comuna, 1)}%</strong></td>
          <td>${fmtNum(c.pct_hacinamiento_comuna, 1)}%</td>
          <td>${fmtNum(c.aire?.pm2_5_media, 1)} µg/m³</td>
          <td>${fmtNum(c.ndvi_medio, 3)}</td>
        </tr>`
      )
      .join("");

    abrirModal(
      "Comparación intercomunal (Calor Landsat, Dosel WorldCover, Censo térmico y Aire)",
      `
        <p class="hint">Vitacura muestra menor temperatura estival (34,9 °C), 33,5% de dosel y solo 7,0% de techos precarios/zinc frente a Cerro Navia y Quilicura.</p>
        <div style="overflow-x:auto;">
          <table class="data-table tabular">
            <thead>
              <tr>
                <th>Comuna</th><th>LST Verano</th><th>Árboles / Cemento</th>
                <th>Techos zinc/prec.</th><th>Hacinamiento</th><th>PM2.5 CAMS</th><th>NDVI medio</th>
              </tr>
            </thead>
            <tbody>${filas}</tbody>
          </table>
        </div>
        <div class="chart-wrap" style="height:240px;"><canvas id="canvasComparar"></canvas></div>
      `
    );

    if (state.compareChartInstance) state.compareChartInstance.destroy();
    const ctx = document.getElementById("canvasComparar").getContext("2d");
    state.compareChartInstance = new window.Chart(ctx, {
      type: "bar",
      data: {
        labels: comunas.map((c) => c.nombre),
        datasets: [
          { label: "Calor verano Landsat (°C)", data: comunas.map((c) => c.lst_verano_mediana_c), backgroundColor: "#ea580c" },
          { label: "Cobertura arbórea %", data: comunas.map((c) => c.cobertura_arboles_comuna_pct), backgroundColor: "#15803d" },
          { label: "Techos zinc/precarios %", data: comunas.map((c) => c.pct_techo_calor_comuna), backgroundColor: "#6366f1" },
        ],
      },
      options: { responsive: true, maintainAspectRatio: false },
    });
  }

  function mostrarModalPlanes() {
    const mod = PU.catalogo?.modelo_negocio || {};
    const planes = mod.escalera_planes || [];
    const cards = planes
      .map(
        (pl) => `
        <div class="plan-card">
          <div style="display:flex;justify-content:space-between;gap:6px;margin-bottom:4px;">
            <strong>${esc(pl.nombre)}</strong>
            <span class="badge badge-hipotesis">${esc(pl.etiqueta || "hipótesis (sin verificar)")}</span>
          </div>
          <div style="font-size:0.92rem;font-weight:700;color:var(--primary);margin-bottom:4px;">
            ${pl.precio_clp === 0 ? "$0 (Gratuito — Freemium permanente)" : `${fmtClp(pl.precio_min_clp)} – ${fmtClp(pl.precio_max_clp)} · ${esc(pl.periodicidad)}`}
          </div>
          <div class="hint" style="margin-bottom:5px;">${esc(pl.publico_objetivo)} · ${esc(pl.horas_soporte)}</div>
          <ul style="margin:0 0 0 16px;padding:0;font-size:0.79rem;">${(pl.incluye || []).map((inc) => `<li>${esc(inc)}</li>`).join("")}</ul>
        </div>`
      )
      .join("");

    abrirModal(
      "Planes y modelo de negocio B2B2G (Compra Ágil)",
      `
        <div class="callout callout-warn">
          <strong>Transparencia:</strong> Todos los montos están etiquetados como <strong>hipótesis (sin verificar)</strong>. ${esc(mod.nota_compra_agil || "")}
        </div>
        <div class="cards-grid">${cards}</div>
        <p class="hint" style="margin-top:10px;"><strong>Nota de licenciamiento:</strong> ${esc(mod.nota_licencia_clima || "")}</p>
      `
    );
  }

  function mostrarModalAyuda() {
    abrirModal(
      "Guía metodológica y fuentes satelitales",
      `
        <ul>
          <li><strong>NASA/USGS Landsat 8/9 (30 m):</strong> temperatura superficial terrestre (LST °C) calculada sobre 5 escenas despejadas de verano 2025–2026 con máscara de nubes QA_PIXEL.</li>
          <li><strong>Copernicus Sentinel-2 (10/20 m):</strong> NDVI (vigor vegetal), SAVI (ajustado a suelo seco), NDMI (<strong>humedad de la vegetación en hojas, no suelo</strong>) y recuperación adaptativa de bordes en plazas angostas.</li>
          <li><strong>ESA WorldCover 2021 (10 m, CC BY 4.0):</strong> distingue dosel arbóreo frente a superficie construida/impermeable (cemento). Las cifras por sitio miden la brecha del entorno de 400 m (no solo de la plaza); la cifra comunal superior se calcula sobre el área total de la comuna.</li>
          <li><strong>Copernicus CAMS y reanálisis ERA5 vía Open-Meteo (CC BY 4.0 no comercial):</strong> calidad del aire comunal (PM2.5, PM10, NO₂, radiación UV) y clima diario de referencia comunal (reanálisis).</li>
          <li><strong>INE Censo 2024 (capa opcional):</strong> ahora prioriza vulnerabilidad térmica-habitacional real (techos de zinc/fibrocemento/precarios y hacinamiento), evitando el sesgo previo por edad en comunas arborizadas.</li>
        </ul>
      `
    );
  }

  function syncPillsAmbitoIA(scope) {
    state.ambitoIA = scope;
    const selIA = document.getElementById("selectAmbitoIA");
    if (selIA) selIA.value = scope;
    document.querySelectorAll("#iaScopePills .pill-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.scope === scope);
    });
  }

  async function cambiarVista(nombreVista) {
    state.vista = nombreVista;
    document.querySelectorAll(".nav-tab").forEach((b) => {
      const act = b.dataset.view === nombreVista;
      b.classList.toggle("active", act);
      b.setAttribute("aria-selected", act ? "true" : "false");
    });
    document.querySelectorAll(".view-pane").forEach((p) => {
      p.classList.toggle("active", p.id === `view-${nombreVista}`);
    });
    if (nombreVista === "mapa" && state.map) {
      setTimeout(() => state.map.invalidateSize(), 60);
    } else if (nombreVista === "informe-ia") {
      syncPillsAmbitoIA(state.ambitoIA);
      renderVistaInformeIA();
      actualizarPanelIA();
    } else if (nombreVista === "casos") {
      if (state.comunaSlug) await cargarComuna(state.comunaSlug);
      renderListaCasos();
    }
  }

  async function seleccionarComuna(slug, origen = "selector") {
    state.comunaSlug = slug;
    state.sitioActivoId = null;
    document.getElementById("selectComuna").value = slug;
    document.getElementById("siteDrawer").classList.add("hidden");
    await cargarComuna(slug);
    renderKpis(slug);
    renderMapa(true);
    renderTop5();

    // Sincroniza también Informe IA y Casos cuando el usuario cambia el selector superior de comuna
    if (origen === "selector") {
      syncPillsAmbitoIA(slug);
      state.filtroComunaCaso = slug;
      const selFCom = document.getElementById("selectFiltroComunaCaso");
      if (selFCom) selFCom.value = slug;
      if (state.vista === "informe-ia") {
        renderVistaInformeIA();
        actualizarPanelIA();
      } else if (state.vista === "casos") {
        renderListaCasos();
      }
    }
    actualizarContadorCasos();
  }

  async function init() {
    const comunas = PU.resumen?.comunas || [];
    const sel = document.getElementById("selectComuna");
    sel.innerHTML = comunas.map((c) => `<option value="${esc(c.slug)}">${esc(c.nombre)}</option>`).join("");

    initMap();

    document.querySelectorAll(".nav-tab").forEach((b) => {
      b.addEventListener("click", () => cambiarVista(b.dataset.view));
    });

    sel.addEventListener("change", (e) => seleccionarComuna(e.target.value, "selector"));
    document.getElementById("selectCapaMapa").addEventListener("change", (e) => {
      state.capa = e.target.value;
      refrescarVistaMapa();
    });
    document.querySelectorAll(".bm-btn").forEach((b) => {
      b.addEventListener("click", () => aplicarBasemap(b.dataset.basemap));
    });
    document.getElementById("chkOcultarPequenos").addEventListener("change", (e) => {
      state.ocultarPequenos = e.target.checked;
      refrescarVistaMapa();
    });
    document.getElementById("selectSenal").addEventListener("change", (e) => {
      state.senalFiltro = e.target.value;
      refrescarVistaMapa();
    });
    document.getElementById("inputBuscar").addEventListener("input", (e) => {
      state.busqueda = e.target.value;
      refrescarVistaMapa();
    });

    const setModo = (modo) => {
      state.modoRanking = modo;
      document.getElementById("btnModoSat").classList.toggle("active", modo === "satelital");
      document.getElementById("btnModoCenso").classList.toggle("active", modo === "mixto");
      document.getElementById("censoSlidersWrap").classList.toggle("hidden", modo !== "mixto");
      document.getElementById("descModoRanking").textContent =
        modo === "satelital"
          ? "Ordena únicamente por calor superficial Landsat °C, falta de dosel/cemento WorldCover y vigor Sentinel-2."
          : "Combina 70% evidencia multi-satélite con 30% vulnerabilidad habitacional Censo 2024 (techos zinc y hacinamiento).";
      refrescarVistaMapa();
    };
    document.getElementById("btnModoSat").addEventListener("click", () => setModo("satelital"));
    document.getElementById("btnModoCenso").addEventListener("click", () => setModo("mixto"));

    const syncPeso = (id, key, lblId) => {
      document.getElementById(id).addEventListener("input", (e) => {
        state.pesosCenso[key] = Number(e.target.value);
        document.getElementById(lblId).textContent = `${state.pesosCenso[key]}%`;
        refrescarVistaMapa();
      });
    };
    syncPeso("pesoTecho", "techo", "valPesoTecho");
    syncPeso("pesoHacin", "hacin", "valPesoHacin");
    syncPeso("pesoBajoVerde", "bajo_verde", "valPesoBajoVerde");

    document.getElementById("btnResetPesos").addEventListener("click", () => {
      state.pesosCenso = { techo: 40, hacin: 30, bajo_verde: 30 };
      document.getElementById("pesoTecho").value = "40";
      document.getElementById("pesoHacin").value = "30";
      document.getElementById("pesoBajoVerde").value = "30";
      document.getElementById("valPesoTecho").textContent = "40%";
      document.getElementById("valPesoHacin").textContent = "30%";
      document.getElementById("valPesoBajoVerde").textContent = "30%";
      refrescarVistaMapa();
    });

    document.querySelectorAll(".tab-btn").forEach((b) => {
      b.addEventListener("click", () => {
        state.tabActiva = b.dataset.tab;
        renderDrawerActual();
      });
    });

    document.getElementById("btnGuardarCasoSitio").addEventListener("click", () => {
      const feat = obtenerFeature(state.sitioActivoId);
      if (feat) {
        guardarSitioEnCasos(feat);
        renderDrawerActual();
      }
    });

    document.getElementById("btnCerrarDrawer").addEventListener("click", () => {
      state.sitioActivoId = null;
      document.getElementById("siteDrawer").classList.add("hidden");
      renderMapa(false);
      renderTop5();
    });

    // Informe IA view bindings (sincronizado con selector global cuando se elige una comuna específica)
    document.querySelectorAll("#iaScopePills .pill-btn").forEach((b) => {
      b.addEventListener("click", async () => {
        const sc = b.dataset.scope;
        syncPillsAmbitoIA(sc);
        if (sc !== "intercomunal" && sc !== state.comunaSlug) {
          await seleccionarComuna(sc, "pill");
        }
        renderVistaInformeIA();
        actualizarPanelIA();
      });
    });
    document.getElementById("selectAmbitoIA").addEventListener("change", async (e) => {
      const sc = e.target.value;
      syncPillsAmbitoIA(sc);
      if (sc !== "intercomunal" && sc !== state.comunaSlug) {
        await seleccionarComuna(sc, "pill");
      }
      renderVistaInformeIA();
      actualizarPanelIA();
    });
    document.getElementById("btnGenerarIAVivo").addEventListener("click", () => {
      const bundle = (PU.informes_inversion || {})[state.ambitoIA];
      if (bundle) generarConIAAmbiente(state.ambitoIA);
    });
    enlazarPanelIA();
    document.getElementById("btnIaDocx").addEventListener("click", () => {
      const bundle = (PU.informes_inversion || {})[state.ambitoIA];
      if (!bundle) return;
      const inf = state.informeIACustom[state.ambitoIA] || bundle.informe;
      const cr = bundle.paquete.cartera_resumen || {};
      descargarWordInforme(
        inf,
        [
          ["Ámbito", bundle.paquete.comuna.nombre],
          ["Sitios priorizados", `${fmtInt(cr.n_sitios_cartera)}`],
          ["Calor máx. Landsat", `${fmtNum(cr.lst_max_cartera_c, 1)} °C`],
          ["Árboles estimados", `${fmtInt(cr.arboles_min_cartera)} – ${fmtInt(cr.arboles_max_cartera)}`],
          ["Presupuesto (hipótesis sin verificar)", `${fmtClp(cr.costo_clp_min_cartera)} – ${fmtClp(cr.costo_clp_max_cartera)}`],
        ],
        `cartera_inversion_${state.ambitoIA}.docx`
      );
    });
    document.getElementById("btnIaPdf").addEventListener("click", () => {
      document.getElementById("printArea").innerHTML = document.getElementById("contenidoInformeIA").innerHTML;
      window.print();
    });
    document.getElementById("btnIaGuardarCaso").addEventListener("click", () => {
      const bundle = (PU.informes_inversion || {})[state.ambitoIA];
      if (!bundle) return;
      const inf = state.informeIACustom[state.ambitoIA] || bundle.informe;
      const id = `guardado-cartera-${state.ambitoIA}-${Date.now()}`;
      const lista = leerCasosGuardados();
      lista.unshift({
        id,
        grupo: "guardado",
        tipoLabel: "Cartera guardada",
        titulo: `${inf.titulo}`,
        comunaSlug: state.ambitoIA === "intercomunal" ? "cerro_navia" : state.ambitoIA,
        siteId: null,
        fecha: new Date().toISOString().slice(0, 10),
        nota: "",
        paquete: bundle.paquete,
        informe: inf,
      });
      guardarCasosGuardados(lista);
      alert("Cartera guardada en Casos y Archivos.");
    });

    // Casos y Archivos view bindings
    document.getElementById("selectFiltroTipoCaso").addEventListener("change", (e) => {
      state.filtroTipoCaso = e.target.value;
      renderListaCasos();
    });
    document.getElementById("selectFiltroComunaCaso").addEventListener("change", async (e) => {
      state.filtroComunaCaso = e.target.value;
      if (state.filtroComunaCaso !== "todas") {
        await seleccionarComuna(state.filtroComunaCaso, "pill");
      }
      renderListaCasos();
    });
    document.getElementById("inputBuscarCaso").addEventListener("input", (e) => {
      state.busquedaCaso = e.target.value;
      renderListaCasos();
    });
    document.getElementById("inputImportarCaso").addEventListener("change", async (e) => {
      const f = e.target.files?.[0];
      if (!f) return;
      try {
        const obj = JSON.parse(await f.text());
        const paq = obj.paquete || obj;
        const inf = obj.informe || {};
        const lista = leerCasosGuardados();
        const id = `importado-${Date.now()}`;
        lista.unshift({
          id,
          grupo: "guardado",
          tipoLabel: "Archivo importado",
          titulo: inf.titulo || paq.titulo || f.name,
          comunaSlug: paq.comuna?.slug || state.comunaSlug || "cerro_navia",
          siteId: paq.sitio?.site_id || null,
          fecha: new Date().toISOString().slice(0, 10),
          nota: obj.nota || "",
          paquete: paq,
          informe: inf,
        });
        guardarCasosGuardados(lista);
        state.casoArchivoSelId = id;
        renderListaCasos();
      } catch (_err) {
        alert("El archivo JSON no tiene un formato válido de caso.");
      }
      e.target.value = "";
    });

    // Modales & Móvil
    document.getElementById("btnComparar").addEventListener("click", mostrarModalComparar);
    document.getElementById("btnPlanes").addEventListener("click", mostrarModalPlanes);
    document.getElementById("btnAyuda").addEventListener("click", mostrarModalAyuda);
    document.getElementById("btnCerrarModal").addEventListener("click", () => {
      document.getElementById("modalBackdrop").classList.add("hidden");
    });
    document.getElementById("modalBackdrop").addEventListener("click", (e) => {
      if (e.target.id === "modalBackdrop") e.target.classList.add("hidden");
    });
    document.getElementById("btnAbrirPanelMovil")?.addEventListener("click", () => {
      document.getElementById("sidebar").classList.add("open");
    });
    document.getElementById("btnToggleSidebar")?.addEventListener("click", () => {
      document.getElementById("sidebar").classList.remove("open");
    });

    if (comunas.length) {
      await seleccionarComuna(comunas[0].slug);
    }
    await actualizarPanelIA();
    actualizarContadorCasos();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
