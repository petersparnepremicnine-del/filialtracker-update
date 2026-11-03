// Monatsupdate als PowerPoint: node build_pptx.js data.json map.png out.pptx
// data.json = Ausgabe von make_data.py (dieselben Inhalte wie die Infografik), map.png = render_map.js
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const [dataPath, mapPath, outPath] = process.argv.slice(2);
const D = JSON.parse(fs.readFileSync(dataPath, "utf8"));
const SKILL = process.env.PPTX_SKILL_DIR || "";

const THEME = {
  name: "Filialtracker",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "0B0B0B", lt1: "FFFFFF", dk2: "006B3B", lt2: "EEF6F1",
    accent1: "008349", accent2: "E3051B", accent3: "EDA100", accent4: "2A78D6",
    accent5: "E87BA4", accent6: "8CCAA6", hlink: "2A78D6", folHlink: "6250D6",
  },
};
const HEX = { green: "008349", dgreen: "006B3B", red: "E3051B", amber: "EDA100", blue: "2A78D6", pink: "E87BA4",
  lgreen: "8CCAA6", grey: "8A8984", text: "0B0B0B", muted: "52514E", line: "DFE9E3", tint: "EEF6F1", white: "FFFFFF" };
const TYPE = {
  open: { color: HEX.green, label: "Neueröffnung", sym: "+" },
  reopen: { color: HEX.green, label: "Wiedereröffnung", sym: "+" },
  close: { color: HEX.red, label: "Schließung", sym: "×" },
  seasonal: { color: HEX.grey, label: "Vermutlich geschlossen", sym: "○" },
  switch: { color: HEX.pink, label: "Kettenwechsel", sym: "⇄" },
  reno: { color: HEX.amber, label: "Renovierung", sym: "■" },
  pipe: { color: HEX.blue, label: "Geplant / erwartet", sym: "▲" },
  neutral: { color: HEX.muted, label: "Hinweis", sym: "i" },
};
const W = 13.333, H = 7.5, M = 0.6;
const fmt = (n) => Number(n).toLocaleString("de-DE");
const dm = (iso) => { const [y, m, d] = iso.split("-").map(Number); return `${d}.${m}.`; };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.title = `${D.title} – ${D.edition}`;
pres.subject = "Filial-Tracker Slowenien";
pres.author = "Filial-Tracker (automatisch erstellt)";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };

// ---------------------------------------------------------------- layouts
const footer = `${D.title} · ${D.edition} · Stand ${D.stand}`;
pres.defineSlideMaster({
  title: "Titel",
  background: { color: HEX.green },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 2.3, w: W - 2 * M, h: 1.6, fontSize: 44, bold: true, color: HEX.white, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: M, y: 4.05, w: W - 2 * M, h: 1.4, fontSize: 20, color: "D6EEDF", valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "Inhalt",
  background: { color: HEX.white },
  margin: [0.4, M, 0.6, M],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.35, w: W - 2 * M, h: 0.75, fontSize: 32, bold: true, color: HEX.dgreen, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: M, y: 1.05, w: W - 2 * M, h: 0.4, fontSize: 14, color: HEX.text, valign: "top", align: "left", margin: 0 }, text: "" } },
    { text: { text: footer, options: { x: M, y: H - 0.45, w: 9, h: 0.3, fontSize: 10, color: HEX.muted, margin: 0, isTextBox: true } } },
  ],
  slideNumber: { x: W - M - 0.6, y: H - 0.45, w: 0.6, h: 0.3, fontSize: 10, color: HEX.muted, align: "right" },
});

function slideBase(title, sub, section) {
  const s = pres.addSlide({ masterName: "Inhalt", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  if (sub) s.addText(sub, { placeholder: "body", color: HEX.muted });
  return s;
}
function badge(s, x, y, t, size = 0.36) {
  const tp = TYPE[t] || TYPE.neutral;
  s.addShape(pres.shapes.OVAL, { x, y, w: size, h: size, fill: { color: tp.color }, line: { color: tp.color }, objectName: `Symbol ${tp.label}` });
  s.addText(tp.sym, { x, y, w: size, h: size, fontSize: size * 34, bold: true, color: HEX.white, align: "center", valign: "middle", margin: 0, isTextBox: true });
}
function card(s, x, y, w, h, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: HEX.white }, line: { color: HEX.line, width: 1 },
    shadow: { type: "outer", color: "000000", opacity: 0.10, blur: 6, offset: 2, angle: 90 }, objectName: name });
}

