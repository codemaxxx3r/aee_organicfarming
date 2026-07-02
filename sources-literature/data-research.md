# Datensätze für das Projekt (Niedersachsen)

Im Folgenden sind die bisher identifizierten Datensätze und Datenquellen für das Projekt zusammengestellt. Der Fokus liegt auf Niedersachsen, da dort eine gute Datenverfügbarkeit besteht und sich verschiedene Geodaten über räumliche Identifikatoren (z. B. Gemeinden, Gemarkungen oder Koordinaten) miteinander verknüpfen lassen.

---

## 1. ALKIS – Amtliches Liegenschaftskatasterinformationssystem

**Zweck**

ALKIS dient als Grundlage zur Begründung der Auswahl Niedersachsens als Untersuchungsregion. Über das Kataster lassen sich Flächennutzungsanteile (z. B. Landwirtschaft, Siedlungsflächen, Wald etc.) bestimmen und Bundesländer vergleichen.

Die ursprüngliche Motivation war, nicht nur die absolute landwirtschaftliche Fläche zu betrachten (bei der Bayern vorne liegt), sondern die Anteile von Landwirtschaft als Flächennutzung.

**Link**

- https://www.adv-online.de/Products/Real-Estate-Cadastre/ALKIS/

---

## 2. Grundwasser-Messstationen (Nitrat)

**Quelle**

Niedersächsisches Umweltportal (NUMIS)

**Inhalt**

Shapefiles der Grundwasser-Messstellen mit Nitratwerten für den Zeitraum **2016–2022**.

**Link**

- https://numis.niedersachsen.de/trefferanzeige%3Bjsessionid%3D762F32FF29C340E51B8FED0F2C9B55C1?docuuid=6E2E0EFE-664B-4DCB-8877-54500E47745E&q=Off-Site

---

## 3. BORIS Niedersachsen – Bodenrichtwerte

**Quelle**

BORIS (Bodenrichtwertinformationssystem)

**Inhalt**

Geodaten zu Bodenrichtwerten. Die Daten können u. a. als Proxy für Landnutzung bzw. wirtschaftliche Nutzung von Flächen dienen.

Der Datensatz wurde bereits als Shapefile heruntergeladen.

Zusätzlich existiert eine Webanwendung mit zeitlicher Darstellung der Bodenrichtwerte (ca. 2000–2025).

### Datensätze

- BORIS Niedersachsen:
  https://www.bodenrichtwerte-deutschland.de/boris/niedersachsen#sec2

- Zeitliche Darstellung der Bodenrichtwerte:
  https://immobilienmarkt.niedersachsen.de/bodenrichtwerte?zoom=6.22&teilmarkt=Bauland&stichtag=2026-01-01

### Hintergrundinformationen

- https://www.gag.niedersachsen.de/startseite/bodenrichtwerte/allgemeine_infos/bodenrichtwerte-im-internet-88303.html

---

## 4. Ergänzende Datensätze

### 4.1 Landwirtschaftliche Struktur- und Bewirtschaftungsdaten

Der BORIS-Datensatz könnte mit Informationen über

- verwendete Düngemittel,
- landwirtschaftliche Bewirtschaftungsformen,
- weitere Agrarstatistiken

ergänzt werden.

Eine mögliche Quelle ist die **Regionalstatistikdatenbank (GENESIS)**. Die Verknüpfung sollte über Gemeinden (GEN) bzw. amtliche Gemeindeschlüssel möglich sein.

**Link**

- https://www.regionalstatistik.de/genesis/online/logon

---

### 4.2 Boden- und Hydrogeologiedaten

Als weitere Ergänzung können Bodeneigenschaften bzw. hydrogeologische Informationen genutzt werden.

Mögliche Datensätze sind:

#### Variante A

Rohstoffsicherungskarte (NIBIS)

- https://numis.niedersachsen.de/trefferanzeige?docuuid=74dfba00-8240-460a-8f22-49759209e6d7

Kartendienst:

