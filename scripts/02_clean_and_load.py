"""02_clean_and_load.py — Clean the raw CSV and load it into SQLite.

- Applies the canonical column mapping.
- Robustly parses datetime columns (multi-format fallback + coerce).
- Normalizes priority and text fields.
- Writes the result into data/helpdesk.db, table `raw_tickets`.

Run:
    python scripts/02_clean_and_load.py
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

from column_mapping import CANONICAL_COLUMNS, infer_mapping

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "helpdesk.db"

DATETIME_COLS = ["created_at", "resolved_at", "first_response_at"]
DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y",
    "%Y/%m/%d",
]

PRIORITY_MAP = {
    "critical": "Critical", "crit": "Critical", "urgent": "Critical",
    "p1": "Critical", "1": "Critical", "sev1": "Critical", "s1": "Critical",
    "high": "High", "p2": "High", "2": "High", "sev2": "High", "s2": "High",
    "medium": "Medium", "med": "Medium", "normal": "Medium",
    "p3": "Medium", "3": "Medium", "sev3": "Medium", "s3": "Medium",
    "low": "Low", "p4": "Low", "4": "Low", "sev4": "Low", "s4": "Low",
}

STATUS_MAP = {
    "open": "Open", "new": "Open",
    "pending": "Pending", "in progress": "Pending", "in_progress": "Pending",
    "on hold": "Pending", "waiting": "Pending",
    "resolved": "Resolved", "solved": "Resolved",
    "closed": "Closed", "complete": "Closed", "completed": "Closed",
}


def find_csvs() -> list[Path]:
    csvs = sorted(RAW_DIR.glob("*.csv"))
    if not csvs:
        print("ERROR: No CSV found in data/raw/. Place a CSV there and re-run.",
              file=sys.stderr)
        sys.exit(1)
    return csvs


def load_and_unify(csv_paths: list[Path]) -> pd.DataFrame:
    """Read every CSV, map to canonical, skip files lacking `created_at`,
    concat the rest. Adds `_source_file` for traceability."""
    frames: list[pd.DataFrame] = []
    for path in csv_paths:
        df_i = pd.read_csv(path, encoding_errors="replace", low_memory=False)
        mapping_i, _ = infer_mapping(list(df_i.columns))
        if "created_at" not in mapping_i.values():
            print(f"[02_clean] SKIP {path.name}: no created_at column found.")
            continue
        df_i = df_i.rename(columns=mapping_i)
        df_i["_source_file"] = path.name
        print(f"[02_clean]   {path.name}: {len(df_i):,} rows, mapped {len(mapping_i)} cols.")
        frames.append(df_i)
    if not frames:
        print("ERROR: No CSV had a usable created_at column.", file=sys.stderr)
        sys.exit(1)
    return pd.concat(frames, ignore_index=True, sort=False)


def parse_datetime(series: pd.Series) -> tuple[pd.Series, int]:
    """Try each known format; fall back to pandas inference. Returns (parsed, unparsed_count)."""
    if series.isna().all():
        return pd.to_datetime(series, errors="coerce"), 0

    s = series.astype("string").str.strip()
    parsed = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    remaining = s.notna() & parsed.isna()

    for fmt in DATE_FORMATS:
        if not remaining.any():
            break
        attempt = pd.to_datetime(s[remaining], format=fmt, errors="coerce")
        good = attempt.notna()
        parsed.loc[attempt.index[good]] = attempt[good]
        remaining = s.notna() & parsed.isna()

    if remaining.any():
        attempt = pd.to_datetime(s[remaining], errors="coerce")
        good = attempt.notna()
        parsed.loc[attempt.index[good]] = attempt[good]

    unparsed = int((s.notna() & parsed.isna()).sum())
    return parsed, unparsed


def normalize_priority(v) -> str | None:
    if pd.isna(v):
        return None
    key = str(v).strip().lower()
    return PRIORITY_MAP.get(key, str(v).strip().title() if key else None)


def normalize_status(v) -> str | None:
    if pd.isna(v):
        return None
    key = str(v).strip().lower()
    return STATUS_MAP.get(key, str(v).strip().title() if key else None)


def title_case(v):
    if pd.isna(v):
        return None
    return str(v).strip().title() if str(v).strip() else None


def main() -> None:
    csv_paths = find_csvs()
    print(f"[02_clean] Found {len(csv_paths)} CSV(s) in data/raw/.")
    df = load_and_unify(csv_paths)
    print(f"[02_clean] Combined: {len(df):,} rows.")

    # Parse created_at early so we can derive first_response_at from
    # `first_response_time_hours` (used by datasets that store the latency
    # as a numeric instead of a timestamp).
    if "created_at" in df.columns:
        df["created_at"], _ = parse_datetime(df["created_at"])

    if "first_response_at" not in df.columns and "first_response_time_hours" in df.columns:
        hours = pd.to_numeric(df["first_response_time_hours"], errors="coerce")
        df["first_response_at"] = df["created_at"] + pd.to_timedelta(hours, unit="h")
        print(f"[02_clean]   derived first_response_at from first_response_time_hours "
              f"({hours.notna().sum():,} rows).")

    for col in CANONICAL_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[CANONICAL_COLUMNS].copy()

    if df["ticket_id"].isna().all():
        df["ticket_id"] = range(1, len(df) + 1)
    df["ticket_id"] = df["ticket_id"].astype("string").str.strip()

    for col in DATETIME_COLS:
        parsed, unparsed = parse_datetime(df[col])
        df[col] = parsed
        print(f"[02_clean]   {col}: parsed OK, {unparsed} unparseable.")

    df["status"] = df["status"].map(normalize_status)
    df["priority"] = df["priority"].map(normalize_priority)
    df["category"] = df["category"].map(title_case)
    df["channel"] = df["channel"].map(title_case)
    df["agent_name"] = df["agent_name"].map(title_case)
    df["team"] = df["team"].map(title_case)

    df["satisfaction_score"] = pd.to_numeric(df["satisfaction_score"], errors="coerce")
    df["reopen_count"] = pd.to_numeric(df["reopen_count"], errors="coerce").fillna(0).astype(int)

    for col in ["status", "priority", "category", "channel", "agent_name", "team"]:
        df[col] = df[col].where(df[col].notna(), None)
    df["description"] = df["description"].astype("string").where(df["description"].notna(), None)

    out_df = df.copy()
    for col in DATETIME_COLS:
        out_df[col] = out_df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
        out_df[col] = out_df[col].where(out_df[col].notna(), None)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    with sqlite3.connect(DB_PATH) as conn:
        out_df.to_sql("raw_tickets", conn, if_exists="replace", index=False)
        n = conn.execute("SELECT COUNT(*) FROM raw_tickets").fetchone()[0]
    print(f"[02_clean] Loaded {n:,} rows into {DB_PATH.relative_to(ROOT)}::raw_tickets")


if __name__ == "__main__":
    main()