// ---------------------------------------------------------------- 1 title
pres.addSection({ title: "Überblick" });
{
  const s = pres.addSlide({ masterName: "Titel", sectionTitle: "Überblick" });
  s.addText(D.title, { placeholder: "title" });
  s.addText([
    { text: D.edition, options: { bold: true, breakLine: true } },
    { text: `Stand ${D.stand} · Zeitraum ${D.period}` },
  ], { placeholder: "body" });
  s.addText("Quelle: Filialliste auf der Website jeder Kette (Filial-Tracker Slowenien)", { x: M, y: H - 0.8, w: 9, h: 0.35, fontSize: 12, color: HEX.tint, margin: 0, isTextBox: true });
  s.addNotes("Monatsupdate des Filial-Trackers. Zahlen: gezählte Lebensmittelgeschäfte laut Filialliste der Ketten.");
}

// ---------------------------------------------------------------- 2 KPIs
{
  const s = slideBase("Auf einen Blick", `Zeitraum ${D.period}`, "Überblick");
  const acc = { neutral: HEX.dgreen, open: HEX.green, close: HEX.red, switch: HEX.pink, reno: HEX.amber, pipe: HEX.blue };
  const cw = (W - 2 * M - 2 * 0.35) / 3, ch = 2.45;
  D.kpis.forEach((k, i) => {
    const x = M + (i % 3) * (cw + 0.35), y = 1.7 + Math.floor(i / 3) * (ch + 0.35);
    card(s, x, y, cw, ch, `Kennzahl ${k.label}`);
    if (k.accent !== "neutral") badge(s, x + 0.3, y + 0.3, k.accent, 0.34);
    s.addText(k.label, { x: x + (k.accent !== "neutral" ? 0.78 : 0.3), y: y + 0.27, w: cw - 1, h: 0.4, fontSize: 16, bold: true, color: HEX.muted, margin: 0, isTextBox: true });
    s.addText(k.value, { x: x + 0.3, y: y + 0.8, w: cw - 0.6, h: 0.95, fontSize: 60, bold: true, color: acc[k.accent] || HEX.text, margin: 0, isTextBox: true });
    s.addText(k.sub, { x: x + 0.3, y: y + 1.75, w: cw - 0.6, h: 0.55, fontSize: 14, color: HEX.muted, margin: 0, valign: "top", isTextBox: true });
  });
  s.addNotes("Gezählt = Lebensmittelgeschäft, nicht geschlossen, keine erwartete Eröffnung. Franchise bleibt bei der Kette, die die Filiale listet.");
}

