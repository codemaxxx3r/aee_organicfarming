# aee_organicfarming

Reproducible data and analysis pipeline for an econometric study of organic
farming and groundwater nitrate pollution in Niedersachsen.

## Data Pipeline

Install the dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Each source has an independent download and preprocessing pipeline:

```bash
# UBA nitrate data
python3 data/scripts/uba_nitrate_report_2024/download.py --insecure
python3 data/scripts/uba_nitrate_report_2024/preprocess.py

# Google Dynamic World
earthengine authenticate
python3 data/scripts/dynamic_world/download.py --ee-project PROJECT_ID
python3 data/scripts/dynamic_world/preprocess.py

# Copernicus CORINE Land Cover
python3 data/scripts/corine_land_cover/download.py --ee-project PROJECT_ID
python3 data/scripts/corine_land_cover/preprocess.py

# Administrative boundaries and Regionalstatistik
python3 data/scripts/administrative_boundaries/download.py
python3 data/scripts/regionalstatistik/preprocess.py

# Final panel
python3 data/scripts/create_panel_dataset.py
```

The data layout is:

```text
data/
  uba_nitrate_report_2024/
    raw/
    processed/
  dynamic_world/
    raw/
    processed/
  corine_land_cover/
    raw/
    processed/
  administrative_boundaries/
    raw/
  regionalstatistik/
    raw/
    processed/
  dataset/
    gw_nitrate_panel_ni.csv
  scripts/
    uba_nitrate_report_2024/
      download.py
      preprocess.py
    dynamic_world/
      download.py
      preprocess.py
    corine_land_cover/
      download.py
      preprocess.py
    administrative_boundaries/
      download.py
    regionalstatistik/
      preprocess.py
    create_panel_dataset.py
```

The UBA ZIP is discarded after extracting the workbook. UBA preprocessing
creates `uba_nitrate_station_year_ni.csv`, which is also the station source for
the land-cover downloads.

Dynamic World is processed in Earth Engine instead of downloading statewide
10 m rasters. Its raw extraction is a long station-year-buffer table for 500 m
and 1 km buffers from 2016-2022. Preprocessing pivots it into one wide
station-year covariate table.

Dynamic World is a 10 m, Sentinel-2-derived land-cover product licensed under
CC BY 4.0:
https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1
The `crops` class is useful as a local agricultural-land proxy, while `grass`
does not distinguish agricultural grassland from other grass cover. Dynamic
World does not identify organic farming practices.

CORINE is downloaded from the Earth Engine asset
`COPERNICUS/CORINE/V20/100m` for the 2006, 2012, and 2018 inventories. The raw
table contains land-cover shares for 500 m and 1 km station buffers.
Preprocessing linearly interpolates these shares between snapshots, producing
annual values from 2006 through 2018. It does not extrapolate beyond 2018.

CORINE has 100 m pixels, a 25 hectare minimum mapping unit, and a 100 m minimum
mapping width. Its 500 m buffer estimates are therefore substantially coarser
than Dynamic World:
https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_CORINE_V20_100m

The final panel contains 1,111 nitrate observations for 103 Niedersachsen
groundwater stations from 2012-2022. Dynamic World covariates cover 2016-2022.
CORINE covariates cover 2012-2018 within the nitrate panel.

Regionalstatistik snapshots for 2010, 2016 and 2020 are harmonized to current
district boundaries and interpolated between census years. Current BKG VG250
Landkreis polygons assign every station to exactly one district. The resulting
covariates cover 2012-2020 in the nitrate panel. Livestock variables remain
missing before 2020 because they are not reported in the 2010 and 2016 source
files.

The static station-to-district mapping is retained for 2021-2022 even though
Regionalstatistik values are unavailable. `reg_data_available` distinguishes
mapped rows from rows with usable time data.

Missing optional sources can be explicitly allowed during development:

```bash
python3 data/scripts/create_panel_dataset.py \
  --allow-missing-dynamic-world \
  --allow-missing-corine \
  --allow-missing-regionalstatistik
```

Future sources should follow the same `raw/` and `processed/` structure. The
final panel builder should consume only processed source tables.
