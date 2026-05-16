-- 01_create_schema.sql
-- Build the star-schema tables. Idempotent: drops old fact/dim tables first
-- so re-runs of the pipeline produce a clean slate.

DROP TABLE IF EXISTS fact_tickets;
DROP TABLE IF EXISTS dim_agent;
DROP TABLE IF EXISTS dim_category;
DROP TABLE IF EXISTS dim_channel;
DROP TABLE IF EXISTS dim_priority;
DROP TABLE IF EXISTS dim_calendar;

CREATE TABLE IF NOT EXISTS dim_agent (
    agent_key     INTEGER PRIMARY KEY,
    agent_name    TEXT,
    team          TEXT
);

CREATE TABLE IF NOT EXISTS dim_category (
    category_key   INTEGER PRIMARY KEY,
    category_name  TEXT
);

CREATE TABLE IF NOT EXISTS dim_channel (
    channel_key   INTEGER PRIMARY KEY,
    channel_name  TEXT
);

CREATE TABLE IF NOT EXISTS dim_priority (
    priority_key      INTEGER PRIMARY KEY,
    priority_name     TEXT,
    sla_target_hours  INTEGER
);

CREATE TABLE IF NOT EXISTS dim_calendar (
    date_key         INTEGER PRIMARY KEY,
    date             TEXT,
    day_of_week      TEXT,
    week_number      INTEGER,
    month_number     INTEGER,
    month_name       TEXT,
    quarter          INTEGER,
    year             INTEGER,
    is_weekend       INTEGER,
    is_business_day  INTEGER
);

CREATE TABLE IF NOT EXISTS fact_tickets (
    ticket_id                   TEXT,
    created_at                  TEXT,
    resolved_at                 TEXT,
    first_response_at           TEXT,
    status                      TEXT,
    agent_key                   INTEGER,
    category_key                INTEGER,
    channel_key                 INTEGER,
    priority_key                INTEGER,
    created_date_key            INTEGER,
    satisfaction_score          REAL,
    reopen_count                INTEGER,
    resolution_hours            REAL,
    response_hours              REAL,
    sla_target_hours            INTEGER,
    sla_breached                INTEGER,
    is_first_contact_resolved   INTEGER,
    ticket_age_band             TEXT
);
