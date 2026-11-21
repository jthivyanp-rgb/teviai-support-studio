"""Enquiry lifecycle and reviewer decisions, independent of the UI."""

from uuid import uuid4

from .activity_logger import make_log_entry
from .business_config import POLICY_NOT_SET
from .data_models import MAX_MESSAGE, MAX_REPLY, REVIEWERS, STATUS_LABELS, Status, timestamp, validate_text
from .risk_detection import HIGH, analyse_enquiry, detect_risks, risk_codes, risk_level

TRANSITIONS = {
    Status.NEW: {Status.CLASSIFIED},
    Status.CLASSIFIED: {Status.DRAFT_READY, Status.ESCALATED},
    Status.DRAFT_READY: {Status.PENDING_REVIEW, Status.ESCALATED},
    Status.PENDING_REVIEW: {Status.DRAFT_READY, Status.APPROVED, Status.REJECTED, Status.ESCALATED},
}
DRAFTABLE = {Status.CLASSIFIED, Status.DRAFT_READY}
EDITABLE = {Status.DRAFT_READY, Status.PENDING_REVIEW}
DECISIONS = {
    Status.APPROVED: "Approved",
    Status.REJECTED: "Rejected",
    Status.ESCALATED: "Escalated",
}
BLOCKING_DRAFT_FLAGS = {
    "UNSUPPORTED_PROMISE", "POLICY_PLACEHOLDER", "DRAFT_PERSONAL_DATA",
    "DELIVERY_CLAIM", "BOOKING_CLAIM", "PRODUCT_CLAIM", "PRIVACY_CLAIM",
}
ESCALATION_FLAGS = {"PRIVACY_REVIEW", "HEALTH_SAFETY", "LEGAL_OR_THREAT"}


def record(events, enquiry, action, *, previous=None):
    risks = enquiry["risks"]
    events.append(make_log_entry(
        enquiry_id=enquiry["id"], action=action, category=enquiry["label"],
        risk_level=risk_level(risks).title(), risk_flags=", ".join(sorted(risk_codes(risks))),
        draft_mode=enquiry["draft_source"], reviewer=enquiry["reviewer"],
        previous_status=STATUS_LABELS[previous] if previous else "",
        status=STATUS_LABELS[enquiry["status"]],
    ))


def transition(enquiry, events, target, action, **updates):
    previous = enquiry["status"]
    if target not in TRANSITIONS.get(previous, set()):
        raise ValueError("This enquiry cannot move to that status.")
    enquiry.update(updates, status=target)
    record(events, enquiry, action, previous=previous)


def create_enquiry(name, channel, message, policies, events, *, sample_id=""):
    message = validate_text(message, "Customer message", MAX_MESSAGE)
    enquiry = {
        "id": "TEV-" + uuid4().hex[:12].upper(), "received_at": timestamp(),
        "customer_name": name.strip() or "Unknown sender", "channel": channel, "message": message,
        **analyse_enquiry(message, policies),
        "status": Status.NEW, "draft": "", "draft_source": "", "final_reply": "",
        "reviewer": "", "decision_reason": "", "sample_id": sample_id,
    }
    record(events, enquiry, "Enquiry received")
    transition(enquiry, events, Status.CLASSIFIED, "Classified")
    return enquiry


def review_risks(enquiry, policies, draft=None):
    return detect_risks(enquiry["message"], enquiry["category"], enquiry["confidence"], policies, draft)


def save_draft(enquiry, events, draft, policies):
    if enquiry["status"] not in DRAFTABLE:
        raise ValueError("This enquiry is unavailable for drafting.")
    text = validate_text(draft["text"], "Draft reply", MAX_REPLY)
    updates = dict(draft=text, final_reply=text, draft_source=draft["source"],
                   policy_snapshot=dict(policies),
                   risks=review_risks(enquiry, policies, text))
    if enquiry["status"] == Status.DRAFT_READY:
        enquiry.update(updates)
        record(events, enquiry, "Draft regenerated", previous=Status.DRAFT_READY)
    else:
        transition(enquiry, events, Status.DRAFT_READY, "Draft created", **updates)


def edit_draft(enquiry, events, reply, policies):
    if enquiry["status"] not in EDITABLE:
        raise ValueError("This draft is closed for editing.")
    reply = validate_text(reply, "Draft reply", MAX_REPLY)
    if reply != enquiry["final_reply"]:
        enquiry.update(final_reply=reply, risks=review_risks(enquiry, policies, reply))
        record(events, enquiry, "Draft edited", previous=enquiry["status"])


def request_review(enquiry, events, reply, policies):
    if enquiry["status"] != Status.DRAFT_READY:
        raise ValueError("Create a draft before submitting it for review.")
    check_policy_snapshot(enquiry, policies)
    edit_draft(enquiry, events, reply, policies)
    transition(enquiry, events, Status.PENDING_REVIEW, "Submitted for review",
               risks=review_risks(enquiry, policies, enquiry["final_reply"]))


def check_approval(final_reply, reviewer, risks, acknowledged):
    problems = []
    if reviewer not in REVIEWERS:
        problems.append("Choose a demo reviewer.")
    try:
        validate_text(final_reply or "", "Draft reply", MAX_REPLY)
    except ValueError as exc:
        problems.append(str(exc))
    codes = risk_codes(risks)
    if codes & ESCALATION_FLAGS:
        problems.append("Escalate this enquiry for specialist review before proceeding.")
    if codes & BLOCKING_DRAFT_FLAGS or POLICY_NOT_SET in (final_reply or ""):
        problems.append("Resolve the flagged content in the reply before approval.")
    if any(risk["severity"] == HIGH for risk in risks) and not acknowledged:
        problems.append("Acknowledge the high-severity flags before approving.")
    return problems


def check_policy_snapshot(enquiry, policies):
    if enquiry.get("policy_snapshot", policies) != policies:
        raise ValueError("Business policies changed. Regenerate the draft before approval.")


def return_for_revision(enquiry, events):
    if enquiry["status"] != Status.PENDING_REVIEW:
        raise ValueError("Only pending reviews can be returned to Draft Studio.")
    transition(enquiry, events, Status.DRAFT_READY, "Returned for revision")


def decide(enquiry, events, target, reviewer, policies, *, reply="", acknowledged=False, reason=""):
    if target not in DECISIONS or target not in TRANSITIONS.get(enquiry["status"], set()):
        raise ValueError("This decision is unavailable for the enquiry’s current status.")
    if reviewer not in REVIEWERS:
        raise ValueError("Choose a demo reviewer.")
    risks = review_risks(enquiry, policies, reply or None)
    if target == Status.APPROVED:
        check_policy_snapshot(enquiry, policies)
        problems = check_approval(reply, reviewer, risks, acknowledged)
        if problems:
            raise ValueError(" ".join(problems))
        edit_draft(enquiry, events, reply, policies)
    transition(enquiry, events, target, DECISIONS[target], reviewer=reviewer,
               risks=risks, decision_reason=reason)
