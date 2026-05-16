"""Shared canonical column-mapping for the IT helpdesk pipeline.

Single source of truth for synonym -> canonical name. Imported by
01_profile_data.py and 02_clean_and_load.py so the two scripts cannot drift.
"""
from __future__ import annotations

CANONICAL_COLUMNS = [
    "ticket_id",
    "created_at",
    "resolved_at",
    "first_response_at",
    "status",
    "priority",
    "category",
    "channel",
    "agent_name",
    "team",
    "satisfaction_score",
    "reopen_count",
    "description",
]

SYNONYMS: dict[str, list[str]] = {
    "ticket_id":          ["ticket_id", "id", "ticket id", "ticket number", "ticketid", "case_id", "case id"],
    "created_at":         ["created_at", "date_created", "open_date", "opened_at", "ticket_created_date", "created", "open date", "submitted_at", "submitted"],
    "resolved_at":        ["resolved_at", "date_resolved", "close_date", "closed_at", "resolution_date", "resolved", "closed", "ticket_resolved_date", "time_to_resolution", "time to resolution"],
    "first_response_at":  ["first_response_at", "first_reply_at", "first response", "first_response", "first reply", "first_reply", "first_response_time", "first response time"],
    "status":             ["status", "ticket_status", "state", "ticket state"],
    "priority":           ["priority", "ticket_priority", "urgency", "severity"],
    "category":           ["category", "issue_type", "ticket_type", "type", "issue category", "ticket category"],
    "channel":            ["channel", "source", "ticket_channel", "contact_channel", "submission_channel", "via"],
    "agent_name":         ["agent_name", "assigned_to", "agent", "assignee", "owner", "handler"],
    "team":               ["team", "department", "group", "queue"],
    "satisfaction_score": ["satisfaction_score", "csat", "rating", "customer_satisfaction_rating", "customer_satisfaction_score", "customer satisfaction", "satisfaction"],
    "reopen_count":       ["reopen_count", "reopens", "times_reopened", "reopened", "reopen"],
    "description":        ["description", "subject", "body", "summary", "ticket_description", "issue_description", "ticket_subject"],
}


def _normalize(s: str) -> str:
    return s.strip().lower().replace("-", "_").replace(" ", "_")


def infer_mapping(raw_headers: list[str]) -> tuple[dict[str, str], list[str]]:
    """Return (mapping raw->canonical, list of unmapped canonical names)."""
    norm_index = {_normalize(h): h for h in raw_headers}
    mapping: dict[str, str] = {}
    used_raw: set[str] = set()
    for canonical, candidates in SYNONYMS.items():
        for cand in candidates:
            key = _normalize(cand)
            if key in norm_index and norm_index[key] not in used_raw:
                mapping[norm_index[key]] = canonical
                used_raw.add(norm_index[key])
                break
    missing = [c for c in CANONICAL_COLUMNS if c not in mapping.values()]
    return mapping, missing
