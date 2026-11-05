#!/bin/bash
# Quartals- und Jahresberichte (vereinbart 5.11.2026): tools/report.sh <Filialtracker_<datum>.xlsx> <lauf-datum> <quarter|year|season>
#   quarter -> quartalsbericht.png/.pdf/.pptx + archiv/<JJJJ>-Q<n>.*      (Lauf im Januar, April, Juli, Oktober)
#   year    -> jahresbericht.png/.pdf/.pptx   + archiv/<JJJJ>-Jahr.*      (Lauf im Januar, Kalenderjahr davor)
#   season  -> jahresbericht_sep-aug.png/...  + archiv/<JJJJ>-<JJJJ>-Sep-Aug.* (Lauf im September)
# Setzt voraus, dass update.sh für denselben Lauf schon gelaufen ist (state.json enthält die Monatsausgabe).
set -euo pipefail
cd "$(dirname "$0")/.."
WB="$(realpath "$1")"; RUN="$2"; KIND="$3"; TMP="$(mktemp -d)"
case "$KIND" in
  quarter) OUT=quartalsbericht ;;
  year)    OUT=jahresbericht ;;
  season)  OUT=jahresbericht_sep-aug ;;
  *) echo "Art: quarter|year|season" >&2; exit 2 ;;
esac
python3 tools/make_data.py "$WB" "$RUN" tools/state.json "$TMP/data.json" --report "$KIND"
# Archivname aus der Ausgabe: "Q4 2026" -> 2026-Q4, "2026" -> 2026-Jahr, "September 2026 – August 2027" -> 2026-2027-Sep-Aug
ARC="$(python3 -c "import json,re,sys;e=json.load(open(sys.argv[1]))['edition'];k=sys.argv[2];y=re.findall(r'\d{4}',e)
print(f'{y[0]}-{e.split()[0]}' if k=='quarter' else f'{y[0]}-Jahr' if k=='year' else f'{y[0]}-{y[1]}-Sep-Aug')" "$TMP/data.json" "$KIND")"
python3 tools/build_infographic.py "$TMP/data.json" tools/svn_border.json "$TMP/r.html"
node tools/render.js "$TMP/r.html" "$OUT.png" "$OUT.pdf"
node tools/render_map.js "$TMP/r.html" "$TMP/map.png"
APPLY="$(find /root/.claude/skills /mnt/skills -path '*pptx/scripts/apply_theme.js' 2>/dev/null | head -1 || true)"
PPTX_SKILL_DIR="${APPLY%/scripts/apply_theme.js}" node tools/build_pptx.js "$TMP/data.json" "$TMP/map.png" "$OUT.pptx"
mkdir -p archiv; for e in png pdf pptx; do cp "$OUT.$e" "archiv/$ARC.$e"; done
echo "fertig: $OUT.png/.pdf/.pptx, archiv/$ARC.*"
