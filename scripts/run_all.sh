#!/usr/bin/env bash
# run_all.sh — execute the full pipeline end-to-end.
#
#   1. Profile the raw CSV in data/raw/
#   2. Clean and load it into data/helpdesk.db::raw_tickets
#   3. Build the star-schema (CREATE / dim populate / fact transform)
#   4. Run validation checks
#   5. Export each table to data/processed/*.csv for Power BI

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DB="data/helpdesk.db"

echo "============================================================"
echo "STEP 1: profile data"
echo "============================================================"
python3 scripts/01_profile_data.py

echo
echo "============================================================"
echo "STEP 2: clean & load into SQLite"
echo "============================================================"
python3 scripts/02_clean_and_load.py

echo
echo "============================================================"
echo "STEP 3a: create schema"
echo "============================================================"
sqlite3 "$DB" < sql/01_create_schema.sql

echo "============================================================"
echo "STEP 3b: populate dims"
echo "============================================================"
sqlite3 "$DB" < sql/02_populate_dims.sql

echo "============================================================"
echo "STEP 3c: transform facts"
echo "============================================================"
sqlite3 "$DB" < sql/03_transform_facts.sql

echo
echo "============================================================"
echo "STEP 4: validation checks"
echo "============================================================"
sqlite3 "$DB" < sql/04_validation_checks.sql

echo
echo "============================================================"
echo "STEP 5: export CSVs to data/processed/"
echo "============================================================"
python3 scripts/03_export_csvs.py

echo
echo "Pipeline completed successfully. Outputs:"
echo "  - data/helpdesk.db"
echo "  - data/processed/*.csv  (import these into Power BI)"
echo "  - documentation/data_profile.md"
