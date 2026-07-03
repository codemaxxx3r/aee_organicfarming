#!/usr/bin/env python3
"""Process Regionalstatistik snapshots and map stations to Landkreise."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable

from shapely.geometry import Point, shape
from shapely.ops import unary_union


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RAW_DIR = ROOT / "data" / "regionalstatistik" / "raw"
DEFAULT_BOUNDARIES = (
    ROOT
    / "data"
    / "administrative_boundaries"
    / "raw"
    / "vg250_krs_ni.geojson"
)
DEFAULT_STATIONS = (
    ROOT
    / "data"
    / "uba_nitrate_report_2024"
    / "processed"
    / "uba_nitrate_station_year_ni.csv"
)
DEFAULT_PROCESSED_DIR = ROOT / "data" / "regionalstatistik" / "processed"
SNAPSHOT_YEARS = (2010, 2016, 2020)
PANEL_END_YEAR = 2022
RAW_METRICS = (
    "agricultural_farms_count",
    "agricultural_area_ha",
    "livestock_farms_count",
    "livestock_units",
    "organic_farms_count",
    "organic_area_ha",
    "organic_livestock_farms_count",
    "organic_livestock_units",
)
DERIVED_METRICS = (
    "organic_farm_share",
    "organic_area_share",
    "livestock_units_per_ha",
    "organic_livestock_unit_share",
)
ALL_METRICS = RAW_METRICS + DERIVED_METRICS
OLD_GOETTINGEN_CODES = ("03152", "03156")
CURRENT_GOETTINGEN_CODE = "03159"


def parse_number(value: str) -> float | None:
    value = value.strip()
    if value in {"", "-", ".", "...", "/"}:
        return None
    return float(value.replace(" ", "").replace(",", "."))


def safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in {None, 0}:
        return None
    return numerator / denominator


def add_derived(record: dict[str, object]) -> dict[str, object]:
    return record | {
        "organic_farm_share": safe_ratio(
            record["organic_farms_count"],
            record["agricultural_farms_count"],
        ),
        "organic_area_share": safe_ratio(
            record["organic_area_ha"],
            record["agricultural_area_ha"],
        ),
        "livestock_units_per_ha": safe_ratio(
            record["livestock_units"],
            record["agricultural_area_ha"],
        ),
        "organic_livestock_unit_share": safe_ratio(
            record["organic_livestock_units"],
            record["livestock_units"],
        ),
    }


def sum_if_complete(values: Iterable[float | None]) -> float | None:
    values = list(values)
    if any(value is None for value in values):
        return None
    return sum(value for value in values if value is not None)


def harmonise_goettingen(
    rows: dict[str, dict[str, object]],
    year: int,
) -> dict[str, dict[str, object]]:
    rows = dict(rows)
    if year < 2020:
        old_rows = [rows[code] for code in OLD_GOETTINGEN_CODES]
        combined: dict[str, object] = {
            "district_code": CURRENT_GOETTINGEN_CODE,
            "district_name": "Göttingen",
            "year": year,
        }
        for metric in RAW_METRICS:
            combined[metric] = sum_if_complete(
                row[metric] for row in old_rows
            )
        rows[CURRENT_GOETTINGEN_CODE] = add_derived(combined)
    for code in OLD_GOETTINGEN_CODES:
        rows.pop(code, None)
    return rows


def read_snapshot(path: Path) -> tuple[int, dict[str, dict[str, object]]]:
    with path.open(encoding="latin-1", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=";"))
    if len(rows) < 10:
        raise ValueError(f"Regionalstatistik file is too short: {path}")
    year = int(rows[6][0])
    records = {}
    for row in rows[9:]:
        if len(row) < 10:
            continue
        district_code = row[0].strip()
        if len(district_code) != 5 or not district_code.startswith("03"):
            continue
        record: dict[str, object] = {
            "district_code": district_code,
            "district_name": row[1].strip(),
            "year": year,
        }
        for metric, value in zip(RAW_METRICS, row[2:10]):
            record[metric] = parse_number(value)
        records[district_code] = add_derived(record)
    return year, harmonise_goettingen(records, year)


def read_all_snapshots(
    raw_dir: Path,
) -> dict[str, dict[int, dict[str, object]]]:
    by_district: dict[str, dict[int, dict[str, object]]] = {}
    files = sorted(
        path
        for path in raw_dir.glob("41141-04-02-4*.csv")
        if path.is_file()
    )
    years_found = set()
    for path in files:
        year, records = read_snapshot(path)
        if year in years_found:
            raise ValueError(f"Duplicate Regionalstatistik year: {year}")
        years_found.add(year)
        if len(records) != 45:
            raise ValueError(
                f"Expected 45 current districts for {year}; got {len(records)}"
            )
        for district_code, record in records.items():
            by_district.setdefault(district_code, {})[year] = record
    missing_years = sorted(set(SNAPSHOT_YEARS) - years_found)
    if missing_years:
        raise ValueError(f"Missing Regionalstatistik years: {missing_years}")
    return by_district


def interpolate_value(
    lower: float | None,
    upper: float | None,
    weight: float,
) -> float | None:
    if lower is None or upper is None:
        return None
    return lower + weight * (upper - lower)


def interpolate_county_years(
    snapshots: dict[str, dict[int, dict[str, object]]],
) -> list[dict[str, object]]:
    output = []
    for district_code in sorted(snapshots):
        district = snapshots[district_code]
        for year in range(SNAPSHOT_YEARS[0], SNAPSHOT_YEARS[-1] + 1):
            lower_year = max(value for value in SNAPSHOT_YEARS if value <= year)
            upper_year = min(value for value in SNAPSHOT_YEARS if value >= year)
            weight = (
                0.0
                if lower_year == upper_year
                else (year - lower_year) / (upper_year - lower_year)
            )
            lower = district[lower_year]
            upper = district[upper_year]
            record: dict[str, object] = {
                "district_code": district_code,
                "district_name": district[SNAPSHOT_YEARS[-1]][
                    "district_name"
                ],
                "year": year,
                "regio_temporal_method": (
                    "snapshot"
                    if lower_year == upper_year
                    else "linear_interpolation"
                ),
                "regio_lower_year": lower_year,
                "regio_upper_year": upper_year,
                "regio_interpolation_weight": weight,
            }
            for metric in ALL_METRICS:
                record[f"reg_{metric}"] = interpolate_value(
                    lower[metric],
                    upper[metric],
                    weight,
                )
            output.append(record)
    return output


def read_district_geometries(
    path: Path,
) -> dict[str, tuple[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    grouped: dict[str, dict[str, object]] = {}
    for feature in data["features"]:
        properties = feature["properties"]
        district_code = properties["ags"]
        item = grouped.setdefault(
            district_code,
            {"name": properties["gen"], "geometries": []},
        )
        item["geometries"].append(shape(feature["geometry"]))
    if len(grouped) != 45:
        raise ValueError(f"Expected 45 district geometries; got {len(grouped)}")
    return {
        code: (str(item["name"]), unary_union(item["geometries"]))
        for code, item in grouped.items()
    }


def unique_stations(path: Path) -> list[dict[str, str]]:
    stations = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            stations[row["station_id"]] = row
    return [stations[key] for key in sorted(stations)]


def map_stations_to_districts(
    station_path: Path,
    boundary_path: Path,
) -> list[dict[str, object]]:
    districts = read_district_geometries(boundary_path)
    output = []
    for station in unique_stations(station_path):
        point = Point(
            float(station["lon_etrs89"]),
            float(station["lat_etrs89"]),
        )
        matches = [
            (code, name)
            for code, (name, geometry) in districts.items()
            if geometry.covers(point)
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Station {station['station_id']} matched {len(matches)} districts"
            )
        district_code, district_name = matches[0]
        output.append(
            {
                "station_id": station["station_id"],
                "district_code": district_code,
                "district_name": district_name,
                "lon_etrs89": station["lon_etrs89"],
                "lat_etrs89": station["lat_etrs89"],
                "mapping_method": "point_in_polygon",
                "boundary_source": "BKG VG250 WFS (Stand 01.01.)",
            }
        )
    return output


def build_station_year_table(
    county_years: list[dict[str, object]],
    mapping: list[dict[str, object]],
) -> list[dict[str, object]]:
    county_index = {
        (str(row["district_code"]), int(row["year"])): row
        for row in county_years
    }
    output = []
    covariate_columns = [
        key
        for key in county_years[0]
        if key not in {"district_code", "district_name", "year"}
    ]
    for station in mapping:
        district_code = str(station["district_code"])
        for year in range(SNAPSHOT_YEARS[0], PANEL_END_YEAR + 1):
            county = county_index.get((district_code, year))
            record: dict[str, object] = {
                "station_id": station["station_id"],
                "year": year,
                "district_code": district_code,
                "district_name": station["district_name"],
                "reg_data_available": int(county is not None),
            }
            for column in covariate_columns:
                record[column] = county[column] if county is not None else None
            output.append(record)
    return output


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"No rows to write: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--boundaries", type=Path, default=DEFAULT_BOUNDARIES)
    parser.add_argument("--stations", type=Path, default=DEFAULT_STATIONS)
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=DEFAULT_PROCESSED_DIR,
    )
    args = parser.parse_args()

    for path in (args.boundaries, args.stations):
        if not path.exists():
            raise FileNotFoundError(path)

    snapshots = read_all_snapshots(args.raw_dir)
    county_years = interpolate_county_years(snapshots)
    mapping = map_stations_to_districts(args.stations, args.boundaries)
    station_years = build_station_year_table(county_years, mapping)

    county_output = args.processed_dir / "regionalstatistik_county_year_ni.csv"
    mapping_output = args.processed_dir / "station_county_mapping.csv"
    station_output = (
        args.processed_dir / "regionalstatistik_station_year_ni.csv"
    )
    write_csv(county_output, county_years)
    write_csv(mapping_output, mapping)
    write_csv(station_output, station_years)

    print(f"Wrote {len(county_years)} county-year rows")
    print(f"Mapped {len(mapping)} stations to districts")
    print(f"Wrote {len(station_years)} station-year rows")
    print(station_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
