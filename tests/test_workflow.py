"""Safety Lab regression scenarios and workflow guardrails."""

import pytest

from sample_data import SAMPLE_ENQUIRIES
from src import approval_workflow as workflow
from src.activity_logger import migrate_event
from src.ai_provider import AI_LABEL, generate_draft
from src.business_config import DEFAULT_POLICIES
from src.data_models import REVIEWERS, Status
from src.safety_lab import SCENARIOS, draft_for, evaluate


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[case[0] for case in SCENARIOS])
def test_scenario(scenario):
    row = evaluate(scenario)
    assert row["Result"] == "Pass", row


def prepare(message):
    events = []
    case = workflow.create_enquiry("Example", "Email", message, DEFAULT_POLICIES, events)
    workflow.save_draft(case, events, draft_for(message), DEFAULT_POLICIES)
    workflow.request_review(case, events, case["final_reply"], DEFAULT_POLICIES)
    return case, events


@pytest.mark.parametrize("reply", [
    "We will refund you.", "Your booking is confirmed.", "The order has shipped.",
    "The price is £40.", "Your account has been deleted.", "Email: fictional@example.com",
    "We’ve refunded you.", "We have issued your refund.", "Your booking for Tuesday is confirmed.",
    "The card security code: 123.",
])
def test_draft_content_blocks_approval_even_when_acknowledged(reply):
    case, events = prepare("Where is my order?")
    before = list(events)
    with pytest.raises(ValueError, match="Resolve the flagged content"):
        workflow.decide(case, events, Status.APPROVED, REVIEWERS[0], DEFAULT_POLICIES,
                        reply=reply, acknowledged=True)
    assert events == before
    assert case["status"] == Status.PENDING_REVIEW


def test_privacy_case_requires_escalation():
    case, events = prepare("Please delete my personal data.")
    with pytest.raises(ValueError, match="specialist review"):
        workflow.decide(case, events, Status.APPROVED, REVIEWERS[0], DEFAULT_POLICIES,
                        reply=case["final_reply"], acknowledged=True)
    workflow.decide(case, events, Status.ESCALATED, REVIEWERS[1], DEFAULT_POLICIES,
                    reason="Privacy or specialist handling")
    assert case["decision_reason"] == "Privacy or specialist handling"
    assert events[-1]["reviewer"] == REVIEWERS[1]


def test_policy_change_requires_regeneration_and_second_decision_is_refused():
    case, events = prepare("Where is my order?")
    policies = dict(DEFAULT_POLICIES, delivery="Staff review delivery requests.")
    with pytest.raises(ValueError, match="policies changed"):
        workflow.decide(case, events, Status.APPROVED, REVIEWERS[0], policies, reply=case["final_reply"])
    workflow.return_for_revision(case, events)
    workflow.save_draft(case, events, draft_for(case["message"], policies), policies)
    workflow.request_review(case, events, case["final_reply"], policies)
    workflow.decide(case, events, Status.APPROVED, REVIEWERS[0], policies, reply=case["final_reply"])
    assert events[-1]["previous_status"] == "Pending review"
    with pytest.raises(ValueError, match="unavailable"):
        workflow.decide(case, events, Status.REJECTED, REVIEWERS[1], policies)


@pytest.mark.parametrize("output", [{"opening": "delay"}, {"opening": "Your order has shipped"}, {"opening": []}])
def test_gemini_response_is_constrained(output):
    sample = SAMPLE_ENQUIRIES[1]
    case = workflow.create_enquiry("", "Email", sample["message"], DEFAULT_POLICIES, [], sample_id=sample["case_id"])
    template = draft_for(case["message"])
    draft, warning = generate_draft(case, template, "test-key", provider=lambda *args: output)
    if output["opening"] == "delay":
        assert draft["source"] == AI_LABEL
        assert not warning
        assert "delay you described" in draft["text"]
    else:
        assert draft == template
        assert warning


def test_manual_and_high_risk_inputs_never_reach_provider():
    def forbidden(*args):
        pytest.fail("Client must not be called.")

    for index, is_sample in [(1, False), (3, True)]:
        sample = SAMPLE_ENQUIRIES[index]
        case = workflow.create_enquiry("", "Email", sample["message"], DEFAULT_POLICIES, [],
                                       sample_id=sample["case_id"] if is_sample else "")
        draft, warning = generate_draft(case, draft_for(case["message"]), "test-key", provider=forbidden)
        assert draft["source"] == "Rule-Based"
        assert warning


def test_legacy_activity_exports_only_metadata():
    row = migrate_event({"enquiry_id": "ENQ-001", "event": "Human decision",
                         "decision": "Approved for manual sending", "customer_name": "Private",
                         "reviewer": "Private", "reply_text": "Private", "note": "Private"})
    assert row["status"] == "Approved — Not Sent"
    assert "Private" not in row.values()
