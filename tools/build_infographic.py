#!/usr/bin/env python3
"""Build the monthly update infographic (HTML) from a JSON data file.

Usage: python build_infographic.py data.json svn.json out.html
Render to PNG with render.js.
"""
import json
import math
import sys
from datetime import date
from html import escape

data = json.load(open(sys.argv[1], encoding="utf-8"))
border = json.load(open(sys.argv[2], encoding="utf-8"))
out = sys.argv[3]

# ---------- colours (validated: tools/dataviz validator, light surface) ----------
C = {
    "open": "#008349",     # SPAR-Grün (Näherung)
    "close": "#e3051b",    # SPAR-Rot (Näherung)
    "seasonal": "#8a8984", # muted
    "switch": "#e87ba4",   # Akzent magenta
    "reno": "#eda100",     # Akzent gelb
    "pipe": "#2a78d6",     # Akzent blau
    "neutral": "#52514e",
}
TYPE_LABEL = {
    "open": "Neueröffnung",
    "close": "Schließung",
    "seasonal": "Vermutlich geschlossen (saisonal)",
    "switch": "Kettenwechsel",
    "reno": "Renovierung",
    "pipe": "Geplant / erwartet",
    "neutral": "Tracker",
    "reopen": "Wiedereröffnung",
}
C["reopen"] = C["open"]


def marker(t, x, y, r=8):
    """Shape per type = secondary encoding (colour is never alone)."""
    c = C[t]
    if t == "close":
        d = r * 0.8
        return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}" stroke="#fcfcfb" stroke-width="2"/>'
                f'<path d="M{x-d/2},{y-d/2}L{x+d/2},{y+d/2}M{x+d/2},{y-d/2}L{x-d/2},{y+d/2}" stroke="#fff" stroke-width="2" stroke-linecap="round"/>')
    if t in ("open", "reopen"):
        d = r * 0.9
        return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}" stroke="#fcfcfb" stroke-width="2"/>'
                f'<path d="M{x-d/2},{y}L{x+d/2},{y}M{x},{y-d/2}L{x},{y+d/2}" stroke="#fff" stroke-width="2" stroke-linecap="round"/>')
    if t == "seasonal":
        return f'<circle cx="{x}" cy="{y}" r="{r-1}" fill="#fcfcfb" stroke="{c}" stroke-width="2.5"/>'
    if t == "switch":
        s = r * 1.15
        return f'<rect x="{x-s}" y="{y-s}" width="{2*s}" height="{2*s}" rx="3" transform="rotate(45 {x} {y})" fill="{c}" stroke="#fcfcfb" stroke-width="2"/>'
    if t == "reno":
        s = r * 0.95
        return f'<rect x="{x-s}" y="{y-s}" width="{2*s}" height="{2*s}" rx="3" fill="{c}" stroke="#fcfcfb" stroke-width="2"/>'
    if t == "pipe":
        h = r * 1.25
        return (f'<path d="M{x},{y-h}L{x+h},{y+h*0.8}L{x-h},{y+h*0.8}Z" fill="{c}" stroke="#fcfcfb" '
                f'stroke-width="2" stroke-linejoin="round"/>')
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/>'


def icon_svg(t, size=22):
    m = size / 2
    return f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" aria-hidden="true">{marker(t, m, m, size*0.34)}</svg>'


# ---------- map ----------
MAP_W, MAP_H, PAD = 860, 470, 20
ring = border["coordinates"][0]
lons = [p[0] for p in ring]
lats = [p[1] for p in ring]
lon0, lon1, lat0, lat1 = min(lons), max(lons), min(lats), max(lats)
k = math.cos(math.radians((lat0 + lat1) / 2))
sx = (MAP_W - 2 * PAD) / ((lon1 - lon0) * k)
sy = (MAP_H - 2 * PAD) / (lat1 - lat0)
s = min(sx, sy)
ox = (MAP_W - (lon1 - lon0) * k * s) / 2
oy = (MAP_H - (lat1 - lat0) * s) / 2


def proj(lon, lat):
    return (round(ox + (lon - lon0) * k * s, 1), round(oy + (lat1 - lat) * s, 1))


