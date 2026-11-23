"""
LLM Information Extraction Module.
CIT AI-Native Engineering Programme - Semester 1 - Assessment 5

Extracts structured JSON from raw student lost/found reports.
Features:
- Configurable API integration (Gemini, OpenAI, or Week 12 endpoint)
- Robust try/except error handling (never crashes on API/JSON failure)
- Fallback local extraction mode for offline demonstrations and grading
- Fact-checking via validator.check_facts()
"""

import json
import logging
import os
import re
from typing import Any, Dict, Optional, Tuple
import requests

from config import (
    ALLOWED_COLOURS,
    ALLOWED_ITEMS,
    ALLOWED_PLACES,
    GEMINI_API_KEY,
    LLM_MODEL,
    OPENAI_API_KEY,
    SYSTEM_PROMPT_PATH,
)
from validator import check_facts, validate_json_extraction

logger = logging.getLogger(__name__)


def load_system_prompt() -> str:
    """Load the 5-role structured system prompt from disk."""
    if SYSTEM_PROMPT_PATH.exists():
        with open(SYSTEM_PROMPT_PATH, mode="r", encoding="utf-8") as f:
            return f.read()
    return (
        "You are an extraction specialist. Extract item, colour, brand, place, "
        "and summary (<= 8 words) as JSON. Return null for missing fields."
    )


def _call_gemini_api(report_text: str, api_key: str) -> Tuple[bool, str]:
    """Call Google Generative Language API (Gemini)."""
    system_instruction = load_system_prompt()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{LLM_MODEL}:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"Extract structured information from this incident report:\n\"{report_text}\""}],
            }
        ],
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0,
        },
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            res_json = response.json()
            candidates = res_json.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return True, parts[0].get("text", "")
            return False, "Empty candidate content from Gemini."
        return False, f"Gemini API HTTP Error {response.status_code}: {response.text}"
    except Exception as e:
        return False, f"Gemini API request error: {e}"


def _call_openai_api(report_text: str, api_key: str) -> Tuple[bool, str]:
    """Call OpenAI or OpenAI-compatible Week 12 API endpoint."""
    system_instruction = load_system_prompt()
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    url = f"{base_url.rstrip('/')}/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Extract structured information from this incident report:\n\"{report_text}\""},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            res_json = response.json()
            choices = res_json.get("choices", [])
            if choices:
                return True, choices[0].get("message", {}).get("content", "")
            return False, "Empty choices from OpenAI endpoint."
        return False, f"OpenAI API HTTP Error {response.status_code}: {response.text}"
    except Exception as e:
        return False, f"OpenAI API request error: {e}"


def _deterministic_fallback_extractor(report_text: str) -> Dict[str, Any]:
    """
    Deterministic rule-based extractor used when offline, in automated test harnesses,
    or when API keys are not supplied. Adheres strictly to the taxonomy and zero-guessing rubric.
    """
    text_lower = report_text.lower()

    # 1. Item Category Extraction with common campus synonyms
    item = "other"
    item_synonyms = {
        "phone": ["phone", "iphone", "samsung", "smartphone", "mobile", "galaxy"],
        "laptop": ["laptop", "macbook", "thinkpad", "dell", "notebook"],
        "headphones": ["headphones", "headphone", "airpods", "earbuds", "earphones", "sony"],
        "bottle": ["bottle", "flask", "hydro flask", "water bottle"],
        "wallet": ["wallet", "purse", "billfold"],
        "keys": ["keys", "key", "keychain", "lanyard"],
        "bag": ["bag", "backpack", "rucksack", "tote"],
        "jacket": ["jacket", "coat", "hoodie", "windbreaker"],
        "glasses": ["glasses", "spectacles", "sunglasses", "ray-ban"],
        "id_card": ["id card", "id", "student card", "campus pass"],
        "umbrella": ["umbrella", "parasol"],
    }

    matched_item = None
    for cat, synonyms in item_synonyms.items():
        for syn in synonyms:
            if re.search(r"\b" + re.escape(syn) + r"\b", text_lower):
                matched_item = cat
                break
        if matched_item:
            break
    if matched_item and matched_item in ALLOWED_ITEMS:
        item = matched_item

    # 2. Colour Extraction (must be in ALLOWED_COLOURS and explicitly in report)
    colour = None
    for c in ALLOWED_COLOURS:
        if re.search(r"\b" + re.escape(c) + r"\b", text_lower):
            colour = c
            break

    # 3. Brand Extraction (known brands only if present in text)
    known_brands = [
        "Samsung", "Apple", "Sony", "Hydro Flask", "Fossil", "Nike",
        "Patagonia", "Ray-Ban", "Dell", "HP", "Lenovo", "Asus", "Bose"
    ]
    brand = None
    for b in known_brands:
        if re.search(r"\b" + re.escape(b) + r"\b", report_text, re.IGNORECASE):
            brand = b
            break

    # 4. Place Extraction (must be in ALLOWED_PLACES and in report)
    place = None
    for p in ALLOWED_PLACES:
        if re.search(r"\b" + re.escape(p) + r"\b", text_lower):
            place = p
            break

    # 5. Summary (<= 8 words, no names)
    summary_parts = []
    if colour:
        summary_parts.append(colour.capitalize())
    if brand:
        summary_parts.append(brand)
    summary_parts.append(item.capitalize())
    if place:
        summary_parts.append(f"at {place}")
    summary = " ".join(summary_parts)
    words = summary.split()
    if len(words) > 8:
        summary = " ".join(words[:8])
    if not summary:
        summary = f"{item.capitalize()} report"

    return {
        "item": item,
        "colour": colour,
        "brand": brand,
        "place": place,
        "summary": summary,
    }


def extract_information(report_text: str, force_offline: bool = False) -> Dict[str, Any]:
    """
    Extract structured lost/found attributes from a report narrative.
    Calls LLM API once per report; verifies and sanitizes facts via check_facts().
    Safely falls back to local deterministic extractor if no API key is provided
    or if API connection fails, guaranteeing the application never crashes.
    """
    raw_json_str = None
    success = False

    # Check for live API availability
    gemini_key = GEMINI_API_KEY or os.getenv("LLM_API_KEY", "")
    openai_key = OPENAI_API_KEY

    if not force_offline:
        if gemini_key:
            success, raw_json_str = _call_gemini_api(report_text, gemini_key)
        elif openai_key:
            success, raw_json_str = _call_openai_api(report_text, openai_key)

    if success and raw_json_str:
        is_valid_json, parsed_data, err_msg = validate_json_extraction(raw_json_str)
        if is_valid_json and parsed_data:
            # Audit facts against raw report to eliminate hallucinations
            return check_facts(parsed_data, report_text)
        else:
            logger.warning(f"LLM generated invalid JSON: {err_msg}. Activating fallback.")

    # Fallback mode (offline, test harness, or API error)
    fallback_data = _deterministic_fallback_extractor(report_text)
    return check_facts(fallback_data, report_text)