// ---------------------------------------------------------------- 3 Was ist neu
pres.addSection({ title: "Änderungen" });
{
  const s = slideBase("Was ist neu", "Die wichtigsten Änderungen im Zeitraum", "Änderungen");
  const cards = D.news;
  const big = cards[0];
  const rest = cards.slice(1, 4);
  const x0 = M, y0 = 1.65, wBig = 6.3, hAll = H - y0 - 0.75;
  function drawCard(c, x, y, w, h, cols, compact) {
    card(s, x, y, w, h, `Karte ${c.head}`);
    badge(s, x + 0.25, y + 0.25, c.type, 0.34);
    const top = compact ? -0.22 : 0;   // compact cards: no tag line
    if (!compact) s.addText((c.tag || TYPE[c.type].label).toUpperCase(), { x: x + 0.72, y: y + 0.2, w: w - 1, h: 0.25, fontSize: 10, bold: true, color: HEX.muted, charSpacing: 1, margin: 0, isTextBox: true });
    s.addText(c.head, { x: x + 0.72, y: y + 0.42 + top, w: w - 0.95, h: 0.35, fontSize: 16, bold: true, color: HEX.text, margin: 0, isTextBox: true });
    const its = c.items || [];
    if (its.length) {
      const per = Math.ceil(its.length / cols), colW = (w - 0.95) / cols;
      // compact items are one paragraph each; estimate wrapping (≈11 characters per inch at 13 pt)
      const cap = Math.max(10, Math.floor((colW - 0.15) * 11));
      const wrapLines = Math.max(...its.map((it) => Math.ceil((it.town.length + 2 + it.name.length) / cap)));
      const lineH = compact ? 0.27 * wrapLines + 0.05 : 0.78;
      for (let ci = 0; ci < cols; ci++) {
        const part = its.slice(ci * per, (ci + 1) * per);
        if (!part.length) continue;
        const runs = [];
        part.forEach((it, j) => {
          const last = j === part.length - 1;
          if (compact) {
            runs.push({ text: it.town + ": ", options: { bold: true, fontSize: 13, color: HEX.text } });
            runs.push({ text: it.name, options: { fontSize: 13, color: HEX.muted, breakLine: !last } });
          } else {
            runs.push({ text: it.town, options: { bold: true, fontSize: 15, color: HEX.text, breakLine: true } });
            runs.push({ text: it.name, options: { fontSize: 12, color: HEX.muted, breakLine: !last, paraSpaceAfter: 12 } });
          }
        });
        s.addText(runs, { x: x + 0.72 + ci * colW, y: y + 0.95 + top, w: colW - 0.15, h: per * lineH + 0.1, valign: "top", margin: 0, fit: "none", isTextBox: true });
      }
      const ny = compact ? y + 0.95 + top + per * lineH + 0.08 : y + h - 0.55;
      if (c.note) s.addText(c.note, { x: x + 0.72, y: ny, w: w - 0.95, h: compact ? 0.3 : 0.45, fontSize: 11, italic: true, color: HEX.muted, valign: compact ? "top" : "bottom", margin: 0, isTextBox: true });
    } else {
      s.addText(c.body || "", { x: x + 0.72, y: y + 0.9, w: w - 0.95, h: h - 1.1, fontSize: 13, color: HEX.text, valign: "top", margin: 0, isTextBox: true });
    }
  }
  if (big) drawCard(big, x0, y0, wBig, hAll, 2, false);
  const xr = x0 + wBig + 0.35, wr = W - M - xr, gap = 0.25;
  const hr = rest.length ? (hAll - gap * (rest.length - 1)) / rest.length : 0;
  rest.forEach((c, i) => drawCard(c, xr, y0 + i * (hr + gap), wr, hr, (c.items || []).length > 1 ? 2 : 1, true));
  s.addNotes("Schließung = nicht mehr auf der Website oder an allen Tagen Mo–So geschlossen. Kettenwechsel werden als Wechsel geführt, nicht als Schließung und Neueröffnung.");
}

// ---------------------------------------------------------------- 4 Karte
{
  const s = slideBase("Wo sich etwas getan hat", "Ereignisse des Zeitraums nach Ort (Postort der Filiale)", "Änderungen");
  const imgW = 8.4, imgH = imgW * 1178 / 2150;
  s.addImage({ path: mapPath, x: M, y: 1.75, w: imgW, h: imgH, altText: "Karte Sloweniens mit den Ereignissen des Monats", objectName: "Karte" });
  const counts = {};
  for (const p of D.map_points) counts[p.type] = (counts[p.type] || 0) + 1;
  const order = ["open", "close", "seasonal", "switch", "reno", "pipe"];
  const x = M + imgW + 0.4; let y = 1.9;
  s.addText("Legende (Orte)", { x, y, w: W - M - x, h: 0.35, fontSize: 16, bold: true, color: HEX.text, margin: 0, isTextBox: true });
  y += 0.55;
  order.forEach((t) => {
    badge(s, x, y, t, 0.34);
    s.addText([{ text: TYPE[t].label, options: { bold: true, breakLine: true } }, { text: `${counts[t] || 0} Ort${(counts[t] || 0) === 1 ? "" : "e"}`, options: { color: HEX.muted, fontSize: 12 } }],
      { x: x + 0.5, y: y - 0.06, w: W - M - x - 0.5, h: 0.55, fontSize: 14, color: HEX.text, margin: 0, valign: "top", isTextBox: true });
    y += 0.68;
  });
  s.addNotes("Jeder Ort zeigt pro Ereignistyp ein Symbol. Mehrere Filialen im selben Ort ergeben ein Symbol.");
}

