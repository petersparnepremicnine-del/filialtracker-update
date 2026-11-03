#!/usr/bin/env python3
"""Turn the Google-Sheet tabs into the data file for the monthly infographic.

Usage:
  python make_data.py sheet_dump.json <run-date YYYY-MM-DD> state.json out.json [--final]

sheet_dump.json: the run's workbook Filialtracker_<date>.xlsx (same tabs as the Google Sheet), or
  {"overview": [...], "changes": [...], "pipeline": [...], "reno": [...], "kand": [...]}
  = the "values" arrays returned by Google Sheets get_values for
    'Übersicht Ketten'!A1:P40, 'Änderungen'!A1:G600, 'Geplante Eröffnungen'!A1:N150,
    'Renovierungen'!A1:O400, 'Kandidaten'!A1:G150.
state.json: kept in the repo; remembers the editions (period, totals). Created if missing.
--final: also update state.json (do this only after the image was published).

Exit code 3 = towns without coordinates (listed on stderr as JSON). Add them to towns_extra.json
({"Town": [lat, lon]}, source in towns_extra_sources.md) and run again; if a town cannot be found,
add it with null and it is left off the map (listed in the infographic footer).
"""
import json
import os
import re
import sys
from datetime import date, timedelta

MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September",
          "Oktober", "November", "Dezember"]
HERE = os.path.dirname(os.path.abspath(__file__))
FIRST_PERIOD_START = "2026-10-23"  # first survey of the tracker


def dmy(d, year=False):
    return f"{d.day}.{d.month}.{d.year}" if year else f"{d.day}.{d.month}."


def pdate(s):
    """ISO date, or YYYY-MM / YYYY -> (date, precision)."""
    s = (s or "").strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return date(int(m[1]), int(m[2]), int(m[3])), "d"
    m = re.fullmatch(r"(\d{4})-(\d{2})", s)
    if m:
        return date(int(m[1]), int(m[2]), 1), "m"
    m = re.fullmatch(r"(\d{4})", s)
    if m:
        return date(int(m[1]), 1, 1), "y"
    return None, None


def table(values, header_row):
    """Rows after the header as dicts (stop at the first empty row)."""
    head = values[header_row]
    out = []
    for r in values[header_row + 1:]:
        if not r or not any(c.strip() for c in r):
            break
        out.append({h: (r[i] if i < len(r) else "") for i, h in enumerate(head)})
    return out


def town_of(addr):
    """Postal town from '..., 4000 Kranj' -> 'Kranj'."""
    m = re.search(r"\b\d{4}\s+(.+)$", addr or "")
    return m[1].strip() if m else ""


def norm_town(t):
    t = re.split(r"\s+-\s+|/", t)[0].strip()
    return t


def int0(s):
    """'53.199' (German thousands) or '53199' or '232839.8' (raw number from xlsx) -> int; '-' -> 0."""
    t = str(s).strip()
    try:
        if re.fullmatch(r"\d{1,3}(\.\d{3})+", t):
            return int(t.replace(".", ""))
        return int(round(float(t.replace(",", "."))))
    except ValueError:
        return 0


# ---------------------------------------------------------------- classify change-log rows
def classify(text):
    t = text
    if re.search(r"^Gleiche Adresse|prüfen \(evtl\. Kettenwechsel\)", t):
        return None  # address pair waiting for the user's decision (open item, not a switch)
    if re.search(r"^Neueröffnung", t):
        return "open"
    if re.search(r"Wiedereröffnet|Wieder auf der Website|Öffnungszeiten wieder da", t):
        return "reopen"
    if re.search(r"Nicht mehr auf der Website|Geschlossen, obwohl noch gelistet|→ Geschlossen", t):
        return "close"
    if re.search(r"Vermutlich geschlossen|An keinem Tag Öffnungszeiten", t):
        return "seasonal"
    if re.search(r"Kettenwechsel|Entscheidung Adressabgleich: gehört zu|Wechsel bestätigt", t):
        return "switch"
    if re.search(r"Erwartete Eröffnung|Neu gelistet \(noch ohne", t):
        return "expected"
    if re.search(r"Franchisenehmer|Franchise", t) and not re.search(r"Kette aufgenommen", t):
        return "franchise"
    if re.search(r"Kette aufgenommen|erstmals erhoben|Erste Erhebung|Regeländerung", t):
        return "tracker"
    return None  # renovations come from their own tab; address pairs, renames, corrections are not shown


