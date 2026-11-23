"""
File handling module for Lost and Found Matcher.
CIT AI-Native Engineering Programme - Semester 1 - Assessment 5

Implements:
- read_report(): Loads CSV input files.
- write_reports(): Generates the four required deliverables (matches.csv,
  no_match.csv, unclaimed.csv, summary.txt).
"""

import csv
import os
from pathlib import Path
from typing import Any, Dict, List


def read_report(filepath: str | Path) -> List[Dict[str, str]]:
    """
    Read a CSV report file (lost.csv or found.csv) and return records as dictionaries.

    Expected CSV columns: id, date, report.
    Safely handles encoding, missing files, and malformed rows with try/except.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Report file not found: {path}")

    records = []
    try:
        with open(path, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            # Validate required columns
            expected_fields = {"id", "date", "report"}
            if not reader.fieldnames or not expected_fields.issubset(set(reader.fieldnames)):
                raise ValueError(
                    f"File '{path.name}' has invalid header. Expected: 'id,date,report', found: {reader.fieldnames}"
                )

            for row_idx, row in enumerate(reader, start=2):
                record = {
                    "id": row.get("id", "").strip(),
                    "date": row.get("date", "").strip(),
                    "report": row.get("report", "").strip(),
                }
                records.append(record)
    except UnicodeDecodeError as e:
        raise ValueError(f"Encoding error reading {path.name}: {e}") from e

    return records


def write_reports(
    output_dir: str | Path,
    matches: List[Dict[str, Any]],
    no_matches: List[Dict[str, Any]],
    unclaimed: List[Dict[str, Any]],
    summary_stats: Dict[str, Any],
) -> Dict[str, str]:
    """
    Generate the four required deliverables in the specified output directory:
    1. matches.csv   - Every suggested pair ranked by score descending
    2. no_match.csv  - Lost reports without any suggested match
    3. unclaimed.csv - Found items without any suggested match
    4. summary.txt   - High-level audit metrics and multiple-claim conflict warnings
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    matches_path = out_path / "matches.csv"
    no_match_path = out_path / "no_match.csv"
    unclaimed_path = out_path / "unclaimed.csv"
    summary_path = out_path / "summary.txt"

    # 1. matches.csv (Best matches first, sorted by match_score descending)
    sorted_matches = sorted(
        matches,
        key=lambda m: (m.get("match_score", 0), m.get("lost_id", "")),
        reverse=True,
    )
    with open(matches_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["lost_id", "found_id", "match_score", "classification", "matching_reasons"])
        for m in sorted_matches:
            reasons_str = "; ".join(m.get("reasons", [])) if isinstance(m.get("reasons"), list) else str(m.get("reasons", ""))
            writer.writerow([
                m.get("lost_id", ""),
                m.get("found_id", ""),
                m.get("match_score", 0),
                m.get("classification", ""),
                reasons_str,
            ])

    # 2. no_match.csv (Lost reports without match)
    with open(no_match_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["lost_id", "date", "item", "report"])
        for item in no_matches:
            writer.writerow([
                item.get("id", ""),
                item.get("date", ""),
                item.get("extracted", {}).get("item") or item.get("item", "unknown"),
                item.get("report", ""),
            ])

    # 3. unclaimed.csv (Found items without match)
    with open(unclaimed_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["found_id", "date", "item", "report"])
        for item in unclaimed:
            writer.writerow([
                item.get("id", ""),
                item.get("date", ""),
                item.get("extracted", {}).get("item") or item.get("item", "unknown"),
                item.get("report", ""),
            ])

    # 4. summary.txt (Audit metrics and multiple-claim alerts)
    with open(summary_path, mode="w", encoding="utf-8") as f:
        f.write("======================================================================\n")
        f.write("          CAMPUS SERVICES LOST AND FOUND - AUDIT SUMMARY REPORT        \n")
        f.write("======================================================================\n\n")
        f.write(f"Total Lost Reports Processed     : {summary_stats.get('total_lost', len(no_matches))}\n")
        f.write(f"Total Found Reports Processed    : {summary_stats.get('total_found', len(unclaimed))}\n")
        f.write(f"Total Suggested Matches Found    : {len(sorted_matches)}\n")
        f.write(f"  - Total Likely Matches (>=3)   : {summary_stats.get('total_likely', 0)}\n")
        f.write(f"  - Total Possible Matches (1-2) : {summary_stats.get('total_possible', 0)}\n")
        f.write(f"Total Unmatched Lost Reports     : {len(no_matches)}\n")
        f.write(f"Total Unclaimed Found Items      : {len(unclaimed)}\n\n")

        f.write("----------------------------------------------------------------------\n")
        f.write("MULTIPLE-CLAIM ALERTS (DOUBLE CLAIM DETECTION)\n")
        f.write("----------------------------------------------------------------------\n")
        multiple_claims = summary_stats.get("multiple_claims", {})
        if multiple_claims:
            f.write(f"ALERT: {len(multiple_claims)} found item(s) have multiple competing claimants!\n\n")
            for found_id, claim_info in multiple_claims.items():
                f.write(f"[*] Found Item ID: {found_id}\n")
                f.write(f"    Item Description: {claim_info.get('found_description', 'N/A')}\n")
                f.write(f"    Compete Count   : {len(claim_info.get('claims', []))} competing lost report(s)\n")
                f.write("    Competing Claims:\n")
                for claim in claim_info.get("claims", []):
                    f.write(
                        f"      - Lost ID: {claim['lost_id']} | Score: {claim['score']} | "
                        f"Class: {claim['classification']} | Lost Report: \"{claim.get('lost_report', '')}\"\n"
                    )
                f.write("    ACTION REQUIRED BY HELP DESK: Do not release item automatically. "
                        "Require claimants to verify non-public identifying details.\n\n")
        else:
            f.write("No multiple-claim conflicts detected in this batch.\n\n")

        f.write("======================================================================\n")
        f.write("CAMPUS HELP DESK VERIFICATION DIRECTIVE:\n")
        f.write("All suggested matches are recommendations only. Campus Services staff\n")
        f.write("must independently verify physical ownership before releasing any item.\n")
        f.write("======================================================================\n")

    return {
        "matches_csv": str(matches_path),
        "no_match_csv": str(no_match_path),
        "unclaimed_csv": str(unclaimed_path),
        "summary_txt": str(summary_path),
    }

