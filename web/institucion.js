(function () {
  "use strict";

  const COLORES = { verde: "#2e9e5b", amarillo: "#f2b01e", rojo: "#d64545", gris: "#8a949e" };
  const estado = { zonas: [], catalogo: {}, slug: null, epocas: [], epoca: null, datos: null, sitios: {}, res: null, activa: null };
  const $ = (s) => document.querySelector(s);
  const fmt = (n) => new Intl.NumberFormat("es-CL", { maximumFractionDigits: 1 }).format(n);

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
    if (!r.ok) throw new Error((cuerpo && cuerpo.detail) || "Error " + r.status);
    return cuerpo;
  }

  const nombreOpcion = (id) => (id === "otro" ? "Otra idea" : (estado.catalogo[id] ? estado.catalogo[id].nombre : id));
  function rangoCosto(id) {
    const o = estado.catalogo[id];
    if (!o || o.costo_min_M === null || o.costo_max_M === null) return null;
    return [o.costo_min_M, o.costo_max_M];
  }
  const textoCosto = (id) => { const r = rangoCosto(id); return r ? "$" + fmt(r[0]) + " a $" + fmt(r[1]) + " M" : "Por cotizar"; };

  async function iniciar() {
    try {
      const [cat, zonas] = await Promise.all([pedir("data/vecino/opciones.json"), pedir("api/votacion/zonas")]);
      cat.opciones.forEach((o) => { estado.catalogo[o.id] = o; });
      estado.zonas = zonas.zonas;
    } catch (e) {
      $("#aviso").replaceChildren(h("div", { class: "aviso" }, "No pudimos cargar los datos. Abre esta página desde el servidor de Pulmón Urbano. " + e.message));
      return;
    }
    const sel = $("#sel-comuna");
    sel.replaceChildren(...estado.zonas.map((z) => h("option", { value: z.slug }, z.nombre)));
    sel.addEventListener("change", () => cargarComuna(sel.value));
    $("#sel-epoca").addEventListener("change", () => elegirEpoca($("#sel-epoca").value));
    $("#btn-md").addEventListener("click", descargarMarkdown);
    $("#btn-pdf").addEventListener("click", () => window.print());
    $("#btn-cerrar").addEventListener("click", cerrarAhora);
    $("#btn-nueva").addEventListener("click", abrirNueva);
    const token = sessionStorage.getItem("pu_admin");
    if (token) $("#token").value = token;
    await cargarComuna(estado.zonas[0].slug);
  }

  async function cargarComuna(slug) {
    estado.slug = slug;
    estado.activa = null;
    $("#detalle").replaceChildren();
    const [datos, per] = await Promise.all([pedir("data/vecino/" + slug + ".json"), pedir("api/votacion/periodos?comuna=" + encodeURIComponent(slug))]);
    estado.datos = datos;
    estado.sitios = Object.fromEntries(datos.sitios.map((s) => [s.id, s]));
    estado.epocas = per.periodos;
    const sel = $("#sel-epoca");
    sel.replaceChildren(...estado.epocas.map((e) => h("option", { value: e.id }, e.nombre + " · " + ({ abierto: "abierta", cerrado: "cerrada", proximo: "próxima" })[e.estado] + (e.demo ? " · DEMO" : ""))));
    const preferida = estado.epocas.find((e) => e.estado === "cerrado" && !e.demo) || estado.epocas.find((e) => e.estado === "cerrado") || estado.epocas[0];
    sel.value = preferida.id;
    await elegirEpoca(preferida.id);
  }

  async function elegirEpoca(id) {
    estado.epoca = estado.epocas.find((e) => e.id === id);
    estado.res = await pedir("api/votacion/resultados?periodo_id=" + encodeURIComponent(id));
    estado.activa = null;
    $("#detalle").replaceChildren();
    pintar();
  }

  function filas() {
    const r = estado.res;
    const lista = [];
    if (r.publicado) {
      for (const [sid, d] of Object.entries(r.sitios)) lista.push({ sid, total: d.total, oculto: d.oculto, opciones: d.opciones || [], otros: d.otros || [] });
    } else {
      for (const [sid, n] of Object.entries(r.votos_por_sitio)) lista.push({ sid, total: n, oculto: true, opciones: [], otros: [] });
    }
    return lista.filter((f) => estado.sitios[f.sid]).sort((a, b) => b.total - a.total);
  }

  function pintar() {
    const e = estado.epoca, r = estado.res;
    const avisos = [];
    if (e.demo) avisos.push(h("div", { class: "aviso-demo" }, "DEMOSTRACIÓN: estos votos son simulados y no representan a ningún vecino real."));
    if (!r.publicado) avisos.push(h("div", { class: "aviso" }, "Esta votación sigue abierta" + (e.dias_restantes ? " (cierra en " + e.dias_restantes + " día(s))" : "") + ". Los porcentajes se publican al cierre para que nadie vote siguiendo a la mayoría. Por ahora solo se ve cuántos votos hay."));
    $("#aviso").replaceChildren(...avisos);

    const lista = filas();
    const conRes = lista.filter((f) => !f.oculto);
    let minTot = 0, maxTot = 0, porCotizar = 0, coincide = 0;
    for (const f of conRes) {
      const gan = f.opciones[0];
      const rg = gan && rangoCosto(gan.id);
      if (rg) { minTot += rg[0]; maxTot += rg[1]; } else porCotizar += 1;
      const rec = estado.sitios[f.sid].opciones.map((o) => o.id);
      if (gan && rec.includes(gan.id)) coincide += 1;
    }
    $("#resumen").replaceChildren(
      tarjeta("Votos en esta votación", String(r.total_votos), e.estado === "cerrado" ? "votación cerrada" : "votación " + e.estado),
      tarjeta("Lugares con resultados", r.publicado ? String(conRes.length) : "—", r.publicado ? "con " + r.min_votos + " votos o más" : "se publican al cierre"),
      tarjeta("Inversión aprox. si se hace lo más pedido", r.publicado && conRes.length ? "$" + fmt(minTot) + " a $" + fmt(maxTot) + " M" : "—", r.publicado ? porCotizar + " lugar(es) por cotizar · hipótesis (sin verificar)" : ""),
      tarjeta("Coincide con la recomendación satelital", r.publicado && conRes.length ? coincide + " de " + conRes.length : "—", "lo más pedido estaba entre las opciones recomendadas"),
    );

    const cuerpo = $("#cuerpo");
    if (!lista.length) {
      cuerpo.replaceChildren(h("tr", {}, h("td", { colspan: "5" }, "Todavía no hay votos en esta votación.")));
      return;
    }
    cuerpo.replaceChildren(...lista.map((f) => {
      const s = estado.sitios[f.sid];
      const gan = f.opciones[0];
      return h("tr", { "data-sid": f.sid, onclick: () => abrirDetalle(f.sid) },
        h("td", {}, h("span", { class: "punto", style: "background:" + COLORES[s.semaforo.color] }), s.nombre, h("div", { class: "pocos" }, s.semaforo.etiqueta + " · " + fmt(s.area_m2) + " m²")),
        h("td", { class: "num" }, String(f.total)),
        h("td", {}, !r.publicado ? h("span", { class: "pocos" }, "Se publica al cierre") : f.oculto ? h("span", { class: "pocos" }, "Pocos votos para mostrar") : [h("span", { class: "pct" }, fmt(gan.pct) + " % "), nombreOpcion(gan.id)]),
        h("td", { class: "num" }, gan && !f.oculto ? textoCosto(gan.id) : "—"),
        h("td", { class: "num" }, "$" + fmt(s.mantencion_M[0]) + " a $" + fmt(s.mantencion_M[1]) + " M"));
    }));
    if (lista[0]) abrirDetalle(lista[0].sid);
  }

  function tarjeta(titulo, valor, pie) { return h("div", { class: "tarjeta" }, h("span", {}, titulo), h("b", {}, valor), h("span", {}, pie)); }

  function abrirDetalle(sid) {
    estado.activa = sid;
    document.querySelectorAll("#cuerpo tr").forEach((tr) => tr.classList.toggle("activa", tr.dataset.sid === sid));
    const s = estado.sitios[sid];
    const f = filas().find((x) => x.sid === sid);
    const r = estado.res;
    const izq = [h("h2", {}, s.nombre), h("p", { class: "nota" }, s.tipo + " · " + fmt(s.area_m2) + " m² · " + s.semaforo.etiqueta + " (índice " + fmt(s.semaforo.indice) + " de 100)"), h("p", {}, s.resumen)];
    for (const k of ["sombra", "calor", "verde", "vecinos"]) if (s.datos[k]) izq.push(h("div", { class: "dato" }, h("b", {}, s.datos[k].titulo + (s.datos[k].etiqueta ? ": " + s.datos[k].etiqueta : "")), h("small", {}, s.datos[k].texto)));
    izq.push(h("div", { class: "dato" }, h("b", {}, "Mantención aproximada"), h("small", {}, "$" + fmt(s.mantencion_M[0]) + " a $" + fmt(s.mantencion_M[1]) + " M al año (hipótesis: $1.625 a $2.962 por m²)")));
    if (s.poca_confianza) izq.push(h("p", { class: "nota" }, "La lectura satelital tiene poca confianza: verificar en terreno."));
    const der = [h("h2", {}, "Lo que votaron los vecinos")];
    if (!r.publicado) der.push(h("p", { class: "nota" }, f.total + " voto(s) hasta ahora. Los porcentajes se publican al cierre."));
    else if (f.oculto) der.push(h("p", { class: "nota" }, "Votaron " + f.total + " persona(s): menos del mínimo (" + r.min_votos + ") para publicar porcentajes."));
    else {
      der.push(h("p", { class: "nota" }, f.total + " votos"));
      f.opciones.forEach((o) => der.push(h("div", { class: "barra" }, h("div", { class: "fila" }, h("span", {}, nombreOpcion(o.id) + " (" + textoCosto(o.id) + ")"), h("b", {}, fmt(o.pct) + " %")), h("div", { class: "pista" }, h("div", { class: "relleno", style: "width:" + Math.min(100, o.pct) + "%" })))));
      const rec = s.opciones.map((o) => o.id);
      der.push(h("p", { class: "nota" }, f.opciones[0] && rec.includes(f.opciones[0].id) ? "Lo más pedido coincide con lo que recomendaba el análisis satelital." : "Lo más pedido es distinto de lo que recomendaba el análisis satelital: conviene revisarlo con el municipio."));
      if (f.otros.length) der.push(h("p", { class: "nota" }, "Ideas propias (texto de los vecinos, sin revisar):"), h("ul", { class: "otros" }, f.otros.map((t) => h("li", {}, t))));
    }
    $("#detalle").replaceChildren(h("div", { class: "caja" }, h("div", { class: "cols" }, h("div", {}, izq), h("div", {}, der)), h("p", { class: "pie" }, "Rangos de costo: obras similares financiadas u hipótesis del catálogo (sin verificar); ver data/opciones_votacion.json para las fuentes.")));
  }

  // ---------- informe en Markdown ----------
  function construirMarkdown() {
    const e = estado.epoca, r = estado.res, z = estado.zonas.find((x) => x.slug === estado.slug);
    const lineas = ["# Resultados de votación vecinal — " + z.nombre, ""];
    if (e.demo) lineas.push("> **DEMOSTRACIÓN: votos simulados.**", "");
    lineas.push("- Votación: " + e.nombre + " (" + e.estado + ")", "- Período: " + e.abre_en.slice(0, 10) + " a " + e.cierra_en.slice(0, 10), "- Votos en total: " + r.total_votos, "");
    if (!r.publicado) { lineas.push("Los porcentajes se publican al cierre de la votación.", ""); return lineas.join("\n"); }
    lineas.push("| Lugar | Votos | Lo que más piden | Inversión aprox. | Mantención al año |", "| --- | ---: | --- | ---: | ---: |");
    const lista = filas();
    for (const f of lista) {
      const s = estado.sitios[f.sid];
      if (f.oculto) { lineas.push("| " + s.nombre + " | " + f.total + " | (pocos votos para publicar) | — | — |"); continue; }
      const g = f.opciones[0];
      lineas.push("| " + s.nombre + " | " + f.total + " | " + fmt(g.pct) + " % " + nombreOpcion(g.id) + " | " + textoCosto(g.id) + " | $" + fmt(s.mantencion_M[0]) + " a $" + fmt(s.mantencion_M[1]) + " M |");
    }
    lineas.push("");
    for (const f of lista.filter((x) => !x.oculto).slice(0, 10)) {
      const s = estado.sitios[f.sid];
      lineas.push("## " + s.nombre, "", "- Estado del lugar: " + s.semaforo.etiqueta + " — " + s.resumen);
      for (const k of ["sombra", "calor", "verde", "vecinos"]) if (s.datos[k]) lineas.push("- " + s.datos[k].titulo + ": " + (s.datos[k].etiqueta ? s.datos[k].etiqueta + " — " : "") + s.datos[k].texto);
      lineas.push("- Votos: " + f.total);
      f.opciones.forEach((o) => lineas.push("  - " + nombreOpcion(o.id) + ": " + fmt(o.pct) + " % (" + o.votos + " votos)"));
      if (f.otros.length) lineas.push("- Ideas propias (sin revisar): " + f.otros.map((t) => "«" + t + "»").join("; "));
      lineas.push("");
    }
    lineas.push("---", "Los rangos de costo son obras similares financiadas o hipótesis del catálogo (sin verificar). La mantención usa $1.625 a $2.962 por m² al año (hipótesis). Los colores comparan cada lugar con los demás sitios escaneados.");
    return lineas.join("\n");
  }

  function descargarMarkdown() {
    const blob = new Blob([construirMarkdown()], { type: "text/markdown;charset=utf-8" });
    const a = h("a", { href: URL.createObjectURL(blob), download: "votacion-" + estado.slug + ".md" });
    document.body.append(a); a.click(); a.remove();
  }

  // ---------- administración ----------
  function cabeceraAdmin() {
    const t = $("#token").value.trim();
    sessionStorage.setItem("pu_admin", t);
    return { "Content-Type": "application/json", "X-Admin-Token": t };
  }
  async function cerrarAhora() {
    try {
      await pedir("api/votacion/admin/cerrar", { method: "POST", headers: cabeceraAdmin(), body: JSON.stringify({ periodo_id: estado.epoca.id }) });
      $("#msg-admin").textContent = "Votación cerrada.";
      await cargarComuna(estado.slug);
    } catch (e) { $("#msg-admin").textContent = e.message; }
  }
  async function abrirNueva() {
    try {
      await pedir("api/votacion/admin/epocas", { method: "POST", headers: cabeceraAdmin(), body: JSON.stringify({ comuna_slug: estado.slug, nombre: $("#nuevo-nombre").value, dias: Number($("#nuevo-dias").value) }) });
      $("#msg-admin").textContent = "Nueva votación abierta.";
      await cargarComuna(estado.slug);
    } catch (e) { $("#msg-admin").textContent = e.message; }
  }

  iniciar();
})();
