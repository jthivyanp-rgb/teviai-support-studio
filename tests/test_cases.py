"""The 10 realistic (fictional) test cases.

Each case runs the real rule-based pipeline on a message from sample_data.py and
checks the category and the exact set of risk flags. TC09 also checks an unsafe
draft reply that a staff member might write, to test unsupported-promise detection.
"""

import pytest

import support_logic as sl
from sample_data import SAMPLE_ENQUIRIES

MESSAGES = {s["case_id"]: s for s in SAMPLE_ENQUIRIES}

# case_id, expected category, expected risk codes, draft to check (or None)
CASES = [
    ("TC01", "refund_request", {"REFUND_DECISION"}, None),
    ("TC02", "delivery_issue", set(), None),
    ("TC03", "product_question", {"HEALTH_SAFETY"}, None),
    ("TC04", "account_privacy", {"PRIVACY_PERSONAL_DATA", "PRIVACY_REVIEW"}, None),
    ("TC05", "complaint", {"LEGAL_OR_THREAT", "NEGATIVE_TONE"}, None),
    ("TC06", "product_question", {"UNCLEAR_POLICY"}, None),
    ("TC07", "general_enquiry", set(), None),
    ("TC08", "general_enquiry", {"LOW_CONFIDENCE"}, None),
    ("TC09", "refund_request", {"REFUND_DECISION", "UNSUPPORTED_PROMISE"},
     "Of course! We guarantee a full refund today and will send free compensation. "
     "This will never happen again."),
    ("TC10", "account_privacy", {"PRIVACY_PERSONAL_DATA", "PRIVACY_REVIEW"}, None),
]


@pytest.mark.parametrize("case_id,category,expected_risks,draft", CASES, ids=[c[0] for c in CASES])
def test_case(case_id, category, expected_risks, draft):
    message = MESSAGES[case_id]["message"]
    result = sl.classify(message)
    assert result["category"] == category
    risks = sl.detect_risks(message, result["category"], result["confidence"], sl.DEFAULT_POLICIES, draft=draft)
    assert sl.risk_codes(risks) == expected_risks


def test_there_are_exactly_ten_cases():
    assert len(CASES) == 10
    assert {c[0] for c in CASES} == set(MESSAGES)
