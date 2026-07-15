# Organic Farming EDA

## Main findings

- Organic-area shares are available for 35 of the 40 sampled
  districts. Five districts are suppressed or missing.
- The mean district share increased from
  3.58% in 2016 to
  5.39% in 2020.
- Every eligible district recorded a positive increase. There is therefore no
  genuinely untreated or never-treated district.
- The descriptive correlation between 2016-2020 organic-area growth and the
  change in district nitrate means from 2012-2015 to 2019-2022 is
  -0.29. This is not a causal estimate.

## Candidate groups

For exploratory plots only:

- `high_growth_exposure`: change of at least
  2.74 percentage points, 9 districts and
  19 stations.
- `low_growth_comparison`: change of at most
  0.86 percentage points, 9 districts and
  28 stations.

These are intensity groups, not identified treatment and control groups.
Treatment is assigned at Landkreis level, so inference must be clustered by
Landkreis rather than monitoring station.

## Why binary DiD is not yet credible

- There is no observed policy adoption date or exogenous treatment event.
- All eligible districts increase organic farming.
- The annual Regionalstatistik values between 2016 and 2020 are interpolated
  from two census snapshots and cannot support an annual event study.
- Baseline balance is weak: the standardised mean difference is
  1.23 for the 2016 organic-area share and
  -1.33 for agricultural area.
- The baseline nitrate-trend SMD is
  0.49, which does not establish
  parallel trends with only nine districts per group.

## Recommended next model

Use organic-area share as a continuous Landkreis-level exposure in a
station-and-year fixed-effects model, cluster standard errors by Landkreis, and
restrict the primary window to observed census years or explicitly label
interpolated exposure. A binary DiD should wait for a defensible external
policy/adoption date.
