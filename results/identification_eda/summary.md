# Classical Identification EDA

## Setup

- Unit of comparison: Landkreis. Organic farming is measured at district level,
  so nitrate is aggregated from stations to district-year means.
- Exposure distinction: high vs. low growth in organic agricultural area share
  from 2016 to 2020.
- Pre-trend period: 2012-2015.
- Main descriptive outcome: mean nitrate in 2016-2020 minus mean nitrate in
  2012-2015.

## Descriptive Findings

- Eligible districts with observed organic shares: 39.
- Mean organic farming share increased from
  3.54% in 2016 to
  5.34% in 2020.
- High-growth districts: 10. Low-growth districts: 10.
- Baseline nitrate mean, 2012-2015: 52.37 mg/L in high-growth
  districts and 53.51 mg/L in low-growth districts.
- Baseline nitrate slope, 2012-2015: 2.15 mg/L per year in
  high-growth districts and -0.24 mg/L per year in low-growth
  districts.
- Correlation between organic growth and nitrate change: -0.35.
- Correlation between 2020 organic share and 2020 nitrate level: 0.09.

## Interpretation

The change-on-change EDA shows a negative descriptive relationship: districts
with stronger organic farming growth tend to have lower nitrate changes over
2016-2020 relative to the 2012-2015 baseline. This is suggestive, not causal.
The pre-trend check is not clean enough for a simple binary Difference-in-
Differences design, because high- and low-growth districts already differ in
their baseline nitrate dynamics. The safer next step is a continuous exposure
model with station and year fixed effects, not a strict treatment/control event
study.