path = "M" + "L".join(f"{x},{y}" for x, y in (proj(*p) for p in ring)) + "Z"
pts = []
seen = {}
for p in data["map_points"]:
    x, y = proj(p["lon"], p["lat"])
    key = (x, y)
    n = seen.get(key, 0)
    seen[key] = n + 1
    x += n * 16  # same town, several events -> side by side
    pts.append((p["type"], x, y))
# draw seasonal first, closes last-ish so overlapping stays legible
order = {"seasonal": 0, "pipe": 1, "reno": 2, "switch": 3, "close": 4, "open": 5}
pts.sort(key=lambda t: order[t[0]])
marks = "".join(marker(t, x, y, 8) for t, x, y in pts)
labels = ""
if "map_labels" not in data:
    # automatic placement: one label per town group, first free position around the marker
    CW = 7.9  # px per character at 13.5px semibold
    boxes = [(x - 10, y - 10, x + 10, y + 10) for _, x, y in pts]
    groups = []
    for p in data["map_points"]:
        x, y = proj(p["lon"], p["lat"])
        for g in groups:
            if abs(g["x"] - x) < 26 and abs(g["y"] - y) < 18:
                if p["town"] not in g["names"]:
                    g["names"].append(p["town"])
                break
        else:
            groups.append({"x": x, "y": y, "names": [p["town"]], "lat": p["lat"], "lon": p["lon"]})
    auto = []

    def hit(b):
        return any(not (b[2] < o[0] or b[0] > o[2] or b[3] < o[1] or b[1] > o[3]) for o in boxes) \
            or b[0] < 2 or b[2] > MAP_W - 2 or b[1] < 2 or b[3] > MAP_H - 2

    for g in groups:
        txt = " · ".join(g["names"])
        w = len(txt) * CW
        x, y = g["x"], g["y"]
        right = x + 14 + 16 * (seen.get((x, y), 1) - 1)
        cands = [("start", right, y + 5), ("end", x - 13, y + 5), ("middle", x, y - 14), ("middle", x, y + 24),
                 ("start", right, y - 9), ("start", right, y + 19), ("end", x - 13, y - 9), ("end", x - 13, y + 19)]
        for anc, tx, ty in cands:
            x0 = tx if anc == "start" else (tx - w if anc == "end" else tx - w / 2)
            b = (x0, ty - 12, x0 + w, ty + 3)
            if not hit(b):
                break
        else:
            anc, tx, ty = cands[0]
            x0 = tx
            b = (x0, ty - 12, x0 + w, ty + 3)
        boxes.append(b)
        auto.append({"text": txt, "lat": g["lat"], "lon": g["lon"], "anchor": anc,
                     "dx": round(tx - x, 1), "dy": round(ty - y, 1)})
    data["map_labels"] = auto
for l in data["map_labels"]:
    x, y = proj(l["lon"], l["lat"])
    labels += (f'<text x="{x + l["dx"]}" y="{y + l["dy"]}" text-anchor="{l["anchor"]}" class="maplbl">'
               f'{escape(l["text"])}</text>')
used_types = []
for t, _, _ in pts:
    if t not in used_types:
        used_types.append(t)
legend_types = ["open", "close", "seasonal", "switch", "reno", "pipe"]
map_legend = "".join(
    f'<span class="lg">{icon_svg(t, 18)}{TYPE_LABEL[t]}</span>' for t in legend_types)
map_svg = (f'<svg viewBox="0 0 {MAP_W} {MAP_H}" width="{MAP_W}" height="{MAP_H}" role="img" '
           f'aria-label="Karte Sloweniens mit den Ereignissen des Monats">'
           f'<path d="{path}" fill="#eef6f1" stroke="#9fd3b5" stroke-width="1.5" stroke-linejoin="round"/>'
           f'{marks}{labels}</svg>')

# ---------- KPI tiles ----------
kpis = ""
for kp in data["kpis"]:
    a = kp["accent"]
    ic = icon_svg(a, 22) if a != "neutral" else ""
    kpis += (f'<div class="kpi" style="--acc:{C[a]}"><div class="kpi-top">{ic}<span>{escape(kp["label"])}</span></div>'
             f'<div class="kpi-val">{escape(kp["value"])}</div><div class="kpi-sub">{escape(kp["sub"])}</div></div>')

