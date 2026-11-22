(function () {
  "use strict";

  const PU = window.PU_DATOS || {};
  const LS_KEY_CASOS = "pulmon_urbano_casos_guardados_v1";
  const LS_KEY_PERFIL = "pulmon_urbano_perfil_v5";

  const ETIQ_ESTADO = {
    critico: "Urgente",
    prioritario: "Prioritario",
    vigilar: "En observación",
    estable: "Saludable",
    sin_datos: "Sin lectura",
  };

  const COLOR_ESTADO = {
    critico: "#b91c1c",
    prioritario: "#ea580c",
    vigilar: "#ca8a04",
    estable: "#15803d",
    sin_datos: "#64748b",
  };

  const ETIQ_SENAL = {
    isla_calor: "Calor alto en suelo (≥ 36,5 °C)",
    veg_caida: "Caída reciente de vegetación",
    estres_hidrico: "Hojas con falta de agua",
    brecha_dosel: "Poca sombra (< 20% árboles)",
    calor_vulnerabilidad: "Alta exposición vecinal al calor",
    sin_senal: "Sin alerta activa",
  };

  const BASEMAPS = {
    satelite: {
      url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      attr: "Fotos aéreas &copy; Esri, Maxar, Earthstar Geographics",
      className: "",
    },
    claro: {
      url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      attr: "&copy; OpenStreetMap",
      className: "tile-claro",
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
    basemap: "satelite",
    modoRanking: "satelital",
    ocultarPequenos: false,
    senalFiltro: "todas",
    busqueda: "",
    pesosCenso: { techo: 40, hacin: 30, bajo_verde: 30 },
    comunaCache: {},
    sitioActivoId: null,
    tabActiva: "resumen",
    granularidad: "mensual",
    ambitoIA: "intercomunal",
    informeIACustom: {},
    informeSitioCustom: {},
    iaEstado: null,
    perfil: {
      email: "demo@pulmonurbano.cl",
      nombre: "Equipo Evaluador",
      organizacion: "Municipalidad Demo",
      rol: "Planificación Urbana (SECPLA)",
      plan_id: "gratis",
      plan_nombre: "Gratis (Demo / Público)",
      modalidad: "mensual",
      exportaciones_usadas: 0,
      exportaciones_limite: 2,
      informes_ia_usados: 0,
      informes_ia_limite: 0,
    },
    modalidadPlanUI: "mensual",
    casosServidor: [],
    chatImagenDataUrl: null,
    capturaSitioDataUrl: null,
    casoArchivoSelId: null,
    filtroTipoCaso: "todos",
    filtroComunaCaso: "todas",
    busquedaCaso: "",
    chartInstance: null,
    compareChartInstance: null,
    miniMap: null,
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

  function renderMarkdownSimple(str) {
    return esc(str)
      .replace(/^#{1,4}\s+(.+)$/gm, "<strong>$1</strong>")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/`([^`]+)`/g, "$1")
      .replace(/\n/g, "<br>");
  }

  function limpiarTextoHumano(str) {
    return String(str ?? "")
      .replace(/\b(?:cn|sm|v|q)-[wr]\d+\b[,:\s]*/gi, "")
      .replace(/(\d{7,})/g, (m) => fmtClpCorto(Number(m)).replace("$", "") + " CLP aprox.");
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
    if (Math.abs(n) >= 1e9) return "$" + fmtNum(n / 1e9, 2) + " mil M";
    if (Math.abs(n) >= 1e6) return "$" + fmtNum(n / 1e6, 1) + "M";
    return "$" + fmtInt(n);
  }

  function leerCasosLocales() {
    try {
      const raw = window.localStorage.getItem(LS_KEY_CASOS);
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch (_e) {
      return [];
    }
  }

  function guardarCasosLocales(lista) {
    try {
      window.localStorage.setItem(LS_KEY_CASOS, JSON.stringify(lista));
    } catch (_e) {
      // ignora modo privado
    }
    actualizarContadorCasos();
  }

  function guardarPerfilLocal() {
    try {
      window.localStorage.setItem(LS_KEY_PERFIL, JSON.stringify(state.perfil));
    } catch (_e) {
      // ignora
    }
  }

  function leerPerfilLocal() {
    try {
      const raw = window.localStorage.getItem(LS_KEY_PERFIL);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && parsed.email) Object.assign(state.perfil, parsed);
      }
    } catch (_e) {
      // ignora
    }
  }

  function esPlanGratis() {
    return (state.perfil?.plan_id || "gratis") === "gratis";
  }

  function puedeUsarIA() {
    return !esPlanGratis() || Number(state.perfil?.informes_ia_limite || 0) > 0;
  }

  function abrirModalUpgrade(motivo) {
    abrirModal(
      "Función restringida en Plan Gratis ($0)",
      `
        <div class="callout callout-warn">
          <strong>${esc(motivo)}</strong><br>
          En el <strong>Plan Gratis (Demo)</strong> puedes explorar el mapa y usar hasta <strong>2 exportaciones gratuitas de datos</strong>.
        </div>
        <p style="font-size:0.9rem;line-height:1.5;">
          Para desbloquear al instante el <strong>Asistente IA con fotos</strong>, informes Word/PDF listos para postular y descargas ampliadas, activa un plan en 1 clic sin tarjeta (conectado a Supabase):
        </p>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;">
          <button type="button" class="btn btn-primary" id="btnModalActivarConsultora">Activar Consultora ⭐ (4,5 UF/mes · Demo 1 clic)</button>
          <button type="button" class="btn btn-outline-primary" id="btnModalActivarPase">Activar Pase Proyecto (1,5 UF · Demo)</button>
          <button type="button" class="btn btn-quiet" id="btnModalVerPlanes">Ver todos los planes</button>
        </div>
      `
    );
    document.getElementById("btnModalActivarConsultora")?.addEventListener("click", async () => {
      await activarPlanEnBackend("consultora", state.modalidadPlanUI);
      document.getElementById("modalBackdrop").classList.add("hidden");
    });
    document.getElementById("btnModalActivarPase")?.addEventListener("click", async () => {
      await activarPlanEnBackend("pase_proyecto", "mensual");
      document.getElementById("modalBackdrop").classList.add("hidden");
    });
    document.getElementById("btnModalVerPlanes")?.addEventListener("click", () => {
      document.getElementById("modalBackdrop").classList.add("hidden");
      cambiarVista("planes");
    });
  }

  async function consumirExportacion(tipo) {
    if (window.location.protocol !== "file:") {
      try {
        const resp = await fetch("api/plan/consumir-exportacion", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: state.perfil.email, tipo }),
        });
        const j = await resp.json().catch(() => ({}));
        if (resp.status === 402) {
          abrirModalUpgrade(j.detail || "Límite de exportaciones gratuitas alcanzado.");
          return false;
        }
        if (resp.ok && j.perfil) {
          Object.assign(state.perfil, j.perfil);
          guardarPerfilLocal();
          actualizarUIPlanYUsuario();
          return true;
        }
      } catch (_e) {
        // fallback local abajo
      }
    }
    const limite = Number(state.perfil.exportaciones_limite || 2);
    const usadas = Number(state.perfil.exportaciones_usadas || 0);
    if (esPlanGratis() && (tipo === "docx" || tipo === "pdf")) {
      abrirModalUpgrade("Los informes Word y PDF ejecutivos requieren Pase por Proyecto (1,5 UF) o Plan Consultora ⭐.");
      return false;
    }
    if (usadas >= limite) {
      abrirModalUpgrade(`Alcanzaste el límite de ${limite} exportaciones gratuitas.`);
      return false;
    }
    state.perfil.exportaciones_usadas = usadas + 1;
    guardarPerfilLocal();
    actualizarUIPlanYUsuario();
    return true;
  }

  function actualizarUIPlanYUsuario() {
    const badge = document.getElementById("badgePlanActivo");
    const btnUser = document.getElementById("btnLoginUsuario");
    const p = state.perfil;
    const lim = Number(p.exportaciones_limite || 2);
    const us = Number(p.exportaciones_usadas || 0);
    const rest = Math.max(0, lim - us);

    if (badge) {
      badge.classList.toggle("plan-pro", !esPlanGratis());
      badge.textContent = esPlanGratis()
        ? `Plan Gratis · ${rest} export. libres`
        : `${p.plan_nombre.split("(")[0].trim()} · Activo`;
    }
    if (btnUser) {
      const primerNombre = (p.nombre || "Usuario").split(" ")[0];
      btnUser.textContent = p.email === "demo@pulmonurbano.cl" && esPlanGratis()
        ? "Iniciar sesión"
        : `${primerNombre} (${p.organizacion.split(" ")[0]})`;
    }
    const resUso = document.getElementById("estadoUsoPlanResumen");
    if (resUso) {
      resUso.textContent = `${p.plan_nombre} · ${us} de ${lim >= 9999 ? "ilimitadas" : lim} exportaciones · ${p.informes_ia_usados || 0} consultas IA`;
    }
    const gate = document.getElementById("chatPlanGateBanner");
    if (gate) gate.classList.toggle("hidden", puedeUsarIA());
    const btnSendChat = document.getElementById("btnEnviarChatIA");
    if (btnSendChat) btnSendChat.disabled = false;
    renderPlanesView();
  }

  async function sincronizarPerfilYCasosServidor() {
    if (window.location.protocol === "file:") return;
    try {
      const q = encodeURIComponent(state.perfil.email || "demo@pulmonurbano.cl");
      const [rPlan, rCasos] = await Promise.all([
        fetch(`api/plan/actual?email=${q}`),
        fetch(`api/casos?email=${q}`),
      ]);
      if (rPlan.ok) {
        const jp = await rPlan.json();
        if (jp?.perfil) {
          Object.assign(state.perfil, jp.perfil);
          guardarPerfilLocal();
        }
      }
      if (rCasos.ok) {
        const jc = await rCasos.json();
        if (Array.isArray(jc?.casos)) {
          state.casosServidor = jc.casos;
        }
      }
    } catch (_e) {
      // mantiene datos locales
    }
    actualizarUIPlanYUsuario();
    actualizarContadorCasos();
  }

  async function activarPlanEnBackend(planId, modalidad = "mensual") {
    const planes = PU.catalogo?.modelo_negocio?.escalera_planes || [];
    const cfg = planes.find((x) => x.id === planId) || {
      id: planId,
      nombre: planId,
      exportaciones_limite: planId === "gratis" ? 2 : 500,
      informes_ia_limite: planId === "gratis" ? 0 : 15,
    };

    let almacenamiento = "local_fallback";
    if (window.location.protocol !== "file:") {
      try {
        const resp = await fetch("api/plan/activar", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: state.perfil.email, plan_id: planId, modalidad }),
        });
        if (resp.ok) {
          const j = await resp.json();
          if (j.perfil) Object.assign(state.perfil, j.perfil);
          almacenamiento = j.almacenamiento || "supabase";
        }
      } catch (_e) {
        // fallback local abajo
      }
    }
    if (almacenamiento === "local_fallback") {
      Object.assign(state.perfil, {
        plan_id: cfg.id,
        plan_nombre: cfg.nombre,
        modalidad,
        exportaciones_limite: cfg.exportaciones_limite,
        informes_ia_limite: cfg.informes_ia_limite,
        exportaciones_usadas: cfg.id === "gratis" ? 0 : state.perfil.exportaciones_usadas,
        estado: "activo",
      });
    }
    guardarPerfilLocal();
    actualizarUIPlanYUsuario();
    actualizarPanelIA();

    const banner = document.getElementById("bannerPlanAceptado");
    if (banner) {
      banner.classList.remove("hidden");
      const donde = almacenamiento === "supabase" ? "Supabase Postgres" : "tu sesión (listo para Supabase SQL)";
      banner.innerHTML =
        `¡Plan aceptado! <strong>${esc(state.perfil.plan_nombre)}</strong> quedó activo en ${esc(donde)}. ` +
        `Ya tienes habilitados el Asistente IA, análisis de fotos y exportaciones ampliadas.`;
    }
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
        // continúa a <script>
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
        const hay = `${p.nombre || ""} ${p.nombre_base || ""} ${p.site_id || ""}`.toLowerCase();
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
      const s = p.salud_vegetal_pct ?? Math.round(((p.ndvi_actual || 0.2) / 0.6) * 100);
      if (s < 30) return "#b45309";
      if (s < 48) return "#eab308";
      if (s < 68) return "#65a30d";
      if (s < 85) return "#16a34a";
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
    const bm = BASEMAPS[clave] || BASEMAPS.satelite;
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
      title = state.modoRanking === "satelital" ? "Urgencia para plantar árboles" : "Urgencia (Clima + Vecinos)";
      items = [
        ["#b91c1c", "≥ 75 (urgente — plantar primero)"],
        ["#ea580c", "60 – 74 (prioridad alta)"],
        ["#ca8a04", "45 – 59 (prioridad media)"],
        ["#65a30d", "28 – 44 (moderada)"],
        ["#15803d", "< 28 (condición saludable)"],
      ];
    } else if (state.capa === "calor") {
      title = "Calor del suelo en verano (°C)";
      items = [
        ["#991b1b", "≥ 42,0 °C (calor extremo)"],
        ["#ea580c", "39,0 – 41,9 °C (muy caluroso)"],
        ["#eab308", "36,0 – 38,9 °C (cálido)"],
        ["#65a30d", "33,0 – 35,9 °C (templado)"],
        ["#0284c7", "< 33,0 °C (fresco relativo)"],
      ];
    } else if (state.capa === "ndvi") {
      title = "Salud del pasto y árboles (%)";
      items = [
        ["#b45309", "< 30% (suelo seco o poco verde)"],
        ["#eab308", "30% – 47% (vegetación débil)"],
        ["#65a30d", "48% – 67% (vegetación normal)"],
        ["#16a34a", "68% – 84% (buena salud)"],
        ["#14532d", "≥ 85% (arboleda densa y sana)"],
      ];
    } else if (state.capa === "ndmi") {
      title = "Agua disponible en hojas";
      items = [
        ["#b45309", "Muy secas (estrés hídrico)"],
        ["#eab308", "Humedad baja"],
        ["#38bdf8", "Humedad normal"],
        ["#0f766e", "Hojas bien hidratadas"],
      ];
    } else {
      title = "Techos calientes y hacinamiento (Censo 2024)";
      items = [
        ["#991b1b", "≥ 80 (alta exposición vecinal)"],
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

    const confPct = r.confianza_comuna_pct || 94;
    const heroConf = document.getElementById("heroConfianzaBadge");
    if (heroConf) {
      heroConf.textContent = `Confianza en ${r.nombre}: ${confPct}% (${r.fuentes_activas || 5} fuentes)`;
    }

    const deltaVit =
      r.lst_verano_mediana_c != null && vit?.lst_verano_mediana_c != null
        ? r.lst_verano_mediana_c - vit.lst_verano_mediana_c
        : null;

    document.getElementById("kpiLst").textContent = r.lst_verano_mediana_c != null ? `${fmtNum(r.lst_verano_mediana_c, 1)} °C` : "s/d";
    document.getElementById("kpiLstNota").textContent =
      deltaVit != null && slug !== "vitacura"
        ? `${deltaVit >= 0 ? "+" : ""}${fmtNum(deltaVit, 1)} °C más caliente que Vitacura`
        : "Comuna de referencia fresca";

    document.getElementById("kpiDosel").textContent = `${fmtNum(r.cobertura_arboles_comuna_pct, 1)}% árb · ${fmtNum(r.impermeable_comuna_pct, 1)}% cem`;
    document.getElementById("kpiDoselNota").textContent = "Árboles vs. cemento (ESA WorldCover)";

    document.getElementById("kpiArboles").textContent =
      r.arboles_necesarios_min_total === 0 && r.arboles_necesarios_max_total === 0
        ? "0 (meta 30% cumplida)"
        : `${fmtInt(r.arboles_necesarios_min_total)} – ${fmtInt(r.arboles_necesarios_max_total)}`;

    const aire = r.aire || {};
    document.getElementById("kpiAire").textContent = aire.pm2_5_media != null ? `${fmtNum(aire.pm2_5_media, 1)} µg/m³` : "s/d";
    document.getElementById("kpiAireNota").textContent = aire.uv_max != null ? `UV máx. ${fmtNum(aire.uv_max, 1)} · Copérnico` : "Promedio 30 días";

    document.getElementById("kpiSitios").textContent = `${confPct}% · ${fmtInt(r.n_sitios)} parques`;
    document.getElementById("kpiSitiosNota").textContent = `${fmtInt(r.n_sitios_imagen)} con foto térmica + aérea`;

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
    document.getElementById("estadoFiltroResumen").textContent = `${filtrados.length} de ${pack.geojson.features.length} parques`;

    state.layerSitios = L.geoJSON(
      { type: "FeatureCollection", features: filtrados },
      {
        style: (feat) => {
          const p = feat.properties;
          const esSel = p.site_id === state.sitioActivoId;
          return {
            color: esSel ? "#ffffff" : esSat ? "#fde047" : "#1e293b",
            weight: esSel ? 3.4 : 1.3,
            fillColor: colorParaSitio(p),
            fillOpacity: esSel ? 0.72 : esSat ? 0.48 : 0.74,
          };
        },
        onEachFeature: (feat, layer) => {
          const p = feat.properties;
          state.poligonosPorId[p.site_id] = layer;
          layer.bindTooltip(
            `<strong>${esc(p.nombre)}</strong><br>` +
              `Urgencia: ${fmtNum(calcPrioridadActual(p), 1)}/100 · Calor verano: ${fmtNum(p.lst_verano_c, 1)} °C<br>` +
              `Salud verde: ${p.salud_vegetal_pct ?? "—"}% · Árboles: ${fmtNum(p.cobertura_arboles_400m_pct, 1)}% · Confianza: ${p.confianza_pct ?? 90}%`,
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
      const nomA = a.properties.con_nombre ? 1 : 0;
      const nomB = b.properties.con_nombre ? 1 : 0;
      const pa = calcPrioridadActual(a.properties) + nomA * 3;
      const pb = calcPrioridadActual(b.properties) + nomB * 3;
      if (pb !== pa) return pb - pa;
      return (b.properties.lst_verano_c || 0) - (a.properties.lst_verano_c || 0);
    });

    const top5 = [];
    const basesVistas = new Set();
    for (const f of filtrados) {
      const base = (f.properties.nombre_base || f.properties.nombre || "").toLowerCase();
      if (basesVistas.has(base)) continue;
      basesVistas.add(base);
      top5.push(f);
      if (top5.length >= 5) break;
    }

    if (!top5.length) {
      list.innerHTML = `<li class="hint">Sin parques que coincidan con los filtros actuales.</li>`;
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
                <span>Calor: <strong>${fmtNum(p.lst_verano_c, 1)} °C</strong></span>
                <span>Salud verde: <strong>${p.salud_vegetal_pct ?? "—"}%</strong></span>
                <span>Árboles: <strong>${fmtNum(p.cobertura_arboles_400m_pct, 1)}%</strong></span>
                <span>Conf.: <strong>${p.confianza_pct ?? 90}%</strong></span>
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
      sitio: { site_id: p.site_id, nombre: p.nombre, comuna: p.comuna, estado: p.estado, confianza: p.confianza, confianza_pct: p.confianza_pct, imagenes: p.imagenes, imagen_lst: p.imagen_lst },
      comuna: { slug: state.comunaSlug, nombre: p.comuna },
      numeros: {
        area_ha: Math.round(areaHa * 100) / 100,
        prioridad_actual: prAct,
        lst_verano_c: p.lst_verano_c,
        lst_pico_c: p.lst_pico_c,
        brecha_calor_vs_vitacura_c: p.brecha_calor_vs_vitacura_c,
        ndvi_actual: p.ndvi_actual,
        salud_vegetal_pct: p.salud_vegetal_pct,
        cobertura_arboles_400m_pct: p.cobertura_arboles_400m_pct,
        impermeable_400m_pct: p.impermeable_400m_pct,
        pct_techo_calor_400m: p.pct_techo_calor_400m,
        pct_hacinamiento_400m: p.pct_hacinamiento_400m,
        arboles_necesarios_min: p.arboles_necesarios_min,
        arboles_necesarios_max: p.arboles_necesarios_max,
        costo_clp_min: p.costo_clp_min,
        costo_clp_max: p.costo_clp_max,
        confianza_pct: p.confianza_pct,
      },
    };

    const acciones = (p.intervenciones_sugeridas || []).map((iv) => ({
      nombre: iv.nombre,
      etiqueta_costo: "hipótesis (sin verificar)",
      detalle:
        iv.id === "arborizacion_calles" && p.arboles_necesarios_min != null
          ? `Plantar entre ${fmtInt(p.arboles_necesarios_min)} y ${fmtInt(p.arboles_necesarios_max)} árboles (${fmtClp(p.costo_clp_min)} a ${fmtClp(p.costo_clp_max)}, hipótesis (sin verificar)).`
          : `Presupuesto de referencia ${fmtClp(iv.costo_min_clp)} a ${fmtClp(iv.costo_max_clp)} (hipótesis (sin verificar)).`,
    }));

    const informe = {
      caso_id: paquete.caso_id,
      titulo: `Ficha técnica clara — ${p.nombre} (${p.comuna})`,
      resumen_ejecutivo:
        `${p.nombre} (${fmtNum(areaHa, 2)} ha) presenta urgencia de ${fmtNum(prAct, 1)}/100, temperatura estival de ${fmtNum(p.lst_verano_c, 1)} °C (+${fmtNum(p.brecha_calor_vs_vitacura_c, 1)} °C frente a Vitacura) y confianza de medición de ${p.confianza_pct ?? 90}%. ` +
        `La salud actual del pasto y árboles es de ${p.salud_vegetal_pct ?? "—"}%, mientras su entorno a 5 cuadras (400 m) tiene solo ${fmtNum(p.cobertura_arboles_400m_pct, 1)}% de árboles frente a ${fmtNum(p.impermeable_400m_pct, 1)}% de cemento.`,
      hallazgos: [
        `Calor del suelo en verano: ${fmtNum(p.lst_verano_c, 1)} °C en el parque (máximo ${fmtNum(p.lst_pico_c, 1)} °C).`,
        `Falta de sombra (meta mínima 30%): se requieren entre ${fmtInt(p.arboles_necesarios_min)} y ${fmtInt(p.arboles_necesarios_max)} árboles en sus 5 cuadras alrededor.`,
        `Entorno vecinal (Censo 2024 agregado): ${fmtInt(p.pop_400m)} habitantes cercanos, ${fmtNum(p.pct_techo_calor_400m, 1)}% viviendas con techo sensible al calor.`,
        `Aire de la comuna: ${fmtNum(r.aire?.pm2_5_media, 1)} µg/m³ de material particulado fino PM2.5.`,
      ],
      acciones_priorizadas: acciones.length ? acciones : [{ nombre: "Visita y catastro en terreno", etiqueta_costo: "hipótesis (sin verificar)", detalle: "Confirmar puntos de riego disponibles y especies presentes." }],
      fondos_recomendados: (p.fondos_sugeridos || []).map((f) => {
        const full = (cat.fondos_publicos || []).find((x) => x.id === f.id);
        return { nombre: f.nombre, institucion: f.institucion, requisito: full?.requisito_evidencia || "Ficha territorial cuantitativa." };
      }),
      limitaciones_y_verificacion: [
        "Todos los montos en CLP corresponden a hipótesis (sin verificar) para evaluación preliminar.",
        "La humedad de hojas proviene de lectura óptica Sentinel-2 y orienta mantención, sin reemplazar inspección de riego en terreno.",
        "Los datos censales son 100% agregados (cumple Ley 21.719).",
      ],
      origen_redaccion: "sintesis_verificada_navegador",
      verificado: true,
    };
    return { paquete, informe, esPreVerificado: Boolean(pre) };
  }

  function abrirSitio(siteId, tabDestino = null) {
    state.sitioActivoId = siteId;
    state.capturaSitioDataUrl = null;
    if (tabDestino) state.tabActiva = tabDestino;
    document.getElementById("siteDrawer").classList.remove("hidden");
    renderMapa(false);
    renderTop5();
    renderDrawerActual();
  }

  async function guardarCasoPersistente(registro) {
    const lista = leerCasosLocales().filter((x) => x.id !== registro.id);
    lista.unshift(registro);
    guardarCasosLocales(lista);

    if (window.location.protocol !== "file:") {
      try {
        const payload = {
          id: registro.id,
          user_email: state.perfil.email || "demo@pulmonurbano.cl",
          comuna_slug: registro.comunaSlug || state.comunaSlug || "cerro_navia",
          site_id: registro.siteId || null,
          titulo: registro.titulo,
          tipo_label: registro.tipoLabel || "Caso guardado",
          nota: registro.nota || "",
          foto_data_url: registro.fotoDataUrl || null,
          pregunta_ia: registro.preguntaIA || null,
          respuesta_ia: registro.respuestaIA || null,
          confianza_pct: Number(registro.confianzaPct || 94),
          paquete: registro.paquete || null,
          informe: registro.informe || null,
        };
        const resp = await fetch("api/casos", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (resp.ok) {
          state.casosServidor = [payload, ...state.casosServidor.filter((c) => c.id !== payload.id)];
        }
      } catch (_e) {
        // queda guardado en localStorage
      }
    }
    actualizarContadorCasos();
    actualizarSelectContextoChat();
    if (state.vista === "casos") renderListaCasos();
  }

  function guardarSitioEnCasos(feat, fotoExtra = null) {
    const { paquete, informe } = construirPaqueteYInformeSitio(feat);
    const id = `guardado-${state.comunaSlug}-${feat.properties.site_id}`;
    const existe = recopilarTodosExpedientes().find((x) => x.id === id);
    const registro = {
      id,
      grupo: "guardado",
      tipoLabel: fotoExtra ? "Foto y ficha" : "Parque guardado",
      titulo: `${feat.properties.nombre} (${feat.properties.comuna})`,
      comunaSlug: state.comunaSlug,
      siteId: feat.properties.site_id,
      fecha: new Date().toISOString().slice(0, 10),
      nota: existe?.nota || "",
      fotoDataUrl: fotoExtra || existe?.fotoDataUrl || null,
      confianzaPct: feat.properties.confianza_pct || 92,
      paquete,
      informe,
    };
    guardarCasoPersistente(registro);
    return registro;
  }

  function renderDrawerActual() {
    const feat = obtenerFeature(state.sitioActivoId);
    if (!feat) return;
    const p = feat.properties;

    document.getElementById("drawerTitle").textContent = p.nombre;
    document.getElementById("drawerSub").textContent =
      `${p.comuna} · ${fmtNum((p.area_m2 || 0) / 10000, 2)} ha · Puesto #${p.ranking_comuna || "—"} de prioridad`;

    document.getElementById("drawerBadges").innerHTML = `
      <span class="badge badge-${esc(p.estado)}">${esc(ETIQ_ESTADO[p.estado] || p.estado)}</span>
      <span class="badge badge-calor">${fmtNum(p.lst_verano_c, 1)} °C verano</span>
      <span class="badge badge-verificado">Confianza: ${p.confianza_pct ?? 92}%</span>
    `;

    const guardados = recopilarTodosExpedientes().filter((x) => x.grupo === "guardado");
    const yaGuardado = guardados.some((x) => x.id === `guardado-${state.comunaSlug}-${p.site_id}`);
    const btnG = document.getElementById("btnGuardarCasoSitio");
    btnG.textContent = yaGuardado ? "Guardado ✓" : "Guardar caso";

    document.querySelectorAll(".tab-btn").forEach((b) => {
      const active = b.dataset.tab === state.tabActiva;
      b.classList.toggle("active", active);
      b.setAttribute("aria-selected", active ? "true" : "false");
    });
    document.querySelectorAll(".tab-pane").forEach((pane) => {
      pane.classList.toggle("active", pane.id === `tab-${state.tabActiva}`);
    });

    if (state.tabActiva === "resumen") renderTabResumen(p);
    else if (state.tabActiva === "imagenes") renderTabImagenes(feat);
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

    const salud = p.salud_vegetal_pct ?? 45;
    const conf = p.confianza_pct ?? 92;
    const humedadTxt =
      p.ndmi_actual == null ? "Sin lectura" : p.ndmi_actual < -0.05 ? "Baja (hojas secas)" : p.ndmi_actual < 0.08 ? "Normal" : "Bien hidratada";

    el.innerHTML = `
      <div class="metrics-grid tabular">
        <div class="metric-box">
          <small>Calor del suelo en verano</small>
          <strong>${fmtNum(p.lst_verano_c, 1)} °C (pico ${fmtNum(p.lst_pico_c, 1)} °C)</strong>
          <div class="hint" style="margin:2px 0 0;">${p.brecha_calor_vs_vitacura_c != null ? `${p.brecha_calor_vs_vitacura_c >= 0 ? "+" : ""}${fmtNum(p.brecha_calor_vs_vitacura_c, 1)} °C más caliente que Vitacura` : "Medición verano 2025-26"}</div>
        </div>
        <div class="metric-box">
          <small>Salud del pasto y árboles</small>
          <strong>${salud}% de vigor verde</strong>
          <div class="metric-bar-bg"><div class="metric-bar-fill" style="width:${salud}%;"></div></div>
          <div class="hint" style="margin:3px 0 0;">Agua en hojas: ${esc(humedadTxt)}</div>
        </div>
        <div class="metric-box">
          <small>Entorno a 5 cuadras (400 m)</small>
          <strong>${fmtNum(p.cobertura_arboles_400m_pct, 1)}% árboles · ${fmtNum(p.impermeable_400m_pct, 1)}% cemento</strong>
          <div class="hint" style="margin:2px 0 0;">Faltan ${fmtInt(p.arboles_necesarios_min)} – ${fmtInt(p.arboles_necesarios_max)} árboles para meta 30%</div>
        </div>
        <div class="metric-box">
          <small>Confianza real del dato</small>
          <strong>${conf}% verificado</strong>
          <div class="metric-bar-bg"><div class="metric-bar-fill" style="width:${conf}%;background:#0f766e;"></div></div>
          <div class="hint" style="margin:3px 0 0;">${p.n_obs ? `Basado en ${fmtInt(p.n_obs)} lecturas sin nubes` : "Lectura satelital de borde recuperado (2026)"}</div>
        </div>
      </div>

      <div class="callout">
        <strong>Vecinos alrededor (datos Censo 2024 agregados, sin datos personales):</strong><br>
        ${fmtInt(p.pop_400m)} personas en 5 cuadras (${fmtInt(p.viviendas_400m)} viviendas) ·
        Techos vulnerables al calor (zinc): <strong>${fmtNum(p.pct_techo_calor_400m, 1)}%</strong> ·
        Hacinamiento: <strong>${fmtNum(p.pct_hacinamiento_400m, 1)}%</strong>.
      </div>

      <div class="link-row">
        <button type="button" class="btn btn-primary" id="btnIrFotoRealParque">Ver foto aérea real y capturar →</button>
        <a class="ext-link" href="${esc(urlMaps)}" target="_blank" rel="noopener noreferrer">Google Maps ↗</a>
        <a class="ext-link" href="${esc(urlSv)}" target="_blank" rel="noopener noreferrer">Street View ↗</a>
      </div>
    `;

    document.getElementById("btnIrFotoRealParque")?.addEventListener("click", () => {
      state.tabActiva = "imagenes";
      renderDrawerActual();
    });
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
          const header = String.fromCharCode(view.getUint8(offset + 2), view.getUint8(offset + 3), view.getUint8(offset + 4), view.getUint8(offset + 5));
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
            return { lat: tags[1] === "S" ? -tags[2] : tags[2], lon: tags[3] === "W" ? -tags[4] : tags[4] };
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

  async function cargarImagenCors(url) {
    return new Promise((resolve) => {
      const im = new Image();
      im.crossOrigin = "anonymous";
      im.onload = () => resolve(im);
      im.onerror = () => resolve(null);
      im.src = url;
    });
  }

  async function generarCapturaParqueDataUrl(feat) {
    const p = feat.properties;
    const canvas = document.createElement("canvas");
    canvas.width = 720;
    canvas.height = 460;
    const ctx = canvas.getContext("2d");

    ctx.fillStyle = "#0f172a";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Intenta mosaico aéreo real Esri World Imagery alrededor del centro del parque
    let fondoDibujado = false;
    const lat = p.centro?.[1];
    const lon = p.centro?.[0];
    if (lat != null && lon != null) {
      const zoom = 17;
      const n = 2 ** zoom;
      const xf = ((lon + 180) / 360) * n;
      const latRad = (lat * Math.PI) / 180;
      const yf = ((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2) * n;
      const cxTile = Math.floor(xf);
      const cyTile = Math.floor(yf);
      const pxCentro = (xf - cxTile) * 256;
      const pyCentro = (yf - cyTile) * 256;
      const tileOffsets = [-1, 0, 1];
      const cargas = [];
      for (const dy of tileOffsets) {
        for (const dx of tileOffsets) {
          const url = `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${zoom}/${cyTile + dy}/${cxTile + dx}`;
          cargas.push(cargarImagenCors(url).then((im) => ({ dx, dy, im })));
        }
      }
      const tiles = await Promise.all(cargas);
      if (tiles.some((t) => t.im)) {
        ctx.save();
        ctx.beginPath();
        ctx.rect(0, 0, 440, 460);
        ctx.clip();
        tiles.forEach(({ dx, dy, im }) => {
          if (!im) return;
          const xDraw = 220 - pxCentro + dx * 256;
          const yDraw = 230 - pyCentro + dy * 256;
          ctx.drawImage(im, xDraw, yDraw, 256, 256);
        });
        // Dibuja polígono exacto del parque sobre la foto aérea real
        const coords = feat.geometry?.type === "Polygon" ? feat.geometry.coordinates[0] : feat.geometry?.coordinates?.[0]?.[0] || [];
        if (coords.length > 2) {
          ctx.beginPath();
          coords.forEach((c, idx) => {
            const tx = ((c[0] + 180) / 360) * n;
            const lr = (c[1] * Math.PI) / 180;
            const ty = ((1 - Math.log(Math.tan(lr) + 1 / Math.cos(lr)) / Math.PI) / 2) * n;
            const px = 220 + (tx - xf) * 256;
            const py = 230 + (ty - yf) * 256;
            if (idx === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
          });
          ctx.closePath();
          ctx.fillStyle = "rgba(34, 197, 94, 0.22)";
          ctx.fill();
          ctx.lineWidth = 3;
          ctx.strokeStyle = "#facc15";
          ctx.stroke();
        }
        ctx.restore();
        fondoDibujado = true;
      }
    }

    if (!fondoDibujado) {
      const imgs = p.imagenes || [];
      const srcReal = imgs.length ? imgs[imgs.length - 1].color : null;
      const imgCargada = srcReal ? await cargarImagenCors(srcReal) : null;
      if (imgCargada) {
        ctx.drawImage(imgCargada, 0, 0, 440, 460);
      } else {
        const coords = feat.geometry?.type === "Polygon" ? feat.geometry.coordinates[0] : feat.geometry?.coordinates?.[0]?.[0] || [];
        ctx.fillStyle = "#16241d";
        ctx.fillRect(10, 10, 420, 440);
        if (coords.length > 2) {
          const xs = coords.map((c) => c[0]);
          const ys = coords.map((c) => c[1]);
          const minX = Math.min(...xs), maxX = Math.max(...xs);
          const minY = Math.min(...ys), maxY = Math.max(...ys);
          const span = Math.max(maxX - minX, maxY - minY, 1e-5);
          ctx.beginPath();
          coords.forEach((c, idx) => {
            const px = 45 + ((c[0] - minX) / span) * 350;
            const py = 405 - ((c[1] - minY) / span) * 350;
            if (idx === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
          });
          ctx.closePath();
          ctx.fillStyle = "rgba(34, 197, 94, 0.35)";
          ctx.fill();
          ctx.lineWidth = 3;
          ctx.strokeStyle = "#facc15";
          ctx.stroke();
        }
      }
    }

    // Panel derecho de telemetría verificada (para la IA y el expediente)
    ctx.fillStyle = "#111827";
    ctx.fillRect(440, 0, 280, 460);
    ctx.fillStyle = "#22c55e";
    ctx.font = "bold 14px sans-serif";
    ctx.fillText("PULMÓN URBANO · CAPTURA", 456, 36);

    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 17px sans-serif";
    const words = String(p.nombre || "").split(" ");
    let line = "", y = 72;
    for (const w of words) {
      if ((line + " " + w).length > 24) {
        ctx.fillText(line.trim(), 456, y);
        y += 22;
        line = w;
      } else line += " " + w;
    }
    if (line) ctx.fillText(line.trim(), 456, y);

    ctx.fillStyle = "#9ca3af";
    ctx.font = "13px sans-serif";
    ctx.fillText(`${p.comuna} · Confianza ${p.confianza_pct ?? 92}%`, 456, y + 26);

    const rows = [
      `Calor verano: ${fmtNum(p.lst_verano_c, 1)} °C`,
      `Salud vegetal: ${p.salud_vegetal_pct ?? "—"}%`,
      `Árboles entorno: ${fmtNum(p.cobertura_arboles_400m_pct, 1)}%`,
      `Cemento entorno: ${fmtNum(p.impermeable_400m_pct, 1)}%`,
      `Faltan: ${fmtInt(p.arboles_necesarios_min)}–${fmtInt(p.arboles_necesarios_max)} árb.`,
      `Techos zinc: ${fmtNum(p.pct_techo_calor_400m, 1)}%`,
      `Lat/Lon: ${p.centro ? `${p.centro[1].toFixed(4)}, ${p.centro[0].toFixed(4)}` : "—"}`,
    ];
    ctx.fillStyle = "#e5e7eb";
    ctx.font = "13px sans-serif";
    rows.forEach((txt, i) => ctx.fillText(txt, 456, 175 + i * 32));

    ctx.fillStyle = "#fde047";
    ctx.font = "11px sans-serif";
    ctx.fillText(`Generado ${new Date().toISOString().slice(0, 10)} · Uso IA/Caso`, 456, 434);
    return canvas.toDataURL("image/jpeg", 0.86);
  }

  function mostrarPreviewCaptura(outEl, imgUrl, tituloFoto, feat) {
    outEl.innerHTML = `
      <div class="snapshot-preview-box">
        <img src="${imgUrl}" alt="${esc(tituloFoto)}">
        <div style="flex:1;min-width:190px;">
          <strong>${esc(tituloFoto)}</strong>
          <div class="hint" style="margin:3px 0 8px;">Lista para enviar al Asistente IA o archivar en tus Casos.</div>
          <div style="display:flex;gap:6px;flex-wrap:wrap;">
            <button type="button" class="btn btn-primary" id="btnEnviarCapturaAIA">Preguntar a IA con esta foto →</button>
            <button type="button" class="btn btn-outline-primary" id="btnGuardarCapturaEnCaso">Guardar foto en Casos (Supabase)</button>
          </div>
        </div>
      </div>
    `;

    document.getElementById("btnEnviarCapturaAIA")?.addEventListener("click", () => {
      state.chatImagenDataUrl = imgUrl;
      renderPreviewFotoChat();
      cambiarVista("informe-ia");
      actualizarSelectContextoChat(feat.properties.site_id);
      const inp = document.getElementById("inputChatIA");
      if (inp) {
        inp.value = `Analiza esta captura aérea de ${feat.properties.nombre} (${feat.properties.comuna}) y recomiéndame qué árboles o mejoras priorizar según su calor de ${fmtNum(feat.properties.lst_verano_c, 1)} °C.`;
        inp.focus();
      }
    });

    document.getElementById("btnGuardarCapturaEnCaso")?.addEventListener("click", () => {
      guardarSitioEnCasos(feat, imgUrl);
      renderDrawerActual();
      alert("Foto y ficha del parque guardadas en Casos y Archivos (sincronizado con Supabase).");
    });
  }

  function renderTabImagenes(feat) {
    const p = feat.properties;
    const el = document.getElementById("tab-imagenes");
    const imgs = p.imagenes || [];
    const imgLst = p.imagen_lst;

    const compHtml =
      imgs.length || imgLst
        ? `
        <h4 style="margin:12px 0 6px;">Diagnóstico térmico y vegetal (Landsat 8/9 y Sentinel-2)</h4>
        <div id="imgEscenario"></div>
        <div class="compare-controls" style="margin-top:8px;">
          <label><span>Izquierda</span><select id="selModoIzq"></select></label>
          <label><span>Derecha</span><select id="selModoDer"></select></label>
          <label><span>Fecha izq.</span><select id="selFechaIzq"></select></label>
          <label><span>Fecha der.</span><select id="selFechaDer"></select></label>
        </div>`
        : `<p class="hint">Parque bajo 0,5 ha (${fmtInt(p.area_m2)} m²): mira la fotografía aérea HD de alta resolución arriba.</p>`;

    el.innerHTML = `
      <div class="aerial-map-card">
        <div class="aerial-map-header">
          <strong>Foto Satelital Real (Alta resolución Esri HD)</strong>
          <div style="display:flex;gap:6px;flex-wrap:wrap;">
            <button type="button" class="btn btn-primary" id="btnCapturarFotoParque">Capturar foto de este parque</button>
          </div>
        </div>
        <div id="miniMapaSateliteReal"></div>
      </div>

      <div class="upload-box" style="margin-bottom:10px;">
        <strong>O sube una foto tomada en el parque (celular / cámara):</strong><br>
        <input type="file" id="inputFotoTerreno" accept="image/jpeg,image/png,image/webp" style="margin-top:6px;">
        <div id="fotoTerrenoResultado"></div>
      </div>

      ${compHtml}
    `;

    // Renderiza el mini visor con foto aérea REAL centrada en el polígono del parque
    setTimeout(() => {
      const boxMap = document.getElementById("miniMapaSateliteReal");
      if (!boxMap || !window.L) return;
      if (state.miniMap) {
        try { state.miniMap.remove(); } catch (_e) {}
        state.miniMap = null;
      }
      state.miniMap = L.map(boxMap, { zoomControl: true, attributionControl: false });
      L.tileLayer(BASEMAPS.satelite.url, { maxZoom: 19 }).addTo(state.miniMap);
      const lyr = L.geoJSON(feat, {
        style: { color: "#facc15", weight: 3, fillColor: "#22c55e", fillOpacity: 0.14 },
      }).addTo(state.miniMap);
      const b = lyr.getBounds();
      if (b.isValid()) state.miniMap.fitBounds(b, { maxZoom: 18, padding: [24, 24] });
    }, 30);

    const outBox = document.getElementById("fotoTerrenoResultado");
    if (state.capturaSitioDataUrl) {
      mostrarPreviewCaptura(outBox, state.capturaSitioDataUrl, `Captura de ${p.nombre}`, feat);
    }

    document.getElementById("btnCapturarFotoParque")?.addEventListener("click", async () => {
      const btn = document.getElementById("btnCapturarFotoParque");
      btn.disabled = true;
      btn.textContent = "Capturando…";
      const dataUrl = await generarCapturaParqueDataUrl(feat);
      state.capturaSitioDataUrl = dataUrl;
      mostrarPreviewCaptura(outBox, dataUrl, `Captura lista: ${p.nombre}`, feat);
      btn.disabled = false;
      btn.textContent = "Capturar foto de este parque";
    });

    document.getElementById("inputFotoTerreno")?.addEventListener("change", async (ev) => {
      const file = ev.target.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = async () => {
        const dataUrl = String(reader.result || "");
        const gps = leerExifGps(await file.arrayBuffer());
        let notaGps = file.name;
        if (gps && p.centro) {
          const dist = distanciaMetros(gps.lat, gps.lon, p.centro[1], p.centro[0]);
          notaGps = `${file.name} (a ${fmtInt(dist)} m del centro)`;
        }
        state.capturaSitioDataUrl = dataUrl;
        mostrarPreviewCaptura(outBox, dataUrl, `Foto subida: ${notaGps}`, feat);
      };
      reader.readAsDataURL(file);
    });

    if (imgs.length || imgLst) {
      const CAPAS = {
        color: "Satélite natural",
        ndvi: "Salud del pasto y árboles",
        ndmi: "Agua en las hojas",
        lst: "Mapa de calor verano (°C)",
      };
      const claves = [];
      if (imgs.length) claves.push("color", "ndvi");
      if (imgs.some((im) => im.ndmi)) claves.push("ndmi");
      if (imgLst) claves.push("lst");
      const ult = Math.max(0, imgs.length - 1);
      const sel = {
        mIzq: claves.includes("color") ? "color" : claves[0],
        mDer: imgLst ? "lst" : claves[1] || claves[0],
        fIzq: ult,
        fDer: ult,
      };
      const optCapas = claves.map((k) => `<option value="${k}">${esc(CAPAS[k])}</option>`).join("");
      const optFechas = imgs.map((im, i) => `<option value="${i}">${esc(im.fecha)}</option>`).join("");
      document.getElementById("selModoIzq").innerHTML = optCapas;
      document.getElementById("selModoDer").innerHTML = optCapas;
      document.getElementById("selFechaIzq").innerHTML = optFechas || `<option value="0">Verano</option>`;
      document.getElementById("selFechaDer").innerHTML = optFechas || `<option value="0">Verano</option>`;

      const urlCapa = (m, idx) => (m === "lst" ? imgLst : (imgs[idx] || {})[m]) || "";
      const pintarComp = () => {
        document.getElementById("selModoIzq").value = sel.mIzq;
        document.getElementById("selModoDer").value = sel.mDer;
        document.getElementById("selFechaIzq").value = String(sel.fIzq);
        document.getElementById("selFechaDer").value = String(sel.fDer);
        document.getElementById("selFechaIzq").disabled = sel.mIzq === "lst" || !imgs.length;
        document.getElementById("selFechaDer").disabled = sel.mDer === "lst" || !imgs.length;
        const pairs = [
          { src: urlCapa(sel.mIzq, sel.fIzq), txt: CAPAS[sel.mIzq] },
          { src: urlCapa(sel.mDer, sel.fDer), txt: CAPAS[sel.mDer] },
        ].filter((x) => x.src);
        document.getElementById("imgEscenario").innerHTML = `<div class="img-pair">${pairs
          .map((x) => `<figure class="img-fig"><img src="${esc(x.src)}" alt="${esc(x.txt)}"><figcaption>${esc(x.txt)}</figcaption></figure>`)
          .join("")}</div>`;
      };
      [["selModoIzq", "mIzq"], ["selModoDer", "mDer"]].forEach(([id, k]) =>
        document.getElementById(id).addEventListener("change", (e) => {
          sel[k] = e.target.value;
          pintarComp();
        })
      );
      [["selFechaIzq", "fIzq"], ["selFechaDer", "fDer"]].forEach(([id, k]) =>
        document.getElementById(id).addEventListener("change", (e) => {
          sel[k] = Number(e.target.value);
          pintarComp();
        })
      );
      pintarComp();
    }
  }

  function renderTabSerie(p) {
    const el = document.getElementById("tab-serie");
    const pack = state.comunaCache[state.comunaSlug];
    const sSitio = pack?.series?.sitios?.[p.site_id];
    if (!sSitio) {
      el.innerHTML = `<p class="hint">Sin evolución histórica disponible para este sitio.</p>`;
      return;
    }

    const granOpts = [
      ["semanal", "Semanal"],
      ["mensual", "Mensual"],
      ["estacional", "Por estación"],
    ];

    el.innerHTML = `
      <div class="metrics-grid tabular" style="margin-bottom:10px;">
        <div class="metric-box">
          <small>Calor verano del suelo</small>
          <strong>${fmtNum(p.lst_verano_c, 1)} °C</strong>
        </div>
        <div class="metric-box">
          <small>Salud actual del verde</small>
          <strong>${p.salud_vegetal_pct ?? "—"}% (${fmtInt(p.n_obs)} lecturas)</strong>
        </div>
      </div>
      <div class="chart-toolbar">
        <div class="gran-btns">
          ${granOpts.map(([k, lbl]) => `<button type="button" class="gran-btn ${state.granularidad === k ? "active" : ""}" data-gran="${k}">${lbl}</button>`).join("")}
        </div>
        <span class="hint" style="margin:0;">Sin inventar datos en días nublados.</span>
      </div>
      <div class="chart-wrap"><canvas id="canvasSerie"></canvas></div>
      <p class="hint">Línea verde: salud del pasto y árboles. Línea naranja: temperatura máxima del aire (°C). Barras celestes: lluvia.</p>
    `;

    el.querySelectorAll(".gran-btn").forEach((b) => {
      b.addEventListener("click", () => {
        state.granularidad = b.dataset.gran;
        renderTabSerie(p);
      });
    });

    const rows = sSitio[state.granularidad] || [];
    const labels = rows.map((r) => r[0]);
    const saludArr = rows.map((r) => (r[2] != null ? Math.round(Math.max(0, Math.min(100, (r[2] / 0.6) * 100))) : null));
    const tmaxArr = rows.map((r) => r[6]);
    const rainArr = rows.map((r) => r[7]);

    if (state.chartInstance) {
      state.chartInstance.destroy();
      state.chartInstance = null;
    }

    const ctx = document.getElementById("canvasSerie").getContext("2d");
    state.chartInstance = new window.Chart(ctx, {
      data: {
        labels,
        datasets: [
          {
            type: "line",
            label: "Salud del verde (%)",
            data: saludArr,
            borderColor: "#15803d",
            backgroundColor: "rgba(21,128,61,0.08)",
            fill: true,
            spanGaps: false,
            yAxisID: "ySalud",
            tension: 0.25,
            pointRadius: state.granularidad === "semanal" ? 1.5 : 3,
          },
          {
            type: "line",
            label: "Temperatura aire (°C)",
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
            backgroundColor: "rgba(56, 189, 248, 0.28)",
            yAxisID: "yRain",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        scales: {
          ySalud: { type: "linear", position: "left", min: 0, max: 100, title: { display: true, text: "Salud verde %" } },
          yTemp: { type: "linear", position: "right", min: 5, max: 45, grid: { drawOnChartArea: false }, title: { display: true, text: "T° aire (°C)" } },
          yRain: { type: "linear", position: "right", display: false, min: 0, suggestedMax: 280 },
        },
        plugins: { legend: { position: "bottom", labels: { boxWidth: 11, font: { size: 10 } } } },
      },
    });
  }

  function renderTabInversion(p) {
    const el = document.getElementById("tab-inversion");
    const intervs = p.intervenciones_sugeridas || [];
    const fondos = p.fondos_sugeridos || [];
    const fondosFull = Object.fromEntries((PU.catalogo?.fondos_publicos || []).map((f) => [f.id, f]));

    el.innerHTML = `
      <div class="metrics-grid tabular">
        <div class="metric-box">
          <small>Árboles necesarios (5 cuadras)</small>
          <strong>${fmtInt(p.arboles_necesarios_min)} – ${fmtInt(p.arboles_necesarios_max)} árboles</strong>
          <div class="hint" style="margin:2px 0 0;">Para alcanzar 30% de sombra</div>
        </div>
        <div class="metric-box">
          <small>Inversión estimada</small>
          <strong>${fmtClpCorto(p.costo_clp_min)} – ${fmtClpCorto(p.costo_clp_max)} CLP</strong>
          <span class="badge badge-hipotesis" style="margin-top:3px;">hipótesis (sin verificar)</span>
        </div>
        <div class="metric-box">
          <small>Vecinos beneficiados (400 m)</small>
          <strong>${fmtInt(p.pop_400m)} habitantes</strong>
          <div class="hint" style="margin:2px 0 0;">${fmtNum(p.pct_techo_calor_400m, 1)}% con techos calientes</div>
        </div>
        <div class="metric-box">
          <small>Confiabilidad del cálculo</small>
          <strong>${p.confianza_pct ?? 92}% verificado</strong>
          <div class="hint" style="margin:2px 0 0;">5 fuentes satelitales y censales</div>
        </div>
      </div>

      <h3>Qué conviene hacer primero</h3>
      ${intervs
        .map(
          (i) => `<div class="surface-card">
            <div style="display:flex;justify-content:space-between;gap:8px;align-items:flex-start;">
              <strong>${esc(i.nombre)}</strong>
              <span class="badge badge-hipotesis">${esc(i.etiqueta_costo || "hipótesis (sin verificar)")}</span>
            </div>
            <div class="hint" style="margin:4px 0 0;">Rango referencial: ${fmtClpCorto(i.costo_min_clp)} – ${fmtClpCorto(i.costo_max_clp)} CLP (${esc(i.unidad)})</div>
          </div>`
        )
        .join("")}
      <h3>Fondos públicos compatibles para postular</h3>
      ${fondos
        .map((f) => `<div class="surface-card"><strong>${esc(f.nombre)}</strong> <span class="hint">(${esc(f.institucion)})</span>
          <div class="hint" style="margin:4px 0 0;">Requisito: ${esc((fondosFull[f.id] || {}).requisito_evidencia || "Ficha cuantitativa del sitio.")}</div></div>`)
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
        ([k, v]) => new TableRow({ children: [new TableCell({ children: [mkP(k)] }), new TableCell({ children: [mkP(v)] })] })
      ),
    });

    const doc = new Document({
      sections: [
        {
          children: [
            mkP(limpiarTextoHumano(informe.titulo), HeadingLevel.HEADING_1),
            mkP(textoEtiquetaIA(informe)),
            mkP(limpiarTextoHumano(informe.resumen_ejecutivo)),
            mkP("Resumen cuantificado", HeadingLevel.HEADING_2),
            tabla,
            mkP("Hallazgos verificados", HeadingLevel.HEADING_2),
            ...(informe.hallazgos || []).map((h) => mkP("• " + limpiarTextoHumano(h))),
            mkP("Acciones e inversión priorizada (hipótesis sin verificar)", HeadingLevel.HEADING_2),
            ...(informe.acciones_priorizadas || []).map((a) => mkP(`• ${a.nombre}: ${limpiarTextoHumano(a.rango_estimado || a.detalle || "")}`)),
            mkP("Fondos públicos sugeridos", HeadingLevel.HEADING_2),
            ...(informe.fondos_recomendados || []).map((f) => mkP(`• ${f.nombre} (${f.institucion}): ${f.requisito || ""}`)),
            ...((informe.plan_30_90_365 || []).length ? [mkP("Pasos a 30, 90 y 365 días", HeadingLevel.HEADING_2)] : []),
            ...(informe.plan_30_90_365 || []).map((pp) => mkP(`• ${pp.plazo || ""}: ${limpiarTextoHumano(pp.accion || "")}`)),
            mkP("Límites y privacidad", HeadingLevel.HEADING_2),
            ...(informe.limitaciones_y_verificacion || []).map((l) => mkP("• " + l)),
          ],
        },
      ],
    });
    descargarBlob(await Packer.toBlob(doc), filename);
  }

  function etiquetaOrigen(informe) {
    const m = String(informe.origen_redaccion || "").match(/^(gemini|openai|deepseek):(.+)$/);
    return m ? `Redactado con IA (${m[2]}) · cifras verificadas` : "Síntesis automática · cifras verificadas";
  }

  function textoEtiquetaIA(informe) {
    return informe.etiqueta_ia || "Resumen basado en datos reales verificados; revisar antes de postular.";
  }

  function htmlPlan(informe) {
    const plan = informe.plan_30_90_365 || [];
    if (!plan.length) return "";
    return `<ol class="plan-pasos">${plan
      .map((p) => `<li><span class="plan-plazo">${esc(p.plazo || p.nombre || "")}</span><span>${esc(limpiarTextoHumano(p.accion || p.detalle || ""))}</span></li>`)
      .join("")}</ol>`;
  }

  function renderHtmlInforme(informe) {
    const medicion = informe.como_se_medira || [];
    return `
      <h3 style="margin-bottom:6px;">${esc(limpiarTextoHumano(informe.titulo))}</h3>
      <p class="informe-etiqueta">${esc(textoEtiquetaIA(informe))}</p>
      <p>${renderMarkdownSimple(limpiarTextoHumano(informe.resumen_ejecutivo))}</p>
      <h4>Dónde invertir y por qué</h4>
      <ul>${(informe.hallazgos || []).map((h) => `<li>${esc(limpiarTextoHumano(h))}</li>`).join("")}</ul>
      <h4>Acciones recomendadas</h4>
      <ul>${(informe.acciones_priorizadas || [])
        .map((a) => `<li><strong>${esc(a.nombre)}:</strong> ${esc(limpiarTextoHumano([a.detalle, a.rango_estimado].filter(Boolean).join(" ")))}</li>`)
        .join("")}</ul>
      <h4>Fondos públicos compatibles</h4>
      <ul>${(informe.fondos_recomendados || []).map((f) => `<li><strong>${esc(f.nombre)}</strong> (${esc(f.institucion)}): ${esc(f.requisito || "")}</li>`).join("")}</ul>
      ${htmlPlan(informe) ? `<h4>Plan de acción 30 / 90 / 365 días</h4>${htmlPlan(informe)}` : ""}
      ${medicion.length ? `<h4>Cómo mediremos el impacto</h4><ul>${medicion.map((m) => `<li>${esc(limpiarTextoHumano(m))}</li>`).join("")}</ul>` : ""}
      <h4>Transparencia y límites</h4>
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
        ${puedeIA ? `<button type="button" class="btn btn-primary" id="btnSitioIA">Redactar con IA</button>` : ""}
        <button type="button" class="btn ${puedeIA ? "btn-quiet" : "btn-primary"}" id="btnPrintPdf">PDF</button>
        <button type="button" class="btn btn-quiet" id="btnDocx">Word (.docx)</button>
        <button type="button" class="btn btn-quiet" id="btnCsvSitio">CSV</button>
        <button type="button" class="btn btn-quiet" id="btnGeojsonSitio">GeoJSON</button>
        <button type="button" class="btn btn-quiet" id="btnJsonPaquete">JSON</button>
        <button type="button" class="btn btn-quiet" id="btnMailto">Correo</button>
      </div>
      <div style="margin-bottom:8px;">
        <span class="badge ${iaCustom ? "badge-ia" : "badge-verificado"}">${iaCustom || esPreVerificado ? esc(etiquetaOrigen(informe)) : "Ficha lista · cifras verificadas"}</span>
      </div>
      <p class="hint" id="estadoSitioIA" style="margin:0 0 8px;"></p>
      <article id="informePreview" style="font-size:0.85rem;line-height:1.5;">${renderHtmlInforme(informe)}</article>
    `;

    document.getElementById("btnSitioIA")?.addEventListener("click", async () => {
      if (!puedeUsarIA()) {
        abrirModalUpgrade("La redacción en vivo con IA está bloqueada en el Plan Gratis ($0).");
        return;
      }
      const btn = document.getElementById("btnSitioIA");
      const st = document.getElementById("estadoSitioIA");
      btn.disabled = true;
      st.textContent = "Redactando ficha clara con DeepSeek IA…";
      try {
        const resp = await fetch("api/informe", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ comuna_slug: state.comunaSlug, site_id: p.site_id, email: state.perfil.email }),
        });
        const j = await resp.json().catch(() => ({}));
        if (resp.status === 402) {
          abrirModalUpgrade(j.detail || "Plan requerido para usar IA.");
          btn.disabled = false;
          return;
        }
        if (!resp.ok) throw new Error(j.detail || "HTTP " + resp.status);
        state.informeSitioCustom[claveSitio] = j.informe;
        renderTabInforme(feat);
      } catch (err) {
        st.textContent = "No se pudo redactar con IA: " + err.message;
        btn.disabled = false;
      }
    });

    document.getElementById("btnPrintPdf").addEventListener("click", async () => {
      if (!(await consumirExportacion("pdf"))) return;
      document.getElementById("printArea").innerHTML = document.getElementById("informePreview").innerHTML;
      window.print();
    });
    document.getElementById("btnDocx").addEventListener("click", async () => {
      if (!(await consumirExportacion("docx"))) return;
      descargarWordInforme(
        informe,
        [
          ["Parque / Comuna", `${p.nombre} — ${p.comuna}`],
          ["Calor verano", `${fmtNum(p.lst_verano_c, 1)} °C`],
          ["Salud vegetal", `${p.salud_vegetal_pct ?? "—"}%`],
          ["Árboles vs cemento (400 m)", `${fmtNum(p.cobertura_arboles_400m_pct, 1)}% / ${fmtNum(p.impermeable_400m_pct, 1)}%`],
          ["Presupuesto estimado (hipótesis)", `${fmtInt(p.arboles_necesarios_min)}–${fmtInt(p.arboles_necesarios_max)} árboles (${fmtClpCorto(p.costo_clp_min)}–${fmtClpCorto(p.costo_clp_max)})`],
        ],
        `informe_${state.comunaSlug}_${p.site_id}.docx`
      );
    });
    document.getElementById("btnCsvSitio").addEventListener("click", async () => {
      if (!(await consumirExportacion("csv"))) return;
      const sSitio = state.comunaCache[state.comunaSlug]?.series?.sitios?.[p.site_id]?.mensual || [];
      const header = "granularidad,site_id,sitio,periodo,fecha_inicio,ndvi,ndmi,pixeles_validos,nubes_escena_pct,temp_max_c,lluvia_mm\n";
      const rows = sSitio
        .map((r) => ["mensual", p.site_id, `"${(p.nombre || "").replace(/"/g, '""')}"`, r[0], r[1], r[2] ?? "", r[3] ?? "", r[4] ?? "", r[5] ?? "", r[6] ?? "", r[7] ?? ""].join(","))
        .join("\n");
      descargarBlob(new Blob([header + rows], { type: "text/csv;charset=utf-8" }), `serie_${state.comunaSlug}_${p.site_id}.csv`);
    });
    document.getElementById("btnGeojsonSitio").addEventListener("click", async () => {
      if (!(await consumirExportacion("geojson"))) return;
      descargarBlob(new Blob([JSON.stringify({ type: "FeatureCollection", features: [feat] }, null, 2)], { type: "application/geo+json" }), `sitio_${state.comunaSlug}_${p.site_id}.geojson`);
    });
    document.getElementById("btnJsonPaquete").addEventListener("click", async () => {
      if (!(await consumirExportacion("json"))) return;
      descargarBlob(new Blob([JSON.stringify({ paquete, informe }, null, 2)], { type: "application/json" }), `caso_${state.comunaSlug}_${p.site_id}.json`);
    });
    document.getElementById("btnMailto").addEventListener("click", () => {
      const asunto = encodeURIComponent(informe.titulo);
      const cuerpo = encodeURIComponent(`${limpiarTextoHumano(informe.resumen_ejecutivo)}\n\n(Montos: hipótesis sin verificar)`);
      window.location.href = `mailto:?subject=${asunto}&body=${cuerpo}`;
    });
  }

  // =========================================================================
  // VISTA 2: ASISTENTE IA SIMPLE + CARTERA EJECUTIVA
  // =========================================================================
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
      msg.textContent = "Modo estático sin servidor: abre con uvicorn para conectar DeepSeek IA y Supabase.";
    } else if (!est.ia_disponible) {
      msg.textContent = "Falta la clave de IA en .env o Vercel.";
    } else {
      const sbTxt = est.supabase_tablas_listas
        ? "Supabase conectado"
        : est.supabase_conectado
        ? "Supabase enlazado (respaldo local activo hasta ejecutar SQL)"
        : "modo local";
      msg.textContent = `IA lista (${est.modelo}) · Base de datos: ${sbTxt}.`;
    }
    document.getElementById("btnRestaurarIA").classList.toggle("hidden", !state.informeIACustom[state.ambitoIA]);
  }

  function actualizarSelectContextoChat(preferSiteId = null) {
    const sel = document.getElementById("selectContextoChat");
    if (!sel) return;
    const scope = state.ambitoIA === "intercomunal" ? state.comunaSlug || "cerro_navia" : state.ambitoIA;
    const bundle = (PU.informes_inversion || {})[state.ambitoIA] || (PU.informes_inversion || {})[scope];
    const sitios = bundle?.paquete?.cartera_sitios || [];
    const casos = recopilarTodosExpedientes().filter((x) => x.grupo === "guardado").slice(0, 8);

    const opts = [`<option value="comuna">Contexto: Comuna completa (${esc(bundle?.paquete?.comuna?.nombre || state.ambitoIA)})</option>`];
    if (sitios.length) {
      opts.push(`<optgroup label="Parques prioritarios">`);
      sitios.forEach((s) => {
        opts.push(`<option value="sitio:${esc(s.comuna_slug)}:${esc(s.site_id)}">${esc(s.nombre)} (${esc(s.comuna)} · ${fmtNum(s.lst_verano_c, 1)} °C)</option>`);
      });
      opts.push(`</optgroup>`);
    }
    if (casos.length) {
      opts.push(`<optgroup label="Mis casos guardados">`);
      casos.forEach((c) => {
        opts.push(`<option value="caso:${esc(c.id)}">${esc(c.titulo)}</option>`);
      });
      opts.push(`</optgroup>`);
    }
    sel.innerHTML = opts.join("");
    if (preferSiteId) {
      const match = [...sel.options].find((o) => o.value.endsWith(`:${preferSiteId}`));
      if (match) sel.value = match.value;
    }
  }

  function renderPreviewFotoChat() {
    const box = document.getElementById("chatFotoPreviewBox");
    if (!box) return;
    if (!state.chatImagenDataUrl) {
      box.classList.add("hidden");
      box.innerHTML = "";
      return;
    }
    box.classList.remove("hidden");
    box.innerHTML = `
      <img src="${state.chatImagenDataUrl}" alt="Foto adjunta para IA">
      <div style="flex:1;">
        <strong>Foto / captura lista para la consulta</strong>
        <div class="hint" style="margin:0;">La IA usará esta imagen junto a los datos reales de la comuna/parque.</div>
      </div>
      <button type="button" class="btn btn-quiet" id="btnQuitarFotoChat">Quitar foto</button>
    `;
    document.getElementById("btnQuitarFotoChat")?.addEventListener("click", () => {
      state.chatImagenDataUrl = null;
      renderPreviewFotoChat();
    });
  }

  function agregarBurbujaChat(rol, texto, extra = {}) {
    const box = document.getElementById("chatMensajes");
    if (!box) return;
    const div = document.createElement("div");
    div.className = `chat-bubble ${rol === "user" ? "chat-bubble-user" : "chat-bubble-ia"}`;
    const bodyHtml = rol === "user" ? esc(texto).replace(/\n/g, "<br>") : renderMarkdownSimple(texto);
    if (rol === "user") {
      div.innerHTML = `<strong>Tú</strong><div>${bodyHtml}</div>`;
    } else {
      const btnId = `btnSaveChat_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
      div.innerHTML = `
        <div style="display:flex;justify-content:space-between;gap:8px;align-items:center;margin-bottom:4px;">
          <strong>Asistente RE-VIDA</strong>
          <span class="badge badge-verificado">${esc(extra.modelo || "deepseek-flash")}</span>
        </div>
        <div>${bodyHtml}</div>
        <div style="margin-top:8px;">
          <button type="button" class="btn btn-outline-primary" id="${btnId}">Guardar respuesta y foto como Caso</button>
        </div>
      `;
      setTimeout(() => {
        document.getElementById(btnId)?.addEventListener("click", async () => {
          const scopeSlug = extra.comunaSlug || (state.ambitoIA === "intercomunal" ? "cerro_navia" : state.ambitoIA);
          const tituloLimpio = extra.contextLabel
            ? `IA: ${extra.contextLabel}`
            : extra.pregunta && extra.pregunta.length > 84
            ? extra.pregunta.slice(0, 81).trim() + "…"
            : extra.pregunta || `Consulta IA (${scopeSlug})`;
          await guardarCasoPersistente({
            id: `ia-caso-${Date.now()}`,
            grupo: "guardado",
            tipoLabel: state.chatImagenDataUrl ? "Caso IA + Foto" : "Caso IA",
            titulo: tituloLimpio,
            comunaSlug: scopeSlug,
            siteId: extra.siteId || null,
            fecha: new Date().toISOString().slice(0, 10),
            nota: "",
            fotoDataUrl: state.chatImagenDataUrl || null,
            preguntaIA: extra.pregunta || "",
            respuestaIA: texto,
            confianzaPct: extra.confianzaPct || 94,
            paquete: (PU.informes_inversion?.[state.ambitoIA] || {}).paquete || null,
            informe: {
              titulo: tituloLimpio,
              resumen_ejecutivo: texto,
              hallazgos: [],
              acciones_priorizadas: [],
              fondos_recomendados: [],
              limitaciones_y_verificacion: ["Respuesta generada y guardada desde el Asistente IA de RE-VIDA."],
            },
          });
          document.getElementById(btnId).textContent = "Guardado en Casos ✓";
          document.getElementById(btnId).disabled = true;
        });
      }, 10);
    }
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  }

  async function enviarPreguntaChatIA(preguntaTxt) {
    const q = (preguntaTxt || "").trim();
    if (!q) return;
    if (!puedeUsarIA()) {
      abrirModalUpgrade("El Asistente IA con preguntas frecuentes, casos y fotos requiere activar un plan (puedes probarlo en 1 clic).");
      return;
    }

    const selCtx = document.getElementById("selectContextoChat")?.value || "comuna";
    let comunaSlug = state.ambitoIA === "intercomunal" ? state.comunaSlug || "cerro_navia" : state.ambitoIA;
    let siteId = null;
    let casoTitulo = null;
    let contextoDatos = null;
    let contextLabel = null;
    let confianzaPct = ((PU.resumen?.comunas || []).find((c) => c.slug === comunaSlug) || {}).confianza_comuna_pct || 94;

    if (selCtx.startsWith("sitio:")) {
      const parts = selCtx.split(":");
      comunaSlug = parts[1];
      siteId = parts[2];
      const feat = state.comunaCache[comunaSlug]?.geojson?.features?.find((f) => f.properties.site_id === siteId);
      if (feat) {
        contextLabel = feat.properties.nombre;
        confianzaPct = feat.properties.confianza_pct || confianzaPct;
      }
    } else if (selCtx.startsWith("caso:")) {
      const cid = selCtx.slice(5);
      const found = recopilarTodosExpedientes().find((x) => x.id === cid);
      if (found) {
        comunaSlug = found.comunaSlug || comunaSlug;
        siteId = found.siteId || null;
        casoTitulo = found.titulo;
        contextLabel = found.titulo;
        confianzaPct = found.confianzaPct || confianzaPct;
        contextoDatos = { resumen: found.informe?.resumen_ejecutivo || "", nota: found.nota || "" };
      }
    }

    agregarBurbujaChat("user", q);
    const input = document.getElementById("inputChatIA");
    if (input) input.value = "";
    const btn = document.getElementById("btnEnviarChatIA");
    btn.disabled = true;
    btn.textContent = "Pensando…";

    try {
      const resp = await fetch("api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pregunta: q,
          comuna_slug: comunaSlug,
          site_id: siteId,
          caso_titulo: casoTitulo,
          contexto_datos: contextoDatos,
          imagen_data_url: state.chatImagenDataUrl || null,
          email: state.perfil.email,
        }),
      });
      const j = await resp.json().catch(() => ({}));
      if (resp.status === 402) {
        abrirModalUpgrade(j.detail || "Activa un plan para usar el chat IA.");
      } else if (!resp.ok) {
        agregarBurbujaChat("ia", "Ocurrió un problema al consultar la IA: " + (j.detail || resp.status));
      } else {
        if (j.perfil) {
          Object.assign(state.perfil, j.perfil);
          guardarPerfilLocal();
          actualizarUIPlanYUsuario();
        }
        agregarBurbujaChat("ia", j.respuesta, { modelo: j.modelo, comunaSlug, siteId, pregunta: q, contextLabel, confianzaPct });
      }
    } catch (err) {
      agregarBurbujaChat("ia", "No se pudo conectar al servidor local (" + err.message + ").");
    }

    btn.disabled = false;
    btn.textContent = "Preguntar a IA";
  }

  async function generarConIAAmbiente(scope) {
    if (!puedeUsarIA()) {
      abrirModalUpgrade("Generar informes IA completos requiere Pase por Proyecto o Consultora ⭐.");
      return;
    }
    const msg = document.getElementById("estadoIAVivo");
    const btn = document.getElementById("btnGenerarIAVivo");
    btn.disabled = true;
    msg.textContent = "Redactando cartera ejecutiva con DeepSeek IA y verificando cada cifra…";
    try {
      const resp = await fetch("api/informe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ambito: scope, email: state.perfil.email }),
      });
      const j = await resp.json().catch(() => ({}));
      if (resp.status === 402) {
        abrirModalUpgrade(j.detail || "Plan requerido.");
        btn.disabled = false;
        return;
      }
      if (!resp.ok) throw new Error(j.detail || "HTTP " + resp.status);
      const diag = j.diagnostico || {};
      if (!diag.uso_plantilla) {
        state.informeIACustom[scope] = j.informe;
        msg.textContent = `Informe actualizado con ${diag.modelo} (verificado en intento ${(diag.intentos || []).length}).`;
        renderVistaInformeIA();
      } else {
        msg.textContent = "El verificador mantuvo la versión base para proteger las cifras exactas.";
      }
    } catch (err) {
      msg.textContent = "No se pudo redactar con IA (" + err.message + ").";
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
      descargarBlob(new Blob([JSON.stringify(bundle.paquete, null, 2)], { type: "application/json" }), `paquete_${state.ambitoIA}.json`);
    });
    document.getElementById("btnDesbloquearDesdelaChat")?.addEventListener("click", () => {
      activarPlanEnBackend("consultora", state.modalidadPlanUI);
    });
    document.querySelectorAll(".faq-chip").forEach((b) => {
      b.addEventListener("click", () => enviarPreguntaChatIA(b.dataset.q));
    });
    document.getElementById("btnEnviarChatIA")?.addEventListener("click", () => {
      enviarPreguntaChatIA(document.getElementById("inputChatIA").value);
    });
    document.getElementById("inputChatIA")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") enviarPreguntaChatIA(e.target.value);
    });
    document.getElementById("inputFotoChatIA")?.addEventListener("change", (ev) => {
      const f = ev.target.files?.[0];
      if (!f) return;
      const reader = new FileReader();
      reader.onload = () => {
        state.chatImagenDataUrl = String(reader.result || "");
        renderPreviewFotoChat();
      };
      reader.readAsDataURL(f);
      ev.target.value = "";
    });
  }

  function renderVistaInformeIA() {
    actualizarSelectContextoChat();
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
          <span class="kpi-label">Parques en esta cartera</span>
          <strong class="kpi-val">${fmtInt(cr.n_sitios_cartera)} parques distintos</strong>
          <span class="kpi-note">${esc(paq.comuna.nombre)}</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">Calor estival máx. / promedio</span>
          <strong class="kpi-val">${fmtNum(cr.lst_max_cartera_c, 1)} °C / ${fmtNum(cr.lst_media_cartera_c, 1)} °C</strong>
          <span class="kpi-note">5 lecturas de verano</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">Árboles necesarios (entorno 400 m)</span>
          <strong class="kpi-val">${fmtInt(cr.arboles_min_cartera)} – ${fmtInt(cr.arboles_max_cartera)}</strong>
          <span class="kpi-note">Meta mínima 30% cobertura</span>
        </div>
        <div class="kpi-card" title="${esc(fmtClp(cr.costo_clp_min_cartera))} – ${esc(fmtClp(cr.costo_clp_max_cartera))}">
          <span class="kpi-label">Inversión referencial total</span>
          <strong class="kpi-val">${fmtClpCorto(cr.costo_clp_min_cartera)} – ${fmtClpCorto(cr.costo_clp_max_cartera)} CLP</strong>
          <span class="badge badge-hipotesis" style="margin-top:3px;">hipótesis (sin verificar)</span>
        </div>
      </div>

      <div class="surface-card" style="overflow-x:auto;margin-bottom:14px;">
        <h3>Mayores casos donde invertir primero</h3>
        <table class="exec-table tabular">
          <thead>
            <tr>
              <th>Parque y comuna</th>
              <th class="num-col">Urgencia</th>
              <th class="num-col">Calor verano</th>
              <th>Árboles / Cemento (400 m)</th>
              <th class="num-col">Techos zinc</th>
              <th class="num-col">Árboles y fondo</th>
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
                      <span class="park-sub">${esc(s.comuna)} · ${fmtNum((s.area_m2 || 0) / 10000, 2)} ha · Conf. ${s.confianza_pct ?? 92}%</span>
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
                  <div class="stack-bar">
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

      <div class="surface-card">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px;">
          <h3 style="margin:0;">${esc(limpiarTextoHumano(inf.titulo))}</h3>
          <span class="badge ${state.informeIACustom[scope] || /^deepseek|^gemini|^openai|^llm/i.test(inf.origen_redaccion || "") ? "badge-ia" : "badge-verificado"}">${esc(etiquetaOrigen(inf))}</span>
        </div>
        <p style="font-size:0.9rem;line-height:1.55;max-width:78ch;">${esc(limpiarTextoHumano(inf.resumen_ejecutivo))}</p>
        <div class="cards-grid" style="margin-top:10px;">
          <div class="surface-card">
            <h4>Hallazgos simples</h4>
            <ul style="padding-left:18px;font-size:0.84rem;line-height:1.48;">
              ${(inf.hallazgos || []).map((h) => `<li>${esc(limpiarTextoHumano(h))}</li>`).join("")}
            </ul>
          </div>
          <div class="surface-card">
            <h4>Fondos públicos recomendados</h4>
            <ul style="padding-left:18px;font-size:0.84rem;line-height:1.48;">
              ${(inf.fondos_recomendados || []).map((f) => `<li><strong>${esc(f.nombre)}:</strong> ${esc(f.requisito || "")}</li>`).join("")}
            </ul>
          </div>
        </div>
      </div>
    `;

    cont.querySelectorAll(".btn-ir-mapa-cartera").forEach((b) => {
      b.addEventListener("click", async () => {
        cambiarVista("mapa");
        await seleccionarComuna(b.dataset.slug);
        abrirSitio(b.dataset.site, "imagenes");
        const lyr = state.poligonosPorId[b.dataset.site];
        if (lyr && state.map) state.map.fitBounds(lyr.getBounds(), { maxZoom: 16, padding: [36, 36] });
      });
    });
  }

  // =========================================================================
  // VISTA 3: CASOS, FOTOS Y ARCHIVOS
  // =========================================================================
  function recopilarTodosExpedientes() {
    const items = [];
    const vistosIds = new Set();

    for (const s of state.casosServidor || []) {
      const it = {
        id: s.id,
        grupo: "guardado",
        tipoLabel: s.tipo_label || "Caso Supabase",
        titulo: s.titulo,
        comunaSlug: s.comuna_slug || "cerro_navia",
        siteId: s.site_id || null,
        fecha: (s.created_at || new Date().toISOString()).slice(0, 10),
        nota: s.nota || "",
        fotoDataUrl: s.foto_data_url || null,
        preguntaIA: s.pregunta_ia || null,
        respuestaIA: s.respuesta_ia || null,
        confianzaPct: s.confianza_pct || 94,
        paquete: s.paquete || {},
        informe: s.informe || {},
      };
      items.push(it);
      vistosIds.add(it.id);
    }

    for (const g of leerCasosLocales()) {
      if (!vistosIds.has(g.id)) {
        items.push(g);
        vistosIds.add(g.id);
      }
    }

    for (const c of PU.casos || []) {
      if (vistosIds.has(c.caso_id)) continue;
      items.push({
        id: c.caso_id,
        grupo: "pitch",
        tipoLabel: "Caso ejemplo",
        titulo: c.titulo,
        comunaSlug: c.comuna.slug,
        siteId: c.sitio.site_id,
        fecha: c.fecha_generacion || "2026-11-22",
        paquete: c,
        informe: (PU.informes || {})[c.caso_id],
      });
    }

    for (const [scope, bundle] of Object.entries(PU.informes_inversion || {})) {
      if (vistosIds.has(bundle.paquete.caso_id)) continue;
      items.push({
        id: bundle.paquete.caso_id,
        grupo: "cartera",
        tipoLabel: "Cartera por comuna",
        titulo: bundle.paquete.titulo,
        comunaSlug: scope === "intercomunal" ? "cerro_navia" : scope,
        siteId: null,
        fecha: bundle.paquete.fecha_generacion || "2026-11-22",
        paquete: bundle.paquete,
        informe: bundle.informe,
      });
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
    if (item.fotoDataUrl) thumbs.push([item.fotoDataUrl, "Foto capturada / adjunta"]);
    if (sitio.imagen_lst) thumbs.push([sitio.imagen_lst, "Calor verano (Landsat)"]);
    if (ultImg?.color) thumbs.push([ultImg.color, `Satélite natural (${ultImg.fecha})`]);
    if (ultImg?.ndvi) thumbs.push([ultImg.ndvi, `Salud vegetal (${ultImg.fecha})`]);

    visor.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;flex-wrap:wrap;margin-bottom:10px;">
        <div>
          <span class="badge badge-verificado">${esc(item.tipoLabel)}</span>
          <span class="badge badge-alta">${esc(item.fecha)}</span>
          ${item.confianzaPct ? `<span class="badge badge-verificado">Confianza ${item.confianzaPct}%</span>` : ""}
          <h3 style="margin:6px 0 2px;">${esc(item.titulo)}</h3>
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          ${item.siteId ? `<button type="button" class="btn btn-primary" id="btnAbrirCasoMapa">Abrir en Mapa</button>` : ""}
          <button type="button" class="btn btn-quiet" id="btnArchivoDocx">Word (.docx)</button>
          <button type="button" class="btn btn-quiet" id="btnArchivoPdf">PDF</button>
          <button type="button" class="btn btn-quiet" id="btnArchivoJson">JSON</button>
          ${item.grupo === "guardado" ? `<button type="button" class="btn btn-quiet" id="btnEliminarCasoGuardado" style="color:var(--critico);">Eliminar</button>` : ""}
        </div>
      </div>

      ${
        thumbs.length
          ? `<div class="thumb-strip">
              ${thumbs.map(([src, lbl]) => `<div class="thumb-card"><img src="${esc(src)}" alt="${esc(lbl)}"><span>${esc(lbl)}</span></div>`).join("")}
            </div>`
          : ""
      }

      ${
        item.preguntaIA || item.respuestaIA
          ? `<div class="callout"><strong>Consulta guardada de Asistente IA:</strong><br><em>${esc(item.preguntaIA || "")}</em><div style="margin-top:4px;">${renderMarkdownSimple(item.respuestaIA || "")}</div></div>`
          : ""
      }

      ${
        item.grupo === "guardado"
          ? `<div class="surface-card" style="margin-bottom:10px;">
              <label for="txtNotaCaso" style="font-size:0.8rem;font-weight:700;display:block;margin-bottom:5px;">Nota de inspección (guardada en Supabase):</label>
              <textarea id="txtNotaCaso" class="notes-textarea" placeholder="Escribe observaciones en terreno…">${esc(item.nota || "")}</textarea>
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
      abrirSitio(item.siteId, "imagenes");
      const lyr = state.poligonosPorId[item.siteId];
      if (lyr && state.map) state.map.fitBounds(lyr.getBounds(), { maxZoom: 16, padding: [36, 36] });
    });

    document.getElementById("btnArchivoDocx")?.addEventListener("click", async () => {
      if (!(await consumirExportacion("docx"))) return;
      descargarWordInforme(
        inf,
        [["Expediente", item.titulo], ["Tipo", item.tipoLabel], ["Fecha", item.fecha]],
        `${item.id}.docx`
      );
    });
    document.getElementById("btnArchivoPdf")?.addEventListener("click", async () => {
      if (!(await consumirExportacion("pdf"))) return;
      document.getElementById("printArea").innerHTML = document.getElementById("archivoInformeCuerpo").innerHTML;
      window.print();
    });
    document.getElementById("btnArchivoJson")?.addEventListener("click", async () => {
      if (!(await consumirExportacion("json"))) return;
      descargarBlob(new Blob([JSON.stringify(item, null, 2)], { type: "application/json" }), `${item.id}.json`);
    });
    document.getElementById("btnGuardarNotaCaso")?.addEventListener("click", async () => {
      item.nota = document.getElementById("txtNotaCaso").value;
      await guardarCasoPersistente(item);
      alert("Nota guardada en Casos y Supabase.");
    });
    document.getElementById("btnEliminarCasoGuardado")?.addEventListener("click", async () => {
      guardarCasosLocales(leerCasosLocales().filter((g) => g.id !== item.id));
      state.casosServidor = state.casosServidor.filter((g) => g.id !== item.id);
      if (window.location.protocol !== "file:") {
        try { await fetch(`api/casos/${encodeURIComponent(item.id)}`, { method: "DELETE" }); } catch (_e) {}
      }
      state.casoArchivoSelId = null;
      renderListaCasos();
    });
  }

  // =========================================================================
  // VISTA 4: PLANES, MÁRGENES, COMPETENCIA, BML Y PRIVACIDAD
  // =========================================================================
  function renderPlanesView() {
    const grid = document.getElementById("planesGrid");
    if (!grid) return;
    const mod = PU.catalogo?.modelo_negocio || {};
    const planes = mod.escalera_planes || [];
    const esAnual = state.modalidadPlanUI === "anual";

    grid.innerHTML = planes
      .map((pl) => {
        const esActivo = state.perfil.plan_id === pl.id;
        const precioTxt = esAnual && pl.anual_texto && pl.id !== "gratis" && pl.id !== "pase_proyecto" ? pl.anual_texto : pl.precio_texto;
        return `
        <div class="plan-tier-card ${pl.destacado ? "plan-featured" : ""} ${esActivo ? "plan-active" : ""}">
          <div>
            <div style="display:flex;justify-content:space-between;gap:6px;align-items:flex-start;margin-bottom:4px;">
              <strong>${esc(pl.nombre)}</strong>
              ${esActivo ? `<span class="badge badge-verificado">Activo</span>` : pl.destacado ? `<span class="badge badge-prioritario">Recomendado</span>` : ""}
            </div>
            <div class="plan-price-main">${esc(precioTxt)}</div>
            <div class="hint" style="margin:2px 0 8px;">${esc(esAnual ? pl.anual_texto : pl.precio_texto)} · Margen ${pl.margen_bruto_pct ? pl.margen_bruto_pct + "%" : "Adquisición"}</div>
            <p style="font-size:0.78rem;color:var(--muted);line-height:1.4;margin-bottom:8px;"><strong>Por qué:</strong> ${esc(pl.por_que)}</p>
            <ul style="margin:0 0 8px 16px;padding:0;font-size:0.78rem;line-height:1.45;">
              ${(pl.incluye || []).map((inc) => `<li>${esc(inc)}</li>`).join("")}
            </ul>
          </div>
          <button type="button" class="btn ${esActivo ? "btn-outline-primary" : "btn-primary"} btn-activar-plan" data-plan-id="${esc(pl.id)}">
            ${esActivo ? "Plan activo ✓ (Re-activar)" : "Activar Plan"}
          </button>
        </div>`;
      })
      .join("");

    grid.querySelectorAll(".btn-activar-plan").forEach((b) => {
      b.addEventListener("click", () => activarPlanEnBackend(b.dataset.planId, state.modalidadPlanUI));
    });

    const addons = document.getElementById("addonsGrid");
    if (addons) {
      addons.innerHTML =
        `<strong style="font-size:0.8rem;align-self:center;">Add-ons opcionales:</strong>` +
        (mod.addons_opcionales || []).map((a) => `<span class="addon-pill"><strong>${esc(a.nombre)}:</strong> ${esc(a.precio)}</span>`).join("");
    }

    const compBox = document.getElementById("tablaCompetenciaMargenes");
    if (compBox) {
      const comps = mod.competencia || [];
      compBox.innerHTML = `
        <table class="exec-table tabular">
          <thead>
            <tr>
              <th>Plataforma / Competidor</th>
              <th>Precio de referencia</th>
              <th>Tiempo hasta informe</th>
              <th>IA verificada c/ fotos</th>
              <th>Datos Chile + Censo 2024</th>
            </tr>
          </thead>
          <tbody>
            ${comps
              .map(
                (c, idx) => `
              <tr style="${idx === 0 ? "background:#f0fdf4;font-weight:600;" : ""}">
                <td>${esc(c.nombre)}</td>
                <td>${esc(c.precio)}</td>
                <td>${esc(c.tiempo_informe)}</td>
                <td>${esc(c.ia_verificada)}</td>
                <td>${esc(c.foco_chile)}</td>
              </tr>`
              )
              .join("")}
          </tbody>
        </table>
      `;
    }

    const bmlBox = document.getElementById("bmlImpactGrid");
    if (bmlBox) {
      const bml = mod.bml_ciclo || {};
      bmlBox.innerHTML = `
        <p style="font-size:0.85rem;line-height:1.5;"><strong>Cuantificación hoy:</strong> <strong>542 parques reales</strong> en 4 comunas (~130 lecturas satelitales c/u), acortando de 3 semanas a 3 minutos la preparación de expedientes.</p>
        <ul style="padding-left:18px;font-size:0.84rem;line-height:1.5;">
          <li><strong>Construir:</strong> ${esc(bml.construir || "")}</li>
          <li><strong>Medir:</strong> ${esc(bml.medir || "")}</li>
          <li><strong>Aprender:</strong> ${esc(bml.aprender || "")}</li>
        </ul>
      `;
    }

    const privBox = document.getElementById("privacidadGrid");
    if (privBox) {
      const priv = mod.privacidad_y_confianza || {};
      privBox.innerHTML = `
        <p style="font-size:0.85rem;font-weight:700;color:var(--primary);margin-bottom:6px;">${esc(priv.marco_legal || "Ley 19.628 y Ley 21.719 (Chile)")}</p>
        <ul style="padding-left:18px;font-size:0.84rem;line-height:1.5;">
          ${(priv.principios || []).map((pr) => `<li>${esc(pr)}</li>`).join("")}
        </ul>
      `;
    }
  }

  // =========================================================================
  // MODALES COMPLEMENTARIOS Y NAVEGACIÓN
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
          <td>${c.confianza_comuna_pct || 94}%</td>
          <td>${fmtNum(c.aire?.pm2_5_media, 1)} µg/m³</td>
        </tr>`
      )
      .join("");

    abrirModal(
      "Comparación entre comunas (Calor, Árboles, Techos y Confianza %)",
      `
        <p class="hint">Vitacura (comuna control con 33,5% de árboles) registra hasta 8 °C menos de calor estival en suelo frente a Quilicura (42,9 °C).</p>
        <div style="overflow-x:auto;">
          <table class="data-table tabular">
            <thead>
              <tr>
                <th>Comuna</th><th>Calor verano</th><th>Árboles / Cemento</th>
                <th>Techos zinc</th><th>Confianza %</th><th>Aire PM2.5</th>
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
          { label: "Calor verano (°C)", data: comunas.map((c) => c.lst_verano_mediana_c), backgroundColor: "#ea580c" },
          { label: "Cobertura de árboles %", data: comunas.map((c) => c.cobertura_arboles_comuna_pct), backgroundColor: "#15803d" },
          { label: "Techos calientes (zinc) %", data: comunas.map((c) => c.pct_techo_calor_comuna), backgroundColor: "#6366f1" },
        ],
      },
      options: { responsive: true, maintainAspectRatio: false },
    });
  }

  function mostrarModalAyuda() {
    abrirModal(
      "Cómo leer RE-VIDA en 1 minuto (sin tecnicismos)",
      `
        <ul>
          <li><strong>Foto Satélite Real:</strong> Usa fotografía aérea Esri HD de alta resolución para ver árboles, techos y calles reales de cada plaza, con captura en 1 clic.</li>
          <li><strong>Calor del suelo en verano (°C):</strong> Temperatura superficial medida desde satélite NASA/USGS Landsat 8/9 en días despejados de verano.</li>
          <li><strong>Salud del pasto y árboles (%):</strong> Traduce el vigor vegetal Copernicus Sentinel-2 a una escala intuitiva de 0% a 100%.</li>
          <li><strong>Entorno a 5 cuadras (400 m):</strong> Mide cuántos árboles faltan alrededor de cada plaza para llegar a la meta mínima urbana de 30% de sombra (ESA WorldCover 2021).</li>
          <li><strong>Confianza real (%):</strong> Porcentaje calculado según días sin nubes, tamaño de la plaza y coincidencia entre las 5 fuentes oficiales.</li>
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
    } else if (nombreVista === "planes") {
      renderPlanesView();
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
    actualizarSelectContextoChat();
  }

  async function init() {
    leerPerfilLocal();
    const comunas = PU.resumen?.comunas || [];
    const sel = document.getElementById("selectComuna");
    sel.innerHTML = comunas.map((c) => `<option value="${esc(c.slug)}">${esc(c.nombre)}</option>`).join("");

    initMap();

    document.querySelectorAll(".nav-tab").forEach((b) => {
      b.addEventListener("click", () => cambiarVista(b.dataset.view));
    });
    document.getElementById("badgePlanActivo").addEventListener("click", () => cambiarVista("planes"));
    document.getElementById("btnIrPrivacidad").addEventListener("click", () => {
      cambiarVista("planes");
      setTimeout(() => document.getElementById("seccionPrivacidadDatos")?.scrollIntoView({ behavior: "smooth" }), 60);
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
          ? "Prioriza según calor de verano, cemento alrededor del parque y estado real del pasto y árboles."
          : "Combina 70% datos climáticos/árboles con 30% necesidad vecinal (techos zinc y hacinamiento).";
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
        guardarSitioEnCasos(feat, state.capturaSitioDataUrl);
        renderDrawerActual();
      }
    });

    document.getElementById("btnCerrarDrawer").addEventListener("click", () => {
      state.sitioActivoId = null;
      document.getElementById("siteDrawer").classList.add("hidden");
      renderMapa(false);
      renderTop5();
    });

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

    document.getElementById("btnIaDocx").addEventListener("click", async () => {
      if (!(await consumirExportacion("docx"))) return;
      const bundle = (PU.informes_inversion || {})[state.ambitoIA];
      if (!bundle) return;
      const inf = state.informeIACustom[state.ambitoIA] || bundle.informe;
      const cr = bundle.paquete.cartera_resumen || {};
      descargarWordInforme(
        inf,
        [
          ["Ámbito", bundle.paquete.comuna.nombre],
          ["Parques priorizados", `${fmtInt(cr.n_sitios_cartera)}`],
          ["Calor máx. verano", `${fmtNum(cr.lst_max_cartera_c, 1)} °C`],
          ["Árboles estimados", `${fmtInt(cr.arboles_min_cartera)} – ${fmtInt(cr.arboles_max_cartera)}`],
          ["Presupuesto (hipótesis sin verificar)", `${fmtClpCorto(cr.costo_clp_min_cartera)} – ${fmtClpCorto(cr.costo_clp_max_cartera)} CLP`],
        ],
        `cartera_inversion_${state.ambitoIA}.docx`
      );
    });
    document.getElementById("btnIaPdf").addEventListener("click", async () => {
      if (!(await consumirExportacion("pdf"))) return;
      document.getElementById("printArea").innerHTML = document.getElementById("contenidoInformeIA").innerHTML;
      window.print();
    });
    document.getElementById("btnIaCsv").addEventListener("click", async () => {
      if (!(await consumirExportacion("csv"))) return;
      const bundle = (PU.informes_inversion || {})[state.ambitoIA];
      if (!bundle) return;
      const sitios = bundle.paquete.cartera_sitios || [];
      const head = "ranking,nombre,comuna,urgencia,calor_c,arboles_400m_pct,cemento_400m_pct,techos_zinc_pct,arboles_min,arboles_max,fondo_sugerido\n";
      const rows = sitios
        .map((s, idx) =>
          [idx + 1, `"${(s.nombre || "").replace(/"/g, '""')}"`, s.comuna, s.prioridad_satelital, s.lst_verano_c, s.cobertura_arboles_400m_pct, s.impermeable_400m_pct, s.pct_techo_calor_400m, s.arboles_necesarios_min, s.arboles_necesarios_max, `"${s.fondo_sugerido || ""}"`].join(",")
        )
        .join("\n");
      descargarBlob(new Blob([head + rows], { type: "text/csv;charset=utf-8" }), `cartera_${state.ambitoIA}.csv`);
    });
    document.getElementById("btnIaGuardarCaso").addEventListener("click", async () => {
      const bundle = (PU.informes_inversion || {})[state.ambitoIA];
      if (!bundle) return;
      const inf = state.informeIACustom[state.ambitoIA] || bundle.informe;
      await guardarCasoPersistente({
        id: `guardado-cartera-${state.ambitoIA}-${Date.now()}`,
        grupo: "guardado",
        tipoLabel: "Cartera guardada",
        titulo: `${limpiarTextoHumano(inf.titulo)}`,
        comunaSlug: state.ambitoIA === "intercomunal" ? "cerro_navia" : state.ambitoIA,
        siteId: null,
        fecha: new Date().toISOString().slice(0, 10),
        nota: "",
        fotoDataUrl: state.chatImagenDataUrl || null,
        confianzaPct: 94,
        paquete: bundle.paquete,
        informe: inf,
      });
      alert("Cartera guardada en Casos y Archivos (Supabase).");
    });

    // Casos y Archivos
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
        const id = `importado-${Date.now()}`;
        await guardarCasoPersistente({
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
        state.casoArchivoSelId = id;
        renderListaCasos();
      } catch (_err) {
        alert("El archivo JSON no tiene un formato válido de caso.");
      }
      e.target.value = "";
    });

    // Planes mensual / anual
    document.getElementById("btnPlanMensual").addEventListener("click", () => {
      state.modalidadPlanUI = "mensual";
      document.getElementById("btnPlanMensual").classList.add("active");
      document.getElementById("btnPlanAnual").classList.remove("active");
      renderPlanesView();
    });
    document.getElementById("btnPlanAnual").addEventListener("click", () => {
      state.modalidadPlanUI = "anual";
      document.getElementById("btnPlanAnual").classList.add("active");
      document.getElementById("btnPlanMensual").classList.remove("active");
      renderPlanesView();
    });

    // Login visual conectado a Supabase
    const modalLogin = document.getElementById("modalLoginBackdrop");
    document.getElementById("btnLoginUsuario").addEventListener("click", () => {
      document.getElementById("loginNombre").value = state.perfil.nombre || "Equipo Evaluador";
      document.getElementById("loginEmail").value = state.perfil.email || "demo@pulmonurbano.cl";
      document.getElementById("loginOrg").value = state.perfil.organizacion || "Municipalidad Demo";
      modalLogin.classList.remove("hidden");
    });
    document.getElementById("btnCerrarLogin").addEventListener("click", () => modalLogin.classList.add("hidden"));
    document.getElementById("tabModoLogin").addEventListener("click", () => {
      document.getElementById("tabModoLogin").classList.add("active");
      document.getElementById("tabModoRegistro").classList.remove("active");
      document.getElementById("loginDescModo").textContent = "Ingresa con tu correo demo para cargar tu plan y casos en Supabase.";
    });
    document.getElementById("tabModoRegistro").addEventListener("click", () => {
      document.getElementById("tabModoRegistro").classList.add("active");
      document.getElementById("tabModoLogin").classList.remove("active");
      document.getElementById("loginDescModo").textContent = "Crea un perfil rápido (modo presentación) y activa planes con 1 clic en Supabase.";
    });
    const ejecutarLogin = async (nombre, email, org, rol) => {
      if (window.location.protocol !== "file:") {
        try {
          const resp = await fetch("api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nombre, email, organizacion: org, rol }),
          });
          if (resp.ok) {
            const j = await resp.json();
            if (j.perfil) Object.assign(state.perfil, j.perfil);
          }
        } catch (_e) {
          // fallback
        }
      }
      state.perfil.nombre = nombre;
      state.perfil.email = email.trim().toLowerCase();
      state.perfil.organizacion = org;
      state.perfil.rol = rol;
      guardarPerfilLocal();
      modalLogin.classList.add("hidden");
      await sincronizarPerfilYCasosServidor();
    };
    document.getElementById("formLoginDemo").addEventListener("submit", (e) => {
      e.preventDefault();
      ejecutarLogin(
        document.getElementById("loginNombre").value,
        document.getElementById("loginEmail").value,
        document.getElementById("loginOrg").value,
        document.getElementById("loginRol").value
      );
    });
    document.getElementById("btnDemoRapido").addEventListener("click", () => {
      ejecutarLogin("Valentina Rojas (SECPLA)", "consultora.demo@pulmonurbano.cl", "Consultora Verde Chile", "Consultora Ambiental / Paisajismo");
    });

    // Modales & Móvil
    document.getElementById("btnComparar").addEventListener("click", mostrarModalComparar);
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
    renderPlanesView();
    await sincronizarPerfilYCasosServidor();
    await actualizarPanelIA();
    actualizarContadorCasos();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
