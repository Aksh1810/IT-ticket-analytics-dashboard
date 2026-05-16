-- 03_transform_facts.sql
-- Build fact_tickets by joining raw_tickets to every dim and computing the
-- derived business columns (resolution_hours, response_hours, SLA breach,
-- first-contact-resolved flag, age band).

DELETE FROM fact_tickets;

INSERT INTO fact_tickets (
    ticket_id,
    created_at,
    resolved_at,
    first_response_at,
    status,
    agent_key,
    category_key,
    channel_key,
    priority_key,
    created_date_key,
    satisfaction_score,
    reopen_count,
    resolution_hours,
    response_hours,
    sla_target_hours,
    sla_breached,
    is_first_contact_resolved,
    ticket_age_band
)
SELECT
    r.ticket_id,
    r.created_at,
    r.resolved_at,
    r.first_response_at,
    r.status,
    da.agent_key,
    dc.category_key,
    dch.channel_key,
    dp.priority_key,
    CAST(strftime('%Y%m%d', r.created_at) AS INTEGER) AS created_date_key,
    r.satisfaction_score,
    COALESCE(r.reopen_count, 0) AS reopen_count,

    -- resolution_hours
    CASE
        WHEN r.resolved_at IS NOT NULL
            THEN (JULIANDAY(r.resolved_at) - JULIANDAY(r.created_at)) * 24
        ELSE NULL
    END AS resolution_hours,

    -- response_hours
    CASE
        WHEN r.first_response_at IS NOT NULL
            THEN (JULIANDAY(r.first_response_at) - JULIANDAY(r.created_at)) * 24
        ELSE NULL
    END AS response_hours,

    dp.sla_target_hours,

    -- sla_breached: 0 for open tickets, 1 if resolution exceeded target
    CASE
        WHEN r.resolved_at IS NULL THEN 0
        WHEN ((JULIANDAY(r.resolved_at) - JULIANDAY(r.created_at)) * 24)
             > dp.sla_target_hours THEN 1
        ELSE 0
    END AS sla_breached,

    -- is_first_contact_resolved: resolved AND never reopened
    CASE
        WHEN r.status = 'Resolved' AND COALESCE(r.reopen_count, 0) = 0 THEN 1
        ELSE 0
    END AS is_first_contact_resolved,

    -- ticket_age_band: bucket open tickets by elapsed hours; resolved -> '(Resolved)'
    CASE
        WHEN r.resolved_at IS NULL THEN
            CASE
                WHEN (JULIANDAY('now') - JULIANDAY(r.created_at)) * 24 <= 24  THEN '0-1 Day'
                WHEN (JULIANDAY('now') - JULIANDAY(r.created_at)) * 24 <= 72  THEN '1-3 Days'
                WHEN (JULIANDAY('now') - JULIANDAY(r.created_at)) * 24 <= 168 THEN '3-7 Days'
                WHEN (JULIANDAY('now') - JULIANDAY(r.created_at)) * 24 <= 336 THEN '7-14 Days'
                ELSE '14+ Days'
            END
        ELSE '(Resolved)'
    END AS ticket_age_band

FROM raw_tickets r
LEFT JOIN dim_agent    da  ON COALESCE(r.agent_name, '(Unassigned)')    = da.agent_name
                          AND COALESCE(r.team,       '(Unknown)')       = da.team
LEFT JOIN dim_category dc  ON COALESCE(r.category,   '(Uncategorized)') = dc.category_name
LEFT JOIN dim_channel  dch ON COALESCE(r.channel,    '(Unknown)')       = dch.channel_name
LEFT JOIN dim_priority dp  ON COALESCE(r.priority,   '(Unknown)')       = dp.priority_name;
