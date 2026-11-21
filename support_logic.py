"""Compatibility imports for the prototype's original logic entry points."""

from src.activity_logger import LOG_COLUMNS, log_to_csv, log_to_dataframe, make_log_entry
from src.approval_workflow import check_approval
from src.business_config import DEFAULT_BUSINESS_NAME, DEFAULT_POLICIES, POLICY_LABELS, POLICY_NOT_SET
from src.classification import CATEGORIES, classify
from src.response_generator import RULE_BASED_LABEL, rule_based_reply
from src.risk_detection import (
    analyse_enquiry, detect_risks, find_personal_data, find_unsupported_promises, redact_pii, risk_codes,
)