- https://nibis.lbeg.de/cardoMap3/?th=RSK25

Pfad:
> Themenkarte → Rohstoffsicherungskarte

#### Variante B

NIBIS Geonetwork

- https://nibis.lbeg.de/geonetwork/srv/eng/catalog.search#/metadata/4a7cad07-673e-44d1-9b90-33cc95bf45e2

Kartendienst:

- https://nibis.lbeg.de/cardoMap3/?th=RSK25

Pfad:
> Themenkarten → Bodenkunde bzw. Hydrogeologie

---

## 5. Alternative Landnutzungsdaten

Alternativ zu BORIS könnten europaweit standardisierte Landnutzungsdaten aus **Copernicus/CORINE Land Cover (CLC)** verwendet werden.

**Link**

- https://land.copernicus.eu/en/products/corine-land-cover?tab=datasets

---

## 6. Geplante Datenintegration und Methoden

Derzeit erscheint folgende Kombination sinnvoll:

1. Nitrat-Messstellen (NUMIS)
2. Bodenrichtwerte (BORIS)
3. Flächennutzung (ALKIS oder alternativ CORINE)
4. Landwirtschaftliche Struktur- und Bewirtschaftungsdaten (GENESIS)
5. Boden- und Hydrogeologiedaten (NIBIS)

Die Verknüpfung der Datensätze kann – je nach Datenquelle – über räumliche Geometrien (Shapefiles), Gemeinden (GEN/AGS), Wasserkörper, Messstellen oder Koordinaten erfolgen.

### 6.1 Identifikation relevanter Veränderungen innerhalb der Daten für Control  und Treatment Gruppierung

Nachdem alle relevanten Datensätze zu einem gemeinsamen Paneldatensatz zusammengeführt wurden, soll der Fokus auf diejenigen Messstationen bzw. Zeiträume gelegt werden, in denen sich die erklärenden Variablen besonders stark verändert haben.

Dabei steht **nicht** die Veränderung der Nitratwerte im Vordergrund (diese bilden die Zielvariable), sondern insbesondere Änderungen in der landwirtschaftlichen Bewirtschaftung. Von besonderem Interesse wären beispielsweise:

- eine Umstellung auf einen höheren Anteil organischer bzw. ökologischer Bewirtschaftungsmethoden,
- Veränderungen im Einsatz von Düngemitteln oder Pflanzenschutzmitteln,
- weitere relevante Änderungen der landwirtschaftlichen Nutzung.

Die Idee besteht darin, natürliche "Behandlungseffekte" (treatments) zu identifizieren und anschließend zu untersuchen, wie sich diese Änderungen zeitlich auf die Nitratkonzentrationen im Grundwasser auswirken.

Falls geeignete Daten zur Bewirtschaftung nicht verfügbar sind, könnten alternativ zeitliche Veränderungen von Boden- oder Standortmerkmalen betrachtet werden. Aufgrund der höheren Komplexität erscheint die Analyse von Änderungen der landwirtschaftlichen Bewirtschaftung jedoch derzeit als der vielversprechendere Ansatz.

### 6.2 Methodik und technische Umsetzung

Die in diesem Dokument zusammengestellten Datensätze bilden die Grundlage für die weitere Analyse. Im nächsten Schritt werden die methodischen Ansätze sowie die geplante technische Umsetzung dokumentiert.

Dazu gehören unter anderem:

- die Aufbereitung und Zusammenführung der Datensätze zu einem Paneldatensatz,
- Verfahren zur räumlichen Verknüpfung (Spatial Joins) und Datenbereinigung,
- die Identifikation relevanter Veränderungen in den erklärenden Variablen,
- statistische und kausale Analyseverfahren (z. B. Panelmodelle, Difference-in-Differences oder Event Studies),
- sowie die verwendeten Software-Tools, Bibliotheken und der geplante Workflow.

Die Details hierzu werden im separaten Dokument **`methodik_und_tools.md`** beschrieben.

