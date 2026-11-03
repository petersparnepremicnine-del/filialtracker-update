#!/bin/bash
# Arbeitsmappe veröffentlichen: tools/publish_workbook.sh <Filialtracker_<datum>.xlsx>
# Legt die Arbeitsmappe als Filialtracker_Slowenien.xlsx auf den Branch "daten" – immer nur EIN Commit
# (der Branch wird jedes Mal ersetzt, frühere Monate bleiben nicht als Verlauf stehen).
# Fester Link: https://raw.githubusercontent.com/petersparnepremicnine-del/filialtracker-update/daten/Filialtracker_Slowenien.xlsx
set -euo pipefail
cd "$(dirname "$0")/.."
WB="$(realpath "$1")"
URL="$(git remote get-url origin)"
TMP="$(mktemp -d)"
cd "$TMP"
git init -q -b daten
cp "$WB" Filialtracker_Slowenien.xlsx
printf 'Aktuelle Arbeitsmappe des Filial-Trackers (nur die neueste Version, wird monatlich ersetzt).\nStand: %s\n' "$(date +%F)" > README.txt
git add Filialtracker_Slowenien.xlsx README.txt
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -q -m "Arbeitsmappe Stand $(date +%F)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push -q -f "$URL" daten
echo "veröffentlicht: Branch daten (1 Commit)"
