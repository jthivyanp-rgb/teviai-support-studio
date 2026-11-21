"""Rule-based enquiry classification."""

import re

from .business_config import POLICY_TOPIC_KEYWORDS

CATEGORIES = {
    "account_privacy": "Privacy",
    "refund_request": "Refund",
    "complaint": "Complaint",
    "delivery_issue": "Delivery",
    "booking_request": "Booking",
    "product_question": "Product",
    "general_enquiry": "Other",
}

# Dictionary order is also the tie-break order (first wins on equal scores).
CATEGORY_KEYWORDS = {
    "account_privacy": [
        "account", "password", "log in", "login", "personal data", "my data",
        "delete my", "unsubscribe", "my email", "email address", "card details",
        "payment details", "update my card", "gdpr",
    ],
    "refund_request": [
        "refund", "money back", "reimburse", "chargeback", "return",
        "cancel my order", "compensation",
    ],
    "complaint": [
        "broken", "damaged", "faulty", "wrong item", "disappointed", "worst",
        "terrible", "awful", "rude", "unacceptable", "complaint", "unhappy", "furious",
    ],
    "delivery_issue": [
        "delivery", "deliver", "delivered", "shipping", "ship", "tracking",
        "parcel", "courier", "arrive", "arrived", "late", "dispatch", "dispatched",
        "where is my order", "order status", "my order hasn't come",
    ],
    "booking_request": ["book", "booking", "appointment", "reservation", "reschedule"],
    "product_question": [
        "size", "colour", "color", "ingredient", "allergy", "allergen", "nut",
        "in stock", "available", "material", "dishwasher", "warranty", "contain",
        "how do i use", "price", "how much", "cost",
    ],
    "general_enquiry": [
        *POLICY_TOPIC_KEYWORDS["opening_hours"], "closing", "saturday", "sunday", "located", "visit",
    ],
}


def _kw_pattern(keyword: str) -> re.Pattern:
    """Whole-word match that also accepts a plural 's' / 'es' ending."""
    return re.compile(r"\b" + re.escape(keyword) + r"(?:s|es)?\b", re.IGNORECASE)


def find_keywords(text: str, keywords: list[str]) -> list[str]:
    return [kw for kw in keywords if _kw_pattern(kw).search(text or "")]


def classify(message: str) -> dict:
    """Keyword-based classification. Returns category, label, confidence, matches."""
    # Normalise common punctuation without modifying the displayed message.
    message = (message or "").replace("’", "'")
    scores = {cat: find_keywords(message, kws) for cat, kws in CATEGORY_KEYWORDS.items()}
    best_cat, best_hits = "general_enquiry", []
    for cat, hits in scores.items():  # dict order = tie-break priority
        if hits and cat == "account_privacy":
            best_cat, best_hits = cat, hits
            break
        if len(hits) > len(best_hits):
            best_cat, best_hits = cat, hits
    if not best_hits:
        confidence = "low"
    elif len(best_hits) == 1:
        confidence = "medium"
    else:
        confidence = "high"
    return {
        "category": best_cat,
        "label": CATEGORIES[best_cat],
        "confidence": confidence,
        "matched_keywords": best_hits,
    }
