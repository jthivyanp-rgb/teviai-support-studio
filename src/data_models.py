"""Workflow statuses and input validation."""

from datetime import datetime, timezone
from enum import StrEnum

MAX_MESSAGE = 4000
MAX_REPLY = 2400
REVIEWERS = ("Demo Owner", "Demo Shift Lead")


class Status(StrEnum):
    NEW = "NEW"
    CLASSIFIED = "CLASSIFIED"
    DRAFT_READY = "DRAFT_READY"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"


STATUS_LABELS = {
    Status.NEW: "New",
    Status.CLASSIFIED: "Classified",
    Status.DRAFT_READY: "Draft ready",
    Status.PENDING_REVIEW: "Pending review",
    Status.APPROVED: "Approved — Not Sent",
    Status.REJECTED: "Rejected",
    Status.ESCALATED: "Escalated",
}

LEGACY_STATUSES = {
    "New": Status.CLASSIFIED,
    "Awaiting approval": Status.PENDING_REVIEW,
    "Approved (not sent)": Status.APPROVED,
    "Rejected": Status.REJECTED,
    "Escalated to owner": Status.ESCALATED,
}


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validate_text(value: str, label: str, limit: int) -> str:
    if len(value) > limit:
        raise ValueError(f"{label} must be {limit:,} characters or fewer.")
    value = value.strip()
    if not value:
        raise ValueError(f"Enter a {label.lower()}.")
    return value
