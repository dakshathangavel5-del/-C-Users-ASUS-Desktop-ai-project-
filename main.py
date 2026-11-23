"""
Main Console Application for AI-Powered Lost and Found Matcher.
CIT AI-Native Engineering Programme - Semester 1 - Assessment 5

Provides an interactive, professional terminal interface:
1. Load Lost Reports
2. Load Found Reports
3. Extract Information Using LLM
4. Find Matching Items
5. View Matching Results
6. View Multiple Claims
7. Generate Output Files
8. Run Evaluation Tests
9. Exit
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    FOUND_CSV_PATH,
    GEMINI_API_KEY,
    LOST_CSV_PATH,
    OPENAI_API_KEY,
    OUTPUT_DIR,
)
from extractor import extract_information
from file_handler import read_report, write_reports
from matcher import find_matches
from validator import is_valid


# ANSI Color formatting helper
class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    DIM = "\033[2m"


def print_banner():
    banner = f"""
{Style.CYAN}{Style.BOLD}========================================================================
             CIT CAMPUS SERVICES - LOST AND FOUND MATCHER
       AI-Native Engineering Programme - Semester 1 Assessment 5
========================================================================{Style.RESET}"""
    print(banner)


def check_api_status() -> str:
    gemini_key = GEMINI_API_KEY or os.getenv("LLM_API_KEY", "")
    openai_key = OPENAI_API_KEY
    if gemini_key:
        return f"{Style.GREEN}Gemini API Connected ({gemini_key[:4]}...{gemini_key[-4:]}){Style.RESET}"
    if openai_key:
        return f"{Style.GREEN}OpenAI API Connected ({openai_key[:4]}...{openai_key[-4:]}){Style.RESET}"
    return f"{Style.YELLOW}No API Key detected (Operating in Deterministic Fallback Mode){Style.RESET}"


class LostAndFoundApp:
    def __init__(self):
        self.lost_reports: List[Dict[str, Any]] = []
        self.found_reports: List[Dict[str, Any]] = []
        self.matches: List[Dict[str, Any]] = []
        self.no_matches: List[Dict[str, Any]] = []
        self.unclaimed: List[Dict[str, Any]] = []
        self.summary_stats: Dict[str, Any] = {}
        self.extracted_done = False

    def print_status_bar(self):
        print(f"\n{Style.BOLD}SYSTEM STATUS:{Style.RESET}")
        lost_count = len(self.lost_reports)
        found_count = len(self.found_reports)
        matches_count = len(self.matches)
        ext_status = f"{Style.GREEN}Completed{Style.RESET}" if self.extracted_done else f"{Style.YELLOW}Pending{Style.RESET}"

        print(f"  • API Connection : {check_api_status()}")
        print(f"  • Lost Reports   : {lost_count} loaded")
        print(f"  • Found Reports  : {found_count} loaded")
        print(f"  • Extraction     : {ext_status}")
        print(f"  • Matches Found  : {matches_count} pairs identified")
        print(f"{Style.DIM}------------------------------------------------------------------------{Style.RESET}")

    def load_lost_reports(self):
        print(f"\n{Style.BOLD}[1] Loading Lost Reports...{Style.RESET}")
        try:
            records = read_report(LOST_CSV_PATH)
            valid_records = []
            for r in records:
                ok, reason = is_valid(r)
                if ok:
                    valid_records.append(r)
                else:
                    print(f"  {Style.RED}[!] Invalid record {r.get('id')}: {reason}{Style.RESET}")
            self.lost_reports = valid_records
            self.extracted_done = False
            self.matches = []
            print(f"{Style.GREEN}✔ Successfully loaded {len(self.lost_reports)} valid lost reports from {LOST_CSV_PATH.name}{Style.RESET}")
        except Exception as e:
            print(f"{Style.RED}✘ Error loading lost reports: {e}{Style.RESET}")

    def load_found_reports(self):
        print(f"\n{Style.BOLD}[2] Loading Found Reports...{Style.RESET}")
        try:
            records = read_report(FOUND_CSV_PATH)
            valid_records = []
            for r in records:
                ok, reason = is_valid(r)
                if ok:
                    valid_records.append(r)
                else:
                    print(f"  {Style.RED}[!] Invalid record {r.get('id')}: {reason}{Style.RESET}")
            self.found_reports = valid_records
            self.extracted_done = False
            self.matches = []
            print(f"{Style.GREEN}✔ Successfully loaded {len(self.found_reports)} valid found reports from {FOUND_CSV_PATH.name}{Style.RESET}")
        except Exception as e:
            print(f"{Style.RED}✘ Error loading found reports: {e}{Style.RESET}")

    def extract_information(self):
        print(f"\n{Style.BOLD}[3] Extracting Structured Information Using LLM...{Style.RESET}")
        if not self.lost_reports or not self.found_reports:
            print(f"{Style.RED}✘ Please load both lost reports (Option 1) and found reports (Option 2) first.{Style.RESET}")
            return

        total_reports = len(self.lost_reports) + len(self.found_reports)
        print(f"Processing {total_reports} total reports ({len(self.lost_reports)} lost, {len(self.found_reports)} found)...")
        print(f"{Style.DIM}Note: Calling LLM exactly once per report (O(N) operations)...{Style.RESET}\n")

        print("--- Extracting Lost Reports ---")
        for idx, item in enumerate(self.lost_reports, start=1):
            sys.stdout.write(f"\r  [{idx}/{len(self.lost_reports)}] Processing {item['id']}... ")
            sys.stdout.flush()
            extracted = extract_information(item["report"])
            item["extracted"] = extracted
        print(f"\r  {Style.GREEN}✔ All {len(self.lost_reports)} lost reports extracted.{Style.RESET}        ")

        print("--- Extracting Found Reports ---")
        for idx, item in enumerate(self.found_reports, start=1):
            sys.stdout.write(f"\r  [{idx}/{len(self.found_reports)}] Processing {item['id']}... ")
            sys.stdout.flush()
            extracted = extract_information(item["report"])
            item["extracted"] = extracted
        print(f"\r  {Style.GREEN}✔ All {len(self.found_reports)} found reports extracted.{Style.RESET}        ")

        self.extracted_done = True
        print(f"\n{Style.GREEN}✔ Information extraction complete. Ready to find matches.{Style.RESET}")

    def find_matches(self):
        print(f"\n{Style.BOLD}[4] Finding Matching Items...{Style.RESET}")
        if not self.extracted_done:
            print(f"{Style.RED}✘ Please perform Information Extraction (Option 3) first.{Style.RESET}")
            return

        print(f"Executing deterministic pairwise comparison ({len(self.lost_reports)} x {len(self.found_reports)} pairs)...")
        self.matches, self.no_matches, self.unclaimed, self.summary_stats = find_matches(
            self.lost_reports, self.found_reports
        )

        likely = self.summary_stats["total_likely"]
        possible = self.summary_stats["total_possible"]
        double_claims = len(self.summary_stats["multiple_claims"])

        print(f"{Style.GREEN}✔ Comparison complete!{Style.RESET}")
        print(f"  • Total Matches Identified : {len(self.matches)}")
        print(f"  • Likely Matches (Score >=3): {likely}")
        print(f"  • Possible Matches (Score 1-2): {possible}")
        if double_claims > 0:
            print(f"  {Style.YELLOW}• Multiple Claims Detected : {double_claims} found item(s) contested!{Style.RESET}")

    def view_matching_results(self):
        print(f"\n{Style.BOLD}[5] Suggested Matching Results (Best Matches First){Style.RESET}")
        if not self.matches:
            print(f"{Style.YELLOW}No matches currently available. Run Option 4 first.{Style.RESET}")
            return

        print(f"{'Lost ID':<8} {'Found ID':<9} {'Score':<6} {'Classification':<16} {'Matching Reasons'}")
        print("-" * 75)
        for m in self.matches:
            reasons_str = "; ".join(m["reasons"])
            cls_color = Style.GREEN if m["classification"] == "LIKELY MATCH" else Style.YELLOW
            print(f"{m['lost_id']:<8} {m['found_id']:<9} {m['match_score']:<6} {cls_color}{m['classification']:<16}{Style.RESET} {reasons_str}")

    def view_multiple_claims(self):
        print(f"\n{Style.BOLD}[6] Double Claim Detection Audit{Style.RESET}")
        if not self.matches:
            print(f"{Style.YELLOW}No matches available. Run Option 4 first.{Style.RESET}")
            return

        multiple_claims = self.summary_stats.get("multiple_claims", {})
        if not multiple_claims:
            print(f"{Style.GREEN}✔ No double claims detected. Each found item has at most one claimant.{Style.RESET}")
            return

        print(f"{Style.YELLOW}WARNING: {len(multiple_claims)} found item(s) have multiple competing claimants!{Style.RESET}\n")
        for f_id, claim_info in multiple_claims.items():
            print(f"{Style.BOLD}Found Item: {f_id}{Style.RESET}")
            print(f"  Description: \"{claim_info.get('found_description')}\"")
            print(f"  Competing Claims ({len(claim_info['claims'])} claimants):")
            for c in claim_info["claims"]:
                print(f"    - Lost ID: {c['lost_id']} | Score: {c['score']} | Class: {c['classification']}")
                print(f"      Report: \"{c['lost_report']}\"")
            print(f"  {Style.MAGENTA}Directive: Help Desk must request unmentioned private detail before release.{Style.RESET}\n")

    def generate_output_files(self):
        print(f"\n{Style.BOLD}[7] Generating Output Files...{Style.RESET}")
        if not self.matches and not self.no_matches:
            print(f"{Style.RED}✘ Please find matches (Option 4) before generating output files.{Style.RESET}")
            return

        result_paths = write_reports(
            OUTPUT_DIR,
            self.matches,
            self.no_matches,
            self.unclaimed,
            self.summary_stats,
        )

        print(f"{Style.GREEN}✔ All 4 required output files generated successfully in {OUTPUT_DIR}:{Style.RESET}")
        print(f"  1. Matches File    : {result_paths['matches_csv']}")
        print(f"  2. No Match File   : {result_paths['no_match_csv']}")
        print(f"  3. Unclaimed File  : {result_paths['unclaimed_csv']}")
        print(f"  4. Summary File    : {result_paths['summary_txt']}")

    def run_evaluation_tests(self):
        print(f"\n{Style.BOLD}[8] Running Automated Evaluation & Red-Team Tests...{Style.RESET}")
        from tests.eval_harness import run_evaluation_harness
        from tests.red_team_tests import run_red_team_tests

        print("\n--- Running Evaluation Test Harness (5 Canonical Pairs) ---")
        eval_ok = run_evaluation_harness()

        print("\n--- Running Red-Team Tests (3 Adversarial Scenarios) ---")
        red_team_ok = run_red_team_tests()

        if eval_ok and red_team_ok:
            print(f"\n{Style.GREEN}{Style.BOLD}✔ ALL EVALUATION AND RED-TEAM TESTS PASSED!{Style.RESET}")
        else:
            print(f"\n{Style.RED}{Style.BOLD}✘ Some tests failed. Review log output above.{Style.RESET}")

    def run(self):
        print_banner()
        while True:
            self.print_status_bar()
            print(f"{Style.BOLD}MAIN MENU:{Style.RESET}")
            print("1. Load Lost Reports")
            print("2. Load Found Reports")
            print("3. Extract Information Using LLM")
            print("4. Find Matching Items")
            print("5. View Matching Results")
            print("6. View Multiple Claims")
            print("7. Generate Output Files")
            print("8. Run Evaluation Tests")
            print("9. Exit")
            print("====================================")

            choice = input(f"{Style.BOLD}Enter option (1-9): {Style.RESET}").strip()

            if choice == "1":
                self.load_lost_reports()
            elif choice == "2":
                self.load_found_reports()
            elif choice == "3":
                self.extract_information()
            elif choice == "4":
                self.find_matches()
            elif choice == "5":
                self.view_matching_results()
            elif choice == "6":
                self.view_multiple_claims()
            elif choice == "7":
                self.generate_output_files()
            elif choice == "8":
                self.run_evaluation_tests()
            elif choice == "9":
                print(f"\n{Style.CYAN}Exiting Lost and Found Matcher. Goodbye!{Style.RESET}\n")
                break
            else:
                print(f"{Style.RED}Invalid option '{choice}'. Please select 1 through 9.{Style.RESET}")


def run_batch_pipeline():
    """Execute the full end-to-end pipeline automatically for testing and verification."""
    print(f"\n{Style.CYAN}Running Automated Batch Pipeline...{Style.RESET}")
    app = LostAndFoundApp()
    app.load_lost_reports()
    app.load_found_reports()
    app.extract_information()
    app.find_matches()
    app.generate_output_files()
    app.run_evaluation_tests()
    print(f"\n{Style.GREEN}Automated pipeline complete!{Style.RESET}")


if __name__ == "__main__":
    # Check command-line flags
    args = [a.lower() for a in sys.argv[1:]]

    if any(a in ("--batch", "--auto") for a in args):
        run_batch_pipeline()
    elif any(a in ("--web", "--server", "-w") for a in args):
        from app import run_web_server
        run_web_server()
    elif any(a in ("--console", "--cli", "--terminal", "-c") for a in args):
        app = LostAndFoundApp()
        app.run()
    else:
        # Default behavior (e.g., Run Without Debugging): Launch CIT Campus Smart Lost & Found Desktop Application
        try:
            from cit_gui import launch_cit_gui
            launch_cit_gui()
        except Exception as e:
            print(f"[!] Unable to initialize CIT Campus Desktop GUI ({e}). Falling back to Console Mode...")
            app = LostAndFoundApp()
            app.run()


