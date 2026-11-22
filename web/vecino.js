(function () {
  "use strict";

  const COLORES = { verde: "#2e9e5b", amarillo: "#f2b01e", rojo: "#d64545", gris: "#8a949e" };
  const EDADES = [["", "Prefiero no decirlo"], ["menos_18", "Menos de 18"], ["18_29", "18 a 29"], ["30_44", "30 a 44"], ["45_59", "45 a 59"], ["60_mas", "60 o más"]];
  const params = new URLSearchParams(location.search);
  const llegoPorQr = params.get("qr") === "1";

  const estado = { zonas: [], zona: null, datos: null, catalogo: {}, epoca: null, mis: new Set(), conteo: {}, resultados: null, sel: null, mapa: null, marcadores: new Map(), resaltado: null };

  // ---------- utilidades (todo el texto entra con textContent: nunca HTML de afuera) ----------
  function h(tag, attrs, ...hijos) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v === false || v === null || v === undefined) continue;
      if (k === "class") el.className = v;
      else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, v === true ? "" : v);
    }
    for (const hijo of hijos.flat()) {
      if (hijo === null || hijo === undefined || hijo === false) continue;
      el.append(hijo.nodeType ? hijo : document.createTextNode(String(hijo)));
    }
    return el;
  }

  async function pedir(url, opciones) {
    const r = await fetch(url, opciones);
    let cuerpo = null;
    try { cuerpo = await r.json(); } catch (_e) { /* sin cuerpo */ }
    if (!r.ok) {
      const e = new Error((cuerpo && cuerpo.detail) || "Error " + r.status);
      e.status = r.status;
      throw e;
    }
    return cuerpo;
  }

  function dispositivo() {
    try {
      let d = localStorage.getItem("pu_dispositivo");
      if (!d) {
        d = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : "anon-" + Date.now() + "-" + Math.random().toString(36).slice(2);
        localStorage.setItem("pu_dispositivo", d);
      }
      return d;
    } catch (_e) {
      if (!estado.efimero) estado.efimero = "anon-" + Date.now() + "-" + Math.random().toString(36).slice(2);
      return estado.efimero;
    }
  }

  const fmt = (n) => new Intl.NumberFormat("es-CL", { maximumFractionDigits: 1 }).format(n);
  function costo(o) {
    if (o.costo_min_M === null || o.costo_max_M === null) return "Costo por cotizar con el municipio";
    return "Entre $" + fmt(o.costo_min_M) + " y $" + fmt(o.costo_max_M) + " millones";
  }

  // ---------- inicio ----------
  async function iniciar() {
    mostrarCargando("Cargando el mapa…");
    try {
      const [cat, ideas, zonas] = await Promise.all([pedir("data/vecino/opciones.json"), pedir("data/vecino/ideas.json"), pedir("api/votacion/zonas")]);
      ideas.ideas.forEach((o) => { estado.catalogo[o.id] = { ...o, costo_min_M: null, costo_max_M: null, costo_nota: "por cotizar con el municipio (no hay dato verificado)", ejemplos: [] }; });
      cat.opciones.forEach((o) => { estado.catalogo[o.id] = o; });
      estado.zonas = zonas.zonas;
    } catch (e) {
      mostrarError("No pudimos cargar los datos. Abre esta página desde el servidor de RE-VIDA (no como archivo). " + e.message);
      return;
    }
    crearMapa();
    pintarZonas();
    const inicial = estado.zonas.find((z) => z.slug === params.get("zona")) || estado.zonas[0];
    await elegirZona(inicial.slug);
    if (params.get("sitio")) elegirSitio(params.get("sitio"));
    const panel = document.getElementById("panel");
    const asa = document.getElementById("panel-asa");
    let toqueY = null;
    let arrastro = false;
    asa.addEventListener("touchstart", (ev) => {
      toqueY = ev.touches[0].clientY;
      arrastro = false;
    }, { passive: true });
    asa.addEventListener("touchend", (ev) => {
      if (toqueY === null) return;
      const dy = ev.changedTouches[0].clientY - toqueY;
      toqueY = null;
      if (dy > 32) { panel.classList.add("baja"); arrastro = true; }
      else if (dy < -32) { panel.classList.remove("baja"); arrastro = true; }
    });
    asa.addEventListener("click", () => {
      if (arrastro) { arrastro = false; return; }
      panel.classList.toggle("baja");
    });
    window.addEventListener("resize", ajustarVista);
  }

  function crearMapa() {
    estado.mapa = L.map("mapa", { zoomControl: false }).setView([-33.45, -70.67], 12);
    L.control.zoom({ position: "bottomright" }).addTo(estado.mapa);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "&copy; OpenStreetMap", maxZoom: 19 }).addTo(estado.mapa);
    estado.mapa.on("click", () => { estado.sel = null; quitarResaltado(); pintarPanel(); });
  }

  function pintarZonas() {
    const nav = document.getElementById("zonas");
    nav.replaceChildren(...estado.zonas.map((z) => h("button", { class: "zona", type: "button", "data-zona": z.slug, "aria-pressed": "false", onclick: () => { estado.sel = null; elegirZona(z.slug); } }, z.nombre)));
  }

  async function elegirZona(slug) {
    const zona = estado.zonas.find((z) => z.slug === slug);
    if (!zona) return;
    estado.zona = zona;
    estado.epoca = zona.epoca;
    estado.sel = null;
    document.querySelectorAll(".zona").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.zona === slug)));
    mostrarCargando("Cargando " + zona.nombre + "…");
    try {
      estado.datos = await pedir("data/vecino/" + slug + ".json");
      const [mis, res] = await Promise.all([
        pedir("api/votacion/mis-votos?periodo_id=" + encodeURIComponent(estado.epoca.id) + "&dispositivo=" + encodeURIComponent(dispositivo())),
        pedir("api/votacion/resultados?periodo_id=" + encodeURIComponent(estado.epoca.id)),
      ]);
      estado.mis = new Set(mis.sitios);
      estado.resultados = res;
      estado.conteo = res.votos_por_sitio || {};
    } catch (e) {
      mostrarError(e.message);
      return;
    }
    pintarMarcadores();
    ajustarVista();
    pintarPanel();
  }

  // Encuadra la comuna; se repite al cambiar el tamaño de la ventana (el mapa mide 0 si se carga oculto).
  function ajustarVista() {
    estado.mapa.invalidateSize();
    const b = estado.datos && estado.datos.comuna.bbox;
    if (b && !estado.sel) {
      const grande = window.innerWidth > 760;  // en pantallas grandes el panel tapa la izquierda; en celular, abajo
      estado.mapa.fitBounds(
        [[b[1], b[0]], [b[3], b[2]]],
        grande
          ? { paddingTopLeft: [400, 70], paddingBottomRight: [20, 30] }
          : { paddingTopLeft: [16, 118], paddingBottomRight: [16, Math.round(window.innerHeight * 0.38)] }
      );
    }
  }

  function pintarMarcadores() {
    estado.marcadores.forEach((m) => estado.mapa.removeLayer(m));
    estado.marcadores.clear();
    quitarResaltado();
    const esMovil = window.innerWidth <= 760;
    for (const s of estado.datos.sitios) {
      const radio = esMovil
        ? (s.area_m2 >= 20000 ? 15 : s.area_m2 >= 3000 ? 11.5 : 9.5)
        : (s.area_m2 >= 20000 ? 13 : s.area_m2 >= 3000 ? 9 : 6.5);
      const yaVote = estado.mis.has(s.id);
      const m = L.circleMarker([s.centro[1], s.centro[0]], { radius: radio, color: yaVote ? "#1f2a30" : "#ffffff", weight: yaVote ? 3 : 2, fillColor: COLORES[s.semaforo.color], fillOpacity: 0.92 });
      m.on("click", (ev) => { L.DomEvent.stopPropagation(ev); elegirSitio(s.id); });
      m.bindTooltip(s.nombre, { direction: "top" });
      m.addTo(estado.mapa);
      estado.marcadores.set(s.id, m);
    }
  }

  function quitarResaltado() {
    if (estado.resaltado) { estado.mapa.removeLayer(estado.resaltado); estado.resaltado = null; }
  }

  function elegirSitio(id) {
    const s = estado.datos && estado.datos.sitios.find((x) => x.id === id);
    if (!s) return;
    estado.sel = s;
    quitarResaltado();
    estado.resaltado = L.geoJSON({ type: "Feature", geometry: s.geometria }, { style: { color: "#1f2a30", weight: 3, fillColor: COLORES[s.semaforo.color], fillOpacity: 0.35 } }).addTo(estado.mapa);
    if (window.innerWidth <= 760) {
      estado.mapa.fitBounds(estado.resaltado.getBounds(), {
        paddingTopLeft: [24, 122],
        paddingBottomRight: [24, Math.round(window.innerHeight * 0.66)],
        maxZoom: 16,
        animate: true,
        duration: 0.6,
      });
    } else {
      estado.mapa.flyTo([s.centro[1], s.centro[0]], Math.max(estado.mapa.getZoom(), 16), { duration: 0.6 });
    }
    document.getElementById("panel").classList.remove("baja");
    pintarPanel();
  }

  // ---------- panel ----------
  function contenedor() { return document.getElementById("panel-contenido"); }
  function mostrarCargando(texto) { contenedor().replaceChildren(h("p", { class: "cargando" }, texto)); }
  function mostrarError(texto) { contenedor().replaceChildren(h("p", { class: "error" }, texto)); }

  function textoEpoca() {
    const e = estado.epoca;
    if (e.estado === "abierto") {
      const d = e.dias_restantes;
      return h("div", { class: "urgencia" }, "Votación abierta: ", h("b", {}, d <= 1 ? "cierra hoy o mañana" : "cierra en " + d + " días"), ". Mientras más vecinos voten, más fuerza tiene lo que se pide.");
    }
    if (e.estado === "cerrado") return h("div", { class: "urgencia cerrada" }, "Esta votación ya cerró.");
    return h("div", { class: "urgencia cerrada" }, "La votación aún no abre.");
  }

  function pintarPanel() {
    const raiz = contenedor();
    const panelEl = document.getElementById("panel");
    if (panelEl) panelEl.classList.toggle("inicio", !estado.sel);
    const nodos = [];
    if (estado.epoca && estado.epoca.demo) nodos.push(h("div", { class: "demo" }, "DEMOSTRACIÓN: estos votos son simulados."));
    if (!estado.sel) {
      nodos.push(
        h("h1", {}, estado.zona ? estado.zona.nombre : "RE-VIDA"),
        h("p", { class: "sub" }, "Toca un punto del mapa para ver cómo está ese lugar y votar qué te gustaría que se construya."),
        estado.epoca ? textoEpoca() : null,
        h("h2", {}, "Qué significan los colores"),
        leyenda(),
        h("p", { class: "nota" }, "Los colores comparan cada lugar con los demás que escaneamos con satélite en las 4 comunas. No son un juicio absoluto."),
      );
      raiz.replaceChildren(...nodos.filter(Boolean));
      return;
    }
    const s = estado.sel;
    nodos.push(
      h("h1", {}, s.nombre),
      h("p", { class: "sub" }, s.tipo + " · " + fmt(s.area_m2) + " m²"),
      h("span", { class: "insignia " + s.semaforo.color }, s.semaforo.etiqueta),
      h("p", { class: "frase" }, s.resumen),
      s.poca_confianza ? h("p", { class: "nota" }, "La lectura satelital de este lugar tiene poca confianza: conviene verificarla en terreno.") : null,
      ...["sombra", "calor", "verde", "vecinos"].map((k) => s.datos[k] ? dato(s.datos[k]) : null),
      h("h2", {}, "¿Qué te gustaría aquí?"),
      textoEpoca(),
      bloqueVoto(s),
    );
    raiz.replaceChildren(...nodos.filter(Boolean));
    raiz.scrollTop = 0;
  }

  function leyenda() {
    const filas = [["verde", "Mejor que la mayoría: buena sombra, menos calor y vegetación sana"], ["amarillo", "Regular: en un punto medio"], ["rojo", "Necesita ayuda: poca sombra, mucho calor o vegetación seca"], ["gris", "Sin datos suficientes del satélite"]];
    return h("div", { class: "leyenda" }, filas.map(([c, t]) => h("div", {}, h("span", { class: "punto", style: "background:" + COLORES[c] }), t)));
  }

  function dato(d) {
    return h("div", { class: "dato" }, h("b", {}, d.titulo), d.etiqueta ? h("span", { class: "pildora " + d.etiqueta.split(" ")[0] }, d.etiqueta) : null, h("small", {}, d.texto));
  }

  // ---------- voto ----------
  function bloqueVoto(s) {
    const e = estado.epoca;
    const n = estado.conteo[s.id] || 0;
    const contador = h("p", { class: "sub" }, n === 0 ? "Sé la primera persona en votar aquí." : n === 1 ? "1 persona ya votó aquí." : n + " personas ya votaron aquí.");
    if (e.estado === "cerrado") return h("div", {}, resultadoCerrado(s));
    if (e.estado !== "abierto") return h("div", {});
    if (estado.mis.has(s.id)) return h("div", {}, contador, gracias(s));
    return h("div", {}, contador, formulario(s));
  }

  function formulario(s) {
    const recomendadas = s.opciones.map((o) => ({ ...estado.catalogo[o.id], razon: o.razon })).filter((o) => o.id);
    let elegida = null;
    const lista = h("div", { role: "radiogroup", "aria-label": "Opciones recomendadas para este lugar" });
    const edad = h("select", { "aria-label": "Tu edad (opcional)" }, EDADES.map(([v, t]) => h("option", { value: v }, t)));
    const error = h("p", { class: "error", hidden: true });
    const boton = h("button", { class: "boton", type: "button", disabled: true }, "Votar");
    const eleccion = h("p", { class: "eleccion", hidden: true });
    const cajaBusqueda = h("div", { class: "busqueda-resultados", "aria-live": "polite" });
    const entrada = h("input", { type: "search", class: "buscador", placeholder: "Busca una idea: huerto, perros, feria, baños…", "aria-label": "Buscar una idea", autocomplete: "off", maxlength: "60" });

    function elegir(o) {
      elegida = o.id;
      boton.disabled = false;
      eleccion.hidden = false;
      eleccion.textContent = "Tu elección: " + o.nombre;
    }

    function tarjeta(o, razon, etiqueta) {
      const input = h("input", { type: "radio", name: "opcion", value: o.id, checked: o.id === elegida });
      const ejemplos = o.ejemplos || [];
      const caja = h("div", { class: "ejemplos", hidden: true }, ejemplos.map((x) => h("div", {}, h("a", { href: x.url, target: "_blank", rel: "noopener noreferrer" }, x.titulo))));
      const ver = ejemplos.length ? h("button", { class: "enlace", type: "button", onclick: (ev) => { ev.preventDefault(); caja.hidden = !caja.hidden; } }, "Ver obras parecidas con fuente") : null;
      input.addEventListener("change", () => elegir(o));
      return h("div", {}, h("label", { class: "opcion" }, input,
        h("span", { class: "nombre" }, o.nombre), etiqueta ? h("span", { class: "etiqueta" }, etiqueta) : null,
        h("span", { class: "razon" }, razon || o.descripcion),
        h("span", { class: "costo" }, costo(o), " ", h("em", {}, "(" + (o.costo_nota || "") + ")"))), ver, caja);
    }

    recomendadas.forEach((o) => lista.append(tarjeta(o, o.razon, "Recomendada")));

    let temporizador = null, secuencia = 0;
    async function buscar(q) {
      const texto = q.trim();
      const mia = ++secuencia;
      if (!texto) {
        cajaBusqueda.replaceChildren();
        return;
      }
      if (texto.length < 2) {
        cajaBusqueda.replaceChildren(h("p", { class: "sub" }, "Escribe al menos 2 letras para buscar."));
        return;
      }
      cajaBusqueda.replaceChildren(h("p", { class: "sub" }, "Buscando…"));
      try {
        const r = await pedir("api/votacion/ideas?q=" + encodeURIComponent(texto) + "&comuna=" + encodeURIComponent(estado.zona.slug) + "&site_id=" + encodeURIComponent(s.id));
        if (mia !== secuencia) return;
        if (r.coincidencias > 0) {
          const titulo = r.coincidencias + (r.coincidencias === 1 ? " resultado" : " resultados") + " para «" + texto + "»";
          cajaBusqueda.replaceChildren(h("p", { class: "sub" }, titulo), ...r.resultados.map((o) => tarjeta(o, o.descripcion, o.recomendada ? "Recomendada para este lugar" : null)));
        } else {
          cajaBusqueda.replaceChildren(h("p", { class: "sub" }, "No encontramos ideas parecidas a «" + texto + "». Prueba con otra palabra."));
        }
      } catch (e) {
        if (mia === secuencia) cajaBusqueda.replaceChildren(h("p", { class: "error" }, "No pudimos buscar ahora: " + e.message));
      }
    }
    entrada.addEventListener("input", () => { clearTimeout(temporizador); temporizador = setTimeout(() => buscar(entrada.value), 250); });

    boton.addEventListener("click", async () => {
      error.hidden = true;
      if (!elegida) return;
      boton.disabled = true; boton.textContent = "Guardando…";
      try {
        await pedir("api/votacion/votar", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ periodo_id: estado.epoca.id, site_id: s.id, opcion_id: elegida, edad_rango: edad.value || null, dispositivo: dispositivo(), via_qr: llegoPorQr }) });
        estado.mis.add(s.id);
        estado.conteo[s.id] = (estado.conteo[s.id] || 0) + 1;
        const m = estado.marcadores.get(s.id);
        if (m) m.setStyle({ color: "#1f2a30", weight: 3 });
        pintarPanel();
      } catch (e) {
        if (e.status === 409) { estado.mis.add(s.id); pintarPanel(); return; }
        error.textContent = e.message; error.hidden = false; boton.disabled = false; boton.textContent = "Votar";
      }
    });
    return h("div", {}, lista,
      h("h2", {}, "¿Se te ocurre otra cosa? Búscala"), entrada, cajaBusqueda,
      h("label", { class: "sub" }, "Tu edad (opcional, ayuda a que los resultados representen a todos)"), edad, eleccion, error, boton);
  }

  function gracias(s) {
    const e = estado.epoca;
    const enlace = location.origin + location.pathname + "?zona=" + encodeURIComponent(estado.zona.slug) + "&sitio=" + encodeURIComponent(s.id) + "&qr=1";
    const compartir = h("button", { class: "boton sec", type: "button" }, "Compartir con mis vecinos");
    compartir.addEventListener("click", async () => {
      try {
        if (navigator.share) await navigator.share({ title: "Vota por " + s.nombre, text: "Vota qué te gustaría en " + s.nombre, url: enlace });
        else { await navigator.clipboard.writeText(enlace); compartir.textContent = "Enlace copiado"; }
      } catch (_e) { /* cancelado */ }
    });
    return h("div", { class: "gracias" }, h("div", { class: "grande", "aria-hidden": "true" }, "✓"), h("b", {}, "¡Gracias! Tu voto quedó guardado."),
      h("p", { class: "sub" }, "Los resultados se publican cuando cierre la votación" + (e.dias_restantes ? " (en " + e.dias_restantes + " día" + (e.dias_restantes === 1 ? "" : "s") + ")." : ".")), compartir);
  }

  function resultadoCerrado(s) {
    const r = estado.resultados;
    if (!r || !r.publicado) return h("p", { class: "sub" }, "Los resultados aún no están disponibles.");
    const dato = r.sitios[s.id];
    if (!dato) return h("p", { class: "sub" }, "Nadie votó en este lugar durante esta votación.");
    if (dato.oculto) return h("p", { class: "nota" }, "Votaron " + dato.total + " persona(s): son muy pocas para mostrar porcentajes (mínimo " + r.min_votos + ").");
    return h("div", {}, h("p", { class: "sub" }, "Resultado final: " + dato.total + " votos."), dato.opciones.map((o) => {
      const nombre = o.id === "otro" ? "Otra idea" : (estado.catalogo[o.id] ? estado.catalogo[o.id].nombre : o.id);
      return h("div", { class: "barra-res" }, h("div", { class: "fila" }, h("span", {}, nombre), h("b", {}, fmt(o.pct) + " %")), h("div", { class: "pista" }, h("div", { class: "relleno", style: "width:" + Math.min(100, o.pct) + "%" })));
    }));
  }

  iniciar();
})();
