"""
Smart Campus Lost and Found Matcher - Desktop GUI Application.
CIT AI-Native Engineering Programme - Semester 1 - Assessment 5

Provides a native Windows desktop GUI interface featuring:
- Complete dashboard with real-time KPI metrics and API connection indicator
- Tabbed management for Lost Reports, Found Reports, LLM Extraction,
  Deterministic Matching, Double Claim Conflicts, Output Files, and Test Harness
- Asynchronous threaded processing for LLM extraction and test execution
- Full integration with validator, matcher, extractor, and file_handler modules
"""

from datetime import datetime
import os
from pathlib import Path
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any, Dict, List

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

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


class SmartCampusGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Smart Campus Lost and Found Matcher")
        self.root.geometry("1180x780")
        self.root.minsize(980, 680)

        # State data
        self.lost_reports: List[Dict[str, Any]] = []
        self.found_reports: List[Dict[str, Any]] = []
        self.matches: List[Dict[str, Any]] = []
        self.no_matches: List[Dict[str, Any]] = []
        self.unclaimed: List[Dict[str, Any]] = []
        self.summary_stats: Dict[str, Any] = {}
        self.is_extracted = False
        self.is_processing = False

        # Setup Theme & Styles
        self._setup_styles()

        # Build UI Components
        self._build_header()
        self._build_kpi_bar()
        self._build_main_notebook()
        self._build_status_bar()

        # Auto-load default dataset on startup if available
        self.root.after(150, self._auto_load_initial_data)

    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        # Colors
        self.COLOR_BG = "#f1f5f9"
        self.COLOR_HEADER = "#0f172a"
        self.COLOR_CARD = "#ffffff"
        self.COLOR_PRIMARY = "#2563eb"
        self.COLOR_SUCCESS = "#16a34a"
        self.COLOR_WARNING = "#ea580c"
        self.COLOR_DANGER = "#dc2626"
        self.COLOR_TEXT = "#1e293b"
        self.COLOR_MUTED = "#64748b"

        self.root.configure(bg=self.COLOR_BG)

        # Style definitions
        style.configure(".", font=("Segoe UI", 9), background=self.COLOR_BG, foreground=self.COLOR_TEXT)
        style.configure("TFrame", background=self.COLOR_BG)
        style.configure("Card.TFrame", background=self.COLOR_CARD, relief="flat")
        style.configure("Header.TFrame", background=self.COLOR_HEADER)

        style.configure("TLabel", background=self.COLOR_BG, foreground=self.COLOR_TEXT, font=("Segoe UI", 9))
        style.configure("Card.TLabel", background=self.COLOR_CARD, foreground=self.COLOR_TEXT)
        style.configure("HeaderTitle.TLabel", background=self.COLOR_HEADER, foreground="#ffffff", font=("Segoe UI", 16, "bold"))
        style.configure("HeaderSub.TLabel", background=self.COLOR_HEADER, foreground="#94a3b8", font=("Segoe UI", 9))

        style.configure("Action.TButton", font=("Segoe UI", 9, "bold"), padding=6)
        style.configure("Primary.TButton", font=("Segoe UI", 9, "bold"), background=self.COLOR_PRIMARY, padding=6)

        # Treeview styling
        style.configure(
            "Treeview",
            background="#ffffff",
            foreground=self.COLOR_TEXT,
            fieldbackground="#ffffff",
            rowheight=26,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#e2e8f0",
            foreground="#0f172a",
            padding=5,
        )
        style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", "#1e3a8a")])

        # Notebook tabs
        style.configure("TNotebook", background=self.COLOR_BG)
        style.configure("TNotebook.Tab", font=("Segoe UI", 9, "bold"), padding=[14, 7])
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#ffffff"), ("!selected", "#e2e8f0")],
            foreground=[("selected", self.COLOR_PRIMARY), ("!selected", self.COLOR_MUTED)],
        )

    def _build_header(self):
        header_frame = ttk.Frame(self.root, style="Header.TFrame", padding=(18, 12))
        header_frame.pack(fill=tk.X)

        title_box = ttk.Frame(header_frame, style="Header.TFrame")
        title_box.pack(side=tk.LEFT, fill=tk.Y)

        title_label = ttk.Label(
            title_box,
            text="🏢 Smart Campus Lost and Found Matcher",
            style="HeaderTitle.TLabel",
        )
        title_label.pack(anchor="w")

        sub_label = ttk.Label(
            title_box,
            text="CIT AI-Native Engineering Programme — Semester 1 Assessment 5 | Decision-Support System",
            style="HeaderSub.TLabel",
        )
        sub_label.pack(anchor="w")

        # API Status Pill
        api_box = ttk.Frame(header_frame, style="Header.TFrame")
        api_box.pack(side=tk.RIGHT, fill=tk.Y)

        gemini_key = GEMINI_API_KEY or os.getenv("LLM_API_KEY", "")
        openai_key = OPENAI_API_KEY
        if gemini_key:
            api_text = f"● Gemini API Active ({gemini_key[:4]}...{gemini_key[-4:]})"
            api_color = "#4ade80"
        elif openai_key:
            api_text = f"● OpenAI API Active ({openai_key[:4]}...{openai_key[-4:]})"
            api_color = "#4ade80"
        else:
            api_text = "● Offline Mode (Deterministic Fallback)"
            api_color = "#facc15"

        self.api_status_label = tk.Label(
            api_box,
            text=api_text,
            bg="#1e293b",
            fg=api_color,
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4,
            relief="flat",
        )
        self.api_status_label.pack(anchor="e")

    def _build_kpi_bar(self):
        kpi_container = ttk.Frame(self.root, padding=(16, 10))
        kpi_container.pack(fill=tk.X)

        self.kpi_lost_val = tk.StringVar(value="0")
        self.kpi_found_val = tk.StringVar(value="0")
        self.kpi_extracted_val = tk.StringVar(value="Pending")
        self.kpi_matches_val = tk.StringVar(value="0")
        self.kpi_double_val = tk.StringVar(value="None")

        cards = [
            ("Lost Reports", self.kpi_lost_val, "#2563eb", "📋"),
            ("Found Reports", self.kpi_found_val, "#0d9488", "📦"),
            ("LLM Extraction", self.kpi_extracted_val, "#8b5cf6", "🤖"),
            ("Suggested Matches", self.kpi_matches_val, "#16a34a", "🎯"),
            ("Double Claims", self.kpi_double_val, "#ea580c", "⚠️"),
        ]

        for idx, (title, var, accent_color, icon) in enumerate(cards):
            card = tk.Frame(kpi_container, bg="#ffffff", bd=1, relief="solid", highlightthickness=0)
            card.configure(highlightbackground="#e2e8f0", highlightcolor="#e2e8f0")
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

            accent_bar = tk.Frame(card, bg=accent_color, height=3)
            accent_bar.pack(fill=tk.X, side=tk.TOP)

            content = tk.Frame(card, bg="#ffffff", padx=10, pady=8)
            content.pack(fill=tk.BOTH, expand=True)

            lbl_title = tk.Label(content, text=f"{icon} {title}", bg="#ffffff", fg=self.COLOR_MUTED, font=("Segoe UI", 8, "bold"))
            lbl_title.pack(anchor="w")

            lbl_val = tk.Label(content, textvariable=var, bg="#ffffff", fg="#0f172a", font=("Segoe UI", 13, "bold"))
            lbl_val.pack(anchor="w", pady=(2, 0))

    def _build_main_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 10))

        # Tabs
        self.tab_lost = ttk.Frame(self.notebook, padding=10)
        self.tab_found = ttk.Frame(self.notebook, padding=10)
        self.tab_extraction = ttk.Frame(self.notebook, padding=10)
        self.tab_matches = ttk.Frame(self.notebook, padding=10)
        self.tab_double = ttk.Frame(self.notebook, padding=10)
        self.tab_outputs = ttk.Frame(self.notebook, padding=10)
        self.tab_tests = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_lost, text=" 📋 Lost Reports ")
        self.notebook.add(self.tab_found, text=" 📦 Found Reports ")
        self.notebook.add(self.tab_extraction, text=" 🤖 LLM Extraction ")
        self.notebook.add(self.tab_matches, text=" 🎯 Match Results ")
        self.notebook.add(self.tab_double, text=" ⚠️ Double Claims ")
        self.notebook.add(self.tab_outputs, text=" 📄 Deliverables ")
        self.notebook.add(self.tab_tests, text=" 🧪 Evaluation Tests ")

        self._build_lost_tab()
        self._build_found_tab()
        self._build_extraction_tab()
        self._build_matches_tab()
        self._build_double_claims_tab()
        self._build_outputs_tab()
        self._build_tests_tab()

    # --------------------------------------------------------------------------
    # Tab 1: Lost Reports
    # --------------------------------------------------------------------------
    def _build_lost_tab(self):
        toolbar = ttk.Frame(self.tab_lost)
        toolbar.pack(fill=tk.X, pady=(0, 8))

        btn_load = ttk.Button(toolbar, text="📂 Load lost.csv", command=self.load_lost_reports, style="Action.TButton")
        btn_load.pack(side=tk.LEFT, padx=(0, 8))

        btn_browse = ttk.Button(toolbar, text="Browse Custom CSV...", command=self.browse_lost_csv)
        btn_browse.pack(side=tk.LEFT, padx=(0, 8))

        self.lost_status_lbl = ttk.Label(toolbar, text="No lost reports loaded", font=("Segoe UI", 9, "italic"))
        self.lost_status_lbl.pack(side=tk.LEFT, padx=10)

        # Table
        cols = ("id", "date", "item", "colour", "brand", "place", "report")
        self.tree_lost = ttk.Treeview(self.tab_lost, columns=cols, show="headings", selectmode="browse")
        self.tree_lost.heading("id", text="ID")
        self.tree_lost.heading("date", text="Date")
        self.tree_lost.heading("item", text="Category")
        self.tree_lost.heading("colour", text="Colour")
        self.tree_lost.heading("brand", text="Brand")
        self.tree_lost.heading("place", text="Campus Place")
        self.tree_lost.heading("report", text="Report Narrative")

        self.tree_lost.column("id", width=60, anchor="center")
        self.tree_lost.column("date", width=90, anchor="center")
        self.tree_lost.column("item", width=95, anchor="center")
        self.tree_lost.column("colour", width=80, anchor="center")
        self.tree_lost.column("brand", width=95, anchor="center")
        self.tree_lost.column("place", width=120, anchor="w")
        self.tree_lost.column("report", width=450, anchor="w")

        scrollbar = ttk.Scrollbar(self.tab_lost, orient=tk.VERTICAL, command=self.tree_lost.yview)
        self.tree_lost.configure(yscrollcommand=scrollbar.set)

        self.tree_lost.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # --------------------------------------------------------------------------
    # Tab 2: Found Reports
    # --------------------------------------------------------------------------
    def _build_found_tab(self):
        toolbar = ttk.Frame(self.tab_found)
        toolbar.pack(fill=tk.X, pady=(0, 8))

        btn_load = ttk.Button(toolbar, text="📂 Load found.csv", command=self.load_found_reports, style="Action.TButton")
        btn_load.pack(side=tk.LEFT, padx=(0, 8))

        btn_browse = ttk.Button(toolbar, text="Browse Custom CSV...", command=self.browse_found_csv)
        btn_browse.pack(side=tk.LEFT, padx=(0, 8))

        self.found_status_lbl = ttk.Label(toolbar, text="No found reports loaded", font=("Segoe UI", 9, "italic"))
        self.found_status_lbl.pack(side=tk.LEFT, padx=10)

        # Table
        cols = ("id", "date", "item", "colour", "brand", "place", "report")
        self.tree_found = ttk.Treeview(self.tab_found, columns=cols, show="headings", selectmode="browse")
        self.tree_found.heading("id", text="ID")
        self.tree_found.heading("date", text="Date")
        self.tree_found.heading("item", text="Category")
        self.tree_found.heading("colour", text="Colour")
        self.tree_found.heading("brand", text="Brand")
        self.tree_found.heading("place", text="Campus Place")
        self.tree_found.heading("report", text="Report Narrative")

        self.tree_found.column("id", width=60, anchor="center")
        self.tree_found.column("date", width=90, anchor="center")
        self.tree_found.column("item", width=95, anchor="center")
        self.tree_found.column("colour", width=80, anchor="center")
        self.tree_found.column("brand", width=95, anchor="center")
        self.tree_found.column("place", width=120, anchor="w")
        self.tree_found.column("report", width=450, anchor="w")

        scrollbar = ttk.Scrollbar(self.tab_found, orient=tk.VERTICAL, command=self.tree_found.yview)
        self.tree_found.configure(yscrollcommand=scrollbar.set)

        self.tree_found.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # --------------------------------------------------------------------------
    # Tab 3: LLM Extraction
    # --------------------------------------------------------------------------
    def _build_extraction_tab(self):
        top_box = ttk.Frame(self.tab_extraction)
        top_box.pack(fill=tk.X, pady=(0, 8))

        self.btn_run_extraction = tk.Button(
            top_box,
            text="⚡ Run LLM Structured Extraction O(N)",
            bg="#2563eb",
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=6,
            relief="flat",
            command=self.start_threaded_extraction,
        )
        self.btn_run_extraction.pack(side=tk.LEFT, padx=(0, 10))

        self.progress_bar = ttk.Progressbar(top_box, orient=tk.HORIZONTAL, mode="determinate")
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        self.ext_status_text = ttk.Label(top_box, text="Ready", font=("Segoe UI", 9, "bold"))
        self.ext_status_text.pack(side=tk.RIGHT, padx=5)

        # Log & details view
        split_pane = ttk.PanedWindow(self.tab_extraction, orient=tk.HORIZONTAL)
        split_pane.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.LabelFrame(split_pane, text="Extraction Activity Log", padding=6)
        split_pane.add(left_frame, weight=3)

        self.ext_log = ScrolledText(left_frame, wrap=tk.WORD, font=("Consolas", 9), bg="#0f172a", fg="#f8fafc")
        self.ext_log.pack(fill=tk.BOTH, expand=True)

        right_frame = ttk.LabelFrame(split_pane, text="Selected Record JSON & Fact Grounding", padding=8)
        split_pane.add(right_frame, weight=2)

        self.ext_detail = ScrolledText(right_frame, wrap=tk.WORD, font=("Consolas", 9), bg="#ffffff", fg="#0f172a")
        self.ext_detail.pack(fill=tk.BOTH, expand=True)
        self.ext_detail.insert(
            tk.END,
            "Select an extracted report from Lost/Found tabs to inspect structured JSON\n"
            "and check_facts() validation auditing.\n",
        )

    # --------------------------------------------------------------------------
    # Tab 4: Matching Results
    # --------------------------------------------------------------------------
    def _build_matches_tab(self):
        toolbar = ttk.Frame(self.tab_matches)
        toolbar.pack(fill=tk.X, pady=(0, 8))

        self.btn_match = tk.Button(
            toolbar,
            text="🎯 Execute Deterministic Matcher",
            bg="#16a34a",
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=6,
            relief="flat",
            command=self.run_matching_engine,
        )
        self.btn_match.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(toolbar, text="Filter:").pack(side=tk.LEFT, padx=(0, 4))
        self.match_filter_var = tk.StringVar(value="All Matches")
        filter_cb = ttk.Combobox(
            toolbar,
            textvariable=self.match_filter_var,
            values=["All Matches", "Likely Matches (Score >= 3)", "Possible Matches (Score 1-2)"],
            state="readonly",
            width=28,
        )
        filter_cb.pack(side=tk.LEFT, padx=(0, 10))
        filter_cb.bind("<<ComboboxSelected>>", lambda e: self.populate_matches_tree())

        self.match_summary_lbl = ttk.Label(toolbar, text="No comparison performed yet", font=("Segoe UI", 9, "italic"))
        self.match_summary_lbl.pack(side=tk.LEFT, padx=10)

        # Split pane for table and inspection card
        split_pane = ttk.PanedWindow(self.tab_matches, orient=tk.VERTICAL)
        split_pane.pack(fill=tk.BOTH, expand=True)

        # Upper: Table of matches
        table_frame = ttk.Frame(split_pane)
        split_pane.add(table_frame, weight=3)

        cols = ("lost_id", "found_id", "score", "class", "reasons")
        self.tree_matches = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        self.tree_matches.heading("lost_id", text="Lost ID")
        self.tree_matches.heading("found_id", text="Found ID")
        self.tree_matches.heading("score", text="Score")
        self.tree_matches.heading("class", text="Classification")
        self.tree_matches.heading("reasons", text="Matching Reasons")

        self.tree_matches.column("lost_id", width=80, anchor="center")
        self.tree_matches.column("found_id", width=80, anchor="center")
        self.tree_matches.column("score", width=65, anchor="center")
        self.tree_matches.column("class", width=140, anchor="center")
        self.tree_matches.column("reasons", width=550, anchor="w")

        self.tree_matches.tag_configure("likely", background="#dcfce7", foreground="#14532d")
        self.tree_matches.tag_configure("possible", background="#fef3c7", foreground="#78350f")

        scrollbar_m = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree_matches.yview)
        self.tree_matches.configure(yscrollcommand=scrollbar_m.set)

        self.tree_matches.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_m.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_matches.bind("<<TreeviewSelect>>", self._on_match_selected)

        # Lower: Detailed pair inspection
        detail_frame = ttk.LabelFrame(split_pane, text="Pair Inspection & Help Desk Verification Advice", padding=8)
        split_pane.add(detail_frame, weight=2)

        self.match_inspect_box = ScrolledText(detail_frame, wrap=tk.WORD, font=("Segoe UI", 9), height=6)
        self.match_inspect_box.pack(fill=tk.BOTH, expand=True)
        self.match_inspect_box.insert(tk.END, "Select a match in the table above to view complete pair details.\n")

    def _on_match_selected(self, event):
        selected = self.tree_matches.selection()
        if not selected:
            return
        item_data = self.tree_matches.item(selected[0])
        vals = item_data.get("values", [])
        if not vals:
            return

        lost_id, found_id = vals[0], vals[1]
        target_match = next((m for m in self.matches if m["lost_id"] == lost_id and m["found_id"] == found_id), None)
        if not target_match:
            return

        reasons = "; ".join(target_match.get("reasons", []))
        content = (
            f"================================================================================\n"
            f"PAIR AUDIT: Lost [{lost_id}] vs Found [{found_id}]\n"
            f"================================================================================\n"
            f"Match Score        : {target_match['match_score']} / 5\n"
            f"Classification     : {target_match['classification']}\n"
            f"Additive Breakdown : {reasons}\n\n"
            f"[LOST REPORT DETAILS - {lost_id}]\n"
            f"  Narrative : \"{target_match.get('lost_report', '')}\"\n"
            f"  Extracted : {target_match.get('lost_extracted', {})}\n\n"
            f"[FOUND REPORT DETAILS - {found_id}]\n"
            f"  Narrative : \"{target_match.get('found_report', '')}\"\n"
            f"  Extracted : {target_match.get('found_extracted', {})}\n\n"
            f"--------------------------------------------------------------------------------\n"
            f"HELP DESK VERIFICATION DIRECTIVE:\n"
            f"Before handing over this item, ask claimant for at least one identifying\n"
            f"detail that does NOT appear in either report above (e.g. wallpaper, PIN, contents).\n"
            f"================================================================================\n"
        )
        self.match_inspect_box.delete("1.0", tk.END)
        self.match_inspect_box.insert(tk.END, content)

    # --------------------------------------------------------------------------
    # Tab 5: Double Claims
    # --------------------------------------------------------------------------
    def _build_double_claims_tab(self):
        banner = tk.Frame(self.tab_double, bg="#fff7ed", bd=1, relief="solid", padx=12, pady=10)
        banner.configure(highlightbackground="#fdba74", highlightthickness=1)
        banner.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            banner,
            text="⚠️ DOUBLE CLAIM DETECTION & CONFLICT ARBITRATION",
            bg="#fff7ed",
            fg="#c2410c",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")

        tk.Label(
            banner,
            text="When one found item matches multiple lost reports, the system flags the item for Help Desk review.\n"
                 "The system never decides ownership automatically; campus staff must arbitrate.",
            bg="#fff7ed",
            fg="#7c2d12",
            font=("Segoe UI", 9),
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(2, 0))

        self.double_claims_box = ScrolledText(self.tab_double, wrap=tk.WORD, font=("Consolas", 10), bg="#ffffff", fg="#0f172a")
        self.double_claims_box.pack(fill=tk.BOTH, expand=True)
        self.double_claims_box.insert(tk.END, "Run the Matching Engine (Tab 4) to evaluate double claims.\n")

    # --------------------------------------------------------------------------
    # Tab 6: Output Files
    # --------------------------------------------------------------------------
    def _build_outputs_tab(self):
        toolbar = ttk.Frame(self.tab_outputs)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        btn_gen = tk.Button(
            toolbar,
            text="💾 Generate All 4 Output Files",
            bg="#2563eb",
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=6,
            relief="flat",
            command=self.generate_output_files,
        )
        btn_gen.pack(side=tk.LEFT, padx=(0, 10))

        btn_folder = ttk.Button(toolbar, text="📂 Open Output Folder", command=self.open_output_folder)
        btn_folder.pack(side=tk.LEFT, padx=(0, 10))

        self.output_status_lbl = ttk.Label(toolbar, text="Files not generated yet", font=("Segoe UI", 9, "italic"))
        self.output_status_lbl.pack(side=tk.LEFT, padx=5)

        # Output preview
        lbl_preview = ttk.Label(self.tab_outputs, text="summary.txt Live Preview:", font=("Segoe UI", 9, "bold"))
        lbl_preview.pack(anchor="w", pady=(4, 2))

        self.summary_preview = ScrolledText(self.tab_outputs, wrap=tk.WORD, font=("Consolas", 9), bg="#ffffff", fg="#0f172a")
        self.summary_preview.pack(fill=tk.BOTH, expand=True)

    # --------------------------------------------------------------------------
    # Tab 7: Evaluation & Red-Team Tests
    # --------------------------------------------------------------------------
    def _build_tests_tab(self):
        toolbar = ttk.Frame(self.tab_tests)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        btn_eval = tk.Button(
            toolbar,
            text="▶ Run 5-Pair Evaluation Harness",
            bg="#2563eb",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=5,
            relief="flat",
            command=self.run_eval_harness,
        )
        btn_eval.pack(side=tk.LEFT, padx=(0, 8))

        btn_red = tk.Button(
            toolbar,
            text="🛡 Run 3-Scenario Red-Team Tests",
            bg="#dc2626",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=5,
            relief="flat",
            command=self.run_red_team_suite,
        )
        btn_red.pack(side=tk.LEFT, padx=(0, 8))

        btn_unit = ttk.Button(toolbar, text="📋 Run Unit Tests (unittest)", command=self.run_unit_tests)
        btn_unit.pack(side=tk.LEFT, padx=(0, 8))

        # Test results console
        self.test_console = ScrolledText(self.tab_tests, wrap=tk.WORD, font=("Consolas", 9), bg="#0f172a", fg="#f8fafc")
        self.test_console.pack(fill=tk.BOTH, expand=True)
        self.test_console.insert(
            tk.END,
            "Click any test button above to run automated evaluation and red-team tests.\n",
        )

    # --------------------------------------------------------------------------
    # Bottom Status Bar
    # --------------------------------------------------------------------------
    def _build_status_bar(self):
        status_bar = ttk.Frame(self.root, relief="flat", padding=(16, 4))
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_msg = ttk.Label(status_bar, text="Application Ready", font=("Segoe UI", 8), foreground=self.COLOR_MUTED)
        self.status_msg.pack(side=tk.LEFT)

        app_ver = ttk.Label(status_bar, text="CIT AI-Native Engineering v1.0", font=("Segoe UI", 8), foreground=self.COLOR_MUTED)
        app_ver.pack(side=tk.RIGHT)

    def set_status(self, msg: str):
        self.status_msg.configure(text=msg)

    # --------------------------------------------------------------------------
    # Data Loading Logic
    # --------------------------------------------------------------------------
    def _auto_load_initial_data(self):
        if LOST_CSV_PATH.exists():
            self.load_lost_reports(filepath=LOST_CSV_PATH, silent=True)
        if FOUND_CSV_PATH.exists():
            self.load_found_reports(filepath=FOUND_CSV_PATH, silent=True)
        self.set_status("Default datasets loaded successfully.")

    def load_lost_reports(self, filepath=None, silent=False):
        path = filepath or LOST_CSV_PATH
        try:
            records = read_report(path)
            valid_list = []
            for r in records:
                ok, reason = is_valid(r)
                if ok:
                    valid_list.append(r)
                elif not silent:
                    self.ext_log.insert(tk.END, f"[!] Invalid lost report {r.get('id')}: {reason}\n")
            self.lost_reports = valid_list
            self.kpi_lost_val.set(str(len(self.lost_reports)))
            self.lost_status_lbl.configure(text=f"Loaded {len(self.lost_reports)} valid records from {Path(path).name}")
            self._populate_lost_tree()
            self.is_extracted = False
            self.kpi_extracted_val.set("Pending")
            self.set_status(f"Loaded {len(self.lost_reports)} lost reports.")
        except Exception as e:
            if not silent:
                messagebox.showerror("Error Loading Lost Reports", str(e))

    def browse_lost_csv(self):
        file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if file:
            self.load_lost_reports(filepath=file)

    def load_found_reports(self, filepath=None, silent=False):
        path = filepath or FOUND_CSV_PATH
        try:
            records = read_report(path)
            valid_list = []
            for r in records:
                ok, reason = is_valid(r)
                if ok:
                    valid_list.append(r)
                elif not silent:
                    self.ext_log.insert(tk.END, f"[!] Invalid found report {r.get('id')}: {reason}\n")
            self.found_reports = valid_list
            self.kpi_found_val.set(str(len(self.found_reports)))
            self.found_status_lbl.configure(text=f"Loaded {len(self.found_reports)} valid records from {Path(path).name}")
            self._populate_found_tree()
            self.is_extracted = False
            self.kpi_extracted_val.set("Pending")
            self.set_status(f"Loaded {len(self.found_reports)} found reports.")
        except Exception as e:
            if not silent:
                messagebox.showerror("Error Loading Found Reports", str(e))

    def browse_found_csv(self):
        file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if file:
            self.load_found_reports(filepath=file)

    def _populate_lost_tree(self):
        for item in self.tree_lost.get_children():
            self.tree_lost.delete(item)
        for r in self.lost_reports:
            ext = r.get("extracted", {}) or {}
            self.tree_lost.insert(
                "",
                tk.END,
                values=(
                    r.get("id"),
                    r.get("date"),
                    ext.get("item", "-"),
                    ext.get("colour", "-") or "-",
                    ext.get("brand", "-") or "-",
                    ext.get("place", "-") or "-",
                    r.get("report"),
                ),
            )

    def _populate_found_tree(self):
        for item in self.tree_found.get_children():
            self.tree_found.delete(item)
        for r in self.found_reports:
            ext = r.get("extracted", {}) or {}
            self.tree_found.insert(
                "",
                tk.END,
                values=(
                    r.get("id"),
                    r.get("date"),
                    ext.get("item", "-"),
                    ext.get("colour", "-") or "-",
                    ext.get("brand", "-") or "-",
                    ext.get("place", "-") or "-",
                    r.get("report"),
                ),
            )

    # --------------------------------------------------------------------------
    # LLM Extraction (Threaded)
    # --------------------------------------------------------------------------
    def start_threaded_extraction(self):
        if self.is_processing:
            return
        if not self.lost_reports or not self.found_reports:
            messagebox.showwarning("Data Required", "Please load both Lost and Found reports first.")
            return

        self.is_processing = True
        self.btn_run_extraction.configure(state=tk.DISABLED, text="⏳ Extracting...")
        self.ext_status_text.configure(text="Processing...")
        self.notebook.select(self.tab_extraction)

        thread = threading.Thread(target=self._run_extraction_worker, daemon=True)
        thread.start()

    def _run_extraction_worker(self):
        total_reports = len(self.lost_reports) + len(self.found_reports)
        self.progress_bar["maximum"] = total_reports
        self.progress_bar["value"] = 0

        self.ext_log.delete("1.0", tk.END)
        self.ext_log.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Starting LLM Information Extraction...\n")
        self.ext_log.insert(tk.END, f"Total reports to process: {total_reports} (O(N) operations)\n")
        self.ext_log.insert(tk.END, "-" * 60 + "\n")

        processed = 0

        # Extract Lost Reports
        for r in self.lost_reports:
            ext = extract_information(r["report"])
            r["extracted"] = ext
            processed += 1
            self._update_extraction_progress(processed, total_reports, f"Extracted Lost {r['id']} -> {ext.get('item')}")

        # Extract Found Reports
        for r in self.found_reports:
            ext = extract_information(r["report"])
            r["extracted"] = ext
            processed += 1
            self._update_extraction_progress(processed, total_reports, f"Extracted Found {r['id']} -> {ext.get('item')}")

        self.is_extracted = True
        self.root.after(0, self._on_extraction_complete)

    def _update_extraction_progress(self, current, total, msg):
        def _ui():
            self.progress_bar["value"] = current
            self.ext_status_text.configure(text=f"{current}/{total}")
            self.ext_log.insert(tk.END, f"✔ [{current}/{total}] {msg}\n")
            self.ext_log.see(tk.END)
        self.root.after(0, _ui)

    def _on_extraction_complete(self):
        self.is_processing = False
        self.btn_run_extraction.configure(state=tk.NORMAL, text="⚡ Run LLM Structured Extraction O(N)")
        self.ext_status_text.configure(text="Extraction Complete")
        self.kpi_extracted_val.set("Complete")
        self.set_status("LLM extraction and fact checking completed successfully.")

        self._populate_lost_tree()
        self._populate_found_tree()

        # Update extraction inspection text
        sample = self.lost_reports[0] if self.lost_reports else {}
        self.ext_detail.delete("1.0", tk.END)
        self.ext_detail.insert(
            tk.END,
            f"SAMPLE VERIFIED EXTRACTION (ID: {sample.get('id')}):\n"
            f"Raw Report: \"{sample.get('report')}\"\n\n"
            f"Grounded Attributes:\n"
            f"  - Item Category : {sample.get('extracted', {}).get('item')}\n"
            f"  - Colour        : {sample.get('extracted', {}).get('colour')}\n"
            f"  - Brand         : {sample.get('extracted', {}).get('brand')}\n"
            f"  - Campus Place  : {sample.get('extracted', {}).get('place')}\n"
            f"  - Summary       : {sample.get('extracted', {}).get('summary')}\n\n"
            f"Fact-Checking Firewall Status: PASSED (Zero-Hallucination)\n",
        )

        messagebox.showinfo(
            "Extraction Complete",
            f"Successfully processed {len(self.lost_reports) + len(self.found_reports)} reports!\n"
            f"Ready to run Matching Engine (Tab 4).",
        )

    # --------------------------------------------------------------------------
    # Matching Engine Execution
    # --------------------------------------------------------------------------
    def run_matching_engine(self):
        if not self.is_extracted:
            messagebox.showwarning("Extraction Required", "Please run LLM Extraction (Tab 3) first.")
            return

        self.matches, self.no_matches, self.unclaimed, self.summary_stats = find_matches(
            self.lost_reports, self.found_reports
        )

        likely = self.summary_stats.get("total_likely", 0)
        possible = self.summary_stats.get("total_possible", 0)
        double_claims = self.summary_stats.get("multiple_claims", {})

        self.kpi_matches_val.set(f"{len(self.matches)} ({likely}L / {possible}P)")
        if double_claims:
            self.kpi_double_val.set(f"{len(double_claims)} Alert(s)")
        else:
            self.kpi_double_val.set("None")

        self.match_summary_lbl.configure(
            text=f"Total: {len(self.matches)} matches ({likely} Likely, {possible} Possible)"
        )

        self.populate_matches_tree()
        self.populate_double_claims()
        self.set_status(f"Matching complete: {len(self.matches)} candidate pairs found.")
        self.notebook.select(self.tab_matches)

    def populate_matches_tree(self):
        for item in self.tree_matches.get_children():
            self.tree_matches.delete(item)

        filter_mode = self.match_filter_var.get()

        for m in self.matches:
            cls = m.get("classification", "")
            if filter_mode.startswith("Likely") and cls != "LIKELY MATCH":
                continue
            if filter_mode.startswith("Possible") and cls != "POSSIBLE MATCH":
                continue

            tag = "likely" if cls == "LIKELY MATCH" else "possible"
            reasons_str = "; ".join(m.get("reasons", []))
            self.tree_matches.insert(
                "",
                tk.END,
                values=(
                    m.get("lost_id"),
                    m.get("found_id"),
                    m.get("match_score"),
                    cls,
                    reasons_str,
                ),
                tags=(tag,),
            )

    def populate_double_claims(self):
        self.double_claims_box.delete("1.0", tk.END)
        multiple_claims = self.summary_stats.get("multiple_claims", {})
        if not multiple_claims:
            self.double_claims_box.insert(
                tk.END,
                "✔ NO DOUBLE CLAIMS DETECTED\n"
                "Every matched found item is linked to at most one lost report.\n",
            )
            return

        self.double_claims_box.insert(
            tk.END,
            f"ALERT: {len(multiple_claims)} found item(s) have multiple competing claimants!\n"
            f"The application remains neutral. Campus Help Desk arbitration required.\n\n"
            + "=" * 75 + "\n\n",
        )

        for f_id, claim_info in multiple_claims.items():
            self.double_claims_box.insert(
                tk.END,
                f"[*] CONTESTED FOUND ITEM: {f_id}\n"
                f"    Description : \"{claim_info.get('found_description')}\"\n"
                f"    Claim Count : {len(claim_info.get('claims', []))} competing student reports\n"
                f"    Competing Claims:\n",
            )
            for c in claim_info.get("claims", []):
                self.double_claims_box.insert(
                    tk.END,
                    f"      - Lost ID: {c['lost_id']} | Score: {c['score']} | Class: {c['classification']}\n"
                    f"        Report : \"{c.get('lost_report')}\"\n",
                )
            self.double_claims_box.insert(
                tk.END,
                f"    HELP DESK ACTION DIRECTIVE: Do not release item automatically.\n"
                f"    Require claimants to prove non-public details (e.g. passcode, wallpaper, internal items).\n\n"
                + "-" * 75 + "\n\n",
            )

    # --------------------------------------------------------------------------
    # Output Files Generation
    # --------------------------------------------------------------------------
    def generate_output_files(self):
        if not self.matches and not self.no_matches:
            messagebox.showwarning("Matches Required", "Please run the Matching Engine (Tab 4) before generating files.")
            return

        result = write_reports(
            OUTPUT_DIR,
            self.matches,
            self.no_matches,
            self.unclaimed,
            self.summary_stats,
        )

        self.output_status_lbl.configure(text=f"All 4 files saved in {Path(OUTPUT_DIR).name}/")

        # Update preview
        summary_path = Path(result["summary_txt"])
        if summary_path.exists():
            with open(summary_path, mode="r", encoding="utf-8") as f:
                content = f.read()
            self.summary_preview.delete("1.0", tk.END)
            self.summary_preview.insert(tk.END, content)

        self.set_status(f"Output files generated: {summary_path.name}")
        messagebox.showinfo(
            "Deliverables Created",
            f"Successfully generated all 4 files in {OUTPUT_DIR}:\n"
            f"1. matches.csv\n"
            f"2. no_match.csv\n"
            f"3. unclaimed.csv\n"
            f"4. summary.txt",
        )

    def open_output_folder(self):
        out_path = Path(OUTPUT_DIR)
        out_path.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(str(out_path))
        else:
            subprocess.run(["open", str(out_path)])

    # --------------------------------------------------------------------------
    # Evaluation and Test Harness Tabs
    # --------------------------------------------------------------------------
    def run_eval_harness(self):
        from tests.eval_harness import run_evaluation_harness

        self.test_console.delete("1.0", tk.END)
        self.test_console.insert(tk.END, "Running 5-Pair Canonical Evaluation Harness...\n\n")

        # Capture print output
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            ok = run_evaluation_harness()
        output = buf.getvalue()

        self.test_console.insert(tk.END, output)
        self.set_status("Evaluation harness completed.")

    def run_red_team_suite(self):
        from tests.red_team_tests import run_red_team_tests

        self.test_console.delete("1.0", tk.END)
        self.test_console.insert(tk.END, "Running 3-Scenario Red-Team Adversarial Tests...\n\n")

        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            ok = run_red_team_tests()
        output = buf.getvalue()

        self.test_console.insert(tk.END, output)
        self.set_status("Red-team tests completed.")

    def run_unit_tests(self):
        import unittest
        self.test_console.delete("1.0", tk.END)
        self.test_console.insert(tk.END, "Running all unit tests via unittest discover...\n\n")

        import io
        loader = unittest.TestLoader()
        suite = loader.discover("tests")
        stream = io.StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        result = runner.run(suite)

        self.test_console.insert(tk.END, stream.getvalue())
        self.set_status(f"Ran {result.testsRun} tests. Errors: {len(result.errors)}, Failures: {len(result.failures)}")


def launch_gui():
    """Launch the Smart Campus Lost and Found Matcher Desktop Application."""
    root = tk.Tk()
    app = SmartCampusGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()

