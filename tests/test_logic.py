"""Unit tests for safety features in support_logic.py."""

import io

import pandas as pd
import pytest

import support_logic as sl


def test_privacy_details_are_specific():
    found = sl.find_personal_data("Card 4111 1111 1111 1111, mail a.b@example.com, phone 07700 900123")
    assert found == ["email address", "payment card number", "phone number"]


def test_card_number_is_high_severity_and_phone_is_medium():
    card = sl.detect_risks("my card is 4111-1111-1111-1111", "account_privacy", "high")
    phone = sl.detect_risks("call 07700 900123", "general_enquiry", "high")
    assert card[0]["severity"] == "high"
    assert [r for r in phone if r["code"] == "PRIVACY_PERSONAL_DATA"][0]["severity"] == "medium"


def test_order_numbers_and_dates_are_not_flagged_as_personal_data():
    assert sl.find_personal_data("Order A1043 placed on 12/05/2026, expiry 09/28") == []


@pytest.mark.parametrize("message", [
    "Is this cake gluten free? I'm coeliac.",
    "The candle caught fire on my table.",
    "I got a rash after using the soap.",
])
def test_health_and_safety_messages_are_flagged_high(message):
    risks = sl.detect_risks(message, sl.classify(message)["category"], "medium")
    flag = [r for r in risks if r["code"] == "HEALTH_SAFETY"]
    assert flag and flag[0]["severity"] == "high"


def test_ordinary_product_question_has_no_health_flag():
    risks = sl.detect_risks("What colour are the large mugs?", "product_question", "medium")
    assert "HEALTH_SAFETY" not in sl.risk_codes(risks)


def test_redaction_removes_personal_data():
    text = "Email jo@example.com, card 4111 1111 1111 1111, phone 07700 900123, order A1043"
    redacted = sl.redact_pii(text)
    assert "jo@example.com" not in redacted
    assert "4111" not in redacted
    assert "900123" not in redacted
    assert "[EMAIL]" in redacted and "[CARD NUMBER]" in redacted and "[PHONE]" in redacted
    assert "A1043" in redacted


@pytest.mark.parametrize("category", list(sl.CATEGORIES))
def test_rule_based_templates_make_no_unsupported_promises(category):
    draft = sl.rule_based_reply(category, "Test Customer", sl.DEFAULT_POLICIES)
    assert draft["source"] == sl.RULE_BASED_LABEL
    assert sl.find_unsupported_promises(draft["text"]) == []
    assert sl.POLICY_NOT_SET not in draft["text"]


MIXED = "Hi, my parcel has not arrived. Can I get a refund?"


def test_mixed_delivery_and_refund_message_draft_covers_both():
    result = sl.analyse_enquiry(MIXED)
    assert result["category"] == "delivery_issue"
    assert "REFUND_DECISION" in sl.risk_codes(result["risks"])
    draft = sl.rule_based_reply(result["category"], "Test Customer", sl.DEFAULT_POLICIES, risks=result["risks"])
    text = draft["text"]
    assert "delivery" in text.lower()
    assert "You also asked about a refund" in text
    assert "not a refund decision" in text
    assert text.rstrip().endswith(sl.DEFAULT_BUSINESS_NAME)
    assert sl.find_unsupported_promises(text) == []
    risks = sl.detect_risks(MIXED, result["category"], result["confidence"], draft=text)
    assert "REFUND_NOT_ADDRESSED" not in sl.risk_codes(risks)


def test_reply_that_ignores_refund_question_is_flagged():
    reply = "Hi, sorry your parcel is late. We will check the tracking for you."
    risks = sl.detect_risks(MIXED, "delivery_issue", "high", draft=reply)
    assert "REFUND_NOT_ADDRESSED" in sl.risk_codes(risks)


def test_no_refund_paragraph_when_refund_not_asked():
    result = sl.analyse_enquiry("My parcel has not arrived yet.")
    draft = sl.rule_based_reply(result["category"], "Test Customer", risks=result["risks"])
    assert "refund" not in draft["text"].lower()


def test_missing_policy_gives_verification_wording_and_flag():
    policies = dict(sl.DEFAULT_POLICIES, refunds="")
    draft = sl.rule_based_reply("refund_request", "Test Customer", policies)
    assert "will check our policy" in draft["text"]
    risks = sl.detect_risks("I want a refund", "refund_request", "medium", policies, draft=draft["text"])
    assert sl.risk_codes(risks) == {"UNCLEAR_POLICY", "REFUND_DECISION"}


def test_approval_blocked_without_reviewer_or_acknowledgement():
    high = [{"code": "REFUND_DECISION", "severity": "high", "title": "", "detail": ""}]
    problems = sl.check_approval("Hello", "", high, acknowledged=False)
    assert len(problems) == 2
    assert sl.check_approval("Hello", "Demo Owner", high, acknowledged=True) == []


def test_approval_blocked_for_empty_reply_and_placeholder():
    assert sl.check_approval("  ", "Demo Owner", [], False)
    assert sl.check_approval("Policy: " + sl.POLICY_NOT_SET, "Demo Owner", [], False)


def test_csv_export_has_columns_and_blocks_formula_injection():
    entries = [sl.make_log_entry(enquiry_id="ENQ-001", reviewer="  =HYPERLINK(\"x\")", action="test")]
    csv_bytes = sl.log_to_csv(entries)
    df = pd.read_csv(io.BytesIO(csv_bytes))
    assert list(df.columns) == sl.LOG_COLUMNS
    assert df.loc[0, "reviewer"].startswith("'  =")


def test_unknown_log_field_is_rejected():
    with pytest.raises(KeyError):
        sl.make_log_entry(not_a_field="x")