# ---------- news cards ----------
news = ""
for n in data["news"]:
    t = n["type"]
    ic = icon_svg(t, 22) if t != "neutral" else '<svg width="22" height="22" viewBox="0 0 22 22"><circle cx="11" cy="11" r="7.5" fill="none" stroke="#52514e" stroke-width="2"/><path d="M11 7.5v4.5M11 14.6v.1" stroke="#52514e" stroke-width="2" stroke-linecap="round"/></svg>'
    news += (f'<div class="card" style="--acc:{C[t]}"><div class="card-h">{ic}<div><div class="tag">{escape(n.get("tag") or TYPE_LABEL[t])}</div>'
             f'<div class="ch">{escape(n["head"])}</div></div></div>')
    if n.get("items"):
        cols = " two" if len(n["items"]) > 1 else ""
        news += f'<ul class="items{cols}">' + "".join(
            f'<li><b>{escape(it["town"])}</b><span>{escape(it["name"])}</span></li>' for it in n["items"]) + "</ul>"
        if n.get("note"):
            news += f'<div class="cnote">{escape(n["note"])}</div>'
    else:
        news += f'<p>{escape(n.get("body", ""))}</p>'
    news += "</div>"

# ---------- Gantt ----------
g = data["gantt"]
d0 = date.fromisoformat(g["start"])
d1 = date.fromisoformat(g["end"])
today = date.fromisoformat(g["today"])
GW, LW, RH, TOP = 1460, 360, 34, 34
plot_w = GW - LW - 230
span = (d1 - d0).days + 1


def gx(d):
    dd = min(max((d - d0).days, 0), span)
    return LW + dd / span * plot_w


