"""Fictional defaults and approved policy topics."""

DEFAULT_BUSINESS_NAME = "Willow Lane Crafts"  # fictional business

# ---------------------------------------------------------------------------
# Business policies (fictional defaults, editable in the app for the session)
# ---------------------------------------------------------------------------

POLICY_LABELS = {
    "refunds": "Refunds and returns",
    "delivery": "Delivery",
    "opening_hours": "Opening hours",
    "privacy": "Customer data / privacy",
    "warranty": "Warranty",
    "international_shipping": "International shipping",
    "discounts": "Discounts and vouchers",
    "wholesale": "Wholesale / bulk orders",
}

DEFAULT_POLICIES = {
    "refunds": (
        "Unused items can be returned within 14 days of delivery for a refund. "
        "Every refund is reviewed by a member of staff."
    ),
    "delivery": (
        "UK orders are usually dispatched within 2 working days. "
        "Tracking details are emailed after dispatch."
    ),
    "opening_hours": "Our shop is open Monday to Saturday, 9am to 5pm, and closed on Sundays.",
    "privacy": (
        "We only use customer data to process orders. Requests to access or delete "
        "data are handled by the owner after an identity check."
    ),
    # Deliberately left empty: the business has not written these policies yet.
    "warranty": "",
    "international_shipping": "",
    "discounts": "",
    "wholesale": "",
}

# Words in a customer message that point to a policy topic.
POLICY_TOPIC_KEYWORDS = {
    "refunds": ["refund", "return", "money back"],
    "delivery": ["delivery", "dispatch", "tracking"],
    "opening_hours": [
        "opening hours", "shop hours", "open", "closed", "opening time", "closing time",
        "shop close", "store close", "do you close", "are you open",
    ],
    "privacy": ["personal data", "personal information", "my data", "delete my account", "gdpr"],
    "warranty": ["warranty", "guarantee"],
    "international_shipping": ["international", "internationally", "overseas", "abroad", "outside the uk"],
    "discounts": ["discount", "coupon", "voucher", "promo code"],
    "wholesale": ["wholesale", "bulk order", "bulk"],
}

POLICY_NOT_SET = "[POLICY NOT SET - write this part yourself]"
