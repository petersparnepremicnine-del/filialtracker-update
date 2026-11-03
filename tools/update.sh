#!/bin/bash
# Monatsupdate bauen: tools/update.sh <Filialtracker_<datum>.xlsx> <lauf-datum YYYY-MM-DD>
# Schreibt monatsupdate.png / .pdf / .pptx (feste Links) und archiv/<YYYY-MM>.png/.pdf,
# merkt sich die Ausgabe in tools/state.json und legt die Arbeitsmappe auf den Branch "daten"
# (tools/publish_workbook.sh, pusht selbst). Danach: git add/commit/push für main.
# Exit 3 = Orte ohne Koordinaten -> in tools/towns_extra.json ergänzen (Quelle in towns_extra_sources.md), neu starten.
set -euo pipefail
cd "$(dirname "$0")/.."
WB="$(realpath "$1")"; RUN="$2"; TMP="$(mktemp -d)"
python3 tools/make_data.py "$WB" "$RUN" tools/state.json "$TMP/data.json"
python3 tools/build_infographic.py "$TMP/data.json" tools/svn_border.json "$TMP/monatsupdate.html"
node tools/render.js "$TMP/monatsupdate.html" monatsupdate.png monatsupdate.pdf
# PowerPoint-Fassung (gleiche Daten): Karte als Bild, dann Folien; Theme-Farben, wenn das pptx-Skill vorhanden ist
node tools/render_map.js "$TMP/monatsupdate.html" "$TMP/map.png"
APPLY="$(find /root/.claude/skills /mnt/skills -path '*pptx/scripts/apply_theme.js' 2>/dev/null | head -1 || true)"
PPTX_SKILL_DIR="${APPLY%/scripts/apply_theme.js}" node tools/build_pptx.js "$TMP/data.json" "$TMP/map.png" monatsupdate.pptx
ED="${RUN:0:7}"; mkdir -p archiv
cp monatsupdate.png "archiv/$ED.png"; cp monatsupdate.pdf "archiv/$ED.pdf"; cp monatsupdate.pptx "archiv/$ED.pptx"
python3 tools/make_data.py "$WB" "$RUN" tools/state.json "$TMP/data.json" --final >/dev/null
tools/publish_workbook.sh "$WB"
echo "fertig: monatsupdate.png/.pdf/.pptx, archiv/$ED.*, Branch daten"
