#!/bin/bash
# Monatsupdate bauen: tools/update.sh <Filialtracker_<datum>.xlsx> <lauf-datum YYYY-MM-DD>
# Schreibt monatsupdate.png / monatsupdate.pdf (feste Links) und archiv/<YYYY-MM>.png/.pdf,
# und merkt sich die Ausgabe in tools/state.json. Danach: git add/commit/push.
# Exit 3 = Orte ohne Koordinaten -> in tools/towns_extra.json ergänzen (Quelle in towns_extra_sources.md), neu starten.
set -euo pipefail
cd "$(dirname "$0")/.."
WB="$(realpath "$1")"; RUN="$2"; TMP="$(mktemp -d)"
python3 tools/make_data.py "$WB" "$RUN" tools/state.json "$TMP/data.json"
python3 tools/build_infographic.py "$TMP/data.json" tools/svn_border.json "$TMP/monatsupdate.html"
node tools/render.js "$TMP/monatsupdate.html" monatsupdate.png monatsupdate.pdf
ED="${RUN:0:7}"; mkdir -p archiv
cp monatsupdate.png "archiv/$ED.png"; cp monatsupdate.pdf "archiv/$ED.pdf"
python3 tools/make_data.py "$WB" "$RUN" tools/state.json "$TMP/data.json" --final >/dev/null
echo "fertig: monatsupdate.png, monatsupdate.pdf, archiv/$ED.*"
