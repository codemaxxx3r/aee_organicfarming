#!/usr/bin/env python3
"""Download and document the UBA nitrate workbook for the Niedersachsen nitrate project."""

from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import sys
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
META_DIR = ROOT / "data" / "metadata"


@dataclass(frozen=True)
class Dataset:
    dataset_id: str
    title: str
    source: str
    url: str
    output: str
    kind: str
    license: str
    temporal_coverage: str
    spatial_coverage: str
    spatial_resolution: str
    description: str
    notes: str = ""
    large: bool = False


DATASETS: tuple[Dataset, ...] = (
    Dataset(
        dataset_id="uba_nitrate_report_2024_xlsx",
        title="UBA Nitratbericht 2024 data download",
        source="Umweltbundesamt (UBA) / Bundeslaender",
        url="https://gis.uba.de/daten/692b5285-78ca-4081-aa31-4b327cf0105f_XLSX.zip",
        output="uba_nitrate_report_2024/692b5285-78ca-4081-aa31-4b327cf0105f_XLSX.zip",
        kind="direct",
        license="CC BY 4.0 according to UBA CSW metadata",
        temporal_coverage="2012-01-01 to 2022-12-31",
        spatial_coverage="Germany; groundwater and surface-water monitoring stations",
        spatial_resolution="Monitoring-station table in XLSX format; coordinates included according to UBA app metadata",
        description="Current UBA Nitratbericht 2024 data used by the UBA nitrate web application. Primary candidate for the nitrate target variable because it is a tabular station-by-year data source rather than a map-only shapefile.",
        notes="The workbook contains both groundwater and surface-water records; filter to Grundwasser before econometric panel construction.",
    ),
)


def request(url: str, token: str | None = None) -> urllib.request.Request:
    headers = {
        "User-Agent": "aee-organicfarming-data-pipeline/0.1",
        "Accept": "*/*",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["Accept"] = "application/json"
    return urllib.request.Request(url, headers=headers)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_url(
    url: str,
    output: Path,
    token: str | None = None,
    overwrite: bool = False,
    insecure: bool = False,
) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not overwrite:
        return {"status": "exists", "path": str(output), "bytes": output.stat().st_size, "sha256": sha256(output)}

    started = time.time()
    context = ssl._create_unverified_context() if insecure else None
    with urllib.request.urlopen(request(url, token=token), timeout=120, context=context) as response:
        tmp = output.with_suffix(output.suffix + ".part")
        with tmp.open("wb") as fh:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                fh.write(chunk)
        tmp.replace(output)

    return {
        "status": "downloaded",
        "path": str(output),
        "bytes": output.stat().st_size,
        "sha256": sha256(output),
        "elapsed_seconds": round(time.time() - started, 2),
    }


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def extract_zip(path: Path, overwrite: bool = False) -> dict | None:
    if path.suffix.lower() != ".zip":
        return None
    extract_dir = path.with_suffix("")
    marker = extract_dir / ".extracted_from_zip"
    if marker.exists() and not overwrite:
        return {"extract_status": "exists", "extract_dir": str(extract_dir)}
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path) as archive:
        archive.extractall(extract_dir)
        names = archive.namelist()
    marker.write_text(path.name + "\n", encoding="utf-8")
    return {"extract_status": "extracted", "extract_dir": str(extract_dir), "extract_members": names}


def append_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true", help="Re-download files that already exist.")
    parser.add_argument("--dry-run", action="store_true", help="Write manifest only, do not download.")
    parser.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification for environments with broken local CA bundles.")
    parser.add_argument("--no-extract", action="store_true", help="Do not extract downloaded ZIP archives.")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)

    manifest_path = META_DIR / "dataset_manifest.json"
    log_path = META_DIR / "download_log.jsonl"
    write_json(manifest_path, [asdict(dataset) for dataset in DATASETS])

    rows: list[dict] = []
    for dataset in DATASETS:
        row = asdict(dataset) | {"downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        if dataset.large and not args.include_large:
            rows.append(row | {"status": "skipped_large"})
            continue
        if args.dry_run:
            rows.append(row | {"status": "dry_run"})
            continue
        try:
            output = RAW_DIR / dataset.output
            result = download_url(dataset.url, output, overwrite=args.overwrite, insecure=args.insecure)
            if not args.no_extract:
                extracted = extract_zip(output, overwrite=args.overwrite)
                if extracted:
                    result |= extracted
            rows.append(row | result)
        except (urllib.error.URLError, TimeoutError) as exc:
            rows.append(row | {"status": "failed", "error": repr(exc)})

    append_jsonl(log_path, rows)
    print(f"Wrote manifest: {manifest_path}")
    print(f"Appended log: {log_path}")
    for row in rows:
        print(f"{row.get('dataset_id')}: {row.get('status')}")
    return 0 if all(row.get("status") not in {"failed", "unexpected_response"} for row in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
