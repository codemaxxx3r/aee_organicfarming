# Data Directory

Each source has its own `raw/` and `processed/` folders. Source-specific scripts
are stored under `data/scripts/`. The combined analysis table is
`data/dataset/gw_nitrate_panel_ni.csv`.

The final table's unit of observation is a groundwater monitoring station and
year. It currently contains 1,111 observations for 103 stations in
Niedersachsen from 2012 to 2022.

## Timeline

| Source | Available in this project | Panel coverage | Important limitation |
| --- | --- | --- | --- |
| UBA nitrate | Annual, 2012-2022 | 2012-2022 | The station panel is unbalanced because nitrate was not measured at every station in every year. |
| Dynamic World | Annual composites, 2016-2022 | 2016-2022 | The source starts in mid-2015, so 2015 is excluded as an incomplete calendar year. Values for 2012-2015 are missing. |
| CORINE | Snapshots for 2006, 2012 and 2018 | 2012-2018 | Land-cover shares are linearly interpolated between snapshots. Nothing is extrapolated beyond 2018, so 2019-2022 are missing. |
| Regionalstatistik | Downloaded file contains 2020 only | Not yet merged | This is a county-level cross-section, not station-level annual data. A single observation cannot be interpolated over time. |

The common period for UBA, Dynamic World and CORINE is **2016-2018**.
Regionalstatistik currently has no multi-year overlap suitable for panel
estimation: its 2020 values can only be joined to stations through their county
for that year.

## Interpretation

CORINE interpolation is applied to continuous buffer shares, not to categorical
raster codes. The interpolated years are modelled values between two observed
land-cover inventories and should not be described as annual observations.
`clc_temporal_method`, `clc_lower_year`, `clc_upper_year` and
`clc_interpolation_weight` document this for every row.

Dynamic World is genuinely time-varying annual satellite information, but it
does not identify organic farming. CORINE is coarser and changes only through
its six-year inventories.

The Regionalstatistik file must be expanded with additional available census
years and matched via county identifiers before it enters this dataset. Its
2020 values should not be copied backward or forward across the panel.

Missing values outside each source's coverage are intentional. Do not replace
them automatically with zero.
