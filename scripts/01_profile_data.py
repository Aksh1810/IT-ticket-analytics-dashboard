"""01_profile_data.py — Profile the raw IT helpdesk CSV.

Discovers the first CSV in data/raw/, prints headers, infers a canonical
column mapping, reports per-column profile stats, and writes a summary
to documentation/data_profile.md.

Run:
    python scripts/01_profile_data.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

from column_mapping import CANONICAL_COLUMNS, infer_mapping

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
DOC_DIR = ROOT / "documentation"
PROFILE_MD = DOC_DIR / "data_profile.md"

DATE_LIKE_CANONICAL = {"created_at", "resolved_at", "first_response_at"}
NUMERIC_LIKE_CANONICAL = {"satisfaction_score", "reopen_count"}

DATE_RE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}")
DATE_RE_US = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}")


def find_csvs() -> list[Path]:
    csvs = sorted(RAW_DIR.glob("*.csv"))
    if not csvs:
        print(
            "ERROR: No CSV found in data/raw/.\n"
            "Place a tickets CSV (e.g. tickets.csv) in data/raw/ then re-run.",
            file=sys.stderr,
        )
        sys.exit(1)
    return csvs


def detect_date_format_mix(series: pd.Series) -> dict[str, int]:
    iso = us = other = empty = 0
    for v in series.dropna().astype(str).head(2000):
        s = v.strip()
        if not s:
            empty += 1
        elif DATE_RE_ISO.match(s):
            iso += 1
        elif DATE_RE_US.match(s):
            us += 1
        else:
            other += 1
    return {"iso_yyyy_mm_dd": iso, "us_mm_dd_yyyy": us, "other": other, "empty": empty}


def profile_column(name: str, series: pd.Series, canonical: str | None) -> dict:
    n = len(series)
    nulls = int(series.isna().sum())
    null_pct = (nulls / n * 100) if n else 0.0
    unique = int(series.nunique(dropna=True))
    samples = (
        series.dropna().astype(str).head(10).tolist()
    )

    info: dict = {
        "name": name,
        "canonical": canonical,
        "dtype": str(series.dtype),
        "nulls": nulls,
        "null_pct": null_pct,
        "unique": unique,
        "samples": samples,
    }

    if canonical in DATE_LIKE_CANONICAL:
        info["date_format_mix"] = detect_date_format_mix(series)

    if canonical in NUMERIC_LIKE_CANONICAL or pd.api.types.is_numeric_dtype(series):
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().any():
            info["numeric"] = {
                "min": float(numeric.min()),
                "max": float(numeric.max()),
                "mean": float(numeric.mean()),
                "negatives": int((numeric < 0).sum()),
            }
    return info


def render_markdown_multi(per_file: list[dict], df: pd.DataFrame,
                          missing: list[str], profiles: list[dict],
                          quality_issues: list[str]) -> str:
    lines: list[str] = []
    lines.append("# Data Profile\n")
    lines.append(f"**CSV files found:** {len(per_file)}  ")
    lines.append(f"**Combined rows (after skipping unusable files):** {len(df):,}  ")
    lines.append(f"**Combined columns:** {len(df.columns)}\n")

    lines.append("## Source Files\n")
    lines.append("| File | Rows | Mapped columns | Included | Reason |")
    lines.append("|---|---:|---:|:---:|---|")
    for p in per_file:
        reason = "OK" if p["included"] else "no `created_at` could be inferred from headers"
        lines.append(f"| `{p['path'].name}` | {p['rows']:,} | {len(p['mapping'])} | "
                     f"{'✓' if p['included'] else '✗'} | {reason} |")
    lines.append("")

    for p in per_file:
        lines.append(f"### `{p['path'].name}` — raw headers\n")
        lines.append("```\n" + ", ".join(p["raw_headers"]) + "\n```\n")
        lines.append("**Mapping:**\n")
        lines.append("| Raw column | Canonical name |")
        lines.append("|---|---|")
        for raw, canonical in p["mapping"].items():
            lines.append(f"| `{raw}` | `{canonical}` |")
        lines.append("")

    if missing:
        lines.append("**Canonical columns absent across ALL included files:** "
                     + ", ".join(f"`{m}`" for m in missing) + "\n")

    lines.append("## Per-Column Profile\n")
    for p in profiles:
        lines.append(f"### `{p['name']}`" + (f" → `{p['canonical']}`" if p['canonical'] else ""))
        lines.append(f"- dtype: `{p['dtype']}`")
        lines.append(f"- nulls: {p['nulls']:,} ({p['null_pct']:.1f}%)")
        lines.append(f"- unique non-null values: {p['unique']:,}")
        if p["samples"]:
            sample_str = ", ".join(f"`{s}`" for s in p["samples"])
            lines.append(f"- sample values: {sample_str}")
        if "numeric" in p:
            num = p["numeric"]
            lines.append(
                f"- numeric: min={num['min']:.2f}, max={num['max']:.2f}, "
                f"mean={num['mean']:.2f}, negatives={num['negatives']}"
            )
        if "date_format_mix" in p:
            mix = p["date_format_mix"]
            lines.append(
                f"- date formats sampled: ISO={mix['iso_yyyy_mm_dd']}, "
                f"US={mix['us_mm_dd_yyyy']}, other={mix['other']}, empty={mix['empty']}"
            )
        lines.append("")

    lines.append("## Data Quality Issues\n")
    if quality_issues:
        for q in quality_issues:
            lines.append(f"- {q}")
    else:
        lines.append("- _(none flagged)_")
    lines.append("")
    return "\n".join(lines)


def load_and_unify(csv_paths: list[Path]) -> tuple[pd.DataFrame, list[dict]]:
    """Read every CSV, map columns, and concat. Skip files with no `created_at`."""
    frames: list[pd.DataFrame] = []
    per_file: list[dict] = []
    for path in csv_paths:
        df_i = pd.read_csv(path, encoding_errors="replace", low_memory=False)
        mapping_i, missing_i = infer_mapping(list(df_i.columns))
        info = {
            "path": path,
            "rows": len(df_i),
            "raw_headers": list(df_i.columns),
            "mapping": mapping_i,
            "missing": missing_i,
            "included": "created_at" in mapping_i.values(),
        }
        per_file.append(info)
        print(f"[01_profile] {path.name}: {len(df_i):,} rows, "
              f"{len(mapping_i)} cols mapped, included={info['included']}")
        if info["included"]:
            df_i = df_i.rename(columns=mapping_i)
            df_i["_source_file"] = path.name
            frames.append(df_i)
        else:
            print(f"   -> SKIP: no 'created_at' could be inferred from headers.")
    if not frames:
        print("ERROR: No CSV had a usable created_at column.", file=sys.stderr)
        sys.exit(1)
    combined = pd.concat(frames, ignore_index=True, sort=False)
    return combined, per_file


def main() -> None:
    csv_paths = find_csvs()
    print(f"[01_profile] Found {len(csv_paths)} CSV(s) in data/raw/.")
    df, per_file = load_and_unify(csv_paths)
    print(f"[01_profile] Combined rows: {len(df):,}  Cols: {len(df.columns)}")
    print(f"[01_profile] Headers: {list(df.columns)}")

    mapping = {c: c for c in df.columns if c in set().union(*(set(p["mapping"].values()) for p in per_file))}
    missing = [c for c in CANONICAL_COLUMNS if c not in df.columns]
    print(f"[01_profile] Canonical columns present: {sorted(c for c in CANONICAL_COLUMNS if c in df.columns)}")
    if missing:
        print(f"[01_profile] Canonical columns absent: {missing}")

    profiles: list[dict] = []
    quality_issues: list[str] = []

    canon_set = set(CANONICAL_COLUMNS)
    for col in df.columns:
        canonical = col if col in canon_set else None
        info = profile_column(col, df[col], canonical)
        profiles.append(info)

        if info["nulls"] == len(df):
            quality_issues.append(f"Column `{col}` is 100% null.")
        if canonical in DATE_LIKE_CANONICAL:
            mix = info.get("date_format_mix", {})
            nonempty = sum(v for k, v in mix.items() if k != "empty")
            distinct_formats = sum(1 for k, v in mix.items() if k != "empty" and v > 0)
            if distinct_formats > 1 and nonempty > 0:
                quality_issues.append(
                    f"Column `{col}` has mixed datetime formats: {mix}."
                )
            if mix.get("other", 0) > 0:
                quality_issues.append(
                    f"Column `{col}` contains {mix['other']} value(s) in an unrecognized date format."
                )
        if "numeric" in info and info["numeric"]["negatives"] > 0:
            quality_issues.append(
                f"Column `{col}` has {info['numeric']['negatives']} negative value(s)."
            )

    for canonical in missing:
        quality_issues.append(f"Canonical column `{canonical}` not present in source (no synonym matched).")

    DOC_DIR.mkdir(parents=True, exist_ok=True)
    md = render_markdown_multi(per_file, df, missing, profiles, quality_issues)
    PROFILE_MD.write_text(md, encoding="utf-8")
    print(f"[01_profile] Wrote {PROFILE_MD.relative_to(ROOT)}")

    print("\n=== DATA QUALITY ISSUES ===")
    if quality_issues:
        for q in quality_issues:
            print(f"  - {q}")
    else:
        print("  (none flagged)")


if __name__ == "__main__":
    main()
