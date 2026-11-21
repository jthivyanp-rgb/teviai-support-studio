"""Session activity metadata and CSV export."""

import pandas as pd

from .data_models import REVIEWERS, timestamp

LOG_COLUMNS = [
    "timestamp", "enquiry_id", "action", "category", "risk_level", "risk_flags",
    "draft_mode", "reviewer", "previous_status", "status",
]


def make_log_entry(**fields) -> dict:
    entry = dict.fromkeys(LOG_COLUMNS, "")
    entry["timestamp"] = timestamp()
    for key, value in fields.items():
        if key not in entry:
            raise KeyError(f"Unknown log field: {key}")
        entry[key] = value
    return entry


def log_to_dataframe(entries: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(entries, columns=LOG_COLUMNS)


def safe_cell(value):
    if isinstance(value, str) and (
        value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n"))
    ):
        return "'" + value
    return value


def log_to_csv(entries: list[dict]) -> bytes:
    return log_to_dataframe(entries).apply(lambda column: column.map(safe_cell)).to_csv(index=False).encode("utf-8")


def migrate_event(entry: dict) -> dict:
    """Keep historical metadata from the earlier prototype without free-text fields."""
    from .data_models import LEGACY_STATUSES, STATUS_LABELS, Status

    def old_status(event, decision):
        if event == "Draft created":
            return Status.PENDING_REVIEW
        if event == "Human decision":
            if decision == "Approved for manual sending":
                return Status.APPROVED
            return LEGACY_STATUSES.get(decision)
        return Status.CLASSIFIED

    status = old_status(entry.get("event"), entry.get("decision"))
    source = entry.get("reply_source", "")
    return make_log_entry(
        timestamp=entry.get("timestamp") or timestamp(), enquiry_id=entry["enquiry_id"],
        action=entry.get("decision") or entry.get("event", ""), category=entry.get("category", ""),
        risk_level="Unknown" if entry.get("risk_flags") else "None",
        risk_flags=entry.get("risk_flags", ""),
        draft_mode=("AI-Assisted" if source.startswith("AI-") else "Rule-Based") if source else "",
        reviewer=entry.get("reviewer") if entry.get("reviewer") in REVIEWERS else "",
        status=STATUS_LABELS.get(status, ""),
    )
