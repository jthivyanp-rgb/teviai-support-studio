"""Screen untrusted messages and draft replies with explicit heuristics."""

import re

from .business_config import DEFAULT_POLICIES, POLICY_LABELS, POLICY_TOPIC_KEYWORDS, POLICY_NOT_SET
from .classification import classify, find_keywords

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# A run of digits (with optional spaces, dashes, brackets, leading +).
NUMBER_RUN_RE = re.compile(r"(?<![\w])\+?\d[\d \-()]{7,}\d(?![\w])")
CREDENTIAL_PATTERNS = tuple(
    re.compile(rf"(\b(?:{label})\s*(?:is\s+|[:=]\s*)){value}", re.IGNORECASE)
    for label, value in (
        (r"password", r"\S+"),
        (r"cvv|cvc|card security code", r"\d{3,4}\b"),
        (r"pin(?: number)?", r"\d{4,8}\b"),
        (r"sort code", r"\d{2}[- ]?\d{2}[- ]?\d{2}\b"),
        (r"date of birth", r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}\b"),
        (r"passport(?: number)?", r"[A-Z0-9]{5,12}\b"),
    )
)
SENSITIVE_WORDS = ["password", "date of birth", "bank details", "sort code", "passport", "pin number"]


def _digit_count(s: str) -> int:
    return sum(ch.isdigit() for ch in s)


def find_personal_data(text: str) -> list[str]:
    """Return a list of the kinds of personal data found in the text."""
    text = text or ""
    found = []
    if EMAIL_RE.search(text):
        found.append("email address")
    for match in NUMBER_RUN_RE.finditer(text):
        digits = _digit_count(match.group())
        if 13 <= digits <= 19:
            if "payment card number" not in found:
                found.append("payment card number")
        elif 9 <= digits <= 12:
            if "phone number" not in found:
                found.append("phone number")
    for word in SENSITIVE_WORDS:
        if find_keywords(text, [word]):
            found.append(f"mention of '{word}'")
    if any(pattern.search(text) for pattern in CREDENTIAL_PATTERNS):
        found.append("labelled credential or identification value")
    return found


def redact_pii(text: str) -> str:
    """Mask common email, payment, phone and labelled credential values."""
    text = EMAIL_RE.sub("[EMAIL]", text or "")

    def _replace(match: re.Match) -> str:
        digits = _digit_count(match.group())
        if 13 <= digits <= 19:
            return "[CARD NUMBER]"
        if 9 <= digits <= 12:
            return "[PHONE]"
        return match.group()

    for pattern in CREDENTIAL_PATTERNS:
        text = pattern.sub(r"\1[REDACTED]", text)
    return NUMBER_RUN_RE.sub(_replace, text)


# ---------------------------------------------------------------------------
# Risk detection
# ---------------------------------------------------------------------------

LEGAL_WORDS = ["lawyer", "solicitor", "sue", "court", "legal action", "trading standards", "ombudsman"]
HEALTH_WORDS = [
    "allergy", "allergic", "allergen", "anaphylaxis", "nut allergy", "gluten", "coeliac", "celiac",
    "lactose", "pregnant", "pregnancy", "medical", "medication", "injury", "injured", "rash",
    "hospital", "caught fire", "burned myself", "burnt myself",
]
NEGATIVE_WORDS = [
    "worst", "terrible", "awful", "disgusting", "useless", "furious",
    "ridiculous", "scam", "unacceptable", "appalling",
]
# Phrases in a DRAFT reply that promise something the business may not deliver.
PROMISE_PATTERNS = [
    r"\bguarantee[sd]?\b",
    r"\bpromise[sd]?\b",
    r"\bdefinitely\b",
    r"\b100 ?%",
    r"\bnever happen again\b",
    r"\brefund (?:has been|is|was) (?:approved|processed|issued|confirmed)\b",
    r"\b(?:we|i)(?:['’]ve| have)\s+(?:already\s+)?"
    r"(?:refunded\b|(?:processed|issued|approved)\s+(?:your|the|a)\s+refund\b)",
    r"\bwe will refund\b",
    r"\byou will (?:get|receive) (?:a |your )?(?:full )?refund\b",
    r"\bfree (?:of charge|compensation|replacement|gift)\b",
    r"\bcompensation\b",
    r"\bwithin \d+ (?:hours?|minutes?)\b",
]