rows = ""
GH = TOP + RH * len(g["rows"]) + 14
# month grid
grid = ""
m = date(d0.year, d0.month, 1)
MONTHS = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
while m <= d1:
    x = gx(m)
    nxt = date(m.year + (m.month // 12), m.month % 12 + 1, 1)
    xe = gx(min(nxt, d1))
    grid += f'<line x1="{x}" y1="{TOP-6}" x2="{x}" y2="{GH-10}" stroke="#e4e3df" stroke-width="1"/>'
    grid += f'<text x="{(x+xe)/2}" y="{TOP-14}" text-anchor="middle" class="axis">{MONTHS[m.month-1]} {m.year}</text>'
    m = nxt
grid += f'<line x1="{gx(d1)+plot_w/span}" y1="{TOP-6}" x2="{gx(d1)+plot_w/span}" y2="{GH-10}" stroke="#e4e3df"/>'
STAT_COL = {"Laufend": C["reno"], "Geplant": C["reno"], "Abgeschlossen": "#c9c8c2"}
for i, r in enumerate(g["rows"]):
    y = TOP + i * RH
    a = date.fromisoformat(r["start"])
    b = date.fromisoformat(r["end"])
    x0, x1 = gx(a), gx(b) + plot_w / span
    col = STAT_COL[r["status"]]
    bh = 18
    by = y + (RH - bh) / 2
    if i % 2 == 0:
        rows += f'<rect x="0" y="{y}" width="{GW}" height="{RH}" fill="#f6f6f3"/>'
    rows += f'<text x="14" y="{y+RH/2+5}" class="glbl">{escape(r["label"])}</text>'
    if r["status"] == "Geplant":
        rows += (f'<rect x="{x0}" y="{by}" width="{max(x1-x0,4)}" height="{bh}" rx="4" fill="url(#hatch)" '
                 f'stroke="{col}" stroke-width="2"/>')
    else:
        rows += f'<rect x="{x0}" y="{by}" width="{max(x1-x0,4)}" height="{bh}" rx="4" fill="{col}"/>'
    if a < d0 or r.get("open_start"):
        rows += f'<path d="M{x0-2},{by+bh/2}l8,-7v14z" fill="#fcfcfb"/>'
    if r.get("open_end"):
        for j in range(3):
            rows += f'<circle cx="{x1+8+j*8}" cy="{by+bh/2}" r="2.5" fill="{col}"/>'
    tag = {"Laufend": "läuft", "Geplant": "geplant", "Abgeschlossen": "fertig"}[r["status"]]
    rows += (f'<text x="{LW+plot_w+16}" y="{y+RH/2-2}" class="gnote">{escape(r["note"])}</text>'
             f'<text x="{LW+plot_w+16}" y="{y+RH/2+13}" class="gscope">Umfang {escape(r["scope"])} · {tag}</text>')
if not g["rows"]:
    rows += f'<text x="14" y="{TOP+24}" class="glbl">Keine laufenden oder geplanten Renovierungen.</text>'
    GH = TOP + 50
tx = gx(today) + plot_w / span / 2
rows += (f'<line x1="{tx}" y1="{TOP-4}" x2="{tx}" y2="{GH-10}" stroke="#0b0b0b" stroke-width="1.5" stroke-dasharray="4 3"/>'
         f'<rect x="{tx-28}" y="{GH-12}" width="56" height="18" rx="9" fill="#0b0b0b"/>'
         f'<text x="{tx}" y="{GH+1}" text-anchor="middle" class="today">heute</text>')
GH += 12
gantt_svg = (f'<svg viewBox="0 0 {GW} {GH}" width="{GW}" height="{GH}" role="img" aria-label="Zeitplan der Renovierungen">'
             f'<defs><pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
             f'<rect width="7" height="7" fill="#fdf3d9"/><line x1="0" y1="0" x2="0" y2="7" stroke="{C["reno"]}" stroke-width="2.5"/></pattern></defs>'
             f'{grid}{rows}</svg>')

# ---------- pipeline ----------
GRADE = {"Bestätigt": "g-conf", "Berichtet": "g-rep", "Gerücht": "g-rum"}
pipe = ""
for p in data["pipeline"]:
    pipe += (f'<div class="pp"><div class="pp-l"><span class="grade {GRADE[p["grade"]]}">{p["grade"]}</span></div>'
             f'<div class="pp-m"><div class="pp-h">{escape(p["chain"])} · {escape(p["town"])}'
             + (f' <span class="flag">{escape(p["flag"])}</span>' if p.get("flag") else "") + '</div>'
             f'<div class="pp-b">{escape(p["what"])}</div></div><div class="pp-r">{escape(p["when"])}</div></div>')

# ---------- chain bars ----------
BW, BLW, BRH, BTOP = 598, 140, 22, 24
SHOWD = any(c.get("delta") is not None for c in data["chains"])   # change vs comparison base (month/quarter/year)
NUMW = 58 if SHOWD else 66     # width of each number column (Gesamt, Eigene, Franchise[, Änderung])
NX = [BW - (3 if SHOWD else 2) * NUMW - 4 + k * NUMW for k in range(4 if SHOWD else 3)]   # right edges
mx = max(c["own"] + c["fr"] for c in data["chains"])
bplot = NX[0] - NUMW - BLW - 12
bars = ""
for x, lab in zip(NX, ("Gesamt", "Eigene", "Fr.", "±") if SHOWD else ("Gesamt", "Eigene", "Franchise")):
    bars += f'<text x="{x}" y="{BTOP-10}" text-anchor="end" class="bhead">{lab}</text>'
for i, c in enumerate(data["chains"]):
    y = BTOP + i * BRH
    if i % 2 == 0:
        bars += f'<rect x="0" y="{y}" width="{BW}" height="{BRH}" fill="#f6f6f3"/>'
    wo = c["own"] / mx * bplot
    wf = c["fr"] / mx * bplot
    bars += f'<text x="{BLW-12}" y="{y+BRH/2+5}" text-anchor="end" class="blbl">{escape(c["name"])}</text>'
    # rounded data-end only at the outer end; 2px surface gap between segments
    if c["fr"]:
        bars += f'<rect x="{BLW}" y="{y+6}" width="{max(wo-2,1)}" height="{BRH-12}" fill="#008349"/>'
        bars += (f'<path d="M{BLW+wo},{y+6}h{max(wf-4,0)}a4,4 0 0 1 4,4v{BRH-20}a4,4 0 0 1 -4,4h-{max(wf-4,0)}z" '
                 f'fill="#8ccaa6"/>')
    else:
        bars += (f'<path d="M{BLW},{y+6}h{max(wo-4,0)}a4,4 0 0 1 4,4v{BRH-20}a4,4 0 0 1 -4,4h-{max(wo-4,0)}z" '
                 f'fill="#008349"/>')
    tot = c["own"] + c["fr"]
    for x, v, cls in zip(NX, (tot, c["own"], c["fr"]), ("btot", "bval", "bval")):
        bars += f'<text x="{x}" y="{y+BRH/2+5}" text-anchor="end" class="{cls}">{v if v else "–"}</text>'
    if SHOWD:
        d = c.get("delta")
        col = "#008349" if d and d > 0 else "#E3051B" if d and d < 0 else "#8a8a85"
        bars += f'<text x="{NX[3]}" y="{y+BRH/2+5}" text-anchor="end" class="bval" fill="{col}" style="fill:{col};font-weight:600">{(f"{d:+d}" if d else "±0") if d is not None else "neu"}</text>'
tot_all = [sum(c["own"] + c["fr"] for c in data["chains"]), sum(c["own"] for c in data["chains"]), sum(c["fr"] for c in data["chains"])]
y = BTOP + len(data["chains"]) * BRH
bars += f'<line x1="0" y1="{y+2}" x2="{BW}" y2="{y+2}" stroke="#c9c8c2"/>'
bars += f'<text x="{BLW-12}" y="{y+20}" text-anchor="end" class="blbl">Gesamt</text>'
for x, v in zip(NX, tot_all):
    bars += f'<text x="{x}" y="{y+20}" text-anchor="end" class="btot">{f"{v:,}".replace(",", ".")}</text>'
if SHOWD:
    dsum = sum(c["delta"] for c in data["chains"] if c.get("delta") is not None)
    col = "#008349" if dsum > 0 else "#E3051B" if dsum < 0 else "#8a8a85"
    bars += f'<text x="{NX[3]}" y="{y+20}" text-anchor="end" class="btot" style="fill:{col}">{f"{dsum:+d}" if dsum else "±0"}</text>'
BH = y + 30
bars_svg = (f'<svg viewBox="0 0 {BW} {BH}" width="{BW}" height="{BH}" role="img" aria-label="Filialen pro Kette">'
            f'<line x1="{BLW}" y1="{BTOP}" x2="{BLW}" y2="{BTOP + len(data["chains"]) * BRH}" stroke="#c9c8c2"/>{bars}</svg>')

if data.get("pipeline_more"):
    pipe += f'<div class="gfoot">+ {data["pipeline_more"]} weitere im Tab „Geplante Eröffnungen“</div>'
open_items = "".join(f"<li>{escape(o)}</li>" for o in data["open_items"])

html = f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8"><title>{escape(data['title'])} – {escape(data['edition'])}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1600px;background:#ffffff;color:#0b0b0b;font-family:Inter,'DejaVu Sans',sans-serif;font-size:16px;line-height:1.4}}
.hdr{{background:#008349;border-bottom:8px solid #e3051b;color:#fff;padding:30px 56px 26px;display:flex;justify-content:space-between;align-items:flex-end}}
.hdr h1{{white-space:nowrap;font-family:'Inter Display',Inter,sans-serif;font-size:42px;font-weight:700;letter-spacing:-.5px}}
.hdr .ed{{font-size:22px;color:#d6eedf;font-weight:500;margin-bottom:6px}}
.hdr .meta{{max-width:470px;text-align:right;color:#e3f3e9;font-size:15px;line-height:1.6}}
.hdr .meta b{{color:#fff}}
.wrap{{padding:26px 56px 28px}}
.kpis{{display:grid;grid-template-columns:repeat(6,1fr);gap:16px;margin-bottom:24px}}
.kpi{{background:#fff;border:1px solid #e4e3df;border-top:5px solid var(--acc);border-radius:10px;padding:16px 18px 18px}}
.kpi-top{{display:flex;align-items:center;gap:8px;font-size:14px;font-weight:600;color:#52514e;height:22px}}
.kpi-val{{font-family:'Inter Display',Inter,sans-serif;font-size:50px;font-weight:700;line-height:1.05;margin-top:8px}}
.kpi-sub{{font-size:13.5px;color:#52514e;margin-top:4px;min-height:36px}}
h2{{color:#006b3b;font-family:'Inter Display',Inter,sans-serif;font-size:24px;font-weight:700;margin-bottom:4px}}
.h2s{{font-size:14px;color:#52514e;margin-bottom:14px}}
.row{{display:grid;gap:28px;margin-bottom:24px}}
.r1{{grid-template-columns:900px 1fr}}
.r3{{grid-template-columns:1fr 640px}}
.panel{{background:#fff;border:1px solid #dfe9e3;border-radius:12px;padding:22px 20px 18px}}
.maplbl{{font-size:13.5px;font-weight:600;fill:#0b0b0b;paint-order:stroke;stroke:#fcfcfb;stroke-width:4px;stroke-linejoin:round}}
.legend{{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13.5px;color:#52514e;margin-top:6px}}
.lg{{display:inline-flex;align-items:center;gap:6px}}
.cards{{display:flex;flex-direction:column;gap:10px}}
.card{{background:#fff;border:1px solid #e4e3df;border-left:5px solid var(--acc);border-radius:10px;padding:11px 16px}}
.card-h{{display:flex;gap:10px;align-items:flex-start}}
.card-h svg{{flex:none;margin-top:2px}}
.tag{{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.6px;color:#52514e}}
.ch{{font-size:17px;font-weight:700;margin-top:1px}}
.items{{list-style:none;margin:6px 0 0 32px;display:grid;grid-template-columns:1fr;gap:4px 14px}}
.items.two{{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}}
.items li{{min-width:0;font-size:13.5px;line-height:1.25;color:#33322f;padding-left:10px;border-left:3px solid var(--acc)}}
.items li b{{display:block;font-size:13.5px;color:#0b0b0b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.items li span{{display:block;font-size:12.5px;color:#52514e;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.cnote{{font-size:12.5px;color:#52514e;margin:6px 0 0 32px;font-style:italic}}
.card p{{font-size:13.5px;line-height:1.35;color:#33322f;margin-top:4px;padding-left:32px}}
.axis{{font-size:13px;fill:#52514e;font-weight:600}}
.glbl{{font-size:14.5px;font-weight:600;fill:#0b0b0b}}
.gnote{{font-size:13.5px;fill:#0b0b0b;font-weight:600}}
.gscope{{font-size:12px;fill:#52514e}}
.today{{font-size:11.5px;fill:#fff;font-weight:700}}
.gfoot{{font-size:13.5px;color:#52514e;margin-top:10px}}
.glegend{{display:flex;gap:20px;font-size:13.5px;color:#52514e;margin:0 0 6px}}
.sw{{display:inline-block;width:26px;height:12px;border-radius:3px;vertical-align:-1px;margin-right:6px}}
.pp{{display:grid;grid-template-columns:104px 1fr 175px;gap:14px;align-items:center;padding:4px 4px;border-bottom:1px solid #eeede9}}
.pp:last-child{{border-bottom:none}}
.grade{{display:inline-block;font-size:12.5px;font-weight:700;padding:4px 10px;border-radius:999px;border:2px solid #2a78d6}}
.g-conf{{background:#2a78d6;color:#fff}}
.g-rep{{background:#fff;color:#1c5cab}}
.g-rum{{background:#fff;color:#52514e;border-style:dashed;border-color:#8a8984}}
.pp-h{{font-weight:700;font-size:16px}}
.flag{{display:inline-block;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#fff;background:#e3051b;border-radius:4px;padding:1px 6px;vertical-align:2px;margin-left:6px}}
.pp-b{{font-size:14px;color:#33322f}}
.pp-r{{text-align:right;font-weight:600;font-size:14.5px}}
.blbl{{font-size:14px;font-weight:600;fill:#0b0b0b}}
.bhead{{font-size:12.5px;font-weight:700;fill:#52514e}}
.btot{{font-size:14px;font-weight:700;fill:#0b0b0b}}
.bval{{font-size:14px;fill:#33322f;font-weight:500}}
.foot{{display:grid;grid-template-columns:1fr 1fr;gap:28px;border-top:1px solid #e4e3df;padding-top:14px}}
.foot h3{{font-size:16px;margin-bottom:6px}}
.foot li{{font-size:14px;color:#33322f;margin-left:18px;margin-bottom:3px}}
.foot p{{font-size:13px;color:#52514e}}
.p2hdr{{display:none}}
@media print{{
 .pb{{break-before:page}}
 .p2hdr{{display:block;background:#008349;border-bottom:6px solid #e3051b;color:#fff;font-weight:700;font-size:20px;padding:10px 24px;border-radius:8px;margin:0 0 18px}}
 .panel,.row,.kpis,.foot{{break-inside:avoid}}
 .gscope,.tag{{font-size:13.5px}}
 .card p,.pp-b,.foot li,.foot p,.h2s,.kpi-sub,.legend,.glegend,.gfoot{{font-size:15px}}
 .axis,.bval,.maplbl,.blbl{{font-size:15px}}
 .pp{{padding:2px 4px}} .pp-b{{font-size:14px}} .row{{margin-bottom:12px}} .wrap{{padding-bottom:0}}
 .p2hdr{{margin-bottom:10px}} .foot{{padding-top:8px}} .gfoot{{margin-top:4px}}
 div.panel[style]{{margin-bottom:12px!important}}
}}
</style></head><body>
<div class="hdr"><div><div class="ed">{escape(data['edition'])}</div><h1>{escape(data['title'])}</h1></div>
<div class="meta">Stand <b>{escape(data['stand'])}</b><br>Zeitraum {escape(data['period'])}</div></div>
<div class="wrap">
<div class="kpis">{kpis}</div>
<div class="row r1">
<div class="panel"><h2>Wo sich etwas getan hat</h2><div class="h2s">Ereignisse des Zeitraums nach Ort</div>{map_svg}<div class="legend">{map_legend}</div></div>
<div><h2>Was ist neu</h2><div class="h2s">Die wichtigsten Änderungen im Überblick</div><div class="cards">{news}</div></div>
</div>
<div class="pb"></div><div class="p2hdr">{escape(data['title'])} · {escape(data['edition'])} · Stand {escape(data['stand'])} · Seite 2</div>
<div class="panel" style="margin-bottom:24px"><h2>Renovierungen und Schließzeiten</h2>
<div class="glegend"><span><span class="sw" style="background:{C['reno']}"></span>läuft</span><span><span class="sw" style="background:url();border:2px solid {C['reno']};background-image:repeating-linear-gradient(45deg,{C['reno']} 0 2px,#fdf3d9 2px 6px)"></span>geplant</span><span><span class="sw" style="background:#c9c8c2"></span>abgeschlossen</span><span style="color:#b07800">● ● ● Ende offen</span></div>
{gantt_svg}<div class="gfoot">{escape(g.get('footnote') or '')}</div></div>
<div class="row r3">
<div class="panel"><h2>Geplante Eröffnungen und Gerüchte</h2><div class="h2s">Nicht gezählt – gezählt wird erst, wenn die Kette die Filiale mit Öffnungszeiten listet</div>{pipe}</div>
<div class="panel"><h2>Filialen pro Kette</h2><div class="h2s">Gezählte Lebensmittelgeschäfte, eigene Filialen und Franchise getrennt{(" · Änderung " + escape(data["delta_base"])) if data.get("delta_base") else ""}</div>
<div class="glegend"><span><span class="sw" style="background:#008349"></span>eigene Filialen</span><span><span class="sw" style="background:#8ccaa6"></span>Franchise (Fr.)</span></div>{bars_svg}</div>
</div>
<div class="foot"><div><h3>Offene Punkte</h3><ul>{open_items}</ul></div>
<div><h3>Quellen und Regeln</h3><p>Gezählt und geschlossen wird nur nach der Filialliste auf der Website jeder Kette. Nachrichten, Register und Karten dienen nur als Beleg (Renovierungen, geplante Standorte). Alle Details und Quellen: Google-Tabelle „Filialtracker Slowenien (Master)“. Karte: Natural Earth; Ortskoordinaten: GeoNames (CC BY 4.0), Postort der Filiale.</p></div></div>
</div></body></html>"""
open(out, "w", encoding="utf-8").write(html)
print("ok", out)
