#!/usr/bin/env python3
"""
Bronze-layer loader: reads the PGCB xlsx file and exports it as a CSV.
"""

import csv
from pathlib import Path

import pandas as pd

XLSX_PATH = Path("data/PGCB_date_power_demand.xlsx")
OUT_PATH = Path("data/raw_pgcb.csv")


def load() -> None:
  print(f"Reading {XLSX_PATH} ...")
  df = pd.read_excel(XLSX_PATH, sheet_name="Sheet1")

  print(f"Rows: {len(df)}  |  Columns: {list(df.columns)}")

  df.to_csv(OUT_PATH, index=False, quoting=csv.QUOTE_MINIMAL, na_rep="NULL")
  print(f"Written {OUT_PATH} ({OUT_PATH.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
  load()