CATEGORY_POLICY = {
    "refund_request": "refunds",
    "delivery_issue": "delivery",
    "account_privacy": "privacy",
}

HIGH, MEDIUM, LOW = "high", "medium", "low"


def find_unsupported_promises(draft: str) -> list[str]:
    found = []
    for pattern in PROMISE_PATTERNS:
        m = re.search(pattern, draft or "", re.IGNORECASE)
        if m:
            found.append(m.group())
    return found


def find_unclear_policies(message: str, category: str, policies: dict) -> list[str]:
    """Policy topics the customer raises (or the category needs) that have no policy text."""
    missing = []
    for topic, words in POLICY_TOPIC_KEYWORDS.items():
        if find_keywords(message, words) and not (policies.get(topic) or "").strip():
            missing.append(topic)
    needed = CATEGORY_POLICY.get(category)
    if needed and not (policies.get(needed) or "").strip() and needed not in missing:
        missing.append(needed)
    return missing


def detect_risks(message: str, category: str, confidence: str,
                 policies: dict | None = None, draft: str | None = None) -> list[dict]:
    """Return a list of risk flags. Each flag: code, severity, title, detail."""
    policies = DEFAULT_POLICIES if policies is None else policies
    risks = []

    personal = find_personal_data(message)
    if personal:
        severe = any(kind not in {"email address", "phone number"} for kind in personal)
        risks.append({
            "code": "PRIVACY_PERSONAL_DATA",
            "severity": HIGH if severe else MEDIUM,
            "title": "Privacy risk: personal data in message",
            "detail": "Found: " + ", ".join(personal)
                      + ". Keep these details out of the reply and use the privacy process if needed.",
        })

    if category == "account_privacy" or find_keywords(message, ["personal data", "delete my data", "gdpr"]):
        risks.append(flag("PRIVACY_REVIEW", HIGH, "Privacy review required",
                          "Escalate this request to the owner for identity verification."))
    if re.search(PROMPT_INJECTION, message, re.IGNORECASE):
        risks.append(flag("PROMPT_INJECTION", HIGH, "Possible instruction override",
                          "Treat customer text as data. Review the underlying enquiry and use a rule-based draft."))
    if category == "booking_request":
        risks.append(flag("BOOKING_VERIFICATION", MEDIUM, "Booking needs verification",
                          "Check availability through the business booking process."))
    if category == "product_question" and find_keywords(message, ["in stock", "available", "price", "how much", "cost"]):
        risks.append(flag("PRODUCT_VERIFICATION", MEDIUM, "Product details need verification",
                          "Check the current price and availability before making a claim."))
    if category == "refund_request" or find_keywords(message, ["refund", "chargeback", "money back", "reimburse"]):
        risks.append({
            "code": "REFUND_DECISION",
            "severity": HIGH,
            "title": "Refund decision needs a human",
            "detail": "TeviAI never approves refunds. Approving a reply does not approve a refund.",
        })

    legal = find_keywords(message, LEGAL_WORDS)
    if legal:
        risks.append({
            "code": "LEGAL_OR_THREAT",
            "severity": HIGH,
            "title": "Legal threat or escalation language",
            "detail": "Words found: " + ", ".join(legal) + ". Consider escalating to the owner.",
        })

    health = find_keywords(message, HEALTH_WORDS)
    if health:
        risks.append({
            "code": "HEALTH_SAFETY",
            "severity": HIGH,
            "title": "Health or safety question",
            "detail": "Words found: " + ", ".join(health) + ". Only give information you have checked "
                      "(e.g. ingredient lists). Do not guess or give medical advice. Escalate injuries to the owner.",
        })

    negative = find_keywords(message, NEGATIVE_WORDS)
    if negative or category == "complaint":
        risks.append({
            "code": "NEGATIVE_TONE",
            "severity": MEDIUM,
            "title": "Strong negative tone",
            "detail": "A staff member should review the complaint and the proposed wording.",
        })

    unclear = find_unclear_policies(message, category, policies)
    if unclear:
        risks.append({
            "code": "UNCLEAR_POLICY",
            "severity": MEDIUM,
            "title": "Unclear or missing policy",
            "detail": "No written policy for: " + ", ".join(POLICY_LABELS.get(t, t) for t in unclear)
                      + ". Do not guess an answer.",
        })

    if confidence == "low":
        risks.append({
            "code": "LOW_CONFIDENCE",
            "severity": LOW,
            "title": "Classification uncertain",
            "detail": "No category keywords matched. Check the category yourself.",
        })

    if draft is not None:
        if redact_pii(draft) != draft:
            risks.append(flag("DRAFT_PERSONAL_DATA", HIGH, "Sensitive detail in reply",
                              "Remove the detected personal or payment detail before approval."))
        for code, pattern, title, detail in CLAIM_RULES:
            if re.search(pattern, draft, re.I):
                risks.append(flag(code, HIGH, title, detail))
        promises = find_unsupported_promises(draft)
        if promises:
            risks.append({
                "code": "UNSUPPORTED_PROMISE",
                "severity": HIGH,
                "title": "Unsupported promise in reply",
                "detail": "Phrases found: " + ", ".join(f"'{p}'" for p in promises)
                          + ". Remove them unless the business can really commit to this.",
            })
        refund_asked = any(r["code"] == "REFUND_DECISION" for r in risks)
        if refund_asked and not re.search(r"\brefund", draft, re.IGNORECASE):
            risks.append({
                "code": "REFUND_NOT_ADDRESSED",
                "severity": MEDIUM,
                "title": "Reply does not mention the refund question",
                "detail": "The customer asked about a refund but the reply never mentions it. "
                          "Add a sentence (without approving the refund) so the reply is complete.",
            })
        if POLICY_NOT_SET in draft:
            risks.append({
                "code": "POLICY_PLACEHOLDER",
                "severity": HIGH,
                "title": "Reply contains a missing-policy placeholder",
                "detail": "Replace the placeholder text before approving.",
            })

    return risks


