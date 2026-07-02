#!/usr/bin/env python3
"""Download the raw UBA Nitratbericht 2024 workbook."""

from __future__ import annotations

import argparse
import ssl
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOWNLOAD_URL = (
    "https://gis.uba.de/daten/"
    "692b5285-78ca-4081-aa31-4b327cf0105f_XLSX.zip"
)
OUTPUT = (
    ROOT
    / "data"
    / "uba_nitrate_report_2024"
    / "raw"
    / "Download_Daten_Nitratbericht_2024.xlsx"
)
WORKBOOK_MEMBER = "Download_Daten_Nitratbericht_2024.xlsx"


def download_workbook(output: Path, overwrite: bool, insecure: bool) -> str:
    if output.exists() and not overwrite:
        return "exists"

    output.parent.mkdir(parents=True, exist_ok=True)
    archive_part = output.with_suffix(".zip.part")
    workbook_part = output.with_suffix(".xlsx.part")
    context = ssl._create_unverified_context() if insecure else None
    request = urllib.request.Request(
        DOWNLOAD_URL,
        headers={"User-Agent": "aee-organicfarming-data-pipeline/0.1"},
    )

    try:
        with urllib.request.urlopen(request, timeout=120, context=context) as response:
            with archive_part.open("wb") as handle:
                while chunk := response.read(1024 * 1024):
                    handle.write(chunk)

        with zipfile.ZipFile(archive_part) as archive:
            if WORKBOOK_MEMBER not in archive.namelist():
                raise FileNotFoundError(
                    f"{WORKBOOK_MEMBER!r} is missing from the UBA download"
                )
            with archive.open(WORKBOOK_MEMBER) as source:
                with workbook_part.open("wb") as target:
                    while chunk := source.read(1024 * 1024):
                        target.write(chunk)
        workbook_part.replace(output)
    finally:
        archive_part.unlink(missing_ok=True)
        workbook_part.unlink(missing_ok=True)

    return "downloaded"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace the existing raw workbook.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification.",
    )
    args = parser.parse_args()

    try:
        status = download_workbook(
            OUTPUT,
            overwrite=args.overwrite,
            insecure=args.insecure,
        )
    except (
        FileNotFoundError,
        urllib.error.URLError,
        TimeoutError,
        zipfile.BadZipFile,
    ) as exc:
        print(f"UBA download failed: {exc}", file=sys.stderr)
        return 1

    print(f"UBA workbook: {status}")
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
