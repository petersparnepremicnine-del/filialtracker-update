# Monatsupdate Lebensmittelhandel Slowenien

Monatliche Infografik zum Filial-Tracker (Eröffnungen, Schließungen, Kettenwechsel, Renovierungen, geplante Standorte).
Wird nach jedem Monatslauf automatisch neu erstellt.

**Feste Links (immer die aktuelle Ausgabe):**

- Bild (Bildschirm, eine Seite): https://raw.githubusercontent.com/petersparnepremicnine-del/filialtracker-update/main/monatsupdate.png
- PDF (Druck, 2 Seiten A4 quer): https://raw.githubusercontent.com/petersparnepremicnine-del/filialtracker-update/main/monatsupdate.pdf
- Arbeitsmappe (alle Tabs, Stand des letzten Laufs): https://raw.githubusercontent.com/petersparnepremicnine-del/filialtracker-update/daten/Filialtracker_Slowenien.xlsx
  (Branch `daten`, enthält immer nur die neueste Version)

Frühere Ausgaben: Ordner `archiv/` (`JJJJ-MM.png` / `.pdf`).

## Ablauf

1. Monatslauf (1. des Monats, Cloud): alle Ketten außer Spar → Infografik wird erstellt (Spar mit Stand des Vormonats).
2. Spar-Prüfung (2. des Monats, Chrome): Spar wird ergänzt → Infografik wird mit derselben Ausgabe neu erstellt.
3. Power Automate (3. des Monats): holt Arbeitsmappe und Infografik in Microsoft 365.

## Werkzeuge (`tools/`)

- `update.sh <arbeitsmappe.xlsx> <datum>` – baut alles aus der Arbeitsmappe des Laufs (gleiche Tabs wie die Google-Tabelle).
- `make_data.py` – liest die Tabs und erstellt die Inhalte (Zeitraum = seit der letzten Ausgabe, `state.json`).
- `build_infographic.py`, `render.js` – Layout (Grün/Rot/Weiß) und Ausgabe als PNG/PDF.
- `towns_si.json` – Ortskoordinaten aus GeoNames (CC BY 4.0); `towns_extra.json` – ergänzte Orte mit Quelle in `towns_extra_sources.md`.
- `svn_border.json` – Staatsgrenze aus Natural Earth (gemeinfrei).

Dieses Repository ist öffentlich. Der Branch `main` enthält die Infografik und die Werkzeuge; die Arbeitsmappe liegt (mit Zustimmung des Nutzers, 3.11.2026) nur auf dem Branch `daten`, der bei jedem Lauf ersetzt wird.
