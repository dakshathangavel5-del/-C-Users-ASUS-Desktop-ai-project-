"""
Deterministic Matching Engine for Lost and Found System.
CIT AI-Native Engineering Programme - Semester 1 - Assessment 5

Implements:
- score_pair(): Mathematical evaluation of pairwise compatibility (Rules 1 to 5).
- find_matches(): Comprehensive nested comparisons, ranking, and double-claim detection.
"""

from datetime import datetime
from typing import Any, Dict, List, Set, Tuple

from config import (
    MAX_DAY_DIFFERENCE,
    SCORE_SAME_BRAND,
    SCORE_SAME_COLOUR,
    SCORE_SAME_PLACE,
    THRESHOLD_LIKELY,
    THRESHOLD_POSSIBLE,
)


def score_pair(lost: Dict[str, Any], found: Dict[str, Any]) -> Tuple[int, str, List[str]]:
    """
    Evaluate pairwise compatibility between a lost report and a found report.

    Rules:
    - Rule 1: Category Match (Both reports must contain same item category).
    - Rule 2: 'other' must never match automatically.
    - Rule 3: Reports more than 30 days apart cannot match.
    - Rule 4: Hard Mismatch:
        * Different colours when both are specified = reject.
        * Different brands when both are specified = reject.
    - Rule 5: Scoring:
        * Same colour = +2
        * Same brand = +2
        * Same place = +1
    - Classification:
        * Score >= 3: LIKELY MATCH
        * Score 1-2: POSSIBLE MATCH
        * Score 0: DO NOT DISPLAY

    Returns:
        (score, classification, reasons_list)
    """
    lost_ext = lost.get("extracted", {}) or {}
    found_ext = found.get("extracted", {}) or {}

    lost_item = lost_ext.get("item")
    found_item = found_ext.get("item")

    # Rule 1: Item Category Match
    if not lost_item or not found_item or lost_item != found_item:
        return 0, "DO NOT DISPLAY", ["Item category mismatch"]

    # Rule 2: 'other' never matches automatically
    if str(lost_item).lower() == "other" or str(found_item).lower() == "other":
        return 0, "DO NOT DISPLAY", ["Category 'other' cannot be matched automatically"]

    # Rule 3: 30-Day Temporal Boundary
    lost_date_str = lost.get("date", "")
    found_date_str = found.get("date", "")
    try:
        lost_date = datetime.strptime(str(lost_date_str).strip(), "%Y-%m-%d").date()
        found_date = datetime.strptime(str(found_date_str).strip(), "%Y-%m-%d").date()
        delta_days = abs((lost_date - found_date).days)
        if delta_days > MAX_DAY_DIFFERENCE:
            return 0, "DO NOT DISPLAY", [f"Dates exceed 30 days apart ({delta_days} days)"]
    except ValueError:
        return 0, "DO NOT DISPLAY", ["Invalid date encountered during comparison"]

    # Rule 4: Hard Mismatches (Colour & Brand)
    lost_colour = lost_ext.get("colour")
    found_colour = found_ext.get("colour")
    if lost_colour and found_colour:
        if str(lost_colour).strip().lower() != str(found_colour).strip().lower():
            return 0, "DO NOT DISPLAY", [
                f"Hard mismatch: Conflicting colours ('{lost_colour}' vs '{found_colour}')"
            ]

    lost_brand = lost_ext.get("brand")
    found_brand = found_ext.get("brand")
    if lost_brand and found_brand:
        if str(lost_brand).strip().lower() != str(found_brand).strip().lower():
            return 0, "DO NOT DISPLAY", [
                f"Hard mismatch: Conflicting brands ('{lost_brand}' vs '{found_brand}')"
            ]

    # Rule 5: Additive Scoring
    score = 0
    reasons = [f"Same item category: {lost_item}"]

    if lost_colour and found_colour and str(lost_colour).strip().lower() == str(found_colour).strip().lower():
        score += SCORE_SAME_COLOUR
        reasons.append(f"Matching colour: {lost_colour} (+{SCORE_SAME_COLOUR})")

    if lost_brand and found_brand and str(lost_brand).strip().lower() == str(found_brand).strip().lower():
        score += SCORE_SAME_BRAND
        reasons.append(f"Matching brand: {lost_brand} (+{SCORE_SAME_BRAND})")

    lost_place = lost_ext.get("place")
    found_place = found_ext.get("place")
    if lost_place and found_place and str(lost_place).strip().lower() == str(found_place).strip().lower():
        score += SCORE_SAME_PLACE
        reasons.append(f"Matching campus place: {lost_place} (+{SCORE_SAME_PLACE})")

    # Classification
    if score >= THRESHOLD_LIKELY:
        classification = "LIKELY MATCH"
    elif score >= THRESHOLD_POSSIBLE:
        classification = "POSSIBLE MATCH"
    else:
        classification = "DO NOT DISPLAY"

    return score, classification, reasons