TABS = {"overview": "Übersicht Ketten", "changes": "Änderungen", "pipeline": "Geplante Eröffnungen",
        "reno": "Renovierungen", "kand": "Kandidaten"}


def load_xlsx(path):
    """Same shape as Google Sheets get_values: list of rows of strings."""
    import datetime as dt
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    out = {}
    for k, name in TABS.items():
        rows = []
        for r in wb[name].iter_rows(values_only=True):
            cells = []
            for v in r:
                if v is None:
                    cells.append("")
                elif isinstance(v, dt.datetime):
                    cells.append(v.date().isoformat())
                elif isinstance(v, dt.date):
                    cells.append(v.isoformat())
                elif isinstance(v, float) and v.is_integer():
                    cells.append(str(int(v)))
                else:
                    cells.append(str(v))
            while cells and cells[-1] == "":
                cells.pop()
            rows.append(cells)
        out[k] = rows
    return out


def main():
    dump_p, run_s, state_p, out_p = sys.argv[1:5]
    final = "--final" in sys.argv
    run = date.fromisoformat(run_s)
    dump = load_xlsx(dump_p) if dump_p.endswith(".xlsx") else json.load(open(dump_p, encoding="utf-8"))
    state = json.load(open(state_p, encoding="utf-8")) if os.path.exists(state_p) else {"editions": []}
    ed_key = f"{run.year}-{run.month:02d}"
    eds = state["editions"]
    cur = next((e for e in eds if e["edition"] == ed_key), None)
    prev = [e for e in eds if e["edition"] < ed_key]
    prev = prev[-1] if prev else None
    if cur:  # republish of the same edition (e.g. after the Spar check): same period start
        p_start = date.fromisoformat(cur["period_start"])
    elif prev:
        p_start = date.fromisoformat(prev["period_end"]) + timedelta(days=1)
    else:
        p_start = date.fromisoformat(FIRST_PERIOD_START)
    p_end = run

    def in_period(d):
        return d is not None and p_start <= d <= p_end

    # ------------------------------------------------------------ overview
    ov = dump["overview"]
    hdr_i = next(i for i, r in enumerate(ov) if r and r[0] == "Kette")
    chains, total, own, fr, addr_open, last_checked = [], 0, 0, 0, 0, {}
    for r in ov[hdr_i + 1:]:
        if not r or not r[0]:
            continue
        name = r[0]
        if name.startswith("Gesamt"):
            total, own, fr = int0(r[3]), int0(r[4]), int0(r[5])
        elif name.startswith("Gleiche Adresse"):
            addr_open = int0(r[3]) if len(r) > 3 else 0
        elif name.startswith("Genossenschaftsläden in Kettenlisten") or name.startswith("Geplante Eröffnungen"):
            continue
        else:
            short = "Genossenschaften" if name.startswith("Landwirtschaftliche") else name
            chains.append({"name": short, "own": int0(r[4]), "fr": int0(r[5]),
                           "area": int0(r[12]) if len(r) > 12 else 0, "area_n": int0(r[13]) if len(r) > 13 else 0,
                           "closed_total": int0(r[8]) if len(r) > 8 else 0})
            if len(r) > 1 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", r[1] or ""):
                last_checked[short] = r[1]
    chains.sort(key=lambda c: -(c["own"] + c["fr"]))

    # ------------------------------------------------------------ change log
    ch = table(dump["changes"], 2)
    ev = {k: [] for k in ["open", "reopen", "close", "seasonal", "switch", "expected", "franchise", "tracker"]}
    for r in ch:
        d, _ = pdate(r.get("Lauf"))
        if not in_period(d):
            continue
        typ = classify(r.get("Änderung", ""))
        if not typ:
            continue
        grocery = r.get("Lebensmittel-geschäft", "")
        if typ in ("open", "reopen", "close", "seasonal", "expected") and grocery not in ("Ja", ""):
            continue
        r["_town"] = norm_town(town_of(r.get("Adresse", "")))
        ev[typ].append(r)

    # ------------------------------------------------------------ renovations
    rn = table(dump["reno"], 2)
    win_start = date(p_end.year, p_end.month, 1) - timedelta(days=1)
    win_start = date(win_start.year, win_start.month, 1)              # first day of previous month
    nm = date(p_end.year + (p_end.month + 1) // 13, (p_end.month % 12) + 1, 1)
    win_end = date(nm.year + (nm.month + 1) // 13, (nm.month % 12) + 1, 1) - timedelta(days=1)  # end of next month
    gantt, reno_running, reno_planned, reno_done_vague = [], 0, 0, []
    for r in rn:
        st = r.get("Status", "")
        s, sp = pdate(r.get("Beginn"))
        e, ep = pdate(r.get("Ende / Wiedereröffnung"))
        town = r.get("Ort", "")
        label = r.get("Filiale", "")
        row = None
        if st.startswith("Laufend"):
            reno_running += 1
            start = s if sp == "d" else p_start
            if e and ep == "d":
                end, note, open_end = e - timedelta(days=1), f"Wiedereröffnung {dmy(e)}", False
            else:
                end, note, open_end = max(start, run) + timedelta(days=14), "kein Wiedereröffnungsdatum", True
            row = dict(status="Laufend", start=start, end=end, note=note, open_end=open_end,
                       open_start=sp != "d")
        elif st.startswith("Geplant") and s and sp == "d":
            reno_planned += 1
            end = (e - timedelta(days=1)) if (e and ep == "d") else s + timedelta(days=14)
            note = f"Wiedereröffnung {dmy(e)}" if (e and ep == "d") else "Ende unbekannt"
            row = dict(status="Geplant", start=s, end=end, note=note, open_end=not (e and ep == "d"),
                       open_start=False)
        elif st.startswith("Abgeschlossen"):
            if e and ep == "d" and in_period(e):
                start = s if sp == "d" else e - timedelta(days=7)
                row = dict(status="Abgeschlossen", start=start, end=e - timedelta(days=1),
                           note=f"wieder offen seit {dmy(e)}", open_end=False, open_start=sp != "d")
            elif e and ep == "m" and (e.year, e.month) in {(p_start.year, p_start.month), (p_end.year, p_end.month)} \
                    and in_period(pdate(r.get("Erfasst am"))[0] or date(1900, 1, 1)):
                reno_done_vague.append(f"{r.get('Kette')} {town}")
        if row:
            lab = label.split(",")[0].strip()
            if r.get("Kette", "").lower()[:4] not in lab.lower():
                lab = f"{r.get('Kette')} {lab}"
            if norm_town(town).lower()[:5] not in lab.lower():
                lab = f"{lab} ({town})"
            row.update(label=lab,
                       scope=r.get("Umfang", "") or "unbekannt", town=town)
            gantt.append(row)
    order = {"Laufend": 0, "Geplant": 1, "Abgeschlossen": 2}
    gantt.sort(key=lambda g: (order[g["status"]], g["start"]))
    gantt = gantt[:10]
    for g in gantt:
        for k in ("start", "end"):
            g[k] = g[k].isoformat()

    # ------------------------------------------------------------ pipeline
    pl = table(dump["pipeline"], 2)
    pipe, grades = [], {"Bestätigt": 0, "Berichtet": 0, "Gerücht": 0}
    for r in pl:
        if r.get("Status") != "Offen":
            continue
        g = r.get("Belegstufe", "")
        grades[g] = grades.get(g, 0) + 1
        first, _ = pdate(r.get("Erstmals berichtet"))
        last, _ = pdate(r.get("Letzter Beleg"))
        known = (cur or {}).get("pipeline_ids_at_start")
        is_new = in_period(first) or (known is not None and r.get("ID") not in known)
        flag = "neu" if is_new else ("aktualisiert" if in_period(last) else "")
        what = r.get("Standort", "")
        if r.get("Art") and r["Art"] != "Neueröffnung":
            what = f"{r['Art']}: {what}"
        what = what.split(";")[0].strip()
        if len(what) > 68:
            what = what[:66].rsplit(" ", 1)[0] + " …"
        pipe.append({"id": r.get("ID", ""), "chain": r.get("Kette", ""), "town": r.get("Ort", ""), "what": what,
                     "when": r.get("Erwartete Eröffnung", "") or "unbekannt", "grade": g, "flag": flag})
    gorder = {"Bestätigt": 0, "Berichtet": 1, "Gerücht": 2}
    pipe.sort(key=lambda p: (p["flag"] == "", gorder.get(p["grade"], 3)))
    pipe_shown = pipe[:7]

    # ------------------------------------------------------------ candidates
    kd = table(dump["kand"], 2)
    cand_new = [k for k in kd if in_period(pdate(k.get("Gefunden am"))[0])]
    cand_open = [k for k in kd if k.get("Status") in ("Offen", "Zu prüfen") and not k.get("Entscheidung")]

    # ------------------------------------------------------------ cards
    def lst(rows, f, n=8):
        items = [f(r) for r in rows]
        items = list(dict.fromkeys(i for i in items if i))
        s = ", ".join(items[:n])
        return s + (f" und {len(items) - n} weitere" if len(items) > n else "")

    def chain_note(rows):
        cs = sorted({r.get("Kette", "") for r in rows})
        return f"alle {cs[0]}" if len(cs) == 1 else ", ".join(cs)

    def store_short(r):
        f = r.get("Filiale", "").split(",")[0].strip()
        return f if r.get("Kette", "").lower()[:4] in f.lower() else f"{r.get('Kette')} {f}"

    def short(t, n=42):
        t = (t or "").strip()
        return t if len(t) <= n else t[:n - 2].rsplit(" ", 1)[0] + " …"

    def items(rows, name_f, n=10):
        """List entries for a card: town (bold) + store name, at most n, duplicates removed."""
        out, seen = [], set()
        for r in rows:
            it = {"town": r.get("_town", ""), "name": short(name_f(r))}
            k = (it["town"], it["name"])
            if k in seen:
                continue
            seen.add(k)
            out.append(it)
        more = max(len(out) - n, 0)
        return out[:n], more

    def card(typ, head, rows, name_f, note=""):
        its, more = items(rows, name_f)
        if more:
            note = (f"+ {more} weitere im Tab „Änderungen“. " + note).strip()
        return {"type": typ, "head": head, "items": its, "note": note}

    one_chain = lambda rows: len({r.get("Kette", "") for r in rows}) == 1
    cards = []
    if ev["open"]:
        cards.append(card("open", f"{len(ev['open'])} Neueröffnung{'en' if len(ev['open']) > 1 else ''}",
                          ev["open"], store_short))
    if ev["close"]:
        reason = "Erfasst durch die Regel vom 26.10.2026: noch gelistet, aber an allen Tagen geschlossen." \
            if all("Regeländerung" in r.get("Änderung", "") for r in ev["close"]) else ""
        nf = (lambda r: r.get("Filiale", "")) if one_chain(ev["close"]) else store_short
        cards.append(card("close", f"{len(ev['close'])} Filiale{'n' if len(ev['close']) > 1 else ''} geschlossen ({chain_note(ev['close'])})",
                          ev["close"], nf, reason))
    if ev["reopen"]:
        cards.append(card("reopen", f"{len(ev['reopen'])} wiedereröffnet", ev["reopen"], store_short))
    if ev["switch"]:
        def sw(r):
            m = re.search(r"Kettenwechsel\s+(\S+\s*→\s*\S+)", r.get("Änderung", ""))
            m2 = re.search(r"gehört zu (\S+)", r.get("Änderung", ""))
            if m:
                return m[1]
            if m2:
                others = [c.strip() for c in r.get("Kette", "").split("/") if c.strip() and c.strip() != m2[1]]
                return f"{others[0]} → {m2[1]}" if others else "jetzt " + m2[1]
            return r.get("Kette", "")
        cards.append(card("switch", f"{len(ev['switch'])} Kettenwechsel", ev["switch"], sw,
                          "Gezählt nur bei der Kette, die die Filiale jetzt betreibt."))
    if ev["seasonal"]:
        cards.append(card("seasonal", f"{len(ev['seasonal'])} vermutlich geschlossen", ev["seasonal"], store_short,
                          "Saisonal geschlossen – weiter gezählt."))
    if ev["expected"]:
        cards.append(card("pipe", f"{len(ev['expected'])} neu gelistet, noch ohne Öffnungszeiten", ev["expected"], store_short,
                          "Erwartete Eröffnung – nicht gezählt."))
    if cand_new:
        cards.append({"type": "neutral", "tag": "Wettbewerber", "head": f"Neue Wettbewerber-Kandidaten: {len(cand_new)}",
                      "body": lst(cand_new, lambda k: k.get("Kandidat")) + " – Entscheidung im Tab „Kandidaten“."})
    if ev["franchise"]:
        cards.append({"type": "neutral", "tag": "Franchise", "head": f"{len(ev['franchise'])} Franchise-Änderungen",
                      "body": lst(ev["franchise"], lambda r: f"{store_short(r)} ({r['_town']})")})
    if ev["tracker"]:
        cards.append({"type": "neutral", "tag": "Tracker", "head": "Erfassung erweitert / Regeln",
                      "body": " ".join(dict.fromkeys(
                          (f"{r.get('Kette')}: {r.get('Änderung')}" if r.get("Kette") not in ("Alle", "") else r.get("Änderung"))
                          .rstrip(".") + "." for r in ev["tracker"]))[:330]})
    if not cards:
        cards.append({"type": "neutral", "head": "Keine Änderungen", "body": "Im Zeitraum keine Eröffnungen, Schließungen oder Kettenwechsel."})
    dropped = cards[4:]
    cards = cards[:4]

    # ------------------------------------------------------------ map points
    towns = json.load(open(os.path.join(HERE, "towns_si.json"), encoding="utf-8"))
    extra_p = os.path.join(HERE, "towns_extra.json")
    extra = json.load(open(extra_p, encoding="utf-8")) if os.path.exists(extra_p) else {}
    lower = {k.lower(): v for k, v in towns.items()}
    lower.update({k.lower(): v for k, v in extra.items()})

    pts, missing, unmapped = [], [], []

    def add(town, typ):
        if not town:
            return
        key = town.lower()
        if key not in lower:
            missing.append(town)
            return
        if lower[key] is None:
            unmapped.append(town)
            return
        lat, lon = lower[key]
        pts.append({"town": town, "lat": lat, "lon": lon, "type": typ})

    for typ, mtyp in [("open", "open"), ("reopen", "open"), ("close", "close"), ("seasonal", "seasonal"),
                      ("switch", "switch"), ("expected", "pipe")]:
        for r in ev[typ]:
            add(r["_town"], mtyp)
    for g in gantt:
        if g["status"] != "Abgeschlossen":
            add(norm_town(g["town"]), "reno")
    for p in pipe:
        add(norm_town(p["town"]), "pipe")
    # one marker per town and type
    seen, uniq = set(), []
    for p in pts:
        k = (p["town"].lower(), p["type"])
        if k not in seen:
            seen.add(k)
            uniq.append(p)
    if missing:
        print(json.dumps(sorted(set(missing)), ensure_ascii=False), file=sys.stderr)
        sys.exit(3)

    # ------------------------------------------------------------ KPIs, header
    prev_total = prev["total"] if prev and not cur else (cur.get("prev_total") if cur else None)
    if prev_total is None and prev:
        prev_total = prev["total"]
    delta = f" · {total - prev_total:+d} ggü. Vormonat" if prev_total is not None else ""
    n_open, n_re = len(ev["open"]), len(ev["reopen"])
    kpis = [
        {"label": "Gezählte Filialen", "value": f"{total:,}".replace(",", "."), "sub": f"{own} eigene · {fr} Franchise{delta}", "accent": "neutral"},
        {"label": "Neueröffnungen", "value": str(n_open), "sub": (f"+ {n_re} wiedereröffnet" if n_re else "keine weitere Wiedereröffnung") if n_open or n_re else "keine neue Filiale gelistet", "accent": "open"},
        {"label": "Schließungen", "value": str(len(ev["close"])), "sub": chain_note(ev["close"]) if ev["close"] else "keine Filiale geschlossen", "accent": "close"},
        {"label": "Kettenwechsel", "value": str(len(ev["switch"])), "sub": "Filialen mit neuem Betreiber" if ev["switch"] else "kein Wechsel", "accent": "switch"},
        {"label": "Renovierungen", "value": str(reno_running), "sub": f"laufend · {reno_planned} weitere geplant", "accent": "reno"},
        {"label": "Geplante Standorte", "value": str(len(pipe)), "sub": f"{grades.get('Bestätigt', 0)} bestätigt · {grades.get('Berichtet', 0)} berichtet · {grades.get('Gerücht', 0)} Gerücht", "accent": "pipe"},
    ]
    if ev["close"] and all("Regeländerung" in r.get("Änderung", "") for r in ev["close"]):
        kpis[2]["sub"] = f"{chain_note(ev['close'])} · durch Regeländerung erfasst"

    first_ed = not prev and not (cur and cur.get("prev_total") is not None)
    period_txt = f"{dmy(p_start)}–{dmy(p_end, True)}" + (" (erste Ausgabe – ab nächstem Monat Vergleich zum Vormonat)" if first_ed else "")

    open_items = []
    if addr_open:
        open_items.append(f"{addr_open} Adressen bei zwei Ketten gelistet – Entscheidung im Tab „Adressabgleich“")
    for k in cand_open:
        open_items.append(f"Kandidat {k.get('Kandidat')} – {k.get('Status').lower()}")
    for c, d in sorted(last_checked.items()):
        dd = date.fromisoformat(d)
        if (run - dd).days > 3:
            open_items.append(f"{c}: zuletzt geprüft am {dmy(dd, True)}")
    if unmapped:
        open_items.append("Nicht auf der Karte (Ort ohne Koordinaten): " + ", ".join(sorted(set(unmapped))))
    if dropped:
        open_items.append("Weitere Änderungen im Tab „Änderungen“: " + ", ".join(c["head"] for c in dropped))
    open_items = open_items[:5]

    out = {
        "title": "Monatsupdate Lebensmittelhandel Slowenien",
        "edition": f"{MONTHS[run.month - 1]} {run.year}",
        "period": period_txt,
        "stand": dmy(run, True),
        "kpis": kpis,
        "map_points": uniq,
        "news": cards,
        "gantt": {"start": win_start.isoformat(), "end": win_end.isoformat(), "today": run.isoformat(), "rows": gantt,
                  "footnote": ("Ebenfalls abgeschlossen (ohne genaue Daten): " + ", ".join(reno_done_vague) + ".") if reno_done_vague else ""},
        "pipeline": pipe_shown,
        "pipeline_more": max(len(pipe) - len(pipe_shown), 0),
        "chains": chains,
        "open_items": open_items,
    }
    json.dump(out, open(out_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    if final:
        rec = {"edition": ed_key, "period_start": p_start.isoformat(), "period_end": p_end.isoformat(),
               "total": total, "prev_total": prev_total,
               # pipeline entries known when the edition was first built (later additions in the same month = "neu")
               "pipeline_ids_at_start": (cur or {}).get("pipeline_ids_at_start") or sorted(p["id"] for p in pipe)}
        state["editions"] = [e for e in eds if e["edition"] != ed_key] + [rec]
        state["editions"].sort(key=lambda e: e["edition"])
        json.dump(state, open(state_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ok", out_p, "cards", len(cards), "points", len(uniq), "gantt", len(gantt), "pipeline", len(pipe))


if __name__ == "__main__":
    main()
