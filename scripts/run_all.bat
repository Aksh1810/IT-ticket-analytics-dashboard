@echo off
REM run_all.bat - execute the full pipeline end-to-end (Windows).
setlocal enableextensions enabledelayedexpansion

pushd "%~dp0.."
set DB=data\helpdesk.db

echo ============================================================
echo STEP 1: profile data
echo ============================================================
python scripts\01_profile_data.py || goto :error

echo.
echo ============================================================
echo STEP 2: clean ^& load into SQLite
echo ============================================================
python scripts\02_clean_and_load.py || goto :error

echo.
echo ============================================================
echo STEP 3a: create schema
echo ============================================================
sqlite3 "%DB%" < sql\01_create_schema.sql || goto :error

echo ============================================================
echo STEP 3b: populate dims
echo ============================================================
sqlite3 "%DB%" < sql\02_populate_dims.sql || goto :error

echo ============================================================
echo STEP 3c: transform facts
echo ============================================================
sqlite3 "%DB%" < sql\03_transform_facts.sql || goto :error

echo.
echo ============================================================
echo STEP 4: validation checks
echo ============================================================
sqlite3 "%DB%" < sql\04_validation_checks.sql || goto :error

echo.
echo ============================================================
echo STEP 5: export CSVs to data\processed\
echo ============================================================
python scripts\03_export_csvs.py || goto :error

echo.
echo Pipeline completed successfully. Outputs:
echo   - data\helpdesk.db
echo   - data\processed\*.csv  (import these into Power BI)
echo   - documentation\data_profile.md
popd
exit /b 0

:error
echo.
echo Pipeline failed. See message above.
popd
exit /b 1
