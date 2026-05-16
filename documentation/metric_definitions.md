# Metric Definitions

Plain-English definitions of every KPI shown on the dashboard, along with the
exact formula, the DAX measure name, and the source columns used.

---

## Total Tickets

- **What it answers:** "How many tickets are in scope right now?"
- **Formula:** Count of rows in `fact_tickets` after slicers are applied.
- **DAX measure:** `[Total Tickets]`
- **Source columns:** `fact_tickets` (any row)
- **Assumptions:** Slicers (date, priority, agent, etc.) narrow the count. With no slicers, this is the all-time count.

---

## MTTR — Mean Time To Resolve

- **What it answers:** "On average, how long does it take us to RESOLVE a ticket?"
- **Formula:** `AVERAGE(resolution_hours)` across tickets where `resolved_at IS NOT NULL`.
- **DAX measures:** `[MTTR Hours]` (numeric), `[MTTR Display]` (formatted `"Xh Ym"`)
- **Source columns:** `fact_tickets[resolution_hours]`
- **Assumptions:** Open tickets are excluded from the average. Negative values (resolved before created — bad data) are flagged in validation but not removed.

---

## MTTA — Mean Time To Acknowledge

- **What it answers:** "On average, how long until an agent makes FIRST contact?"
- **Formula:** `AVERAGE(response_hours)` across tickets where `first_response_at IS NOT NULL`.
- **DAX measures:** `[MTTA Hours]`, `[MTTA Display]`
- **Source columns:** `fact_tickets[response_hours]`
- **Assumptions:** Tickets that never received a response are excluded.

---

## FCR Rate — First Contact Resolution Rate

- **What it answers:** "What share of resolved tickets were one-and-done?"
- **Formula:** `FCR Count / Tickets Resolved (period) × 100`, where `FCR Count = COUNT(is_first_contact_resolved = 1)`.
- **DAX measures:** `[FCR Count]`, `[FCR Rate]`, `[FCR Rate Display]`
- **Source columns:** `fact_tickets[is_first_contact_resolved]`, `fact_tickets[resolved_at]`
- **Assumptions:** FCR is proxied as `status='Resolved' AND reopen_count=0`. Tickets with no `reopen_count` value are treated as `0` reopens.

---

## SLA Compliance Rate

- **What it answers:** "What % of resolved tickets met their SLA?"
- **Formula:** `SLA Compliant Count / Tickets Resolved × 100`. A ticket is compliant when `sla_breached = 0` AND it was actually resolved.
- **DAX measures:** `[SLA Compliant Count]`, `[SLA Breach Count]`, `[SLA Compliance Rate]`, `[SLA Compliance Display]`
- **Source columns:** `fact_tickets[sla_breached]`, `fact_tickets[resolved_at]`, `fact_tickets[sla_target_hours]`
- **Assumptions:** Open tickets are excluded from the compliance denominator (they are tracked separately via SLA At Risk).

---

## SLA At Risk

- **What it answers:** "Which OPEN tickets are about to breach their SLA?"
- **Formula:** Count of tickets where `resolved_at IS NULL` AND `hours_elapsed_since_created >= 0.8 × sla_target_hours`.
- **DAX measure:** `[SLA At Risk]`
- **Source columns:** `fact_tickets[created_at]`, `fact_tickets[resolved_at]`, `fact_tickets[sla_target_hours]`
- **Assumptions:** Uses `NOW()` at query time, so the value updates on every refresh.

---

## Backlog Count

- **What it answers:** "How many tickets are currently unresolved?"
- **Formula:** `COUNT(resolved_at IS NULL)`.
- **DAX measure:** `[Backlog Count]`
- **Source columns:** `fact_tickets[resolved_at]`
- **Assumptions:** Includes tickets in `Open` and `Pending` status alike.

---

## Aging Buckets

- **What it answers:** "How OLD is our backlog?"
- **Formula:** `ticket_age_band` is precomputed in SQL using elapsed hours since `created_at`:
  - `0-1 Day` ≤ 24h
  - `1-3 Days` 24–72h
  - `3-7 Days` 72–168h
  - `7-14 Days` 168–336h
  - `14+ Days` > 336h
  - `(Resolved)` for closed tickets.
- **DAX measures:** `[Tickets in 0-1 Day band]`, `[Tickets in 1-3 Days band]`, `[Tickets in 3-7 Days band]`, `[Tickets in 7+ Days band]`, `[Oldest Open Ticket Days]`
- **Source columns:** `fact_tickets[ticket_age_band]`, `fact_tickets[created_at]`, `fact_tickets[resolved_at]`
- **Assumptions:** Bands are frozen at ETL time (snapshot). For "live" aging in Power BI, the user can recompute with `DATEDIFF(created_at, NOW(), HOUR)`.

---

## CSAT Score

- **What it answers:** "How satisfied are customers with how their tickets were handled?"
- **Formula:** `AVERAGE(satisfaction_score)` across tickets with a non-null score.
- **DAX measures:** `[Avg CSAT]`, `[CSAT Display]`, `[CSAT Satisfied Rate]` (% ≥ 4), `[CSAT Dissatisfied Rate]` (% ≤ 2)
- **Source columns:** `fact_tickets[satisfaction_score]`
- **Assumptions:** Missing scores are excluded entirely — they neither boost nor drag the average. Reported on a 1.0–5.0 scale.