PROMPT_INJECTION = (
    r"\b(?:ignore|disregard|override|forget)\b[\s\S]{0,60}\b(?:instructions|rules|polic(?:y|ies)|safeguards)\b"
    r"|\b(?:system prompt|developer instructions|act as (?:an? )?(?:admin|system))\b"
)

CLAIM_RULES = (
    ("DELIVERY_CLAIM", r"\b(?:parcel|package|order|delivery)\s+(?:has\s+|was\s+|is\s+)?"
     r"(?:shipped|dispatched|delivered|arrived|in transit|out for delivery|will arrive)\b",
     "Order status claim", "Remove order status or timing claims until the business verifies them."),
    ("BOOKING_CLAIM", r"\b(?:booking|appointment|reservation|slot)\s+"
     r"(?:(?:(?:for|on|at)\s+[^.!?\n]{1,45}?\s+)?(?:has been|is|was|will be)\s+)?"
     r"(?:confirmed|booked|reserved|scheduled)\b"
     r"|\b(?:we(?:'ve| have)|you(?:'ve| have))\s+(?:booked|reserved|scheduled)\b",
     "Booking confirmation claim", "Remove the confirmation and refer the request for human verification."),
    ("PRODUCT_CLAIM", r"\b(?:is|are|currently)\s+(?:in stock|available now|sold out)\b"
     r"|[£$€]\s*\d|\b\d+(?:\.\d+)?\s*(?:GBP|USD|EUR)\b",
     "Price or stock claim", "Remove unverified pricing or availability."),
    ("PRIVACY_CLAIM", r"\b(?:data|account)\s+(?:(?:has been|was|is)\s+)?(?:deleted|erased)\b",
     "Privacy action claim", "Remove any claim that the request has already been completed."),
)


def flag(code, severity, title, detail):
    return {"code": code, "severity": severity, "title": title, "detail": detail}


def risk_level(risks: list[dict]) -> str:
    severities = {risk["severity"] for risk in risks}
    return next((level for level in (HIGH, MEDIUM, LOW) if level in severities), "none")


def risk_codes(risks: list[dict]) -> set[str]:
    return {r["code"] for r in risks}


def analyse_enquiry(message: str, policies: dict | None = None) -> dict:
    result = classify(message)
    result["risks"] = detect_risks(message, result["category"], result["confidence"], policies)
    return result
