# Data Dictionary

This document describes every column in the star-schema CSVs that Power BI imports.

---

## `fact_tickets`

One row per support ticket. The grain is "ticket".

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `ticket_id` | Text | Unique ticket identifier from the source system. | `TCK-00042` | N |
| `created_at` | Date/Time | Timestamp when the ticket was opened. | `2024-03-12 09:14:00` | N |
| `resolved_at` | Date/Time | Timestamp when the ticket was resolved. NULL if still open. | `2024-03-12 11:02:00` | Y |
| `first_response_at` | Date/Time | Timestamp of the first agent response. NULL if never replied. | `2024-03-12 09:31:00` | Y |
| `status` | Text | Canonical status: `Open`, `Pending`, `Resolved`, `Closed`. | `Resolved` | Y |
| `agent_key` | Whole Number | Foreign key to `dim_agent`. | `17` | N |
| `category_key` | Whole Number | Foreign key to `dim_category`. | `4` | N |
| `channel_key` | Whole Number | Foreign key to `dim_channel`. | `2` | N |
| `priority_key` | Whole Number | Foreign key to `dim_priority`. | `1` | N |
| `created_date_key` | Whole Number | YYYYMMDD integer; foreign key to `dim_calendar`. | `20240312` | N |
| `satisfaction_score` | Decimal | Post-resolution CSAT rating (1–5). NULL when not collected. | `4` | Y |
| `reopen_count` | Whole Number | How many times the ticket was reopened. Default `0`. | `0` | N |
| `resolution_hours` | Decimal | `(resolved_at - created_at)` in hours. NULL if unresolved. | `1.80` | Y |
| `response_hours` | Decimal | `(first_response_at - created_at)` in hours. NULL if no reply yet. | `0.28` | Y |
| `sla_target_hours` | Whole Number | SLA target inherited from `dim_priority` at ETL time. | `4` | N |
| `sla_breached` | Whole Number | `1` if resolution exceeded the SLA target, else `0`. Open tickets are `0`. | `0` | N |
| `is_first_contact_resolved` | Whole Number | `1` if status=Resolved AND reopen_count=0, else `0`. | `1` | N |
| `ticket_age_band` | Text | Aging bucket for open tickets (`0-1 Day`, `1-3 Days`, `3-7 Days`, `7-14 Days`, `14+ Days`) or `(Resolved)`. | `1-3 Days` | N |

---

## `dim_agent`

One row per (agent, team) combination.

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `agent_key` | Whole Number | Surrogate key. | `17` | N |
| `agent_name` | Text | Display name. `(Unassigned)` for rows with no agent. | `Maria Lopez` | N |
| `team` | Text | Team / department. `(Unknown)` if not provided. | `Tier 2 Support` | N |

---

## `dim_category`

One row per ticket category.

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `category_key` | Whole Number | Surrogate key. | `4` | N |
| `category_name` | Text | Issue type. `(Uncategorized)` if not provided. | `Hardware` | N |

---

## `dim_channel`

One row per submission channel.

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `channel_key` | Whole Number | Surrogate key. | `2` | N |
| `channel_name` | Text | How the ticket was filed (`Email`, `Phone`, `Chat`, `Web`, `Portal`, ...). | `Email` | N |

---

## `dim_priority`

One row per priority level. SLA targets are seeded by business rule.

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `priority_key` | Whole Number | Surrogate key. | `1` | N |
| `priority_name` | Text | `Critical`, `High`, `Medium`, `Low`, or `(Unknown)`. | `Critical` | N |
| `sla_target_hours` | Whole Number | Hours allowed by SLA. Critical=4, High=8, Medium=24, Low=72. | `4` | N |

---

## `dim_calendar`

One row per date from earliest `created_at` through today + 30 days.

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `date_key` | Whole Number | YYYYMMDD integer; primary key. Joins to `fact_tickets[created_date_key]`. | `20240312` | N |
| `date` | Date | Calendar date. | `2024-03-12` | N |
| `day_of_week` | Text | Full day name. | `Tuesday` | N |
| `week_number` | Whole Number | ISO-style week of year. | `11` | N |
| `month_number` | Whole Number | Month 1–12. | `3` | N |
| `month_name` | Text | Full month name. | `March` | N |
| `quarter` | Whole Number | Calendar quarter 1–4. | `1` | N |
| `year` | Whole Number | Four-digit year. | `2024` | N |
| `is_weekend` | Whole Number | `1` if Saturday/Sunday, else `0`. | `0` | N |
| `is_business_day` | Whole Number | `1` if Monday–Friday, else `0`. | `1` | N |