def find_matches(
    lost_list: List[Dict[str, Any]],
    found_list: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Compare all lost reports against all found reports using nested loops.

    Returns:
    - matches: list of suggested match dictionaries (Score >= 1), sorted by score descending.
    - no_matches: list of lost reports with 0 suggested matches.
    - unclaimed: list of found reports with 0 suggested matches.
    - summary_stats: dictionary containing aggregate metrics and double-claim alerts.
    """
    matches: List[Dict[str, Any]] = []

    # Nested loop comparison: Compare every lost report against every found report
    for lost in lost_list:
        for found in found_list:
            score, classification, reasons = score_pair(lost, found)
            if score >= THRESHOLD_POSSIBLE and classification != "DO NOT DISPLAY":
                matches.append({
                    "lost_id": lost.get("id"),
                    "found_id": found.get("id"),
                    "match_score": score,
                    "classification": classification,
                    "reasons": reasons,
                    "lost_report": lost.get("report"),
                    "found_report": found.get("report"),
                    "lost_extracted": lost.get("extracted"),
                    "found_extracted": found.get("extracted"),
                })

    # Sort matches descending by score, then by lost_id
    matches.sort(key=lambda m: (m["match_score"], m["lost_id"]), reverse=True)

    # Track matched IDs
    matched_lost_ids: Set[str] = {m["lost_id"] for m in matches}
    matched_found_ids: Set[str] = {m["found_id"] for m in matches}

    # Separate unmatched lists
    no_matches = [lost for lost in lost_list if lost.get("id") not in matched_lost_ids]
    unclaimed = [found for found in found_list if found.get("id") not in matched_found_ids]

    # Double claim detection: Group matches by found_id
    found_lookup = {f["id"]: f for f in found_list}
    claims_by_found: Dict[str, List[Dict[str, Any]]] = {}
    for m in matches:
        f_id = m["found_id"]
        if f_id not in claims_by_found:
            claims_by_found[f_id] = []
        claims_by_found[f_id].append({
            "lost_id": m["lost_id"],
            "score": m["match_score"],
            "classification": m["classification"],
            "lost_report": m["lost_report"],
        })

    # Identify found items with multiple competing lost claims
    multiple_claims: Dict[str, Dict[str, Any]] = {}
    for f_id, claim_records in claims_by_found.items():
        if len(claim_records) > 1:
            found_item_obj = found_lookup.get(f_id, {})
            multiple_claims[f_id] = {
                "found_id": f_id,
                "found_description": found_item_obj.get("report", ""),
                "claims": sorted(claim_records, key=lambda c: c["score"], reverse=True),
            }

    # Compile Summary Statistics
    total_likely = sum(1 for m in matches if m["classification"] == "LIKELY MATCH")
    total_possible = sum(1 for m in matches if m["classification"] == "POSSIBLE MATCH")

    summary_stats = {
        "total_lost": len(lost_list),
        "total_found": len(found_list),
        "total_matches": len(matches),
        "total_likely": total_likely,
        "total_possible": total_possible,
        "total_unmatched_lost": len(no_matches),
        "total_unclaimed_found": len(unclaimed),
        "multiple_claims": multiple_claims,
    }

    return matches, no_matches, unclaimed, summary_stats

