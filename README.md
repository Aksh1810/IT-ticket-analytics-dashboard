# IT Helpdesk Ticket Analytics Dashboard

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-2.x-150458?logo=pandas&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-Service-F2C811?logo=powerbi&logoColor=black)
![DAX](https://img.shields.io/badge/DAX-30%20Measures-217346)

An end-to-end data engineering and analytics project — raw IT support ticket CSV → cleaned SQLite star schema → Power BI Service dashboard — with full SQL transformations, 30 DAX measures, and documentation designed for a non-technical IT manager audience.

---

## What This Project Does

IT support teams generate thousands of tickets but rarely have a structured way to answer the questions that matter: *Are we meeting SLA targets? Which categories take the longest to resolve? Is our backlog growing?*

This project builds the full answer:

1. **Ingest** — a Python profiler reads any CSV with ticket data, infers column names from synonyms, flags data quality issues, and writes a profiling report.
2. **Clean** — a second Python script normalises priority labels, parses mixed datetime formats, derives `first_response_at` from numeric hour offsets, and loads everything into SQLite.
3. **Model** — four SQL scripts build a star schema: dimension tables for agent, category, channel, priority, and a recursive-CTE-generated calendar, plus a fact table with derived columns (`resolution_hours`, `sla_breached`, `is_first_contact_resolved`, `ticket_age_band`).
4. **Validate** — a fifth SQL script runs five labelled sanity checks (orphan keys, negative hours, row-count parity).
5. **Export** — a Python script writes six CSVs for direct import into Power BI Service.
6. **Visualise** — 30 DAX measures covering Volume, Efficiency (MTTR/MTTA), FCR, SLA, Backlog Aging, Agent Performance, and CSAT, with a step-by-step Power BI web build guide.

**Source data:** [Customer Support Tickets 200k](https://www.kaggle.com) — 200,000 rows across 10 categories, 5 channels, 4 priority levels, spanning 2022–2025.

---

## Dashboard Pages

| Page | Key Visuals |
|---|---|
| **Overview** | Total tickets, open backlog, MTTR, SLA compliance, CSAT cards; tickets-over-time line chart; tickets by priority bar; aging donut |
| **SLA & Performance** | SLA breach count + at-risk count; breach rate by category column chart; agent performance matrix with conditional formatting |
| **CSAT** | Avg CSAT, satisfied %, dissatisfied %; CSAT by category bar |

---

## Folder Structure

```
IT-ticket-analytics-dashboard/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── scripts/
│   ├── column_mapping.py        ← shared synonym dict (single source of truth)
│   ├── 01_profile_data.py       ← profile any CSV, write data_profile.md
│   ├── 02_clean_and_load.py     ← clean + load into SQLite raw_tickets table
│   ├── 03_export_csvs.py        ← export star schema to data/processed/*.csv
│   ├── run_all.sh               ← full pipeline runner (macOS/Linux)
│   └── run_all.bat              ← full pipeline runner (Windows)
│
├── sql/
│   ├── 01_create_schema.sql     ← DDL for fact + all dims
│   ├── 02_populate_dims.sql     ← INSERT dims + recursive calendar CTE
│   ├── 03_transform_facts.sql   ← INSERT fact_tickets with derived columns
│   └── 04_validation_checks.sql ← 5 labelled sanity SELECTs
│
├── data/
│   ├── raw/                     ← drop source CSV(s) here
│   ├── processed/               ← generated: 6 CSVs for Power BI
│   └── helpdesk.db              ← generated: SQLite warehouse (gitignored)
│
├── measures/
│   └── all_measures.dax         ← all 30 DAX measures, grouped by theme
│
├── documentation/
│   ├── data_profile.md          ← auto-generated quality report (gitignored)
│   ├── data_dictionary.md       ← every column in every table
│   ├── metric_definitions.md    ← plain-English KPI definitions + DAX names
│   ├── assumptions.md           ← SLA thresholds, FCR proxy, null handling
│   └── powerbi_setup_guide.md   ← click-by-click Power BI Service build guide
│
└── screenshots/                 ← add after building the dashboard
    ├── 01_overview_page.png
    ├── 02_sla_performance_page.png
    └── 03_csat_page.png
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> On macOS with Homebrew Python, if pip blocks the install, use:
> `pip install --break-system-packages -r requirements.txt`
> or use the system Python: `/usr/bin/python3`

### 2. Add your data

Drop a tickets CSV into `data/raw/`. The pipeline auto-discovers it. If multiple CSVs are present, it processes each and skips any that lack a `created_at`-equivalent column.

Tested with:
- `customer_support_tickets_200k.csv` — 200,000 rows, full schema
- Any CSV with columns like `ticket_id`, `created_at`, `status`, `priority`, `category`, `channel`, `satisfaction_score`

### 3. Run the pipeline

```bash
bash scripts/run_all.sh        # macOS / Linux
scripts\run_all.bat            # Windows
```

**What runs:**

| Step | Script | Output |
|---|---|---|
| 1 | `01_profile_data.py` | Prints quality report, writes `documentation/data_profile.md` |
| 2 | `02_clean_and_load.py` | Cleans data, loads `raw_tickets` into `data/helpdesk.db` |
| 3a | `sql/01_create_schema.sql` | Creates fact + dim tables |
| 3b | `sql/02_populate_dims.sql` | Populates dims + calendar |
| 3c | `sql/03_transform_facts.sql` | Builds `fact_tickets` with all derived columns |
| 4 | `sql/04_validation_checks.sql` | 5 sanity checks — all should show 0 bad rows |
| 5 | `03_export_csvs.py` | Exports 6 CSVs to `data/processed/` |

### 4. Build the dashboard

Follow [`documentation/powerbi_setup_guide.md`](documentation/powerbi_setup_guide.md) — step-by-step instructions for Power BI Service (browser, no desktop app required).

---

## Key Metrics Produced

| Metric | Description |
|---|---|
| **MTTR** | Mean Time To Resolve — average hours from open to close |
| **MTTA** | Mean Time To Acknowledge — average hours to first agent response |
| **FCR Rate** | First Contact Resolution — % resolved without a reopen |
| **SLA Compliance** | % of resolved tickets that met the SLA target |
| **SLA At Risk** | Open tickets that have consumed ≥ 80% of their SLA window |
| **Backlog Count** | Total unresolved tickets right now |
| **Aging Bands** | 0–1 day / 1–3 days / 3–7 days / 7–14 days / 14+ days |
| **CSAT** | Average customer satisfaction score (1–5, nulls excluded) |

SLA targets: Critical = 4 h · High = 8 h · Medium = 24 h · Low = 72 h

---

## Tech Stack

| Layer | Tool |
|---|---|
| Ingestion & cleaning | Python 3, pandas |
| Warehouse | SQLite 3 |
| Transformations | SQL (4 scripts, version-controlled) |
| Visualisation | Power BI Service (app.powerbi.com) |
| Measures | DAX (30 measures across 7 themes) |

---

## Screenshots

> Add after building the dashboard in Power BI Service.

![Overview Page](screenshots/01_overview_page.png)
![SLA & Performance Page](screenshots/02_sla_performance_page.png)
![CSAT Page](screenshots/03_csat_page.png)

---

## Documentation

| File | Contents |
|---|---|
| [`data_dictionary.md`](documentation/data_dictionary.md) | Every column in every fact and dim table |
| [`metric_definitions.md`](documentation/metric_definitions.md) | Plain-English KPI definitions, formulas, DAX names |
| [`assumptions.md`](documentation/assumptions.md) | SLA thresholds, FCR proxy, null handling decisions |
| [`powerbi_setup_guide.md`](documentation/powerbi_setup_guide.md) | Click-by-click Power BI Service build guide |
| [`data_profile.md`](documentation/data_profile.md) | Auto-generated quality report (run Step 1 to populate) |
