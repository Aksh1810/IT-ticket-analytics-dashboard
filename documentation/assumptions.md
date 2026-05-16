# Assumptions and Data Handling Decisions

This document records every business and data-cleaning decision the pipeline makes. If a stakeholder questions a number on the dashboard, the answer lives here.

---

## SLA Targets

| Priority | SLA Target (hours) | Rationale |
|---|---|---|
| Critical | 4 | Business-impacting outage; same-business-day fix. |
| High | 8 | Production-impacting but non-outage; one business day. |
| Medium | 24 | Standard request; one calendar day. |
| Low | 72 | Convenience request; three calendar days. |

These thresholds are encoded in `dim_priority.sla_target_hours` and used to compute `sla_breached`. They are easy to change: edit `sql/02_populate_dims.sql` and re-run the pipeline.

---

## First Contact Resolution (FCR) Proxy

The raw data does not track "interaction count" directly. We approximate FCR with:

```
is_first_contact_resolved = (status = 'Resolved' AND COALESCE(reopen_count, 0) = 0)
```

**Implication:** Tickets reopened even once do not count as FCR. Tickets without a `reopen_count` column in the source default to `0` (assumed first-time resolution).

---

## Open Tickets in SLA Breach Calculation

A ticket is **only** marked as `sla_breached = 1` after it has actually been resolved and its `resolution_hours` exceeded the target.

- Open tickets (no `resolved_at`) always have `sla_breached = 0`.
- The dashboard tracks at-risk open tickets separately via `[SLA At Risk]`, which fires at 80% of target hours elapsed.

This avoids "phantom breaches" disappearing from the compliance rate the moment they breach, while keeping the manager aware of imminent risk.

---

## MTTR Null Handling

`resolution_hours` is `NULL` when `resolved_at IS NULL`. The MTTR measures filter out NULLs:

```
AVERAGEX(FILTER(FactTickets, NOT ISBLANK(resolution_hours)), resolution_hours)
```

**Implication:** MTTR reflects only tickets that have actually closed. A growing backlog of slow-to-resolve tickets will not artificially inflate MTTR.

---

## MTTA Null Handling

Same pattern as MTTR: tickets that have never received a first response are excluded from `[MTTA Hours]`.

---

## CSAT Null Handling

`satisfaction_score` is often missing (customers don't always rate). Every CSAT measure guards with `<> BLANK()`:

```
AVERAGE(score) where score <> BLANK()
```

**Implication:** Unrated tickets do not depress or inflate the CSAT score. Response-rate context belongs in a separate measure (not in scope here).

---

## Priority Normalization

Source values like `P1`, `1`, `Urgent`, `S1` are mapped to canonical `Critical`. The full map lives in `scripts/02_clean_and_load.py::PRIORITY_MAP`. Unknown values are passed through title-cased and fall into the `(Unknown)` bucket of `dim_priority` with a default 24-hour SLA.

---

## Status Normalization

Source statuses are mapped to four canonical buckets: `Open`, `Pending`, `Resolved`, `Closed`. Variants like `In Progress`, `On Hold`, `Waiting` collapse to `Pending`. `Solved` collapses to `Resolved`. Unknown values pass through title-cased.

---

## Missing Dimension Values

Rather than dropping rows, we substitute readable placeholders during dim population:

- `agent_name` NULL → `(Unassigned)`
- `team` NULL → `(Unknown)`
- `category` NULL → `(Uncategorized)`
- `channel` NULL → `(Unknown)`
- `priority` NULL → `(Unknown)`

This keeps every fact row visible in the dashboard while flagging gaps clearly.

---

## Negative `resolution_hours`

If `resolved_at` is earlier than `created_at` (bad data), `resolution_hours` will be negative. The pipeline does **not** silently fix or filter these. Instead, `sql/04_validation_checks.sql::CHECK 4` reports the count so the analyst can decide whether to fix the source.

---

## Known Data Quality Issues

Auto-detected issues are written to `documentation/data_profile.md` after Step 1 runs against your specific CSV. Common patterns to expect:

- **Mixed datetime formats** in the same column (e.g., `2024-03-12` next to `3/12/2024`). The cleaner tries multiple formats then falls back to pandas inference; unparseable values become `NULL`.
- **Null `first_response_at`** for old tickets that closed without a logged response.
- **High null `satisfaction_score` rate** is typical (most customers don't rate).
- **Reopened tickets** without an explicit `reopen_count` column — assumed `0`.
