"""Draft replies from approved business policies and neutral templates."""

from .business_config import DEFAULT_BUSINESS_NAME, DEFAULT_POLICIES, POLICY_LABELS, POLICY_TOPIC_KEYWORDS
from .classification import find_keywords
from .risk_detection import risk_codes

RULE_BASED_LABEL = "Rule-Based"

TEMPLATES = {
    "refund_request": (
        "Hi {name},\n\nThank you for getting in touch about a refund.\n\n{refunds}\n\n"
        "A member of our team will review your request and reply to you personally. "
        "Please note that this message is not a refund decision.\n\nKind regards,\n{business}"
    ),
    "delivery_issue": (
        "Hi {name},\n\nThank you for your message about your delivery, and sorry for any inconvenience. "
        "{delivery}\n\nWe will check the status of your order and get back to you "
        "with an update.\n\nKind regards,\n{business}"
    ),
    "complaint": (
        "Hi {name},\n\nThank you for telling us about this, and we are sorry to hear about your experience. "
        "A member of our team will look into what happened and contact you to discuss the next steps.\n\n"
        "Kind regards,\n{business}"
    ),
    "product_question": (
        "Hi {name},\n\nThank you for your question. We want to give you accurate information, so a member "
        "of our team will check the product details and reply to you.\n\nKind regards,\n{business}"
    ),
    "booking_request": (
        "Hi {name},\n\nThank you for your booking enquiry. A member of our team can check "
        "availability and follow up with the options.\n\nKind regards,\n{business}"
    ),
    "account_privacy": (
        "Hi {name},\n\nThank you for your message. {privacy}\n\nFor your security, please do not send "
        "passwords or full card numbers by message. We will contact you to confirm your identity before "
        "making any changes.\n\nKind regards,\n{business}"
    ),
    "general_enquiry": (
        "Hi {name},\n\nThank you for getting in touch. {opening_hours}\n\nIf there is anything else we can "
        "help with, just reply to this message.\n\nKind regards,\n{business}"
    ),
}


REFUND_ADDON = (
    "You also asked about a refund.\n\n{refunds}\n\n"
    "A member of our team will review the refund request separately. "
    "Please note that this message is not a refund decision."
)

SIGN_OFF = "\n\nKind regards,\n"


def rule_based_reply(category: str, customer_name: str, policies: dict | None = None,
                     business_name: str = DEFAULT_BUSINESS_NAME, risks: list[dict] | None = None,
                     *, message: str = "") -> dict:
    """Fill the category template. If the message also asks for a refund (REFUND_DECISION flag)
    but the category is not 'refund_request', a refund paragraph is added before the sign-off."""
    policies = DEFAULT_POLICIES if policies is None else policies
    first_name = "there"
    values = {key: (policies.get(key) or "").strip() or
              f"A team member will check our policy on {label.lower()}."
              for key, label in POLICY_LABELS.items()}
    if category == "general_enquiry" and message and not find_keywords(message, POLICY_TOPIC_KEYWORDS["opening_hours"]):
        values["opening_hours"] = "Could you tell us a little more about what you need help with?"
    template = TEMPLATES.get(category, TEMPLATES["general_enquiry"])
    text = template.format(name=first_name, business=business_name, **values)
    if category != "refund_request" and "REFUND_DECISION" in risk_codes(risks or []):
        body, _, signature = text.rpartition(SIGN_OFF)
        text = body + "\n\n" + REFUND_ADDON.format(**values) + SIGN_OFF + signature
    return {"text": text, "source": RULE_BASED_LABEL}
