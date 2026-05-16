-- 04_validation_checks.sql
-- Labeled validation queries. Each prints a label + result count so the
-- pipeline output is grep-able.

.headers on
.mode column

SELECT 'CHECK 1: fact_tickets rows whose created_date_key has no match in dim_calendar (should be 0)' AS label,
       COUNT(*) AS bad_rows
FROM fact_tickets f
LEFT JOIN dim_calendar c ON c.date_key = f.created_date_key
WHERE c.date_key IS NULL;

SELECT 'CHECK 2: fact_tickets rows with NULL agent_key (should be 0)' AS label,
       COUNT(*) AS bad_rows
FROM fact_tickets
WHERE agent_key IS NULL;

SELECT 'CHECK 3: sla_breached=1 ticket count by priority (sanity)' AS label;
SELECT dp.priority_name,
       COUNT(*) AS breached_tickets
FROM fact_tickets f
JOIN dim_priority dp ON dp.priority_key = f.priority_key
WHERE f.sla_breached = 1
GROUP BY dp.priority_name
ORDER BY breached_tickets DESC;

SELECT 'CHECK 4: rows with negative resolution_hours (should be 0)' AS label,
       COUNT(*) AS bad_rows
FROM fact_tickets
WHERE resolution_hours < 0;

SELECT 'CHECK 5: row-count parity (raw_tickets vs fact_tickets — should match)' AS label,
       (SELECT COUNT(*) FROM raw_tickets)  AS raw_rows,
       (SELECT COUNT(*) FROM fact_tickets) AS fact_rows,
       CASE
           WHEN (SELECT COUNT(*) FROM raw_tickets) = (SELECT COUNT(*) FROM fact_tickets)
               THEN 'PASS'
           ELSE 'FAIL'
       END AS result;
