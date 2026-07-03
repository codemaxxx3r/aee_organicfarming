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
| Regionalstatistik | Kreis snapshots for 2010, 2016 and 2020 | 2012-2020 | Values are linearly interpolated between census years and assigned to stations through current Landkreis boundaries. Livestock variables are available only in 2020. |

The common period for all four sources is **2016-2018**.

## Interpretation

CORINE interpolation is applied to continuous buffer shares, not to categorical
raster codes. The interpolated years are modelled values between two observed
land-cover inventories and should not be described as annual observations.
`clc_temporal_method`, `clc_lower_year`, `clc_upper_year` and
`clc_interpolation_weight` document this for every row.

Dynamic World is genuinely time-varying annual satellite information, but it
does not identify organic farming. CORINE is coarser and changes only through
its six-year inventories.

Regionalstatistik is reported for Kreise rather than monitoring stations. Each
station is assigned to one current Landkreis by point-in-polygon using BKG
VG250 boundaries. The mapping is stored in
`regionalstatistik/processed/station_county_mapping.csv`.
All 103 stations match exactly one district; the stations cover 40 of
Niedersachsen's 45 current districts. `district_code` remains populated for all
panel years, while `reg_data_available` identifies the 913 rows from 2012-2020
that have Regionalstatistik time data.

The former districts Göttingen (`03152`) and Osterode am Harz (`03156`) are
summed for 2010 and 2016 to match the current Göttingen district (`03159`).
Regional values are then linearly interpolated between 2010, 2016 and 2020.
Symbols for unavailable or confidential values (`-`, `.`) remain missing and
are never interpreted as zero. In particular, livestock counts and livestock
units are not reported in the 2010 and 2016 files, so livestock density is
available only for 2020.

The boundary file is stored separately under `administrative_boundaries/raw/`.
Source: BKG VG250 WFS, Data licence Germany - attribution - version 2.0.

Missing values outside each source's coverage are intentional. Do not replace
them automatically with zero.
