# aee_organicfarming

Reproducible data and analysis pipeline for an econometric study of organic farming
and groundwater nitrate pollution in Niedersachsen.

## Data Download

The current downloader focuses only on the UBA nitrate workbook:

```bash
python3 scripts/download_datasets.py --insecure
```

`--insecure` is needed in this local environment because Python cannot verify the
installed CA bundle for several public German/EU portals. Omit it on machines
with a working CA setup.

The script writes:

- `data/raw/` for downloaded source files and portal/API metadata
- `data/metadata/dataset_manifest.json` for source documentation
- `data/metadata/download_log.jsonl` for checksums, status, and extraction logs

The current UBA Nitratbericht 2024 data download is downloaded and extracted to:

`data/raw/uba_nitrate_report_2024/692b5285-78ca-4081-aa31-4b327cf0105f_XLSX/Download_Daten_Nitratbericht_2024.xlsx`

The UBA workbook can be converted into analysis-ready CSV tables with:

```bash
python3 scripts/prepare_uba_nitrate_panel.py
```

This writes:

- `data/processed/uba_nitrate_report_2024/gw_stations_de.csv`
- `data/processed/uba_nitrate_report_2024/gw_nitrate_panel_de.csv`
- `data/processed/uba_nitrate_report_2024/gw_nitrate_panel_ni.csv`
- `data/processed/uba_nitrate_report_2024/summary.json`

For the nitrate target variable, this UBA dataset is the stronger first
candidate than the NUMIS shapefile: it is a tabular XLSX data release for the
Nitratbericht 2024, covers 2012-01-01 to 2022-12-31 according to UBA CSW
metadata, and uses CC BY 4.0. It contains groundwater and surface-water records,
so the later processing step must filter to groundwater before building the
station-by-year panel.

Initial workbook inspection:

- `GW_Messstellen`: 767 groundwater stations with coordinates and water-body IDs
- `GW_Nitrat_MW`: 7,311 groundwater station-year annual nitrate means, 2012-2022
- Niedersachsen is directly identifiable through `NI_...` groundwater station
  codes: 103 stations and 1,111 annual nitrate rows
- `OW_*` sheets contain surface-water records and should stay out of the first
  groundwater target-variable panel

`data/gis/` is not needed at this stage because the UBA workflow starts from
tabular station coordinates and annual values. We can recreate a GIS folder later
once we begin spatial joins, buffers, or exported geospatial layers.
