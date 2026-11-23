"""
Configuration module for Lost and Found Matcher.
CIT AI-Native Engineering Programme - Semester 1 - Assessment 5

Contains all configurable taxonomies, matching scores, file paths, and LLM API settings.
All unspecified lists are kept configurable here for faculty-approved values.
"""

import os
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# File paths
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
PROMPTS_DIR = BASE_DIR / "prompts"

LOST_CSV_PATH = DATA_DIR / "lost.csv"
FOUND_CSV_PATH = DATA_DIR / "found.csv"

MATCHES_CSV_PATH = OUTPUT_DIR / "matches.csv"
NO_MATCH_CSV_PATH = OUTPUT_DIR / "no_match.csv"
UNCLAIMED_CSV_PATH = OUTPUT_DIR / "unclaimed.csv"
SUMMARY_TXT_PATH = OUTPUT_DIR / "summary.txt"
SYSTEM_PROMPT_PATH = PROMPTS_DIR / "system_prompt.txt"

# --------------------------------------------------------------------------
# Configurable Campus Taxonomy (Subject to Faculty Confirmation)
# --------------------------------------------------------------------------

ALLOWED_ITEMS = {
    "phone",
    "laptop",
    "headphones",
    "bottle",
    "wallet",
    "keys",
    "bag",
    "jacket",
    "glasses",
    "id_card",
    "umbrella",
    "other",
}

ALLOWED_COLOURS = {
    "black",
    "white",
    "blue",
    "red",
    "green",
    "silver",
    "grey",
    "gray",
    "yellow",
    "brown",
    "gold",
    "pink",
    "purple",
    "orange",
}

ALLOWED_PLACES = {
    "library",
    "canteen",
    "sports centre",
    "science building",
    "main building",
    "computer lab",
    "lecture hall a",
    "lecture hall b",
    "bus stop",
    "quad",
    "student union",
    "cafeteria",
}

# --------------------------------------------------------------------------
# Matching Engine Scoring Parameters (Rules from Specification)
# --------------------------------------------------------------------------

SCORE_SAME_COLOUR = 2
SCORE_SAME_BRAND = 2
SCORE_SAME_PLACE = 1

THRESHOLD_LIKELY = 3      # Score >= 3: LIKELY MATCH
THRESHOLD_POSSIBLE = 1    # Score 1-2: POSSIBLE MATCH
                          # Score 0: DO NOT DISPLAY

MAX_DAY_DIFFERENCE = 30   # Rule 3: Reports > 30 days apart cannot match

# --------------------------------------------------------------------------
# LLM Integration Settings
# --------------------------------------------------------------------------

# Supported providers: "gemini", "openai", "openrouter", "mock"
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("LLM_API_KEY", ""))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")

# Maximum words for summary rule
MAX_SUMMARY_WORDS = 8