// ---------------------------------------------------------------- 5 Renovierungen
{
  const s = slideBase("Renovierungen und Schließzeiten", "Laufende, geplante und kürzlich abgeschlossene Renovierungen", "Änderungen");
  const head = ["Filiale", "Ort", "Status", "Umfang", "Zeitraum", "Hinweis"].map((t) => ({ text: t, options: { bold: true, color: HEX.white, fill: { color: HEX.dgreen } } }));
  const stCol = { Laufend: HEX.amber, Geplant: HEX.blue, Abgeschlossen: HEX.grey };
  const rows = D.gantt.rows.map((r, i) => {
    const fill = { color: i % 2 ? HEX.white : HEX.tint };
    const period = `${r.open_start ? "bis " : dm(r.start) + " – "}${r.open_end ? "offen" : dm(r.end)}`.replace("bis bis", "bis");
    return [
      { text: r.label, options: { fill, bold: true } },
      { text: r.town, options: { fill } },
      { text: r.status, options: { fill, bold: true, color: stCol[r.status] === HEX.grey ? HEX.muted : (r.status === "Laufend" ? "9A6A00" : HEX.blue) } },
      { text: r.scope, options: { fill } },
      { text: r.open_start ? `bis ${r.open_end ? "offen" : dm(r.end)}` : period, options: { fill } },
      { text: r.note, options: { fill } },
    ];
  });
  s.addTable([head, ...rows], { x: M, y: 1.7, w: W - 2 * M, colW: [3.9, 1.7, 1.4, 1.1, 1.6, 2.433], fontSize: 13, color: HEX.text,
    border: { type: "solid", pt: 0.5, color: HEX.line }, rowH: 0.42, valign: "middle", margin: [0.04, 0.1, 0.04, 0.1] });
  if (D.gantt.footnote) s.addText(D.gantt.footnote, { x: M, y: H - 0.95, w: W - 2 * M, h: 0.35, fontSize: 12, color: HEX.muted, margin: 0, isTextBox: true });
  s.addNotes("Umfang: Groß = Fläche geändert, Neubau oder Totalsanierung oder mehr als 28 Tage geschlossen; Mittel = 5–28 Tage oder komplette Neueinrichtung; Klein = Teilerneuerung.");
}

// ---------------------------------------------------------------- 6 Geplante Eröffnungen
pres.addSection({ title: "Ausblick" });
{
  const s = slideBase("Geplante Eröffnungen und Gerüchte", "Nicht gezählt – gezählt wird erst, wenn die Kette die Filiale mit Öffnungszeiten listet", "Ausblick");
  const gcol = { "Bestätigt": HEX.blue, "Berichtet": "1C5CAB", "Gerücht": HEX.muted };
  const head = ["Kette · Ort", "Vorhaben", "Belegstufe", "Erwartet", ""].map((t) => ({ text: t, options: { bold: true, color: HEX.white, fill: { color: HEX.dgreen } } }));
  const rows = D.pipeline.map((p, i) => {
    const fill = { color: i % 2 ? HEX.white : HEX.tint };
    return [
      { text: `${p.chain} · ${p.town}`, options: { fill, bold: true } },
      { text: p.what, options: { fill } },
      { text: p.grade, options: { fill, bold: true, color: gcol[p.grade] || HEX.text } },
      { text: p.when, options: { fill } },
      { text: p.flag ? p.flag.toUpperCase() : "", options: { fill, bold: true, color: HEX.red, fontSize: 11 } },
    ];
  });
  s.addTable([head, ...rows], { x: M, y: 1.7, w: W - 2 * M, colW: [2.4, 5.1, 1.4, 2.1, 1.133], fontSize: 13, color: HEX.text,
    border: { type: "solid", pt: 0.5, color: HEX.line }, rowH: 0.48, valign: "middle", margin: [0.04, 0.1, 0.04, 0.1] });
  s.addText("Belegstufen: Bestätigt = Kette selbst oder amtliches Dokument · Berichtet = Medienbericht · Gerücht = unbestätigter Hinweis", { x: M, y: H - 0.95, w: W - 2 * M, h: 0.35, fontSize: 12, color: HEX.muted, margin: 0, isTextBox: true });
  s.addNotes("NEU = im Zeitraum neu aufgenommen, AKTUALISIERT = neuer Beleg im Zeitraum.");
}

