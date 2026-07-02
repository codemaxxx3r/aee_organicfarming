# Ziel nach allen Blöcken A, B, C ...

ist ein Datensatz von ca.:

| station_id | year | nitrate | agriculture_share | forest_share | settlement_share | soil_type | permeability |
|------------|------|----------|-------------------|--------------|------------------|-----------|--------------|

Um Treatment-Variablen aufzubauen wie:

| Municipality | Year | Organic_share |
|--------------|------|---------------|
| A | 2012 | 3 % |
| A | 2013 | 3 % |
| A | 2014 | 5 % |
| A | 2015 | 19 % |
| A | 2016 | 20 % |

Dann könnte man z.B. definieren:

### Treatment-Year

erstes Jahr,  
in dem Organic_share  
deutlich steigt

oder

### Treatment

Δ Organic_share > 10 Prozentpunkte

Das wäre wesentlich sauberer als einfach "Öko ja/nein".

Erst wenn eine belastbare Treatment-Variable definiert ist, den finalen Paneldatensatz erstellen und anschließend mit CSDID, DRDID oder einer Staggered Adoption Difference-in-Differences analysieren.

---

# A. Landnutzung und landwirtschaftliche Flächen

Das Ziel dieses Blocks ist:

Für jede Grundwasser-Messstation bestimmen, welche landwirtschaftlichen Flächen in ihrer Umgebung liegen und wie diese genutzt werden.

## Priorität 1: ALKIS Landnutzung

Der Datensatz enthält bereits die tatsächliche Nutzung der Flächen:

- Landwirtschaft
- Wald
- Wohngebiet
- Industrie
- Grünland
- Gewässer
- usw.

Damit können wir z.B. für jede Messstation berechnen:

- Anteil Landwirtschaft im 500 m Radius
- Anteil Landwirtschaft im 1 km Radius
- Anteil Acker
- Anteil Grünland
- Anteil Siedlung
- Anteil Wald

Das sind später ausgezeichnete Kontrollvariablen.

### Spatial Join

```text
Messstation
↓
500 m Buffer
↓
ALKIS Polygone
↓
Flächenanteile berechnen
```

---

# B. Daten zur Änderung der Policy (Treatment)

In dem Block suchen wir nicht einfach Ökonutzungsdaten/Flächen, sondern statistische:

Wann wurde Fläche X von konventionell → ökologisch umgestellt?

## Möglichkeit B.1: GENESIS

Das wäre mein erster Kandidat.

Falls GENESIS Daten enthält wie:

| Gemeinde | Jahr | Biofläche |
|-----------|------|------------|

oder

| Gemeinde | Jahr | Anteil Ökolandbau |
|-----------|------|-------------------|

dann hätten wir direkt:

### Gemeinde A

| Jahr | Anteil |
|------|---------|
| 2012 | 3 % |
| 2013 | 4 % |
| 2014 | 4 % |
| 2015 | 12 % |
| 2016 | 13 % |

Hier könnte man definieren:

**Treatment = 2015**

Das wäre nahezu ideal.

## Möglichkeit B.2: Landwirtschaftszählungen 2020

https://www.statistik.niedersachsen.de/presse/niedersachsischer-oko-landbau-endgultige-ergebnisse-der-landwirtschaftszahlung-2020-202434.html

Das Landesamt für Statistik veröffentlicht regelmäßig Daten zu:

- ökologischen Betrieben
- ökologisch bewirtschafteter Fläche
- Anbauflächen
- Kulturarten

Falls diese auf Gemeinde- oder Kreisebene vorliegen, könnten sie ebenfalls als zeitvariierende Treatment-Variable dienen.

## Möglichkeit B.3: LAVES / Landwirtschaftsministerium 2024

https://www.laves.niedersachsen.de/startseite/lebensmittel/okologischer_landbau/entwicklung_des_okologischen_landbaus_in_nds/entwicklung-des-okologischen-landbaus-in-niedersachsen-und-bremen-73625.html

Diese liefern viele Statistiken über den Ausbau des Ökolandbaus.

Allerdings scheint das meist auf Landesebene oder aggregiert vorzuliegen.

Das wäre interessant zur Beschreibung des Trends, aber wahrscheinlich zu grob für ein DiD.

---

# C. NIBIS Bodenwerte

*Nur falls wir genug Zeit haben, als Confoundervariable*

https://www.lbeg.niedersachsen.de/kartenserver/nibis/niedersaechsisches-bodeninformationssystem-nibis-841.html

- Bodentyp
- Bodenart
- Wasserdurchlässigkeit
- Hydrogeologie
- Grundwasserneubildung

Denn Nitrat transportiert sich in Sandböden völlig anders als in Tonböden.

---

# D. DiD Methoden anwenden

Erst wenn eine belastbare Treatment-Variable definiert ist, den finalen Paneldatensatz erstellen und anschließend mit CSDID, DRDID oder einer Staggered Adoption Difference-in-Differences analysieren.