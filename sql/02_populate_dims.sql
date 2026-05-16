-- 02_populate_dims.sql
-- Populate every dim table from distinct values in raw_tickets.
-- Surrogate keys are generated via ROW_NUMBER(). dim_calendar uses a
-- recursive CTE spanning min(created_at) ... today+30 days.

DELETE FROM dim_agent;
DELETE FROM dim_category;
DELETE FROM dim_channel;
DELETE FROM dim_priority;
DELETE FROM dim_calendar;

-- ============================================================
-- dim_agent
-- ============================================================
INSERT INTO dim_agent (agent_key, agent_name, team)
SELECT
    ROW_NUMBER() OVER (ORDER BY COALESCE(agent_name, '(Unassigned)'), COALESCE(team, '(Unknown)')) AS agent_key,
    COALESCE(agent_name, '(Unassigned)')                                                          AS agent_name,
    COALESCE(team,       '(Unknown)')                                                             AS team
FROM (
    SELECT DISTINCT agent_name, team FROM raw_tickets
);

-- ============================================================
-- dim_category
-- ============================================================
INSERT INTO dim_category (category_key, category_name)
SELECT
    ROW_NUMBER() OVER (ORDER BY COALESCE(category, '(Uncategorized)')) AS category_key,
    COALESCE(category, '(Uncategorized)')                              AS category_name
FROM (
    SELECT DISTINCT category FROM raw_tickets
);

-- ============================================================
-- dim_channel
-- ============================================================
INSERT INTO dim_channel (channel_key, channel_name)
SELECT
    ROW_NUMBER() OVER (ORDER BY COALESCE(channel, '(Unknown)')) AS channel_key,
    COALESCE(channel, '(Unknown)')                              AS channel_name
FROM (
    SELECT DISTINCT channel FROM raw_tickets
);

-- ============================================================
-- dim_priority — SLA targets seeded from business rule
-- ============================================================
INSERT INTO dim_priority (priority_key, priority_name, sla_target_hours)
SELECT
    ROW_NUMBER() OVER (ORDER BY
        CASE COALESCE(priority, '(Unknown)')
            WHEN 'Critical' THEN 1
            WHEN 'High'     THEN 2
            WHEN 'Medium'   THEN 3
            WHEN 'Low'      THEN 4
            ELSE 5
        END
    ) AS priority_key,
    COALESCE(priority, '(Unknown)') AS priority_name,
    CASE COALESCE(priority, '(Unknown)')
        WHEN 'Critical' THEN 4
        WHEN 'High'     THEN 8
        WHEN 'Medium'   THEN 24
        WHEN 'Low'      THEN 72
        ELSE 24
    END AS sla_target_hours
FROM (
    SELECT DISTINCT priority FROM raw_tickets
);

-- ============================================================
-- dim_calendar — recursive CTE from earliest created_at to today + 30 days
-- ============================================================
WITH RECURSIVE bounds AS (
    SELECT
        date(COALESCE(MIN(created_at), date('now'))) AS start_date,
        date('now', '+30 days')                      AS end_date
    FROM raw_tickets
),
calendar(d) AS (
    SELECT start_date FROM bounds
    UNION ALL
    SELECT date(d, '+1 day') FROM calendar, bounds
    WHERE date(d, '+1 day') <= end_date
)
INSERT INTO dim_calendar (
    date_key, date, day_of_week, week_number, month_number, month_name,
    quarter, year, is_weekend, is_business_day
)
SELECT
    CAST(strftime('%Y%m%d', d) AS INTEGER) AS date_key,
    d                                       AS date,
    CASE CAST(strftime('%w', d) AS INTEGER)
        WHEN 0 THEN 'Sunday'    WHEN 1 THEN 'Monday'  WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday' WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END                                                    AS day_of_week,
    CAST(strftime('%W', d) AS INTEGER)                     AS week_number,
    CAST(strftime('%m', d) AS INTEGER)                     AS month_number,
    CASE CAST(strftime('%m', d) AS INTEGER)
        WHEN 1 THEN 'January'  WHEN 2 THEN 'February' WHEN 3 THEN 'March'
        WHEN 4 THEN 'April'    WHEN 5 THEN 'May'      WHEN 6 THEN 'June'
        WHEN 7 THEN 'July'     WHEN 8 THEN 'August'   WHEN 9 THEN 'September'
        WHEN 10 THEN 'October' WHEN 11 THEN 'November' WHEN 12 THEN 'December'
    END                                                    AS month_name,
    ((CAST(strftime('%m', d) AS INTEGER) - 1) / 3) + 1     AS quarter,
    CAST(strftime('%Y', d) AS INTEGER)                     AS year,
    CASE WHEN CAST(strftime('%w', d) AS INTEGER) IN (0, 6) THEN 1 ELSE 0 END AS is_weekend,
    CASE WHEN CAST(strftime('%w', d) AS INTEGER) IN (0, 6) THEN 0 ELSE 1 END AS is_business_day
FROM calendar;