// ---------------------------------------------------------------- 7 Filialen pro Kette
pres.addSection({ title: "Markt" });
{
  const s = slideBase("Filialen pro Kette", "Gezählte Lebensmittelgeschäfte, eigene Filialen und Franchise getrennt", "Markt");
  const ch = [...D.chains].reverse();  // largest on top in a bar chart
  s.addChart(pres.charts.BAR, [
    { name: "Eigene Filialen", labels: ch.map((c) => c.name), values: ch.map((c) => c.own) },
    { name: "Franchise", labels: ch.map((c) => c.name), values: ch.map((c) => c.fr) },
  ], {
    x: M, y: 1.6, w: 6.9, h: 5.3, barDir: "bar", barGrouping: "stacked", barGapWidthPct: 45,
    chartColors: [HEX.green, HEX.lgreen], showLegend: true, legendPos: "t", legendFontSize: 12, legendFontFace: "+mn-lt", legendColor: HEX.muted,
    catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", catAxisLabelColor: HEX.text,
    valAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt", valAxisLabelColor: HEX.muted,
    valGridLine: { color: "E4E3DF", size: 0.5 }, catGridLine: { style: "none" }, valAxisLineShow: false,
    showTitle: false, objectName: "Diagramm Filialen pro Kette",
  });
  const tot = D.chains.reduce((a, c) => a + c.own + c.fr, 0);
  const head = ["Kette", "Gesamt", "Eigene", "Franchise", "Anteil"].map((t, i) => ({ text: t, options: { bold: true, color: HEX.white, fill: { color: HEX.dgreen }, align: i ? "right" : "left" } }));
  const rows = D.chains.map((c, i) => {
    const fill = { color: i % 2 ? HEX.white : HEX.tint };
    const t = c.own + c.fr;
    return [
      { text: c.name, options: { fill, bold: true } },
      { text: fmt(t), options: { fill, align: "right", bold: true } },
      { text: fmt(c.own), options: { fill, align: "right" } },
      { text: c.fr ? fmt(c.fr) : "–", options: { fill, align: "right" } },
      { text: `${(100 * t / tot).toFixed(1).replace(".", ",")} %`, options: { fill, align: "right", color: HEX.muted } },
    ];
  });
  const own = D.chains.reduce((a, c) => a + c.own, 0), fr = D.chains.reduce((a, c) => a + c.fr, 0);
  rows.push(["Gesamt", fmt(tot), fmt(own), fmt(fr), "100 %"].map((t, i) => ({ text: t, options: { bold: true, align: i ? "right" : "left", fill: { color: "DDEEE4" } } })));
  s.addTable([head, ...rows], { x: 7.8, y: 1.6, w: W - M - 7.8, colW: [1.45, 0.78, 0.75, 0.92, 1.033], fontSize: 11, color: HEX.text,
    border: { type: "solid", pt: 0.5, color: HEX.line }, rowH: 0.3, valign: "middle", margin: [0.02, 0.08, 0.02, 0.08] });
  s.addNotes("Anteil = Anteil an allen gezählten Filialen der erfassten Ketten (nach Anzahl, nicht nach Umsatz oder Fläche).");
}

