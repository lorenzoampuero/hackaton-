(function () {
  "use strict";

  const NS = "http://www.w3.org/2000/svg";
  const SEM = { verde: { css: "--bueno", clase: "s-bueno" }, amarillo: { css: "--alerta", clase: "s-regular" }, rojo: { css: "--critico", clase: "s-malo" }, gris: { css: "--sin-dato", clase: "s-nodato" } };
  const EDADES = [["menos_18", "Menos de 18"], ["18_29", "18 a 29"], ["30_44", "30 a 44"], ["45_59", "45 a 59"], ["60_mas", "60 o más"]];
  const estado = { zonas: [], catalogo: {}, slug: null, epocas: [], epoca: null, datos: null, sitios: {}, res: null, filas: [], activa: null, filtro: null, mapa: null, capa: null, tarjetas: [] };
  const $ = (s) => document.querySelector(s);
  const fmt = (n, d = 1) => new Intl.NumberFormat("es-CL", { maximumFractionDigits: d }).format(n);
  const moneda = (m) => "$" + fmt(m, 1) + " M";
  const cssVar = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

  // ---------- utilidades (todo texto entra con textContent o nodos de texto) ----------
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
  function S(tag, attrs, ...hijos) {
    const el = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v === false || v === null || v === undefined) continue;
      if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, String(v));
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
  const vacio = (t) => h("p", { class: "vacio" }, t);
  const nombreOpcion = (id) => (id === "otro" ? "Otra idea (texto libre)" : estado.catalogo[id] ? estado.catalogo[id].nombre : id);
  function rangoCosto(id) {
    const o = estado.catalogo[id];
    return o && o.costo_min_M != null && o.costo_max_M != null ? [o.costo_min_M, o.costo_max_M] : null;
  }
  const textoCosto = (id) => { const r = rangoCosto(id); return r ? moneda(r[0]) + " a " + moneda(r[1]) : "Por cotizar"; };
  function recortar(texto, px, tam = 12) {
    const max = Math.max(4, Math.floor(px / (tam * 0.56)));
    return texto.length > max ? texto.slice(0, max - 1) + "…" : texto;
  }
  function bonito(max) {  // techo "redondo" para un eje
    if (max <= 0) return 1;
    const p = Math.pow(10, Math.floor(Math.log10(max)));
    for (const m of [1, 2, 2.5, 5, 10]) if (m * p >= max) return m * p;
    return 10 * p;
  }
  function ejeNice(max, n = 4) {  // techo y paso limpios: 0, 10, 20, 30… en vez de 0, 12.5, 25…
    if (max <= 0) return { max: 1, paso: 0.25 };
    const crudo = max / n, p = Math.pow(10, Math.floor(Math.log10(crudo)));
    const paso = ([1, 2, 2.5, 5, 10].map((m) => m * p).find((s) => s >= crudo)) || 10 * p;
    return { max: paso * Math.ceil(max / paso - 1e-9), paso };
  }
  const fechaCorta = new Intl.DateTimeFormat("es-CL", { day: "numeric", month: "short", timeZone: "UTC" });

  // ---------- tooltip ----------
  const tip = $("#tip");
  function mostrarTip(ev, titulo, filas) {
    tip.replaceChildren(h("div", { class: "t" }, titulo), ...filas.map((f) => h("div", { class: "f" }, f.color ? h("span", { class: "k", style: "background:" + f.color }) : null, h("span", { class: "n" }, f.n), h("b", {}, f.v))));
    tip.hidden = false;
    const w = tip.offsetWidth, hh = tip.offsetHeight;
    let x = ev.clientX + 14, y = ev.clientY + 14;
    if (x + w > window.innerWidth - 8) x = ev.clientX - w - 14;
    if (y + hh > window.innerHeight - 8) y = ev.clientY - hh - 14;
    tip.style.left = Math.max(8, x) + "px";
    tip.style.top = Math.max(8, y) + "px";
  }
  const ocultarTip = () => { tip.hidden = true; };

  // ---------- datos derivados ----------
  function derivar() {
    const r = estado.res, filas = [];
    const totales = r.publicado ? Object.fromEntries(Object.entries(r.sitios).map(([k, v]) => [k, v.total])) : r.votos_por_sitio;
    for (const [sid, total] of Object.entries(totales)) {
      const s = estado.sitios[sid];
      if (!s) continue;
      const d = r.publicado ? r.sitios[sid] : null;
      const oculto = !d || d.oculto;
      filas.push({ sid, s, total, oculto, opciones: d && !d.oculto ? d.opciones : [], otros: d && !d.oculto ? d.otros : [], gan: d && !d.oculto ? d.opciones[0] : null });
    }
    filas.sort((a, b) => b.total - a.total);
    estado.filas = filas;
  }
  const visibles = () => (estado.filtro ? estado.filas.filter((f) => f.gan && f.gan.id === estado.filtro) : estado.filas);

  function agregarOpciones() {
    const m = new Map();
    for (const f of estado.filas) {
      if (f.oculto) continue;
      f.opciones.forEach((o, i) => {
        const a = m.get(o.id) || { id: o.id, nombre: nombreOpcion(o.id), votos: 0, lugares: 0 };
        a.votos += o.votos;
        if (i === 0) a.lugares += 1;
        m.set(o.id, a);
      });
    }
    return [...m.values()].sort((a, b) => b.votos - a.votos);
  }

  function aplicarFiltro(id) {
    estado.filtro = estado.filtro === id ? null : id;
    pintar(false);
  }

  // ---------- tarjetas de gráficos (gráfico o tabla, siempre) ----------
  function vistaTabla(t) {
    return h("table", { class: "vista" }, h("thead", {}, h("tr", {}, t.cab.map((c, i) => h("th", { class: t.nums && t.nums.includes(i) ? "num" : "" }, c)))),
      h("tbody", {}, t.filas.map((fila) => h("tr", {}, fila.map((c, i) => h("td", { class: t.nums && t.nums.includes(i) ? "num" : "" }, c))))));
  }
  function crearTarjeta({ clase, titulo, sub, render, tabla }) {
    const cuerpo = h("div", { class: "cuerpo" });
    const btn = tabla ? h("button", { type: "button", "aria-pressed": "false", title: "Alternar entre gráfico y tabla" }, "Ver tabla") : null;
    const el = h("article", { class: "card " + clase }, h("header", { class: "card-cab" }, h("div", {}, h("h2", {}, titulo), sub ? h("p", { class: "sub" }, sub) : null), btn), cuerpo);
    let enTabla = false;
    const t = {
      el, ancho: 0,
      dibujar() {
        if (!estado.res) return;
        cuerpo.replaceChildren();
        if (enTabla) cuerpo.append(vistaTabla(tabla()));
        else render(cuerpo, cuerpo.clientWidth || 360);
      },
    };
    if (btn) btn.addEventListener("click", () => { enTabla = !enTabla; btn.setAttribute("aria-pressed", String(enTabla)); btn.textContent = enTabla ? "Ver gráfico" : "Ver tabla"; t.dibujar(); });
    new ResizeObserver(() => { if (!enTabla && Math.abs(cuerpo.clientWidth - t.ancho) > 8) { t.ancho = cuerpo.clientWidth; t.dibujar(); } }).observe(cuerpo);
    return t;
  }

  const barraRedondeada = (x, y, w, alto, r) => {
    r = Math.max(0, Math.min(r, alto / 2, w));
    return "M" + x + "," + y + " H" + (x + w - r) + " Q" + (x + w) + "," + y + " " + (x + w) + "," + (y + r) + " V" + (y + alto - r) + " Q" + (x + w) + "," + (y + alto) + " " + (x + w - r) + "," + (y + alto) + " H" + x + " Z";
  };

  // ===== 1) Lo que más piden (barras; sirven también de filtro) =====
  function dibujarOpciones(el, ancho) {
    if (!estado.res.publicado) { el.append(vacio("Los porcentajes de cada idea se publican cuando cierra la votación. Mientras tanto mira la participación y el mapa.")); return; }
    const agg = agregarOpciones();
    if (!agg.length) { el.append(vacio("Ningún lugar llegó al mínimo de votos para mostrar porcentajes.")); return; }
    const total = agg.reduce((a, o) => a + o.votos, 0);
    const top = agg.slice(0, 8);
    const resto = agg.slice(8);
    if (resto.length) top.push({ id: "__resto", nombre: "Otras " + resto.length + " ideas", votos: resto.reduce((a, o) => a + o.votos, 0), lugares: resto.reduce((a, o) => a + o.lugares, 0) });
    const filaH = 30, barH = 16, etiqW = Math.min(210, Math.round(ancho * 0.46)), der = 52;
    const alto = top.length * filaH + 6;
    const esc = (v) => (ancho - etiqW - der) * v / top[0].votos;
    const svg = S("svg", { width: ancho, height: alto, viewBox: "0 0 " + ancho + " " + alto, role: "group", "aria-label": "Votos por tipo de obra" });
    top.forEach((o, i) => {
      const y = i * filaH + 4, activo = !estado.filtro || estado.filtro === o.id, w = Math.max(3, esc(o.votos)), clic = o.id !== "__resto";
      const g = S("g", { class: "fila", tabindex: clic ? 0 : null, role: clic ? "button" : null, "aria-pressed": clic ? String(estado.filtro === o.id) : null, "aria-label": o.nombre + ": " + fmt(o.votos / total * 100) + " % de los votos" });
      g.append(S("rect", { class: "foco", x: 0, y: y - 4, width: ancho, height: filaH, fill: "transparent", rx: 6 }),
        S("text", { x: 0, y: y + barH / 2 + 4 }, recortar(o.nombre, etiqW - 10)),
        S("path", { class: "barra" + (activo ? "" : " apagada"), d: barraRedondeada(etiqW, y, w, barH, 4) }),
        S("text", { class: "val", x: etiqW + w + 8, y: y + barH / 2 + 4 }, fmt(o.votos / total * 100) + " %"));
      g.addEventListener("pointermove", (ev) => mostrarTip(ev, o.nombre, [{ color: cssVar("--serie-1"), n: "Votos", v: fmt(o.votos, 0) }, { n: "Del total", v: fmt(o.votos / total * 100) + " %" }, { n: "Lugares donde gana", v: fmt(o.lugares, 0) }]));
      g.addEventListener("pointerleave", ocultarTip);
      if (clic) {
        g.addEventListener("click", () => aplicarFiltro(o.id));
        g.addEventListener("keydown", (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); aplicarFiltro(o.id); } });
      }
      svg.append(g);
    });
    el.append(svg, h("p", { class: "insight" }, "Haz clic en una barra para ver solo los lugares donde esa idea gana."));
  }
  const tablaOpciones = () => ({ cab: ["Idea", "Votos", "% del total", "Lugares donde gana"], nums: [1, 2, 3], filas: (() => { const a = agregarOpciones(), t = a.reduce((x, o) => x + o.votos, 0) || 1; return a.map((o) => [o.nombre, fmt(o.votos, 0), fmt(o.votos / t * 100) + " %", fmt(o.lugares, 0)]); })() });

  // ===== 2) Votos en el tiempo (línea acumulada) =====
  function serieDiaria() {
    const pd = estado.res.participacion.por_dia;
    if (!pd.length) return [];
    const mapa = Object.fromEntries(pd.map((x) => [x.fecha, x.votos]));
    const dias = [];
    let acum = 0;
    for (let d = new Date(pd[0].fecha + "T00:00:00Z"), fin = new Date(pd[pd.length - 1].fecha + "T00:00:00Z"); d <= fin; d = new Date(d.getTime() + 86400000)) {
      const k = d.toISOString().slice(0, 10), n = mapa[k] || 0;
      acum += n;
      dias.push({ fecha: k, n, acum });
    }
    return dias;
  }
  function dibujarTiempo(el, ancho) {
    const dias = serieDiaria();
    if (dias.length < 2) { el.append(vacio("Todavía no hay suficientes días de votación para dibujar la curva.")); return; }
    const m = { l: 42, r: 74, t: 14, b: 28 }, alto = 230, pw = ancho - m.l - m.r, ph = alto - m.t - m.b;
    const eje = ejeNice(dias[dias.length - 1].acum), ymax = eje.max;
    const X = (i) => m.l + pw * i / (dias.length - 1), Y = (v) => m.t + ph - ph * v / ymax;
    const svg = S("svg", { width: ancho, height: alto, viewBox: "0 0 " + ancho + " " + alto, role: "img", "aria-label": "Votos acumulados por día" });
    for (let v = 0; v <= ymax + 1e-9; v += eje.paso) {
      const y = Y(v);
      svg.append(S("line", { class: "rejilla", x1: m.l, x2: ancho - m.r, y1: y, y2: y }), S("text", { x: m.l - 8, y: y + 4, "text-anchor": "end" }, fmt(v, 0)));
    }
    [0, Math.floor((dias.length - 1) / 2), dias.length - 1].forEach((i, k) => svg.append(S("text", { x: X(i), y: alto - 8, "text-anchor": k === 0 ? "start" : k === 2 ? "end" : "middle" }, fechaCorta.format(new Date(dias[i].fecha + "T00:00:00Z")))));
    const linea = dias.map((d, i) => (i ? "L" : "M") + X(i) + "," + Y(d.acum)).join(" ");
    svg.append(S("path", { class: "area", d: linea + " L" + X(dias.length - 1) + "," + Y(0) + " L" + X(0) + "," + Y(0) + " Z" }), S("path", { class: "linea", d: linea }));
    const ult = dias[dias.length - 1];
    svg.append(S("circle", { class: "punto-fin anillo", cx: X(dias.length - 1), cy: Y(ult.acum), r: 4.5 }),
      S("text", { class: "val", x: X(dias.length - 1) + 10, y: Y(ult.acum) + 4 }, fmt(ult.acum, 0) + " votos"));
    const mira = S("line", { class: "mira", y1: m.t, y2: m.t + ph, visibility: "hidden" }), marca = S("circle", { class: "punto-fin anillo", r: 4.5, visibility: "hidden" });
    const capa = S("rect", { x: m.l, y: m.t, width: pw, height: ph, fill: "transparent" });
    capa.addEventListener("pointermove", (ev) => {
      const rect = svg.getBoundingClientRect(), px = ev.clientX - rect.left - m.l;
      const i = Math.max(0, Math.min(dias.length - 1, Math.round(px / pw * (dias.length - 1)))), d = dias[i];
      mira.setAttribute("x1", X(i)); mira.setAttribute("x2", X(i)); mira.setAttribute("visibility", "visible");
      marca.setAttribute("cx", X(i)); marca.setAttribute("cy", Y(d.acum)); marca.setAttribute("visibility", "visible");
      mostrarTip(ev, fechaCorta.format(new Date(d.fecha + "T00:00:00Z")), [{ color: cssVar("--serie-1"), n: "Votos acumulados", v: fmt(d.acum, 0) }, { n: "Ese día", v: "+" + fmt(d.n, 0) }]);
    });
    capa.addEventListener("pointerleave", () => { mira.setAttribute("visibility", "hidden"); marca.setAttribute("visibility", "hidden"); ocultarTip(); });
    svg.append(mira, marca, capa);
    const mejor = dias.reduce((a, d) => (d.n > a.n ? d : a), dias[0]);
    el.append(svg, h("p", { class: "insight" }, "El día con más votos fue el ", h("b", {}, fechaCorta.format(new Date(mejor.fecha + "T00:00:00Z"))), " (", fmt(mejor.n, 0), " votos)."));
  }
  const tablaTiempo = () => ({ cab: ["Día", "Votos ese día", "Acumulado"], nums: [1, 2], filas: serieDiaria().map((d) => [d.fecha, fmt(d.n, 0), fmt(d.acum, 0)]) });

  // ===== 3) Quiénes votaron (edad) frente a los vecinos del entorno =====
  function referencia60() {
    let num = 0, den = 0;
    for (const f of estado.filas) if (f.s.pct_60_mas != null) { num += f.s.pct_60_mas * f.total; den += f.total; }
    return den ? num / den : null;
  }
  function distribucionEdades() {
    const e = estado.res.participacion.edades, conDato = EDADES.reduce((a, [k]) => a + (e[k] || 0), 0);
    return { conDato, sinDato: e.sin_dato || 0, filas: EDADES.map(([k, nombre]) => ({ k, nombre, n: e[k] || 0, pct: conDato ? 100 * (e[k] || 0) / conDato : 0 })) };
  }
  function dibujarEdades(el, ancho) {
    const d = distribucionEdades();
    if (!d.conDato) { el.append(vacio("Nadie indicó su edad todavía.")); return; }
    const ref = referencia60(), maxv = bonito(Math.max(...d.filas.map((f) => f.pct), ref || 0) * 1.08);
    const filaH = 32, barH = 16, etiqW = 92, der = 50, alto = d.filas.length * filaH + 6;
    const esc = (v) => (ancho - etiqW - der) * v / maxv;
    const svg = S("svg", { width: ancho, height: alto, viewBox: "0 0 " + ancho + " " + alto, role: "img", "aria-label": "Porcentaje de votantes por tramo de edad" });
    d.filas.forEach((f, i) => {
      const y = i * filaH + 5, w = Math.max(3, esc(f.pct)), g = S("g", {});
      g.append(S("rect", { x: 0, y: y - 5, width: ancho, height: filaH, fill: "transparent" }), S("text", { x: 0, y: y + barH / 2 + 4 }, f.nombre),
        S("path", { class: "barra", d: barraRedondeada(etiqW, y, w, barH, 4) }), S("text", { class: "val", x: etiqW + w + 8, y: y + barH / 2 + 4 }, fmt(f.pct, 0) + " %"));
      if (f.k === "60_mas" && ref != null) g.append(S("rect", { class: "rombo", x: etiqW + esc(ref) - 5, y: y + barH / 2 - 5, width: 10, height: 10, transform: "rotate(45 " + (etiqW + esc(ref)) + " " + (y + barH / 2) + ")" }));
      g.addEventListener("pointermove", (ev) => mostrarTip(ev, f.nombre, [{ color: cssVar("--serie-1"), n: "De los votantes", v: fmt(f.pct, 1) + " %" }, { n: "Personas", v: fmt(f.n, 0) }].concat(f.k === "60_mas" && ref != null ? [{ n: "Vecinos 60+ en el entorno", v: fmt(ref, 1) + " %" }] : [])));
      g.addEventListener("pointerleave", ocultarTip);
      svg.append(g);
    });
    const p60 = d.filas.find((f) => f.k === "60_mas").pct;
    let frase = null;
    if (ref != null) frase = p60 < ref - 5 ? ["Faltan voces de 60 años o más: votaron ", h("b", {}, fmt(p60, 0) + " %"), " y viven ", h("b", {}, fmt(ref, 0) + " %"), " cerca de los lugares votados."]
      : ["La participación de 60 años o más (", h("b", {}, fmt(p60, 0) + " %"), ") es parecida a la de los vecinos del entorno (", h("b", {}, fmt(ref, 0) + " %"), ")."];
    el.append(...[svg, h("div", { class: "leyenda" }, h("span", {}, h("i", { class: "llave", style: "background:var(--serie-1)" }), "Votantes"), ref != null ? h("span", {}, h("i", { class: "llave rombo", style: "background:var(--ink)" }), "Vecinos de 60+ cerca (Censo 2024)") : null),
      frase ? h("p", { class: "insight" }, frase) : null, d.sinDato ? h("p", { class: "sub" }, d.sinDato + " persona(s) no indicaron su edad.") : null].filter(Boolean));
  }
  const tablaEdades = () => { const d = distribucionEdades(); return { cab: ["Edad", "Personas", "% de los votantes"], nums: [1, 2], filas: d.filas.map((f) => [f.nombre, fmt(f.n, 0), fmt(f.pct, 1) + " %"]) }; };

  // ===== 4) Necesidad y demanda (dispersión con burbujas) =====
  function dibujarDispersion(el, ancho) {
    const pts = visibles().filter((f) => f.s.semaforo.indice != null).map((f) => ({ f, x: f.s.semaforo.indice, y: f.total, pop: f.s.poblacion_400m || 0 }));
    if (!pts.length) { el.append(vacio("Todavía no hay lugares con votos para comparar.")); return; }
    const m = { l: 44, r: 14, t: 18, b: 44 }, alto = Math.round(Math.min(380, Math.max(250, ancho * 0.6))), pw = ancho - m.l - m.r, ph = alto - m.t - m.b;
    const eje = ejeNice(Math.max(...pts.map((p) => p.y)) * 1.08), ymax = eje.max, maxPop = Math.max(...pts.map((p) => p.pop), 1);
    const X = (v) => m.l + pw * v / 100, Y = (v) => m.t + ph - ph * v / ymax, R = (p) => 5 + 9 * Math.sqrt(p / maxPop);
    const svg = S("svg", { width: ancho, height: alto, viewBox: "0 0 " + ancho + " " + alto, role: "img", "aria-label": "Condición del lugar frente a votos recibidos" });
    for (let v = 0; v <= ymax + 1e-9; v += eje.paso) { svg.append(S("line", { class: "rejilla", x1: m.l, x2: ancho - m.r, y1: Y(v), y2: Y(v) }), S("text", { x: m.l - 8, y: Y(v) + 4, "text-anchor": "end" }, fmt(v, 0))); }
    svg.append(S("rect", { class: "zona", x: X(0), y: Y(ymax), width: X(33) - X(0), height: Y(ymax * 0.5) - Y(ymax) }),
      S("text", { class: "fuerte", x: X(0) + 8, y: Y(ymax) + 16 }, "Prioridad: mala condición y mucha participación"));
    [33, 66].forEach((v) => svg.append(S("line", { class: "rejilla", x1: X(v), x2: X(v), y1: m.t, y2: m.t + ph })));
    [[16.5, "Necesita ayuda"], [49.5, "Regular"], [83, "Buen estado"]].forEach(([v, t]) => svg.append(S("text", { x: X(v), y: alto - 24, "text-anchor": "middle" }, t)));
    svg.append(S("text", { x: m.l + pw / 2, y: alto - 6, "text-anchor": "middle" }, "Condiciones del lugar según el satélite (peor → mejor)"), S("text", { x: m.l, y: m.t - 4 }, "Votos"));
    const circ = pts.map((p) => {
      const c = S("circle", { class: "burbuja anillo" + (estado.activa === p.f.sid ? " sel" : ""), cx: X(p.x), cy: Y(p.y), r: R(p.pop), style: "fill:var(" + SEM[p.f.s.semaforo.color].css + ")" });
      svg.append(c);
      return c;
    });
    const capa = S("rect", { x: m.l, y: m.t, width: pw, height: ph, fill: "transparent", style: "cursor:pointer" });
    let cercano = null;
    const buscar = (ev) => {
      const rect = svg.getBoundingClientRect(), px = ev.clientX - rect.left, py = ev.clientY - rect.top;
      let mejor = null, dmin = 44;
      pts.forEach((p, i) => { const dd = Math.hypot(X(p.x) - px, Y(p.y) - py) - R(p.pop) * 0.4; if (dd < dmin) { dmin = dd; mejor = i; } });
      return mejor;
    };
    capa.addEventListener("pointermove", (ev) => {
      const i = buscar(ev);
      circ.forEach((c, k) => c.classList.toggle("sel", k === i || estado.activa === pts[k].f.sid));
      cercano = i;
      if (i === null) { ocultarTip(); return; }
      const p = pts[i], s = p.f.s;
      mostrarTip(ev, s.nombre, [{ color: cssVar(SEM[s.semaforo.color].css), n: s.semaforo.etiqueta, v: "índice " + fmt(s.semaforo.indice, 0) }, { n: "Votos", v: fmt(p.y, 0) }, { n: "Personas a 400 m", v: p.pop ? fmt(p.pop, 0) : "s/d" }, { n: "Lo más pedido", v: p.f.gan ? nombreOpcion(p.f.gan.id) : "se publica al cierre" }]);
    });
    capa.addEventListener("pointerleave", () => { ocultarTip(); circ.forEach((c, k) => c.classList.toggle("sel", estado.activa === pts[k].f.sid)); });
    capa.addEventListener("click", () => { if (cercano !== null) abrirDetalle(pts[cercano].f.sid); });
    svg.append(capa);
    el.append(svg, h("div", { class: "leyenda" }, ...["rojo", "amarillo", "verde"].map((c) => h("span", {}, h("i", { class: "llave", style: "background:var(" + SEM[c].css + ")" }), { rojo: "Necesita ayuda", amarillo: "Regular", verde: "Buen estado" }[c])), h("span", {}, "Tamaño: personas que viven a 400 m")));
  }
  const tablaDispersion = () => ({ cab: ["Lugar", "Condición", "Índice", "Votos", "Personas a 400 m"], nums: [2, 3, 4], filas: visibles().map((f) => [f.s.nombre, f.s.semaforo.etiqueta, f.s.semaforo.indice != null ? fmt(f.s.semaforo.indice, 0) : "s/d", fmt(f.total, 0), f.s.poblacion_400m ? fmt(f.s.poblacion_400m, 0) : "s/d"]) });

  // ===== 5) Inversión aproximada por tipo de obra (punto + barra de rango) =====
  function inversionPorOpcion() {
    const m = new Map();
    let porCotizar = 0;
    for (const f of visibles()) {
      if (f.oculto || !f.gan) continue;
      const r = rangoCosto(f.gan.id);
      if (!r) { porCotizar += 1; continue; }
      const a = m.get(f.gan.id) || { id: f.gan.id, nombre: nombreOpcion(f.gan.id), min: 0, max: 0, lugares: 0 };
      a.min += r[0]; a.max += r[1]; a.lugares += 1;
      m.set(f.gan.id, a);
    }
    return { filas: [...m.values()].sort((a, b) => b.max - a.max), porCotizar };
  }
  function dibujarInversion(el, ancho) {
    if (!estado.res.publicado) { el.append(vacio("La inversión estimada se calcula al cierre de la votación, con lo más pedido en cada lugar.")); return; }
    const { filas, porCotizar } = inversionPorOpcion();
    if (!filas.length) { el.append(vacio("No hay obras con costo de referencia en esta selección." + (porCotizar ? " " + porCotizar + " lugar(es) quedan por cotizar." : ""))); return; }
    const top = filas.slice(0, 8), filaH = 34, etiqW = Math.min(190, Math.round(ancho * 0.4)), der = 12, m = { t: 6, b: 26 }, alto = top.length * filaH + m.t + m.b;
    const eje = ejeNice(Math.max(...top.map((f) => f.max)) * 1.04), xmax = eje.max, X = (v) => etiqW + (ancho - etiqW - der) * v / xmax;
    const svg = S("svg", { width: ancho, height: alto, viewBox: "0 0 " + ancho + " " + alto, role: "img", "aria-label": "Inversión aproximada por tipo de obra" });
    for (let v = 0, k = 0; v <= xmax + 1e-9; v += eje.paso, k++) { svg.append(S("line", { class: "rejilla", x1: X(v), x2: X(v), y1: m.t, y2: alto - m.b }), S("text", { x: X(v), y: alto - 8, "text-anchor": v + eje.paso > xmax + 1e-9 ? "end" : k === 0 ? "start" : "middle" }, fmt(v, 0))); }
    top.forEach((f, i) => {
      const cy = m.t + i * filaH + filaH / 2, mid = (f.min + f.max) / 2, g = S("g", {});
      g.append(S("rect", { x: 0, y: cy - filaH / 2, width: ancho, height: filaH, fill: "transparent" }), S("text", { x: 0, y: cy + 4 }, recortar(f.nombre + " (" + f.lugares + ")", etiqW - 10)),
        S("line", { x1: X(f.min), x2: X(f.max), y1: cy, y2: cy, stroke: "var(--serie-1)", "stroke-width": 2, "stroke-linecap": "round" }),
        S("line", { x1: X(f.min), x2: X(f.min), y1: cy - 5, y2: cy + 5, stroke: "var(--serie-1)", "stroke-width": 2 }), S("line", { x1: X(f.max), x2: X(f.max), y1: cy - 5, y2: cy + 5, stroke: "var(--serie-1)", "stroke-width": 2 }),
        S("circle", { class: "punto-fin anillo", cx: X(mid), cy, r: 5 }));
      g.addEventListener("pointermove", (ev) => mostrarTip(ev, f.nombre, [{ color: cssVar("--serie-1"), n: "Entre", v: moneda(f.min) + " y " + moneda(f.max) }, { n: "Punto medio", v: moneda(mid) }, { n: "Lugares", v: fmt(f.lugares, 0) }]));
      g.addEventListener("pointerleave", ocultarTip);
      svg.append(g);
    });
    const tMin = filas.reduce((a, f) => a + f.min, 0), tMax = filas.reduce((a, f) => a + f.max, 0);
    el.append(svg, h("div", { class: "leyenda" }, h("span", {}, h("i", { class: "llave", style: "background:var(--serie-1)" }), "Punto medio"), h("span", {}, h("i", { class: "llave linea", style: "background:var(--serie-1)" }), "Rango de mínimo a máximo (millones de pesos)")),
      h("p", { class: "insight" }, "Si se hiciera lo más pedido en cada lugar: ", h("b", {}, moneda(tMin) + " a " + moneda(tMax)), porCotizar ? ". " + porCotizar + " lugar(es) quedan por cotizar (sin costo verificado)." : ".", " Hipótesis, sin verificar."));
  }
  const tablaInversion = () => { const { filas } = inversionPorOpcion(); return { cab: ["Obra", "Lugares", "Mínimo (M)", "Máximo (M)"], nums: [1, 2, 3], filas: filas.map((f) => [f.nombre, fmt(f.lugares, 0), fmt(f.min, 1), fmt(f.max, 1)]) }; };

  // ---------- mapa ----------
  function crearMapa() {
    if (estado.mapa) return;
    estado.mapa = L.map("mapa", { zoomControl: true, scrollWheelZoom: false }).setView([-33.45, -70.67], 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "&copy; OpenStreetMap", maxZoom: 19 }).addTo(estado.mapa);
    estado.capa = L.layerGroup().addTo(estado.mapa);
  }
  function pintarMapa() {
    crearMapa();
    estado.capa.clearLayers();
    const conVotos = new Map(visibles().map((f) => [f.sid, f]));
    const anillo = cssVar("--surface"), gris = cssVar("--apagado");
    for (const s of estado.datos.sitios) {
      if (conVotos.has(s.id)) continue;
      L.circleMarker([s.centro[1], s.centro[0]], { radius: 3, weight: 0, fillColor: gris, fillOpacity: 0.65, interactive: false }).addTo(estado.capa);
    }
    const maxV = Math.max(1, ...[...conVotos.values()].map((f) => f.total)), lim = [];
    for (const f of conVotos.values()) {
      const s = f.s, p = [s.centro[1], s.centro[0]], radio = 6 + 15 * Math.sqrt(f.total / maxV);
      const mk = L.circleMarker(p, { radius: radio, color: anillo, weight: 2, fillColor: cssVar(SEM[s.semaforo.color].css), fillOpacity: 0.86 });
      mk.bindTooltip("<b>" + "" + "</b>", { direction: "top" });
      mk.setTooltipContent(L.DomUtil.create("div"));
      mk.getTooltip().getContent().textContent = s.nombre + " · " + f.total + " votos";
      mk.on("click", () => abrirDetalle(f.sid));
      mk.addTo(estado.capa);
      lim.push(p);
    }
    setTimeout(() => {
      estado.mapa.invalidateSize();
      if (lim.length) estado.mapa.fitBounds(lim, { padding: [40, 40], maxZoom: 16 });
      else if (estado.datos.comuna.bbox) { const b = estado.datos.comuna.bbox; estado.mapa.fitBounds([[b[1], b[0]], [b[3], b[2]]]); }
    }, 60);
  }

  // ---------- encabezado e indicadores ----------
  function contar(el, hasta) {
    const ini = Number(el.dataset.v || 0);
    el.dataset.v = String(hasta);
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || ini === hasta) { el.textContent = fmt(hasta, 0); return; }
    const t0 = performance.now(), dur = 900;
    const paso = (t) => { const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3); el.textContent = fmt(Math.round(ini + (hasta - ini) * e), 0); if (k < 1) requestAnimationFrame(paso); };
    requestAnimationFrame(paso);
  }
  function pintarHero() {
    const e = estado.epoca, r = estado.res, z = estado.zonas.find((x) => x.slug === estado.slug);
    $("#hero-eyebrow").textContent = "Votación vecinal · " + z.nombre;
    $("#hero-titulo").textContent = e.estado === "cerrado" ? "Esto es lo que pidieron los vecinos" : "Los vecinos están votando ahora";
    $("#hero-sub").textContent = e.estado === "cerrado" ? "Resultados por lugar, junto con lo que mide el satélite y la inversión aproximada de cada idea." : "Los porcentajes se publican al cierre. Mientras tanto, sigue cuántos votos llegan y quiénes participan.";
    contar($("#hero-num"), r.total_votos);
    $("#hero-leyenda").textContent = r.total_votos === 1 ? "voto de vecinos" : "votos de vecinos";
    const chips = [h("span", { class: "chip" }, e.nombre), h("span", { class: "chip" }, e.estado === "cerrado" ? "Cerrada" : e.estado === "abierto" ? "Abierta · cierra en " + e.dias_restantes + " día(s)" : "Próxima")];
    if (e.demo) chips.push(h("span", { class: "chip alerta" }, "DEMOSTRACIÓN: votos simulados"));
    chips.push(h("span", { class: "chip" }, estado.filas.length + " lugares con votos"));
    if (r.confianza_global) chips.push(h("span", { class: "chip" }, "Confianza " + ETI_CONF[r.confianza_global.nivel].toLowerCase()));
    if (e.estado === "abierto") chips.push(h("span", { class: "chip vivo" }, h("i", { class: "pulso" }), "En vivo"));
    $("#hero-chips").replaceChildren(...chips);
    const dias = serieDiaria(), cont = $("#hero-spark");
    cont.replaceChildren();
    if (dias.length > 1) {
      const w = 230, hh = 46, mx = dias[dias.length - 1].acum, X = (i) => w * i / (dias.length - 1), Y = (v) => hh - 4 - (hh - 8) * v / mx;
      const l = dias.map((d, i) => (i ? "L" : "M") + X(i) + "," + Y(d.acum)).join(" ");
      cont.append(S("svg", { width: w, height: hh, viewBox: "0 0 " + w + " " + hh }, S("path", { d: l + " L" + w + "," + hh + " L0," + hh + " Z", fill: "#fff", opacity: 0.16 }), S("path", { d: l, fill: "none", stroke: "#fff", "stroke-width": 2, "stroke-linecap": "round" }), S("circle", { cx: w - 1, cy: Y(mx), r: 4.5, fill: "#fff" })));
    }
  }
  function tile(et, val, nota, meter) {
    return h("div", { class: "tile" }, h("div", { class: "et" }, et), h("div", { class: "val" + (String(val).length > 13 ? " largo" : "") }, val), nota ? h("div", { class: "nota" }, nota) : null, meter != null ? h("div", { class: "meter" }, h("i", { style: "width:" + Math.max(2, Math.min(100, meter)) + "%" })) : null);
  }
  const b = (x) => h("b", {}, String(x));
  const confDe = (sid) => (estado.res && estado.res.confianza && estado.res.confianza[sid]) || null;
  const ETI_CONF = { alta: "Alta", media: "Media", baja: "Baja" };
  const pillConf = (c) => (c ? h("span", { class: "conf " + c.nivel, title: c.razones.join(" · ") }, h("i", {}), ETI_CONF[c.nivel] + " · " + c.puntos) : h("span", { class: "pocos" }, "—"));
  function costo5(f) {  // obra + 5 años de mantención del lugar (hipótesis)
    if (f.oculto || !f.gan) return null;
    const r = rangoCosto(f.gan.id);
    if (!r) return null;
    return [r[0] + 5 * f.s.mantencion_M[0], r[1] + 5 * f.s.mantencion_M[1]];
  }
  function totales() {
    const vis = visibles(), conRes = vis.filter((f) => !f.oculto);
    const { filas: inv, porCotizar } = inversionPorOpcion();
    let c5min = 0, c5max = 0;
    conRes.forEach((f) => { const c = costo5(f); if (c) { c5min += c[0]; c5max += c[1]; } });
    return { vis, conRes, inv, porCotizar, tMin: inv.reduce((a, f) => a + f.min, 0), tMax: inv.reduce((a, f) => a + f.max, 0), c5min, c5max, coincide: conRes.filter((f) => estado.sitios[f.sid].opciones.some((o) => o.id === f.gan.id)).length };
  }
  function pintarKpis() {
    const r = estado.res, part = r.participacion, T = totales(), g = r.confianza_global;
    const qr = part.total ? 100 * part.via_qr / part.total : 0;
    const k = [tile("Lugares con votos", fmt(T.vis.length, 0), estado.filtro ? "filtrados por una idea" : "de " + estado.datos.sitios.length + " escaneados en la comuna", 100 * T.vis.length / estado.datos.sitios.length),
      g ? tile("Confianza de los resultados", ETI_CONF[g.nivel] + " · " + g.puntos + "/100", g.razones[0], g.puntos) : null,
      tile("Dijeron entrar por QR", fmt(qr, 0) + " %", fmt(part.via_qr, 0) + " de " + fmt(part.total, 0) + " votos (aún sin firma)", qr)];
    if (r.publicado) {
      k.push(tile("Inversión aprox. de lo más pedido", T.conRes.length && T.inv.length ? moneda(T.tMin) + " a " + moneda(T.tMax) : "—", T.porCotizar ? T.porCotizar + " lugar(es) por cotizar · hipótesis" : "hipótesis (sin verificar)"),
        tile("Costo a 5 años (obra + mantención)", T.c5max ? moneda(T.c5min) + " a " + moneda(T.c5max) : "—", "mantención: $1.625 a $2.962 por m² al año (hipótesis)"),
        tile("Coincide con la recomendación del satélite", T.conRes.length ? fmt(T.coincide, 0) + " de " + fmt(T.conRes.length, 0) : "—", "lo más pedido estaba entre las opciones recomendadas", T.conRes.length ? 100 * T.coincide / T.conRes.length : null));
    } else {
      k.push(tile("Días para el cierre", fmt(estado.epoca.dias_restantes, 0), "cierra el " + estado.epoca.cierra_en.slice(0, 10)), tile("Porcentajes", "Al cierre", "se publican cuando termina la votación"));
    }
    $("#kpis").replaceChildren(...k.filter(Boolean));
  }

  // Hallazgos automáticos: reglas simples sobre los datos, sin IA y sin cifras que no estén en la pantalla.
  function hallazgos() {
    const r = estado.res, e = estado.epoca, vis = estado.filas, out = [];
    if (!vis.length) return [{ n: "info", x: ["Todavía no hay votos en esta votación."] }];
    if (!r.publicado) {
      out.push({ n: "info", x: ["Van ", b(r.total_votos), " votos en ", b(vis.length), " lugares" + (e.dias_restantes ? "; la votación cierra en " + e.dias_restantes + " día(s)." : ".")] });
    } else {
      const agg = agregarOpciones(), tot = agg.reduce((a, o) => a + o.votos, 0) || 1;
      if (agg[0]) out.push({ n: "ok", x: ["Los vecinos piden sobre todo ", b(agg[0].nombre), " (", fmt(agg[0].votos / tot * 100, 0), " % de los votos); es lo más pedido en ", b(agg[0].lugares), " lugares."] });
      const rojos = vis.filter((f) => !f.oculto && f.s.semaforo.color === "rojo");
      if (rojos.length) {
        const m = new Map();
        rojos.forEach((f) => m.set(f.gan.id, (m.get(f.gan.id) || 0) + 1));
        const top = [...m.entries()].sort((a, c) => c[1] - a[1])[0];
        out.push({ n: "alerta", x: ["En ", b(rojos.length), rojos.length === 1 ? " lugar que el satélite marca" : " lugares que el satélite marca", " como «necesita ayuda», lo más pedido es ", b(nombreOpcion(top[0])), " (", top[1], " de ", rojos.length, ")."] });
      }
      const distinto = vis.filter((f) => !f.oculto && !f.s.opciones.some((o) => o.id === f.gan.id));
      if (distinto.length) out.push({ n: "alerta", x: ["En ", b(distinto.length), distinto.length === 1 ? " lugar" : " lugares", " los vecinos pidieron algo distinto a lo que recomendaba el análisis (", distinto.slice(0, 2).map((f) => f.s.nombre).join(", "), distinto.length > 2 ? ", …" : "", "): conviene conversarlo con el municipio."] });
    }
    const ref = referencia60(), ed = distribucionEdades(), p60 = ed.filas.find((f) => f.k === "60_mas").pct;
    if (ed.conDato && ref != null && p60 < ref - 5) out.push({ n: "riesgo", x: ["Faltan voces de 60 años o más: votaron ", b(fmt(p60, 0) + " %"), " y viven ", b(fmt(ref, 0) + " %"), " cerca de los lugares votados."] });
    const bajos = vis.filter((f) => { const c = confDe(f.sid); return c && c.nivel === "baja"; });
    if (bajos.length) out.push({ n: "riesgo", x: [b(bajos.length), bajos.length === 1 ? " lugar tiene confianza baja" : " lugares tienen confianza baja", " (pocos votos o patrones raros, como muchos votos en una hora): conviene verificar", bajos.length === 1 ? "lo" : "los", " antes de decidir."] });
    if (r.publicado) {
      const T = totales();
      if (T.c5max) out.push({ n: "info", x: ["Hacer lo más pedido en cada lugar costaría ", b(moneda(T.c5min) + " a " + moneda(T.c5max)), " en 5 años, contando obra y mantención (hipótesis)."] });
    }
    return out.slice(0, 6);
  }
  function pintarHallazgos() {
    const lista = hallazgos(), ico = { ok: "✓", alerta: "!", riesgo: "▲", info: "i" };
    $("#hallazgos").replaceChildren(h("h2", {}, "Lo que debes saber"), h("p", { class: "sub" }, "Resumen automático a partir de los datos de esta votación."),
      h("ol", {}, lista.map((x) => h("li", {}, h("span", { class: "ico " + x.n, "aria-hidden": "true" }, ico[x.n]), h("div", {}, ...x.x)))));
  }

  // ---------- ranking y detalle ----------
  function pintarTabla() {
    const cuerpo = $("#cuerpo"), vis = visibles(), r = estado.res;
    if (!vis.length) { cuerpo.replaceChildren(h("tr", {}, h("td", { colspan: "6" }, "Todavía no hay votos en esta selección."))); return; }
    cuerpo.replaceChildren(...vis.map((f) => {
      const s = f.s, g = f.gan, c5 = costo5(f);
      return h("tr", { "data-sid": f.sid, class: estado.activa === f.sid ? "activa" : "", onclick: () => abrirDetalle(f.sid) },
        h("td", {}, h("span", { class: "punto " + SEM[s.semaforo.color].clase }), s.nombre, h("div", { class: "pocos" }, s.semaforo.etiqueta + " · " + fmt(s.area_m2, 0) + " m²")),
        h("td", { class: "num" }, fmt(f.total, 0)),
        h("td", {}, pillConf(confDe(f.sid))),
        h("td", {}, !r.publicado ? h("span", { class: "pocos" }, "Se publica al cierre") : f.oculto ? h("span", { class: "pocos" }, "Pocos votos para mostrar") : h("div", { class: "gana" }, h("div", { class: "linea1" }, nombreOpcion(g.id), " ", h("em", {}, fmt(g.pct) + " %")), h("div", { class: "minibarra" }, h("i", { style: "width:" + Math.min(100, g.pct) + "%" })))),
        h("td", { class: "num" }, g && !f.oculto ? textoCosto(g.id) : "—"),
        h("td", { class: "num" }, c5 ? moneda(c5[0]) + " a " + moneda(c5[1]) : f.oculto ? "—" : "Por cotizar"));
    }));
  }
  function bloqueFondos(f) {
    if (!estado.fondos || !f.gan) return null;
    const ids = estado.fondos.por_opcion[f.gan.id] || [];
    if (!ids.length) return [h("h2", {}, "Dónde postular"), h("p", { class: "nota" }, "El catálogo todavía no asocia un fondo a «" + nombreOpcion(f.gan.id) + "». Habría que revisar las bases vigentes con el municipio.")];
    return [h("h2", {}, "Fondos donde podría postularse"), h("p", { class: "nota" }, "Según el catálogo interno de RE-VIDA; hay que confirmar las bases vigentes."),
      ...ids.map((id) => { const fo = estado.fondos.fondos[id]; return h("div", { class: "fondo" }, h("b", {}, fo.nombre), h("small", {}, fo.enfoque), h("small", {}, "Piden: " + fo.requisito_evidencia)); }),
      h("p", { class: "nota" }, "Este informe aporta parte de esa evidencia: demanda vecinal medida, mediciones del lugar y participación local.")];
  }
  function abrirDetalle(sid) {
    estado.activa = sid;
    document.querySelectorAll("#cuerpo tr").forEach((tr) => tr.classList.toggle("activa", tr.dataset.sid === sid));
    const f = estado.filas.find((x) => x.sid === sid), s = estado.sitios[sid], r = estado.res;
    if (!f) return;
    const c = confDe(sid), c5 = costo5(f);
    const izq = [h("h2", {}, s.nombre), h("p", { class: "nota" }, s.tipo + " · " + fmt(s.area_m2, 0) + " m² · " + s.semaforo.etiqueta + (s.semaforo.indice != null ? " (índice " + fmt(s.semaforo.indice, 0) + " de 100)" : "")), h("p", {}, s.resumen)];
    for (const k of ["sombra", "calor", "verde", "vecinos"]) if (s.datos[k]) izq.push(h("div", { class: "dato" }, h("b", {}, s.datos[k].titulo + (s.datos[k].etiqueta ? ": " + s.datos[k].etiqueta : "")), h("small", {}, s.datos[k].texto)));
    izq.push(h("div", { class: "dato" }, h("b", {}, "Mantención aproximada"), h("small", {}, moneda(s.mantencion_M[0]) + " a " + moneda(s.mantencion_M[1]) + " al año (hipótesis: $1.625 a $2.962 por m²)")));
    if (c5) izq.push(h("div", { class: "dato" }, h("b", {}, "Costo a 5 años"), h("small", {}, moneda(c5[0]) + " a " + moneda(c5[1]) + " (obra de lo más pedido + 5 años de mantención; hipótesis)")));
    if (s.poca_confianza) izq.push(h("p", { class: "nota" }, "La lectura satelital tiene poca confianza: verificar en terreno."));
    const der = [];
    if (c) der.push(h("h2", {}, "Confianza del resultado"), h("p", {}, pillConf(c)), h("ul", { class: "razones" }, c.razones.map((x) => h("li", {}, x))));
    der.push(h("h2", {}, "Lo que votaron los vecinos"));
    if (!r.publicado) der.push(h("p", { class: "nota" }, f.total + " voto(s) hasta ahora. Los porcentajes se publican al cierre."));
    else if (f.oculto) der.push(h("p", { class: "nota" }, "Votaron " + f.total + " persona(s): menos del mínimo (" + r.min_votos + ") para publicar porcentajes."));
    else {
      der.push(h("p", { class: "nota" }, f.total + " votos"));
      f.opciones.forEach((o) => der.push(h("div", { class: "barra-res" }, h("div", { class: "fila" }, h("span", {}, nombreOpcion(o.id) + " · " + textoCosto(o.id)), h("b", {}, fmt(o.pct) + " %")), h("div", { class: "minibarra" }, h("i", { style: "width:" + Math.min(100, o.pct) + "%" })))));
      const rec = s.opciones.map((o) => o.id);
      der.push(h("p", { class: "nota" }, f.gan && rec.includes(f.gan.id) ? "Lo más pedido coincide con lo que recomendaba el análisis satelital." : "Lo más pedido es distinto de lo que recomendaba el análisis satelital: conviene revisarlo con el municipio."));
      if (f.otros.length) der.push(h("p", { class: "nota" }, "Ideas escritas por vecinos (texto sin revisar):"), h("ul", {}, f.otros.map((t) => h("li", {}, t))));
      const fondos = bloqueFondos(f);
      if (fondos) der.push(...fondos);
    }
    $("#detalle").replaceChildren(h("div", { class: "caja" }, h("div", { class: "cols" }, h("div", {}, izq), h("div", {}, der))));
    dibujarDispersionOnly();
  }
  function dibujarDispersionOnly() { const t = estado.tarjetas.find((x) => x.id === "dispersion"); if (t) t.t.dibujar(); }

  // ---------- orquestación ----------
  function construirTablero() {
    const tab = $("#tablero");
    const mapaCard = h("article", { class: "card c-7" }, h("header", { class: "card-cab" }, h("div", {}, h("h2", {}, "Mapa de la demanda"), h("p", { class: "sub" }, "El tamaño del círculo son los votos; el color, cómo está el lugar según el satélite."))),
      h("div", { id: "mapa", role: "application", "aria-label": "Mapa de lugares con votos" }),
      h("div", { class: "leyenda" }, ...["rojo", "amarillo", "verde"].map((c) => h("span", {}, h("i", { class: "llave", style: "background:var(" + SEM[c].css + ")" }), { rojo: "Necesita ayuda", amarillo: "Regular", verde: "Buen estado" }[c])), h("span", {}, h("i", { class: "llave", style: "background:var(--apagado)" }), "Sin votos")));
    const defs = [
      { id: "opciones", clase: "c-5", titulo: "Lo que más piden", sub: "Porcentaje de los votos por tipo de obra", render: dibujarOpciones, tabla: tablaOpciones },
      { id: "tiempo", clase: "c-7", titulo: "Votos en el tiempo", sub: "Votos acumulados por día", render: dibujarTiempo, tabla: tablaTiempo },
      { id: "edades", clase: "c-5", titulo: "Quiénes votaron", sub: "Edad de los votantes frente a los vecinos del entorno", render: dibujarEdades, tabla: tablaEdades },
      { id: "dispersion", clase: "c-7", titulo: "Necesidad y demanda", sub: "Cada círculo es un lugar: abajo a la izquierda, mala condición y pocos votos", render: dibujarDispersion, tabla: tablaDispersion },
      { id: "inversion", clase: "c-5", titulo: "Inversión aproximada por tipo de obra", sub: "Suma de lo más pedido en cada lugar", render: dibujarInversion, tabla: tablaInversion },
    ];
    estado.tarjetas = defs.map((d) => ({ id: d.id, t: crearTarjeta(d) }));
    tab.replaceChildren(mapaCard, ...estado.tarjetas.map((x) => x.t.el), crearCardComparar());
    crearMapa();
  }
  function actualizarChip() {
    const c = $("#chip-filtro");
    c.hidden = !estado.filtro;
    if (estado.filtro) c.textContent = "Mostrando solo lugares donde gana: " + nombreOpcion(estado.filtro) + "  ✕";
  }
  function pintar(reiniciarDetalle = true) {
    derivar();
    const e = estado.epoca, avisos = [];
    if (e.demo) avisos.push(h("div", { class: "aviso-demo" }, "DEMOSTRACIÓN: estos votos son simulados y no representan a ningún vecino real."));
    if (!estado.res.publicado) avisos.push(h("div", { class: "aviso" }, "Esta votación sigue abierta" + (e.dias_restantes ? " (cierra en " + e.dias_restantes + " día(s))" : "") + ". Los porcentajes se publican al cierre para que nadie vote siguiendo a la mayoría."));
    $("#avisos").replaceChildren(...avisos);
    if (estado.filtro && !estado.filas.some((f) => f.gan && f.gan.id === estado.filtro)) estado.filtro = null;
    actualizarChip();
    pintarHero(); pintarKpis(); pintarHallazgos(); pintarTabla(); pintarMapa();
    estado.tarjetas.forEach((x) => x.t.dibujar());
    const vis = visibles();
    if (reiniciarDetalle || !vis.some((f) => f.sid === estado.activa)) { if (vis[0]) abrirDetalle(vis[0].sid); else $("#detalle").replaceChildren(); }
  }

  async function iniciar() {
    aplicarTemaInicial();
    try {
      const [cat, ideas, zonas, fondos] = await Promise.all([pedir("data/vecino/opciones.json"), pedir("data/vecino/ideas.json"), pedir("api/votacion/zonas"), pedir("data/vecino/fondos.json").catch(() => null)]);
      estado.fondos = fondos;
      ideas.ideas.forEach((o) => { estado.catalogo[o.id] = { ...o, costo_min_M: null, costo_max_M: null }; });
      cat.opciones.forEach((o) => { estado.catalogo[o.id] = o; });
      estado.zonas = zonas.zonas;
    } catch (e) {
      $("#avisos").replaceChildren(h("div", { class: "aviso" }, "No pudimos cargar los datos. Abre esta página desde el servidor de RE-VIDA. " + e.message));
      return;
    }
    construirTablero();
    const sel = $("#sel-comuna");
    sel.replaceChildren(...estado.zonas.map((z) => h("option", { value: z.slug }, z.nombre)));
    sel.addEventListener("change", () => { estado.filtro = null; cargarComuna(sel.value); });
    $("#sel-epoca").addEventListener("change", () => { estado.filtro = null; elegirEpoca($("#sel-epoca").value); });
    $("#chip-filtro").addEventListener("click", () => aplicarFiltro(estado.filtro));
    $("#btn-md").addEventListener("click", descargarMarkdown);
    $("#btn-pdf").addEventListener("click", () => window.print());
    $("#btn-geo").addEventListener("click", descargarGeoJSON);
    $("#btn-csv").addEventListener("click", descargarCSV);
    $("#btn-cerrar").addEventListener("click", cerrarAhora);
    $("#btn-nueva").addEventListener("click", abrirNueva);
    $("#btn-tema").addEventListener("click", alternarTema);
    const token = (() => { try { return sessionStorage.getItem("pu_admin"); } catch (_e) { return null; } })();
    if (token) $("#token").value = token;
    await cargarComuna(estado.zonas[0].slug);
    cargarComparacion();
  }
  async function cargarComuna(slug) {
    estado.slug = slug; estado.activa = null;
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
    pintar(true);
    programarVivo();
  }


  // ---------- en vivo ----------
  let reloj = null;
  function programarVivo() {
    clearInterval(reloj);
    if (estado.epoca && estado.epoca.estado === "abierto") reloj = setInterval(refrescarVivo, 15000);
  }
  async function refrescarVivo() {
    if (document.hidden || !estado.epoca) return;
    try {
      const r = await pedir("api/votacion/resultados?periodo_id=" + encodeURIComponent(estado.epoca.id));
      if (r.epoca.estado !== estado.epoca.estado) { await cargarComuna(estado.slug); return; }
      if (r.total_votos !== estado.res.total_votos) {
        const nuevos = r.total_votos - estado.res.total_votos;
        estado.res = r;
        pintar(false);
        avisar((nuevos > 0 ? "+" + nuevos + " voto(s) nuevo(s)" : "Resultados actualizados"));
      }
    } catch (_e) { /* sin red: se reintenta */ }
  }
  let temporizadorAviso = null;
  function avisar(texto) {
    const el = $("#toast");
    el.textContent = texto;
    el.hidden = false;
    clearTimeout(temporizadorAviso);
    temporizadorAviso = setTimeout(() => { el.hidden = true; }, 3500);
  }

  // ---------- comparar comunas ----------
  function crearCardComparar() {
    return h("article", { class: "card c-12", id: "card-comparar" },
      h("header", { class: "card-cab" }, h("div", {}, h("h2", {}, "Comparar comunas"), h("p", { class: "sub" }, "Lo que piden en cada comuna, en su votación más reciente. Haz clic en una fila para abrirla."))),
      h("div", { class: "cuerpo", id: "comparar-cuerpo" }, vacio("Cargando comparación…")));
  }
  function topDe(res) {
    const m = new Map();
    let tot = 0;
    for (const d of Object.values(res.sitios || {})) {
      if (d.oculto) continue;
      for (const o of d.opciones) { m.set(o.id, (m.get(o.id) || 0) + o.votos); tot += o.votos; }
    }
    const t = [...m.entries()].sort((a, c) => c[1] - a[1])[0];
    return t ? { id: t[0], pct: 100 * t[1] / tot } : null;
  }
  async function cargarComparacion() {
    const cont = $("#comparar-cuerpo");
    if (!cont) return;
    try {
      const filas = await Promise.all(estado.zonas.map(async (z) => {
        const per = (await pedir("api/votacion/periodos?comuna=" + encodeURIComponent(z.slug))).periodos;
        const ep = per.find((e) => e.estado === "cerrado" && !e.demo) || per.find((e) => e.estado === "cerrado") || per[0];
        const res = await pedir("api/votacion/resultados?periodo_id=" + encodeURIComponent(ep.id));
        return { z, ep, res, top: res.publicado ? topDe(res) : null };
      }));
      const maxV = Math.max(1, ...filas.map((f) => f.res.total_votos));
      cont.replaceChildren(h("div", { class: "tabla-caja" }, h("table", { class: "comparar-tabla" },
        h("thead", {}, h("tr", {}, ["Comuna", "Votos", "Lugares con votos", "Lo más pedido", "Confianza", "Votación"].map((c) => h("th", {}, c)))),
        h("tbody", {}, filas.map((f) => h("tr", { class: f.z.slug === estado.slug ? "actual" : "", tabindex: "0", onclick: () => abrirComuna(f.z.slug), onkeydown: (ev) => { if (ev.key === "Enter") abrirComuna(f.z.slug); } },
          h("td", {}, b(f.z.nombre)),
          h("td", {}, h("div", { class: "barra-comp" }, h("div", { class: "minibarra" }, h("i", { style: "width:" + (100 * f.res.total_votos / maxV) + "%" })), b(fmt(f.res.total_votos, 0)))),
          h("td", {}, fmt(Object.keys(f.res.publicado ? f.res.sitios : f.res.votos_por_sitio).length, 0)),
          h("td", {}, f.top ? [nombreOpcion(f.top.id), " ", h("span", { class: "pocos" }, fmt(f.top.pct, 0) + " %")] : h("span", { class: "pocos" }, f.res.publicado ? "Sin lugares con votos suficientes" : "Se publica al cierre")),
          h("td", {}, f.res.total_votos ? pillConf(f.res.confianza_global) : h("span", { class: "pocos" }, "Sin votos")),
          h("td", {}, f.ep.nombre.replace(/ \(votos simulados\)/, "") + (f.ep.demo ? " · DEMO" : "") + " · " + ({ abierto: "abierta", cerrado: "cerrada", proximo: "próxima" })[f.ep.estado])))))));
    } catch (e) { cont.replaceChildren(vacio("No pudimos cargar la comparación: " + e.message)); }
  }
  function abrirComuna(slug) {
    estado.filtro = null;
    $("#sel-comuna").value = slug;
    cargarComuna(slug).then(() => window.scrollTo({ top: 0, behavior: "smooth" }));
  }

  // ---------- exportar mapa y datos ----------
  function filasExport() {
    return estado.filas.map((f) => {
      const s = f.s, g = f.gan, r = g ? rangoCosto(g.id) : null, c5 = costo5(f), c = confDe(f.sid);
      return { id: f.sid, nombre: s.nombre, tipo: s.tipo, area_m2: s.area_m2, votos: f.total, idea_ganadora: g ? nombreOpcion(g.id) : "", porcentaje: g ? g.pct : "", inversion_min_M: r ? r[0] : "", inversion_max_M: r ? r[1] : "",
        mantencion_anual_min_M: s.mantencion_M[0], mantencion_anual_max_M: s.mantencion_M[1], costo_5_anios_min_M: c5 ? c5[0] : "", costo_5_anios_max_M: c5 ? c5[1] : "",
        condicion: s.semaforo.etiqueta, indice_condicion: s.semaforo.indice == null ? "" : s.semaforo.indice, confianza: c ? c.nivel : "", confianza_puntos: c ? c.puntos : "" };
    });
  }
  function bajar(nombre, mime, texto) {
    const a = h("a", { href: URL.createObjectURL(new Blob([texto], { type: mime })), download: nombre });
    document.body.append(a); a.click(); a.remove();
  }
  function descargarGeoJSON() {
    const meta = Object.fromEntries(filasExport().map((x) => [x.id, x]));
    const fc = { type: "FeatureCollection", name: "revida-" + estado.slug, features: estado.filas.map((f) => ({ type: "Feature", geometry: estado.sitios[f.sid].geometria, properties: meta[f.sid] })) };
    bajar("revida-" + estado.slug + ".geojson", "application/geo+json;charset=utf-8", JSON.stringify(fc));
  }
  function descargarCSV() {
    const datos = filasExport();
    if (!datos.length) return;
    const cols = Object.keys(datos[0]), cel = (v) => { const s = String(v); return /[";\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
    bajar("revida-" + estado.slug + ".csv", "text/csv;charset=utf-8", "﻿" + [cols.join(";"), ...datos.map((d) => cols.map((c) => cel(d[c])).join(";"))].join("\n"));
  }

  // ---------- tema ----------
  function aplicarTemaInicial() {
    try { const t = localStorage.getItem("pu_tema"); if (t === "light" || t === "dark") document.documentElement.setAttribute("data-theme", t); } catch (_e) { /* sin almacenamiento */ }
  }
  function alternarTema() {
    const oscuro = (document.documentElement.getAttribute("data-theme") || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")) === "dark";
    const nuevo = oscuro ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", nuevo);
    try { localStorage.setItem("pu_tema", nuevo); } catch (_e) { /* sin almacenamiento */ }
    if (estado.res) pintar(false);
  }

  // ---------- informe en Markdown ----------
  function construirMarkdown() {
    const e = estado.epoca, r = estado.res, z = estado.zonas.find((x) => x.slug === estado.slug);
    const l = ["# Resultados de votación vecinal — " + z.nombre, ""];
    if (e.demo) l.push("> **DEMOSTRACIÓN: votos simulados.**", "");
    l.push("- Votación: " + e.nombre + " (" + e.estado + ")", "- Período: " + e.abre_en.slice(0, 10) + " a " + e.cierra_en.slice(0, 10), "- Votos en total: " + r.total_votos, "- Entraron por QR: " + r.participacion.via_qr, "");
    if (!r.publicado) { l.push("Los porcentajes se publican al cierre de la votación.", ""); return l.join("\n"); }
    const agg = agregarOpciones(), tot = agg.reduce((a, o) => a + o.votos, 0) || 1;
    l.push("## Lo que más piden", "", "| Idea | Votos | % | Lugares donde gana |", "| --- | ---: | ---: | ---: |", ...agg.map((o) => "| " + o.nombre + " | " + o.votos + " | " + fmt(o.votos / tot * 100) + " % | " + o.lugares + " |"), "");
    l.push("## Lugares", "", "| Lugar | Votos | Lo que más piden | Inversión aprox. | Mantención al año |", "| --- | ---: | --- | ---: | ---: |");
    for (const f of estado.filas) {
      const s = f.s;
      if (f.oculto) { l.push("| " + s.nombre + " | " + f.total + " | (pocos votos para publicar) | — | — |"); continue; }
      l.push("| " + s.nombre + " | " + f.total + " | " + fmt(f.gan.pct) + " % " + nombreOpcion(f.gan.id) + " | " + textoCosto(f.gan.id) + " | " + moneda(s.mantencion_M[0]) + " a " + moneda(s.mantencion_M[1]) + " |");
    }
    l.push("");
    for (const f of estado.filas.filter((x) => !x.oculto).slice(0, 10)) {
      const s = f.s;
      l.push("### " + s.nombre, "", "- Estado del lugar: " + s.semaforo.etiqueta + " — " + s.resumen);
      for (const k of ["sombra", "calor", "verde", "vecinos"]) if (s.datos[k]) l.push("- " + s.datos[k].titulo + ": " + (s.datos[k].etiqueta ? s.datos[k].etiqueta + " — " : "") + s.datos[k].texto);
      f.opciones.forEach((o) => l.push("  - " + nombreOpcion(o.id) + ": " + fmt(o.pct) + " % (" + o.votos + " votos)"));
      l.push("");
    }
    l.push("---", "Los rangos de costo son obras similares financiadas o hipótesis del catálogo (sin verificar). La mantención usa $1.625 a $2.962 por m² al año (hipótesis). Los colores comparan cada lugar con los demás sitios escaneados.");
    return l.join("\n");
  }
  function descargarMarkdown() {
    const blob = new Blob([construirMarkdown()], { type: "text/markdown;charset=utf-8" });
    const a = h("a", { href: URL.createObjectURL(blob), download: "votacion-" + estado.slug + ".md" });
    document.body.append(a); a.click(); a.remove();
  }

  // ---------- administración ----------
  function cabeceraAdmin() {
    const t = $("#token").value.trim();
    try { sessionStorage.setItem("pu_admin", t); } catch (_e) { /* sin almacenamiento */ }
    return { "Content-Type": "application/json", "X-Admin-Token": t };
  }
  async function cerrarAhora() {
    try { await pedir("api/votacion/admin/cerrar", { method: "POST", headers: cabeceraAdmin(), body: JSON.stringify({ periodo_id: estado.epoca.id }) }); $("#msg-admin").textContent = "Votación cerrada."; await cargarComuna(estado.slug); }
    catch (e) { $("#msg-admin").textContent = e.message; }
  }
  async function abrirNueva() {
    try { await pedir("api/votacion/admin/epocas", { method: "POST", headers: cabeceraAdmin(), body: JSON.stringify({ comuna_slug: estado.slug, nombre: $("#nuevo-nombre").value, dias: Number($("#nuevo-dias").value) }) }); $("#msg-admin").textContent = "Nueva votación abierta."; await cargarComuna(estado.slug); }
    catch (e) { $("#msg-admin").textContent = e.message; }
  }

  iniciar();
})();
