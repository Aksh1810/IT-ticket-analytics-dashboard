"""03_export_csvs.py — Export the star-schema tables from SQLite to CSV.

Power BI imports the CSVs in data/processed/ directly; this script is the
last hop of the pipeline.

Run:
    python scripts/03_export_csvs.py
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "helpdesk.db"
OUT_DIR = ROOT / "data" / "processed"

TABLES = [
    "fact_tickets",
    "dim_agent",
    "dim_category",
    "dim_channel",
    "dim_priority",
    "dim_calendar",
]


def main() -> None:
    if not DB_PATH.exists():
        print(f"ERROR: {DB_PATH} not found. Run 02_clean_and_load.py and the SQL "
              "scripts first.", file=sys.stderr)
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        for table in TABLES:
            df = pd.read_sql(f"SELECT * FROM {table}", conn)
            out = OUT_DIR / f"{table}.csv"
            df.to_csv(out, index=False)
            print(f"[03_export] {table:15s} -> {out.relative_to(ROOT)}  ({len(df):,} rows)")


if __name__ == "__main__":
    main()