// ---------------------------------------------------------------- 8 Verkaufsfläche
{
  const s = slideBase("Durchschnittliche Verkaufsfläche je Filiale", "m² je Filiale mit bekannter Fläche – Näherungswerte aus der alten Standortliste (Konkurrenz)", "Markt");
  const withA = D.chains.filter((c) => c.area_n > 0).map((c) => ({ ...c, avg: Math.round(c.area / c.area_n) }))
    .sort((a, b) => a.avg - b.avg);
  s.addChart(pres.charts.BAR, [{ name: "Ø Verkaufsfläche (m²)", labels: withA.map((c) => c.name), values: withA.map((c) => c.avg) }], {
    x: M, y: 1.6, w: 7.6, h: 5.2, barDir: "bar", barGapWidthPct: 45, chartColors: [HEX.green],
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelFontFace: "+mn-lt", dataLabelColor: HEX.text, dataLabelFormatCode: "#,##0",
    catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", catAxisLabelColor: HEX.text,
    valAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt", valAxisLabelColor: HEX.muted, valAxisLabelFormatCode: "#,##0",
    valGridLine: { color: "E4E3DF", size: 0.5 }, catGridLine: { style: "none" }, showLegend: false, showTitle: false,
    objectName: "Diagramm Verkaufsfläche",
  });
  const x = 8.6, w = W - M - x;
  const totArea = withA.reduce((a, c) => a + c.area, 0);
  card(s, x, 1.75, w, 1.7, "Kennzahl Gesamtfläche");
  s.addText("Erfasste Verkaufsfläche", { x: x + 0.3, y: 1.9, w: w - 0.6, h: 0.35, fontSize: 14, bold: true, color: HEX.muted, margin: 0, isTextBox: true });
  s.addText(`${fmt(totArea)} m²`, { x: x + 0.3, y: 2.3, w: w - 0.6, h: 0.75, fontSize: 36, bold: true, color: HEX.dgreen, margin: 0, isTextBox: true });
  s.addText(`aus ${fmt(withA.reduce((a, c) => a + c.area_n, 0))} Filialen mit bekannter Fläche`, { x: x + 0.3, y: 3.0, w: w - 0.6, h: 0.35, fontSize: 12, color: HEX.muted, margin: 0, isTextBox: true });
  const missing = D.chains.filter((c) => c.area_n === 0).map((c) => c.name);
  const partial = D.chains.filter((c) => c.area_n > 0 && c.area_n < c.own + c.fr).map((c) => `${c.name} (${c.area_n} von ${c.own + c.fr})`);
  const lines = [];
  if (missing.length) lines.push({ text: `Keine Flächen: ${missing.join(", ")}`, options: { bullet: true, breakLine: true } });
  if (partial.length) lines.push({ text: `Teilweise: ${partial.join(", ")}`, options: { bullet: true, breakLine: true } });
  lines.push({ text: "Keine Kette veröffentlicht Verkaufsflächen; Werte ohne Datum, ca.", options: { bullet: true } });
  card(s, x, 3.7, w, 3.0, "Hinweise Verkaufsfläche");
  s.addText("Datenlage", { x: x + 0.3, y: 3.85, w: w - 0.6, h: 0.35, fontSize: 14, bold: true, color: HEX.muted, margin: 0, isTextBox: true });
  s.addText(lines, { x: x + 0.3, y: 4.25, w: w - 0.6, h: 2.3, fontSize: 13, color: HEX.text, valign: "top", margin: 0, paraSpaceAfter: 6, isTextBox: true });
  s.addNotes("Durchschnitt = Summe der bekannten Verkaufsflächen / Anzahl Filialen mit Fläche. Nur Verkaufsfläche, keine Gesamt- oder Mietfläche.");
}

// ---------------------------------------------------------------- 9 Offene Punkte
{
  const s = slideBase("Offene Punkte und Quellen", "", "Markt");
  card(s, M, 1.5, 6.3, 5.0, "Offene Punkte");
  s.addText("Offene Punkte", { x: M + 0.3, y: 1.7, w: 5.7, h: 0.4, fontSize: 20, bold: true, color: HEX.text, margin: 0, isTextBox: true });
  s.addText(D.open_items.map((o, i) => ({ text: o, options: { bullet: true, breakLine: i < D.open_items.length - 1 } })),
    { x: M + 0.3, y: 2.25, w: 5.7, h: 4.0, fontSize: 15, color: HEX.text, valign: "top", margin: 0, paraSpaceAfter: 10, isTextBox: true });
  const x = M + 6.3 + 0.35, w = W - M - x;
  card(s, x, 1.5, w, 5.0, "Quellen und Regeln");
  s.addText("Quellen und Regeln", { x: x + 0.3, y: 1.7, w: w - 0.6, h: 0.4, fontSize: 20, bold: true, color: HEX.text, margin: 0, isTextBox: true });
  const src = [
    "Gezählt und geschlossen wird nur nach der Filialliste auf der Website jeder Kette.",
    "Nachrichten, Register und Karten dienen nur als Beleg (Renovierungen, geplante Standorte).",
    "Franchise bleibt bei der Kette, die die Filiale listet, wird aber getrennt ausgewiesen.",
    "Alle Details und Quellen: Arbeitsmappe „Filialtracker Slowenien (Master)“.",
  ];
  s.addText(src.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < src.length - 1 } })),
    { x: x + 0.3, y: 2.25, w: w - 0.6, h: 4.0, fontSize: 15, color: HEX.text, valign: "top", margin: 0, paraSpaceAfter: 10, isTextBox: true });
}

(async () => {
  await pres.writeFile({ fileName: outPath });
  if (SKILL) {
    const { applyTheme } = require(path.join(SKILL, "scripts/apply_theme.js"));
    await applyTheme(outPath, THEME);
  }
  console.log("ok", outPath);
})();
