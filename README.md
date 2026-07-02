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
  dataset/
    gw_nitrate_panel_ni.csv
  scripts/
    uba_nitrate_report_2024/
      download.py
      preprocess.py
    dynamic_world/
      download.py
      preprocess.py
    create_panel_dataset.py
```

The UBA ZIP is discarded after extracting the workbook. UBA preprocessing
creates `uba_nitrate_station_year_ni.csv`, which is also the station source for
the Dynamic World download.

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

The final panel contains 1,111 nitrate observations for 103 Niedersachsen
groundwater stations from 2012-2022. Dynamic World starts in mid-2015, so
complete calendar-year covariates begin in 2016; earlier rows remain empty for
these variables.

Until Dynamic World has been authenticated and processed, create an UBA-only
development panel with:

```bash
python3 data/scripts/create_panel_dataset.py --allow-missing-dynamic-world
```

Future sources should follow the same `raw/` and `processed/` structure. The
final panel builder should consume only processed source tables.
