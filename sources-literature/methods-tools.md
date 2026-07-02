# Methodik und Tools

Dieses Dokument beschreibt den geplanten methodischen Workflow sowie die technischen Werkzeuge für die Analyse. Die zugrunde liegenden Datensätze sind im Dokument **`datensaetze.md`** beschrieben.

---

# 1. Datenaufbereitung

Zunächst werden sämtliche in `data-research.md` beschriebenen Datenquellen aufbereitet und in einen gemeinsamen Paneldatensatz überführt.

Dabei gehören insbesondere folgende Schritte dazu:

- Import der Excel-, CSV- und Shapefile-Datensätze
- Vereinheitlichung von IDs und Zeitformaten
- Räumliche Verknüpfung (Spatial Join)
- Zusammenführung aller Variablen auf Messstellen- und Jahresebene
- Bereinigung fehlender oder inkonsistenter Werte
- Erstellung eines finalen Paneldatensatzes

---

# 2. Identifikation relevanter Änderungen

Sobald der Paneldatensatz erstellt wurde, sollen diejenigen Messstationen bzw. Regionen identifiziert werden, bei denen sich die erklärenden Variablen besonders stark verändert haben.

Dabei liegt der Fokus **nicht** auf Veränderungen der Nitratwerte (Zielvariable), sondern auf Änderungen der landwirtschaftlichen Bewirtschaftung.

Insbesondere interessieren Zeitpunkte, an denen beispielsweise

- von konventioneller auf organische bzw. ökologische Bewirtschaftung umgestellt wurde,
- sich der Einsatz von Düngemitteln oder Pflanzenschutzmitteln deutlich verändert hat,
- oder andere relevante Änderungen der landwirtschaftlichen Nutzung stattgefunden haben.

Diese Änderungen definieren später die Behandlungszeitpunkte (Treatment).

---

# 3. Geplantes kausales Design

## Difference-in-Differences (DiD)

Grundidee:

- Flächen identifizieren, bei denen zwischen ca. 2000 und 2025 auf organische Bewirtschaftungsmethoden umgestellt wurde.
- Den Zeitpunkt der Umstellung als Treatment-Zeitpunkt speichern.
- Für diese Flächen nahegelegene Grundwasser-Messstationen bestimmen.
- Den räumlichen Bezug zwischen landwirtschaftlicher Fläche und Messstation herstellen.
- Anschließend untersuchen, ob sich die Nitratwerte nach der Umstellung systematisch verändern.

Da verschiedene Flächen die Umstellung zu unterschiedlichen Zeitpunkten durchführen (Staggered Adoption), eignet sich ein klassisches DiD-Modell nur eingeschränkt.

Geplant ist daher der Einsatz moderner Verfahren für Difference-in-Differences mit mehreren Behandlungszeitpunkten.

Mögliche Verfahren:

- Callaway & Sant'Anna Difference-in-Differences (CSDID)
- Doubly Robust Difference-in-Differences (DRDID)
- Staggered Adoption Difference-in-Differences
- Event-Study-Analysen zur Untersuchung dynamischer Effekte

---

# 4. Offene Punkte

- Geeigneten Datensatz zur Umstellung auf organische Bewirtschaftung finden.
- Definition der räumlichen Zuordnung zwischen landwirtschaftlichen Flächen und Messstationen.
- Auswahl geeigneter Kontrollgruppen.
- Festlegung des räumlichen Radius bzw. Einzugsgebiets einer Messstation.
- Auswahl des endgültigen DiD-Schätzverfahrens.