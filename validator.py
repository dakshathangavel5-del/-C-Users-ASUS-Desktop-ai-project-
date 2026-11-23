"""
Validation module for Lost and Found Matcher.
CIT AI-Native Engineering Programme - Semester 1 - Assessment 5

Implements:
- is_valid(): Validates input CSV records (schema, dates, non-empty fields).
- check_facts(): Audits LLM extraction against raw report text (hallucination firewall).
- validate_json_extraction(): Parses and validates structured LLM JSON responses.
"""

from datetime import datetime
import json
import re
from typing import Any, Dict, Optional, Tuple

from config import (
    ALLOWED_COLOURS,
    ALLOWED_ITEMS,
    ALLOWED_PLACES,
    MAX_SUMMARY_WORDS,
)


def is_valid(record: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a single raw report dictionary from CSV.
    Checks:
    - Expected dictionary structure
    - Non-empty 'id'
    - Valid ISO 8601 calendar date (YYYY-MM-DD) via Python datetime
    - Non-empty 'report' text
    """
    if not isinstance(record, dict):
        return False, "Record must be a dictionary."

    record_id = record.get("id")
    if not record_id or not str(record_id).strip():
        return False, "Missing or empty 'id'."

    date_str = record.get("date")
    if not date_str or not str(date_str).strip():
        return False, f"Missing or empty 'date' for ID {record_id}."

    try:
        parsed_date = datetime.strptime(str(date_str).strip(), "%Y-%m-%d").date()
    except ValueError:
        return False, f"Invalid date format for ID {record_id}: '{date_str}'. Expected YYYY-MM-DD."

    report_text = record.get("report")
    if not report_text or not str(report_text).strip():
        return False, f"Missing or empty 'report' narrative for ID {record_id}."

    return True, "Valid"


def validate_json_extraction(raw_response: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Safely parse and validate the JSON string returned by the LLM.
    Handles markdown backticks, unexpected formatting, and missing keys.
    """
    if not raw_response or not raw_response.strip():
        return False, None, "Empty response from LLM."

    text = raw_response.strip()

    # Strip markdown code fencing if present (e.g. ```json ... ```)
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON syntax: {e}"

    if not isinstance(data, dict):
        return False, None, "LLM response JSON is not an object/dictionary."

    required_keys = {"item", "colour", "brand", "place", "summary"}
    missing_keys = required_keys - set(data.keys())
    if missing_keys:
        return False, None, f"JSON missing required key(s): {', '.join(sorted(missing_keys))}"

    return True, data, "Valid JSON"


def _is_token_in_text(token: Optional[str], text: str) -> bool:
    """Helper to check if a token actually appears in the text as a substring/word."""
    if not token or not text:
        return False
    # Case-insensitive search using word boundaries or clean matching
    pattern = r"\b" + re.escape(token.strip().lower()) + r"\b"
    return bool(re.search(pattern, text.lower())) or token.strip().lower() in text.lower()


def clean_mobile_number(phone_raw: Any) -> str:
    """
    Clean and extract the digits from a phone/contact string.
    Removes spaces, hyphens, parentheses, and leading country code (+91 or 91 if followed by 10 digits).
    """
    if not phone_raw:
        return ""
    digits = re.sub(r"\D", "", str(phone_raw).strip())
    # If 12 digits starting with 91, strip country code
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    # If 11 digits starting with 0, strip leading 0
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits


def validate_indian_mobile(phone_raw: Any) -> Tuple[bool, str]:
    """
    Validate student contact numbers against standard 10-digit Indian mobile specifications.
    
    Requirements:
    - Must be non-empty.
    - Must not contain alphabets or invalid special characters.
    - Must resolve to exactly 10 digits.
    - Standard Indian mobile numbers start with 6, 7, 8, or 9.
    
    Returns:
        (is_valid: bool, error_message: str)
    """
    if not phone_raw or not str(phone_raw).strip():
        return False, "Invalid mobile number. Please enter a valid 10-digit number."

    raw_str = str(phone_raw).strip()

    # Reject if contains any alphabetic characters
    if re.search(r"[a-zA-Z]", raw_str):
        return False, "Invalid mobile number. Please enter a valid 10-digit number."

    digits = clean_mobile_number(raw_str)

    # Must be exactly 10 digits
    if len(digits) != 10:
        return False, "Invalid mobile number. Please enter a valid 10-digit number."

    # Indian mobile numbers begin with 6, 7, 8, or 9
    if digits[0] not in ("6", "7", "8", "9"):
        return False, "Invalid mobile number. Please enter a valid 10-digit number."

    return True, ""


def check_facts(extracted: Dict[str, Any], raw_report: str) -> Dict[str, Any]:
    """
    Audit LLM extraction against raw report text (Hallucination Firewall).

    Verifies:
    1. Item category belongs to ALLOWED_ITEMS; otherwise falls back to 'other' or None.
    2. Colour belongs to ALLOWED_COLOURS AND is actually present in raw_report.
       If ungrounded or invalid, resets to None.
    3. Brand is actually present in raw_report.
       If ungrounded or guessed, resets to None (Zero-Hallucination rule).
    4. Place belongs to ALLOWED_PLACES AND is actually present in raw_report.
       If ungrounded or invalid, resets to None.
    5. Summary is enforced to be <= MAX_SUMMARY_WORDS words.
    """
    if not isinstance(extracted, dict):
        return {
            "item": "other",
            "colour": None,
            "brand": None,
            "place": None,
            "summary": "Invalid extraction",
        }

    clean_data = dict(extracted)
    report_text = raw_report or ""

    # 1. Validate Item Category
    raw_item = str(clean_data.get("item", "")).strip().lower() if clean_data.get("item") else None
    if raw_item in ALLOWED_ITEMS:
        clean_data["item"] = raw_item
    else:
        # If item category is unrecognised, classify as 'other'
        clean_data["item"] = "other"

    # 2. Validate Colour (Allowed list + Grounded in raw text)
    raw_colour = str(clean_data.get("colour", "")).strip().lower() if clean_data.get("colour") else None
    if raw_colour:
        # Must be in approved colour taxonomy
        is_allowed = raw_colour in ALLOWED_COLOURS
        # Must actually appear in student's report text
        is_grounded = _is_token_in_text(raw_colour, report_text)
        if is_allowed and is_grounded:
            clean_data["colour"] = raw_colour
        else:
            clean_data["colour"] = None
    else:
        clean_data["colour"] = None

    # 3. Validate Brand (Zero Hallucination: Must appear in raw text)
    raw_brand = str(clean_data.get("brand", "")).strip() if clean_data.get("brand") else None
    if raw_brand:
        if _is_token_in_text(raw_brand, report_text):
            clean_data["brand"] = raw_brand
        else:
            # LLM hallucinated or inferred a brand that was not in the report
            clean_data["brand"] = None
    else:
        clean_data["brand"] = None

    # 4. Validate Place (Allowed list + Grounded in raw text)
    raw_place = str(clean_data.get("place", "")).strip().lower() if clean_data.get("place") else None
    if raw_place:
        is_allowed = raw_place in ALLOWED_PLACES
        is_grounded = _is_token_in_text(raw_place, report_text)
        if is_allowed and is_grounded:
            clean_data["place"] = raw_place
        else:
            clean_data["place"] = None
    else:
        clean_data["place"] = None

    # 5. Validate Summary (Word count constraint)
    raw_summary = str(clean_data.get("summary", "")).strip()
    words = raw_summary.split()
    if len(words) > MAX_SUMMARY_WORDS:
        clean_data["summary"] = " ".join(words[:MAX_SUMMARY_WORDS])
    else:
        clean_data["summary"] = raw_summary

    return clean_data

