# aee_organicfarming

Reproducible data and analysis pipeline for an econometric study of organic farming
and groundwater nitrate pollution in Niedersachsen.

## Data Download

Download the UBA Nitratbericht 2024 workbook:

```bash
python3 scripts/download_datasets.py --insecure
```

`--insecure` is needed in this local environment because Python cannot verify the
installed CA bundle for several public German/EU portals. Omit it on machines
with a working CA setup.

The ZIP is used only for transport and discarded. The raw data is:

`data/raw/uba_nitrate_report_2024/Download_Daten_Nitratbericht_2024.xlsx`

Create the analysis-ready Niedersachsen station-year panel:

```bash
python3 scripts/create_panel_dataset.py
```

This writes the single modeling table:

`data/processed/gw_nitrate_panel_ni.csv`

The panel starts with 1,111 nitrate observations for 103 Niedersachsen
groundwater stations from 2012-2022. Station attributes from `GW_Messstellen`
are joined into the panel during creation, so a separate station CSV is not
needed.

Future datasets should be joined into this same panel using station, year, and
spatial identifiers as appropriate. Raw source files remain separate under
`data/raw/`.
