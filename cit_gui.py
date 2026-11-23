"""
CIT CAMPUS – SMART LOST AND FOUND DESKTOP APPLICATION
Clean, professional, fully functional Windows desktop application.
Uses Python, PySide6, SQLite, LLM extraction, and deterministic AI matching.
"""

from datetime import datetime
import os
from pathlib import Path
import shutil
import sys
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QDate, QSize, Qt
from PySide6.QtGui import QColor, QCursor, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import ALLOWED_COLOURS, ALLOWED_ITEMS, ALLOWED_PLACES, DATA_DIR
import database
from validator import clean_mobile_number, validate_indian_mobile

# Photos directory
PHOTOS_DIR = DATA_DIR / "photos"
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------------------
# Professional Green and White Modern Theme (QSS)
# ------------------------------------------------------------------------------
CIT_THEME_QSS = """
/* Global Window */
QMainWindow, QWidget {
    background-color: #f8fafc;
    color: #0f172a;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

/* Sidebar */
#sidebarFrame {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #064e3b, stop:1 #022c22);
    border: none;
    border-right: 1px solid #047857;
    min-width: 240px;
    max-width: 240px;
}

#portalTitle {
    color: #ffffff;
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 0.5px;
}

#portalSub {
    color: #6ee7b7;
    font-size: 12px;
    font-weight: 600;
}

/* Navigation Buttons */
QPushButton.navBtn {
    background-color: transparent;
    color: #ecfdf5;
    text-align: left;
    padding: 11px 18px;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    margin: 3px 12px;
}

QPushButton.navBtn:hover {
    background-color: #047857;
    color: #ffffff;
}

QPushButton.navBtn:checked {
    background-color: #10b981;
    color: #ffffff;
    font-weight: 700;
}

/* Top Header Bar */
#topHeaderBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 14px 30px;
}

#headerTitle {
    font-size: 21px;
    font-weight: 800;
    color: #064e3b;
    letter-spacing: 0.5px;
}

#headerSubtitle {
    font-size: 13px;
    font-weight: 600;
    color: #10b981;
}

/* Clickable Dashboard Statistic Cards */
QFrame.statCard {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px;
}

QFrame.statCard:hover {
    border: 2px solid #10b981;
    background-color: #f0fdf4;
}

QLabel.statTitle {
    color: #64748b;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

QLabel.statValue {
    color: #064e3b;
    font-size: 30px;
    font-weight: 800;
    margin-top: 4px;
}

QLabel.statHint {
    color: #059669;
    font-size: 11px;
    font-weight: 600;
    margin-top: 2px;
}

/* Large Reporting Action Options */
QFrame.reportOptionCard {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 12px;
    padding: 22px;
}

QFrame.reportOptionCard:hover {
    border: 2px solid #10b981;
    background-color: #f0fdf4;
}

/* Standard Buttons */
QPushButton.submitBtn {
    background-color: #2563eb;
    color: #ffffff;
    border: 1px solid #1d4ed8;
    border-radius: 8px;
    padding: 12px 28px;
    font-weight: 800;
    font-size: 14px;
    letter-spacing: 0.4px;
}

QPushButton.submitBtn:hover {
    background-color: #1d4ed8;
    border-color: #1e40af;
}

QPushButton.submitBtn:pressed {
    background-color: #1e40af;
}

QPushButton.submitBtn:disabled {
    background-color: #93c5fd;
    border-color: #bfdbfe;
    color: #eff6ff;
}

QPushButton.primaryBtn {
    background-color: #16a34a;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 700;
    font-size: 13px;
}

QPushButton.primaryBtn:hover {
    background-color: #15803d;
}

QPushButton.secondaryBtn {
    background-color: #ffffff;
    color: #064e3b;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton.secondaryBtn:hover {
    background-color: #f1f5f9;
    border-color: #94a3b8;
}

/* Tables */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    gridline-color: #f1f5f9;
    selection-background-color: #dcfce7;
    selection-color: #065f46;
    font-size: 12px;
}

QHeaderView::section {
    background-color: #f8fafc;
    color: #064e3b;
    font-weight: 700;
    font-size: 12px;
    border: none;
    border-bottom: 2px solid #e2e8f0;
    padding: 10px 8px;
}

/* Forms */
QLineEdit, QComboBox, QDateEdit, QTextEdit {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
    border: 2px solid #10b981;
}

/* Badges */
QLabel.badgeLikely {
    background-color: #dcfce7;
    color: #15803d;
    font-weight: 700;
    border-radius: 6px;
    padding: 4px 8px;
}

QLabel.badgePossible {
    background-color: #fef3c7;
    color: #b45309;
    font-weight: 700;
    border-radius: 6px;
    padding: 4px 8px;
}

QLabel.badgeVerified {
    background-color: #16a34a;
    color: #ffffff;
    font-weight: 700;
    border-radius: 6px;
    padding: 4px 8px;
}

QLabel.badgeConflict {
    background-color: #fee2e2;
    color: #b91c1c;
    font-weight: 700;
    border-radius: 6px;
    padding: 4px 8px;
    border: 1px solid #fca5a5;
}

QLabel.badgeResolved {
    background-color: #dcfce7;
    color: #15803d;
    font-weight: 700;
    border-radius: 6px;
    padding: 4px 8px;
    border: 1px solid #86efac;
}
"""


# ------------------------------------------------------------------------------
# Clickable Statistic Card Widget
# ------------------------------------------------------------------------------
class ClickableStatCard(QFrame):
    def __init__(self, title: str, value_text: str, hint_text: str, on_click_callback):
        super().__init__()
        self.setProperty("class", "statCard")
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.callback = on_click_callback

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setProperty("class", "statTitle")
        layout.addWidget(lbl_title)

        self.lbl_value = QLabel(value_text)
        self.lbl_value.setProperty("class", "statValue")
        layout.addWidget(self.lbl_value)

        self.lbl_hint = QLabel(hint_text)
        self.lbl_hint.setProperty("class", "statHint")
        layout.addWidget(self.lbl_hint)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.callback:
            self.callback()
        super().mousePressEvent(event)

    def set_value(self, val: str):
        self.lbl_value.setText(val)


class DoubleClaimStatCard(QFrame):
    def __init__(self, on_click_callback):
        super().__init__()
        self.setProperty("class", "statCard")
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.callback = on_click_callback

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(3)

        lbl_title = QLabel("⚠️  DOUBLE CLAIMS")
        lbl_title.setProperty("class", "statTitle")
        layout.addWidget(lbl_title)

        self.lbl_value = QLabel("0 CONFLICTS")
        self.lbl_value.setStyleSheet("color: #b45309; font-size: 24px; font-weight: 800; margin-top: 4px;")
        layout.addWidget(self.lbl_value)

        self.lbl_sub = QLabel("Pending: 0  |  Resolved: 0")
        self.lbl_sub.setStyleSheet("color: #059669; font-size: 11px; font-weight: 700; margin-top: 2px;")
        layout.addWidget(self.lbl_sub)

        lbl_hint = QLabel("Click to arbitrate conflicts →")
        lbl_hint.setProperty("class", "statHint")
        layout.addWidget(lbl_hint)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.callback:
            self.callback()
        super().mousePressEvent(event)

    def set_data(self, total: int, pending: int, resolved: int):
        self.lbl_value.setText(f"{total} CONFLICT{'S' if total != 1 else ''}")
        if pending > 0:
            self.lbl_value.setStyleSheet("color: #dc2626; font-size: 24px; font-weight: 800; margin-top: 4px;")
        else:
            self.lbl_value.setStyleSheet("color: #059669; font-size: 24px; font-weight: 800; margin-top: 4px;")
        self.lbl_sub.setText(f"Pending: {pending}  |  Resolved: {resolved}")


# ------------------------------------------------------------------------------
# Main Application Window (CIT CAMPUS)
# ------------------------------------------------------------------------------
class CITCampusMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CIT CAMPUS – Smart Lost & Found Portal")
        self.resize(1260, 820)
        self.setMinimumSize(1040, 680)

        # Initialize database and execute pairwise matching
        database.init_database()
        database.run_database_matching()

        # Uploaded photo paths
        self.selected_lost_photo: Optional[str] = None
        self.selected_found_photo: Optional[str] = None
        self.selected_claim_photo: Optional[str] = None

        # Apply Global Styling
        self.setStyleSheet(CIT_THEME_QSS)

        # Build Main Frame
        self._build_ui()

        # Populate all dashboard data and tables
        self.refresh_all_data()

    def _build_ui(self):
        root_widget = QWidget()
        self.setCentralWidget(root_widget)

        root_layout = QHBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Left Sidebar (7 Simple Options)
        self._build_sidebar(root_layout)

        # 2. Main Area (Top Header + Stacked Pages)
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._build_header(main_layout)

        self.pages_stack = QStackedWidget()
        main_layout.addWidget(self.pages_stack, 1)

        # Build 10 Pages
        self.page_dashboard = self._build_dashboard_page()           # 0
        self.page_report_lost = self._build_report_lost_page()       # 1
        self.page_report_found = self._build_report_found_page()     # 2
        self.page_lodge_claim = self._build_lodge_claim_page()       # 3
        self.page_lost_items = self._build_lost_items_page()         # 4
        self.page_found_items = self._build_found_items_page()       # 5
        self.page_double_claims = self._build_double_claims_page()   # 6
        self.page_ai_matches = self._build_ai_matches_page()         # 7
        self.page_successful = self._build_successful_matches_page() # 8
        self.page_notifications = self._build_notifications_page()   # 9

        self.pages_stack.addWidget(self.page_dashboard)
        self.pages_stack.addWidget(self.page_report_lost)
        self.pages_stack.addWidget(self.page_report_found)
        self.pages_stack.addWidget(self.page_lodge_claim)
        self.pages_stack.addWidget(self.page_lost_items)
        self.pages_stack.addWidget(self.page_found_items)
        self.pages_stack.addWidget(self.page_double_claims)
        self.pages_stack.addWidget(self.page_ai_matches)
        self.pages_stack.addWidget(self.page_successful)
        self.pages_stack.addWidget(self.page_notifications)

        root_layout.addWidget(main_container, 1)

    # --------------------------------------------------------------------------
    # Left Sidebar Navigation (9 Simple Options)
    # --------------------------------------------------------------------------
    def _build_sidebar(self, parent_layout: QHBoxLayout):
        sidebar = QFrame()
        sidebar.setObjectName("sidebarFrame")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(6)

        # Header Title in Sidebar
        title_box = QWidget()
        tb_l = QVBoxLayout(title_box)
        tb_l.setContentsMargins(10, 0, 10, 14)
        tb_l.setSpacing(2)

        lbl_top = QLabel("CIT CAMPUS")
        lbl_top.setObjectName("portalTitle")
        tb_l.addWidget(lbl_top)

        lbl_sub = QLabel("Smart Lost & Found")
        lbl_sub.setObjectName("portalSub")
        tb_l.addWidget(lbl_sub)
        layout.addWidget(title_box)

        # 10 Navigation Options
        self.sidebar_buttons: List[QPushButton] = []
        nav_items = [
            ("📊  Dashboard", 0),
            ("➕  Report Lost Item", 1),
            ("📥  Report Found Item", 2),
            ("⚖️  Lodge Claim", 3),
            ("📋  My Lost Items", 4),
            ("📦  My Found Items", 5),
            ("⚠️  Double Claims", 6),
            ("🤖  AI Matches", 7),
            ("✔️  Successful Matches", 8),
            ("🔔  Notifications", 9),
        ]

        for label, idx in nav_items:
            btn = QPushButton(label)
            btn.setProperty("class", "navBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, target=idx: self.navigate_to(target))
            layout.addWidget(btn)
            self.sidebar_buttons.append(btn)

        layout.addStretch()

        # Sidebar Footer
        lbl_foot = QLabel("CIT Campus Services\nDecision Support System")
        lbl_foot.setStyleSheet("color: #a7f3d0; font-size: 11px; padding: 10px;")
        lbl_foot.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_foot)

        parent_layout.addWidget(sidebar)

        if self.sidebar_buttons:
            self.sidebar_buttons[0].setChecked(True)

    def navigate_to(self, page_index: int):
        """Navigate to specific stacked page and synchronize sidebar button state."""
        self.pages_stack.setCurrentIndex(page_index)
        for i, btn in enumerate(self.sidebar_buttons):
            btn.setChecked(i == page_index)

        # Update Header Subtitle
        subtitles = [
            "Campus property overview and real-time statistics",
            "Submit a lost property report with detailed characteristics",
            "Register recovered campus property for owner verification",
            "Lodge a direct ownership claim with private identifying proof",
            "All student-submitted lost property reports with live status",
            "All recovered items currently held in campus custody with live status",
            "Double claim conflict detection and Help Desk arbitration workflow",
            "Pending candidate pairs awaiting Help Desk verification",
            "Officially confirmed and verified property handoffs",
            "Real-time notifications, AI match discoveries, and dispute alerts",
        ]
        if page_index < len(subtitles):
            self.header_page_sub.setText(subtitles[page_index])

        # Refresh page data on navigation
        if page_index in (0, 3, 4, 5, 6, 7, 8, 9):
            self.refresh_all_data()

    # --------------------------------------------------------------------------
    # Application Header: CIT CAMPUS | Smart Lost & Found Portal
    # --------------------------------------------------------------------------
    def _build_header(self, parent_layout: QVBoxLayout):
        header = QFrame()
        header.setObjectName("topHeaderBar")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 14, 30, 14)

        left_box = QVBoxLayout()
        left_box.setSpacing(2)

        # Exact required display: CIT CAMPUS / Smart Lost & Found Portal
        self.header_page_title = QLabel("CIT CAMPUS")
        self.header_page_title.setObjectName("headerTitle")
        self.header_page_sub = QLabel("Smart Lost & Found Portal")
        self.header_page_sub.setObjectName("headerSubtitle")

        left_box.addWidget(self.header_page_title)
        left_box.addWidget(self.header_page_sub)
        layout.addLayout(left_box)

        layout.addStretch()

        # Status Badge
        portal_badge = QLabel("● Campus Services Live")
        portal_badge.setStyleSheet(
            "background-color: #ecfdf5; color: #065f46; border: 1px solid #10b981; "
            "border-radius: 14px; padding: 6px 16px; font-weight: 700; font-size: 12px;"
        )
        layout.addWidget(portal_badge)

        # Notification Bell Button in Header
        self.btn_header_notif = QPushButton("🔔  Notifications")
        self.btn_header_notif.setStyleSheet(
            "background-color: #f1f5f9; color: #064e3b; border: 1px solid #cbd5e1; "
            "border-radius: 14px; padding: 6px 14px; font-weight: 700; font-size: 12px; cursor: pointer;"
        )
        self.btn_header_notif.setCursor(Qt.PointingHandCursor)
        self.btn_header_notif.clicked.connect(lambda: self.navigate_to(9))
        layout.addWidget(self.btn_header_notif)

        parent_layout.addWidget(header)

    # --------------------------------------------------------------------------
    # Page 0: Main Dashboard (Clickable Statistic Cards & Action Cards)
    # --------------------------------------------------------------------------
    def _build_dashboard_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 20, 30, 24)
        layout.setSpacing(22)

        # 1. FIVE STATISTIC CARDS (All Clickable)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.card_lost = ClickableStatCard(
            "TOTAL LOST REPORTS",
            "0",
            "Click to view all lost items →",
            lambda: self.navigate_to(4),
        )
        self.card_found = ClickableStatCard(
            "TOTAL FOUND REPORTS",
            "0",
            "Click to view all found items →",
            lambda: self.navigate_to(5),
        )
        self.card_double = DoubleClaimStatCard(
            lambda: self.navigate_to(6),
        )
        self.card_success = ClickableStatCard(
            "SUCCESSFUL MATCHES",
            "0",
            "Click to view verified matches →",
            lambda: self.navigate_to(8),
        )
        self.card_pending = ClickableStatCard(
            "PENDING MATCHES",
            "0",
            "Click to view candidate pairs →",
            lambda: self.navigate_to(7),
        )

        stats_layout.addWidget(self.card_lost)
        stats_layout.addWidget(self.card_found)
        stats_layout.addWidget(self.card_double)
        stats_layout.addWidget(self.card_success)
        stats_layout.addWidget(self.card_pending)
        layout.addLayout(stats_layout)

        # 2. REPORTING SECTION: THREE ATTRACTIVE OPTIONS IMMEDIATELY BELOW
        rep_box = QFrame()
        rep_l = QHBoxLayout(rep_box)
        rep_l.setContentsMargins(0, 0, 0, 0)
        rep_l.setSpacing(14)

        # Option 1: Report Lost Item Card
        opt_lost_card = QFrame()
        opt_lost_card.setProperty("class", "reportOptionCard")
        opt_lost_card.setCursor(QCursor(Qt.PointingHandCursor))
        opt_lost_card.mousePressEvent = lambda e: self.navigate_to(1)

        ol_layout = QVBoxLayout(opt_lost_card)
        ol_layout.setSpacing(8)

        lbl_ol_title = QLabel("➕  OPTION 1: REPORT LOST ITEM")
        lbl_ol_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #064e3b;")
        ol_layout.addWidget(lbl_ol_title)

        lbl_ol_desc = QLabel(
            "Misplaced an item on campus? Submit a lost report with category, colour, "
            "brand, date, location, description, and photograph."
        )
        lbl_ol_desc.setStyleSheet("color: #475569; font-size: 12px; line-height: 1.4;")
        lbl_ol_desc.setWordWrap(True)
        ol_layout.addWidget(lbl_ol_desc)

        btn_open_lost = QPushButton("Open Lost Item Form →")
        btn_open_lost.setProperty("class", "primaryBtn")
        btn_open_lost.clicked.connect(lambda: self.navigate_to(1))
        ol_layout.addWidget(btn_open_lost, 0, Qt.AlignLeft)
        rep_l.addWidget(opt_lost_card, 1)

        # Option 2: Report Found Item Card
        opt_found_card = QFrame()
        opt_found_card.setProperty("class", "reportOptionCard")
        opt_found_card.setCursor(QCursor(Qt.PointingHandCursor))
        opt_found_card.mousePressEvent = lambda e: self.navigate_to(2)

        of_layout = QVBoxLayout(opt_found_card)
        of_layout.setSpacing(8)

        lbl_of_title = QLabel("📥  OPTION 2: REPORT FOUND ITEM")
        lbl_of_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #064e3b;")
        of_layout.addWidget(lbl_of_title)

        lbl_of_desc = QLabel(
            "Found an item on campus grounds? Register recovered property with date, "
            "location, description, and photograph into secure custody."
        )
        lbl_of_desc.setStyleSheet("color: #475569; font-size: 12px; line-height: 1.4;")
        lbl_of_desc.setWordWrap(True)
        of_layout.addWidget(lbl_of_desc)

        btn_open_found = QPushButton("Open Found Item Form →")
        btn_open_found.setProperty("class", "primaryBtn")
        btn_open_found.clicked.connect(lambda: self.navigate_to(2))
        of_layout.addWidget(btn_open_found, 0, Qt.AlignLeft)
        rep_l.addWidget(opt_found_card, 1)

        # Option 3: Lodge Ownership Claim / Double Claim Card
        opt_claim_card = QFrame()
        opt_claim_card.setProperty("class", "reportOptionCard")
        opt_claim_card.setCursor(QCursor(Qt.PointingHandCursor))
        opt_claim_card.mousePressEvent = lambda e: self.navigate_to(3)

        oc_layout = QVBoxLayout(opt_claim_card)
        oc_layout.setSpacing(8)

        lbl_oc_title = QLabel("⚖️  OPTION 3: LODGE CLAIM / CONFLICT")
        lbl_oc_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #064e3b;")
        oc_layout.addWidget(lbl_oc_title)

        lbl_oc_desc = QLabel(
            "Recognize an item held in campus custody? Lodge an ownership claim with unmentioned "
            "private proof details for Help Desk arbitration."
        )
        lbl_oc_desc.setStyleSheet("color: #475569; font-size: 12px; line-height: 1.4;")
        lbl_oc_desc.setWordWrap(True)
        oc_layout.addWidget(lbl_oc_desc)

        btn_open_claim = QPushButton("Lodge Ownership Claim →")
        btn_open_claim.setProperty("class", "primaryBtn")
        btn_open_claim.clicked.connect(lambda: self.navigate_to(3))
        oc_layout.addWidget(btn_open_claim, 0, Qt.AlignLeft)
        rep_l.addWidget(opt_claim_card, 1)

        layout.addWidget(rep_box)

        # 3. RECENT ITEMS: TWO SECTIONS AT THE BOTTOM
        # Section 1: Recently Lost Items
        sec_lost_header = QHBoxLayout()
        lbl_sec_lost = QLabel("📋  1. RECENTLY LOST ITEMS")
        lbl_sec_lost.setStyleSheet("font-size: 15px; font-weight: 800; color: #0f172a;")
        sec_lost_header.addWidget(lbl_sec_lost)
        sec_lost_header.addStretch()

        btn_view_lost = QPushButton("View All Lost Items →")
        btn_view_lost.setProperty("class", "secondaryBtn")
        btn_view_lost.clicked.connect(lambda: self.navigate_to(4))
        sec_lost_header.addWidget(btn_view_lost)
        layout.addLayout(sec_lost_header)

        self.dash_table_lost = QTableWidget(0, 8)
        self.dash_table_lost.setHorizontalHeaderLabels(["Photo", "Item Name", "Category", "Colour", "Brand", "Date Lost", "Location", "Status"])
        self.dash_table_lost.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.dash_table_lost.setColumnWidth(0, 60)
        self.dash_table_lost.setFixedHeight(180)
        self.dash_table_lost.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dash_table_lost.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.dash_table_lost)

        # Section 2: Recently Found Items
        sec_found_header = QHBoxLayout()
        lbl_sec_found = QLabel("📦  2. RECENTLY FOUND ITEMS")
        lbl_sec_found.setStyleSheet("font-size: 15px; font-weight: 800; color: #0f172a;")
        sec_found_header.addWidget(lbl_sec_found)
        sec_found_header.addStretch()

        btn_view_found = QPushButton("View All Found Items →")
        btn_view_found.setProperty("class", "secondaryBtn")
        btn_view_found.clicked.connect(lambda: self.navigate_to(5))
        sec_found_header.addWidget(btn_view_found)
        layout.addLayout(sec_found_header)

        self.dash_table_found = QTableWidget(0, 8)
        self.dash_table_found.setHorizontalHeaderLabels(["Photo", "Item Name", "Category", "Colour", "Brand", "Date Found", "Location", "Status"])
        self.dash_table_found.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.dash_table_found.setColumnWidth(0, 60)
        self.dash_table_found.setFixedHeight(180)
        self.dash_table_found.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dash_table_found.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.dash_table_found)

        # Nothing else below these two sections
        scroll.setWidget(container)
        return scroll

    # --------------------------------------------------------------------------
    # Page 1: Report Lost Item Form
    # --------------------------------------------------------------------------
    def _build_report_lost_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 24, 40, 30)
        layout.setSpacing(16)

        header_box = QVBoxLayout()
        lbl_t = QLabel("Report Lost Item")
        lbl_t.setStyleSheet("font-size: 18px; font-weight: 800; color: #064e3b;")
        lbl_s = QLabel("Fill in the fields below. Once submitted, the AI matching algorithm compares your item against all found property.")
        lbl_s.setStyleSheet("color: #64748b; font-size: 12px;")
        header_box.addWidget(lbl_t)
        header_box.addWidget(lbl_s)
        layout.addLayout(header_box)

        # Form Card
        form_card = QFrame()
        form_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px;")
        grid = QGridLayout(form_card)
        grid.setSpacing(14)

        # Success Banner
        self.banner_lost_success = QLabel("")
        self.banner_lost_success.setStyleSheet(
            "background-color: #ecfdf5; color: #065f46; border: 1.5px solid #10b981; "
            "border-radius: 8px; padding: 14px; font-weight: 700; font-size: 13px;"
        )
        self.banner_lost_success.setWordWrap(True)
        self.banner_lost_success.hide()
        layout.addWidget(self.banner_lost_success)

        # Item Name & Category
        grid.addWidget(QLabel("Item Name *"), 0, 0)
        name_box = QVBoxLayout()
        name_box.setSpacing(2)
        self.form_lost_name = QLineEdit()
        self.form_lost_name.setPlaceholderText("e.g. Black Samsung Galaxy Phone")
        self.form_lost_name.textChanged.connect(self._validate_lost_name)
        self.err_lost_name = QLabel("")
        self.err_lost_name.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: 600;")
        self.err_lost_name.hide()
        name_box.addWidget(self.form_lost_name)
        name_box.addWidget(self.err_lost_name)
        grid.addLayout(name_box, 0, 1)

        grid.addWidget(QLabel("Category *"), 0, 2)
        self.form_lost_category = QComboBox()
        self.form_lost_category.addItems(sorted(list(ALLOWED_ITEMS)))
        grid.addWidget(self.form_lost_category, 0, 3)

        # Colour & Brand
        grid.addWidget(QLabel("Colour"), 1, 0)
        self.form_lost_colour = QComboBox()
        self.form_lost_colour.addItem("Select colour...")
        self.form_lost_colour.addItems(sorted(list(ALLOWED_COLOURS)))
        grid.addWidget(self.form_lost_colour, 1, 1)

        grid.addWidget(QLabel("Brand"), 1, 2)
        self.form_lost_brand = QLineEdit()
        self.form_lost_brand.setPlaceholderText("e.g. Samsung, Apple, Sony, Nike")
        grid.addWidget(self.form_lost_brand, 1, 3)

        # Date Lost & Location
        grid.addWidget(QLabel("Date Lost *"), 2, 0)
        self.form_lost_date = QDateEdit()
        self.form_lost_date.setCalendarPopup(True)
        self.form_lost_date.setDate(QDate.currentDate())
        grid.addWidget(self.form_lost_date, 2, 1)

        grid.addWidget(QLabel("Location Lost *"), 2, 2)
        self.form_lost_location = QComboBox()
        self.form_lost_location.addItems(sorted(list(ALLOWED_PLACES)))
        grid.addWidget(self.form_lost_location, 2, 3)

        # Detailed Description
        grid.addWidget(QLabel("Detailed Description *"), 3, 0)
        desc_box = QVBoxLayout()
        desc_box.setSpacing(2)
        self.form_lost_desc = QTextEdit()
        self.form_lost_desc.setPlaceholderText("Provide specific details: scratches, lock-screen wallpaper, stickers, accessories, serial number...")
        self.form_lost_desc.setFixedHeight(85)
        self.form_lost_desc.textChanged.connect(self._validate_lost_desc)
        self.err_lost_desc = QLabel("")
        self.err_lost_desc.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: 600;")
        self.err_lost_desc.hide()
        desc_box.addWidget(self.form_lost_desc)
        desc_box.addWidget(self.err_lost_desc)
        grid.addLayout(desc_box, 3, 1, 1, 3)

        # Upload Photograph
        grid.addWidget(QLabel("Upload Photograph"), 4, 0)
        photo_box = QHBoxLayout()
        btn_photo = QPushButton("📷 Choose Photo...")
        btn_photo.setProperty("class", "secondaryBtn")
        btn_photo.clicked.connect(self._browse_lost_photo)
        self.lbl_lost_photo_path = QLabel("No photo selected")
        self.lbl_lost_photo_path.setStyleSheet("color: #64748b; font-size: 11px;")
        photo_box.addWidget(btn_photo)
        photo_box.addWidget(self.lbl_lost_photo_path)
        photo_box.addStretch()
        grid.addLayout(photo_box, 4, 1, 1, 3)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e2e8f0; margin: 8px 0;")
        grid.addWidget(sep, 5, 0, 1, 4)

        # Student Name & ID
        grid.addWidget(QLabel("Student Name *"), 6, 0)
        sname_box = QVBoxLayout()
        sname_box.setSpacing(2)
        self.form_lost_student_name = QLineEdit()
        self.form_lost_student_name.setPlaceholderText("Full Name")
        self.form_lost_student_name.textChanged.connect(self._validate_lost_student_name)
        self.err_lost_student_name = QLabel("")
        self.err_lost_student_name.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: 600;")
        self.err_lost_student_name.hide()
        sname_box.addWidget(self.form_lost_student_name)
        sname_box.addWidget(self.err_lost_student_name)
        grid.addLayout(sname_box, 6, 1)

        grid.addWidget(QLabel("Student ID *"), 6, 2)
        sid_box = QVBoxLayout()
        sid_box.setSpacing(2)
        self.form_lost_student_id = QLineEdit()
        self.form_lost_student_id.setPlaceholderText("e.g. CIT2026-891")
        self.form_lost_student_id.textChanged.connect(self._validate_lost_student_id)
        self.err_lost_student_id = QLabel("")
        self.err_lost_student_id.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: 600;")
        self.err_lost_student_id.hide()
        sid_box.addWidget(self.form_lost_student_id)
        sid_box.addWidget(self.err_lost_student_id)
        grid.addLayout(sid_box, 6, 3)

        # Contact Info (10-Digit Indian Mobile Number)
        grid.addWidget(QLabel("Mobile Number *"), 7, 0)
        contact_box = QVBoxLayout()
        contact_box.setSpacing(2)
        self.form_lost_contact = QLineEdit()
        self.form_lost_contact.setPlaceholderText("Enter 10-digit mobile number (e.g. 9876543210)")
        self.form_lost_contact.textChanged.connect(self._validate_lost_contact)
        self.err_lost_contact = QLabel("")
        self.err_lost_contact.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: 600;")
        self.err_lost_contact.setWordWrap(True)
        self.err_lost_contact.hide()
        contact_box.addWidget(self.form_lost_contact)
        contact_box.addWidget(self.err_lost_contact)
        grid.addLayout(contact_box, 7, 1, 1, 3)

        # Submit Button
        self.btn_submit_lost = QPushButton("🚀  Submit Lost Report")
        self.btn_submit_lost.setProperty("class", "submitBtn")
        self.btn_submit_lost.setFixedHeight(44)
        self.btn_submit_lost.setCursor(Qt.PointingHandCursor)
        self.btn_submit_lost.clicked.connect(self._submit_lost_report)
        grid.addWidget(self.btn_submit_lost, 8, 1, 1, 2)

        layout.addWidget(form_card)

        # Live AI Matching Results Section
        self.live_lost_results_card = QFrame()
        self.live_lost_results_card.setStyleSheet(
            "background-color: #ffffff; border: 1.5px solid #93c5fd; border-radius: 12px; padding: 20px; margin-top: 10px;"
        )
        self.live_lost_results_layout = QVBoxLayout(self.live_lost_results_card)
        self.live_lost_results_layout.setSpacing(12)
        self.live_lost_results_card.hide()
        layout.addWidget(self.live_lost_results_card)

        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def _validate_lost_name(self) -> bool:
        if not self.form_lost_name.text().strip():
            self.err_lost_name.setText("Item name is required. Please enter a valid item name.")
            self.err_lost_name.show()
            self.form_lost_name.setStyleSheet("border: 2px solid #ef4444;")
            return False
        self.err_lost_name.setText("")
        self.err_lost_name.hide()
        self.form_lost_name.setStyleSheet("")
        return True

    def _validate_lost_desc(self) -> bool:
        if not self.form_lost_desc.toPlainText().strip():
            self.err_lost_desc.setText("Detailed description is required.")
            self.err_lost_desc.show()
            self.form_lost_desc.setStyleSheet("border: 2px solid #ef4444;")
            return False
        self.err_lost_desc.setText("")
        self.err_lost_desc.hide()
        self.form_lost_desc.setStyleSheet("")
        return True

    def _validate_lost_student_name(self) -> bool:
        if not self.form_lost_student_name.text().strip():
            self.err_lost_student_name.setText("Student name is required.")
            self.err_lost_student_name.show()
            self.form_lost_student_name.setStyleSheet("border: 2px solid #ef4444;")
            return False
        self.err_lost_student_name.setText("")
        self.err_lost_student_name.hide()
        self.form_lost_student_name.setStyleSheet("")
        return True

    def _validate_lost_student_id(self) -> bool:
        if not self.form_lost_student_id.text().strip():
            self.err_lost_student_id.setText("Student ID is required.")
            self.err_lost_student_id.show()
            self.form_lost_student_id.setStyleSheet("border: 2px solid #ef4444;")
            return False
        self.err_lost_student_id.setText("")
        self.err_lost_student_id.hide()
        self.form_lost_student_id.setStyleSheet("")
        return True

    def _validate_lost_contact(self) -> bool:
        raw = self.form_lost_contact.text().strip()
        if not raw:
            self.err_lost_contact.setText("Invalid mobile number. Please enter a valid 10-digit number.")
            self.err_lost_contact.show()
            self.form_lost_contact.setStyleSheet("border: 2px solid #ef4444;")
            return False

        is_valid, msg = validate_indian_mobile(raw)
        if not is_valid:
            self.err_lost_contact.setText("Invalid mobile number. Please enter a valid 10-digit number.")
            self.err_lost_contact.show()
            self.form_lost_contact.setStyleSheet("border: 2px solid #ef4444;")
            return False

        if database.is_contact_number_registered(raw):
            self.err_lost_contact.setText("This mobile number is already registered. Please enter a different number.")
            self.err_lost_contact.show()
            self.form_lost_contact.setStyleSheet("border: 2px solid #ef4444;")
            return False

        # Valid & Unique: automatically clear error message and restore normal styling
        self.err_lost_contact.setText("")
        self.err_lost_contact.hide()
        self.form_lost_contact.setStyleSheet("")
        return True

    def _browse_lost_photo(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Item Photograph", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file:
            dest = PHOTOS_DIR / f"lost_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{Path(file).name}"
            try:
                shutil.copy(file, dest)
                self.selected_lost_photo = str(dest)
            except Exception:
                self.selected_lost_photo = file
            self.lbl_lost_photo_path.setText(Path(file).name)

    def _submit_lost_report(self):
        # Validate all required fields
        v_name = self._validate_lost_name()
        v_desc = self._validate_lost_desc()
        v_sname = self._validate_lost_student_name()
        v_sid = self._validate_lost_student_id()
        v_contact = self._validate_lost_contact()

        if not (v_name and v_desc and v_sname and v_sid and v_contact):
            return

        # Prevent multiple accidental submissions
        self.btn_submit_lost.setEnabled(False)
        self.btn_submit_lost.setText("Submitting Report...")

        try:
            item_name = self.form_lost_name.text().strip()
            cat = self.form_lost_category.currentText().strip()
            col = self.form_lost_colour.currentText().strip()
            if col.startswith("Select"):
                col = None
            brand = self.form_lost_brand.text().strip() or None
            date_str = self.form_lost_date.date().toString("yyyy-MM-dd")
            loc = self.form_lost_location.currentText().strip()
            desc = self.form_lost_desc.toPlainText().strip()
            s_name = self.form_lost_student_name.text().strip()
            s_id = self.form_lost_student_id.text().strip()
            contact = clean_mobile_number(self.form_lost_contact.text().strip())

            new_id = database.insert_lost_report({
                "item_name": item_name,
                "category": cat,
                "colour": col,
                "brand": brand,
                "date_lost": date_str,
                "location": loc,
                "description": desc,
                "photo_path": self.selected_lost_photo,
                "student_name": s_name,
                "student_id": s_id,
                "contact_info": contact,
            })

            # Automatically compare submitted lost item against existing found items
            match_res = database.match_single_lost(new_id)
            self.refresh_all_data()

            # Render live matching results section directly
            self._render_live_lost_matches(match_res)

            match_cnt = match_res.get("matches_count", 0)
            if match_cnt > 0:
                self.banner_lost_success.setText(
                    f"✔ Report Submitted Successfully! Item registered under ID: {new_id}.\n"
                    f"🎉 Good news! AI matching automatically detected {match_cnt} potential match(es) for your item! Review details below."
                )
            else:
                self.banner_lost_success.setText(
                    f"✔ Report Submitted Successfully! Item registered under ID: {new_id}.\n"
                    f"Status: Searching. No matching items found yet. We will notify you automatically when a match becomes available."
                )
            self.banner_lost_success.show()

            # Clear form fields
            self.form_lost_name.clear()
            self.form_lost_brand.clear()
            self.form_lost_desc.clear()
            self.form_lost_student_name.clear()
            self.form_lost_student_id.clear()
            self.form_lost_contact.clear()
            self.selected_lost_photo = None
            self.lbl_lost_photo_path.setText("No photo selected")

            QMessageBox.information(
                self,
                "Lost Report Submitted",
                f"Your lost report has been registered under ID: {new_id}.\n\n"
                f"Student Mobile: {contact}\n"
                f"Data successfully saved to database. Records will persist after restart."
            )
        finally:
            self.btn_submit_lost.setEnabled(True)
            self.btn_submit_lost.setText("🚀  Submit Lost Report")

    # --------------------------------------------------------------------------
    # Page 2: Report Found Item Form
    # --------------------------------------------------------------------------
    def _build_report_found_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 24, 40, 30)
        layout.setSpacing(16)

        header_box = QVBoxLayout()
        lbl_t = QLabel("Report Found Item")
        lbl_t.setStyleSheet("font-size: 18px; font-weight: 800; color: #064e3b;")
        lbl_s = QLabel("Register recovered campus property. The AI matching algorithm will check for matching student lost reports.")
        lbl_s.setStyleSheet("color: #64748b; font-size: 12px;")
        header_box.addWidget(lbl_t)
        header_box.addWidget(lbl_s)
        layout.addLayout(header_box)

        # Success Banner
        self.banner_found_success = QLabel("")
        self.banner_found_success.setStyleSheet(
            "background-color: #ecfdf5; color: #065f46; border: 1.5px solid #10b981; "
            "border-radius: 8px; padding: 14px; font-weight: 700; font-size: 13px;"
        )
        self.banner_found_success.setWordWrap(True)
        self.banner_found_success.hide()
        layout.addWidget(self.banner_found_success)

        # Form Card
        form_card = QFrame()
        form_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px;")
        grid = QGridLayout(form_card)
        grid.setSpacing(14)

        # Item Name & Category
        grid.addWidget(QLabel("Item Name *"), 0, 0)
        fname_box = QVBoxLayout()
        fname_box.setSpacing(2)
        self.form_found_name = QLineEdit()
        self.form_found_name.setPlaceholderText("e.g. Silver Apple MacBook Air")
        self.form_found_name.textChanged.connect(self._validate_found_name)
        self.err_found_name = QLabel("")
        self.err_found_name.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: 600;")
        self.err_found_name.hide()
        fname_box.addWidget(self.form_found_name)
        fname_box.addWidget(self.err_found_name)
        grid.addLayout(fname_box, 0, 1)

        grid.addWidget(QLabel("Category *"), 0, 2)
        self.form_found_category = QComboBox()
        self.form_found_category.addItems(sorted(list(ALLOWED_ITEMS)))
        grid.addWidget(self.form_found_category, 0, 3)

        # Colour & Brand
        grid.addWidget(QLabel("Colour"), 1, 0)
        self.form_found_colour = QComboBox()
        self.form_found_colour.addItem("Select colour...")
        self.form_found_colour.addItems(sorted(list(ALLOWED_COLOURS)))
        grid.addWidget(self.form_found_colour, 1, 1)

        grid.addWidget(QLabel("Brand"), 1, 2)
        self.form_found_brand = QLineEdit()
        self.form_found_brand.setPlaceholderText("e.g. Apple, Samsung, Sony")
        grid.addWidget(self.form_found_brand, 1, 3)

        # Date Found & Location
        grid.addWidget(QLabel("Date Found *"), 2, 0)
        self.form_found_date = QDateEdit()
        self.form_found_date.setCalendarPopup(True)
        self.form_found_date.setDate(QDate.currentDate())
        grid.addWidget(self.form_found_date, 2, 1)

        grid.addWidget(QLabel("Location Found *"), 2, 2)
        self.form_found_location = QComboBox()
        self.form_found_location.addItems(sorted(list(ALLOWED_PLACES)))
        grid.addWidget(self.form_found_location, 2, 3)

        # Detailed Description
        grid.addWidget(QLabel("Detailed Description *"), 3, 0)
        fdesc_box = QVBoxLayout()
        fdesc_box.setSpacing(2)
        self.form_found_desc = QTextEdit()
        self.form_found_desc.setPlaceholderText("Describe where it was found, table/room number, condition, accessories...")
        self.form_found_desc.setFixedHeight(85)
        self.form_found_desc.textChanged.connect(self._validate_found_desc)
        self.err_found_desc = QLabel("")
        self.err_found_desc.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: 600;")
        self.err_found_desc.hide()
        fdesc_box.addWidget(self.form_found_desc)
        fdesc_box.addWidget(self.err_found_desc)
        grid.addLayout(fdesc_box, 3, 1, 1, 3)

        # Upload Photograph
        grid.addWidget(QLabel("Upload Photograph"), 4, 0)
        photo_box = QHBoxLayout()
        btn_photo = QPushButton("📷 Choose Photo...")
        btn_photo.setProperty("class", "secondaryBtn")
        btn_photo.clicked.connect(self._browse_found_photo)
        self.lbl_found_photo_path = QLabel("No photo selected")
        self.lbl_found_photo_path.setStyleSheet("color: #64748b; font-size: 11px;")
        photo_box.addWidget(btn_photo)
        photo_box.addWidget(self.lbl_found_photo_path)
        photo_box.addStretch()
        grid.addLayout(photo_box, 4, 1, 1, 3)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e2e8f0; margin: 8px 0;")
        grid.addWidget(sep, 5, 0, 1, 4)

        # Finder Name & Contact
        grid.addWidget(QLabel("Finder Name *"), 6, 0)
        finder_box = QVBoxLayout()
        finder_box.setSpacing(2)
        self.form_found_finder = QLineEdit()
        self.form_found_finder.setPlaceholderText("Student / Security Officer Name")
        self.form_found_finder.textChanged.connect(self._validate_found_finder)
        self.err_found_finder = QLabel("")
        self.err_found_finder.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: 600;")
        self.err_found_finder.hide()
        finder_box.addWidget(self.form_found_finder)
        finder_box.addWidget(self.err_found_finder)
        grid.addLayout(finder_box, 6, 1)

        grid.addWidget(QLabel("Mobile Number *"), 6, 2)
        fcontact_box = QVBoxLayout()
        fcontact_box.setSpacing(2)
        self.form_found_contact = QLineEdit()
        self.form_found_contact.setPlaceholderText("10-digit mobile number")
        self.form_found_contact.textChanged.connect(self._validate_found_contact)
        self.err_found_contact = QLabel("")
        self.err_found_contact.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: 600;")
        self.err_found_contact.setWordWrap(True)
        self.err_found_contact.hide()
        fcontact_box.addWidget(self.form_found_contact)
        fcontact_box.addWidget(self.err_found_contact)
        grid.addLayout(fcontact_box, 6, 3)

        # Submit Button
        self.btn_submit_found = QPushButton("📥  Submit Found Report")
        self.btn_submit_found.setProperty("class", "submitBtn")
        self.btn_submit_found.setFixedHeight(44)
        self.btn_submit_found.setCursor(Qt.PointingHandCursor)
        self.btn_submit_found.clicked.connect(self._submit_found_report)
        grid.addWidget(self.btn_submit_found, 7, 1, 1, 2)

        layout.addWidget(form_card)

        # Live AI Matching Results Section
        self.live_found_results_card = QFrame()
        self.live_found_results_card.setStyleSheet(
            "background-color: #ffffff; border: 1.5px solid #93c5fd; border-radius: 12px; padding: 20px; margin-top: 10px;"
        )
        self.live_found_results_layout = QVBoxLayout(self.live_found_results_card)
        self.live_found_results_layout.setSpacing(12)
        self.live_found_results_card.hide()
        layout.addWidget(self.live_found_results_card)

        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def _validate_found_name(self) -> bool:
        if not self.form_found_name.text().strip():
            self.err_found_name.setText("Item name is required.")
            self.err_found_name.show()
            self.form_found_name.setStyleSheet("border: 2px solid #ef4444;")
            return False
        self.err_found_name.setText("")
        self.err_found_name.hide()
        self.form_found_name.setStyleSheet("")
        return True

    def _validate_found_desc(self) -> bool:
        if not self.form_found_desc.toPlainText().strip():
            self.err_found_desc.setText("Detailed description is required.")
            self.err_found_desc.show()
            self.form_found_desc.setStyleSheet("border: 2px solid #ef4444;")
            return False
        self.err_found_desc.setText("")
        self.err_found_desc.hide()
        self.form_found_desc.setStyleSheet("")
        return True

    def _validate_found_finder(self) -> bool:
        if not self.form_found_finder.text().strip():
            self.err_found_finder.setText("Finder name is required.")
            self.err_found_finder.show()
            self.form_found_finder.setStyleSheet("border: 2px solid #ef4444;")
            return False
        self.err_found_finder.setText("")
        self.err_found_finder.hide()
        self.form_found_finder.setStyleSheet("")
        return True

    def _validate_found_contact(self) -> bool:
        raw = self.form_found_contact.text().strip()
        if not raw:
            self.err_found_contact.setText("Invalid mobile number. Please enter a valid 10-digit number.")
            self.err_found_contact.show()
            self.form_found_contact.setStyleSheet("border: 2px solid #ef4444;")
            return False

        is_valid, msg = validate_indian_mobile(raw)
        if not is_valid:
            self.err_found_contact.setText("Invalid mobile number. Please enter a valid 10-digit number.")
            self.err_found_contact.show()
            self.form_found_contact.setStyleSheet("border: 2px solid #ef4444;")
            return False

        self.err_found_contact.setText("")
        self.err_found_contact.hide()
        self.form_found_contact.setStyleSheet("")
        return True

    def _browse_found_photo(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Item Photograph", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file:
            dest = PHOTOS_DIR / f"found_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{Path(file).name}"
            try:
                shutil.copy(file, dest)
                self.selected_found_photo = str(dest)
            except Exception:
                self.selected_found_photo = file
            self.lbl_found_photo_path.setText(Path(file).name)

    def _submit_found_report(self):
        v_name = self._validate_found_name()
        v_desc = self._validate_found_desc()
        v_finder = self._validate_found_finder()
        v_contact = self._validate_found_contact()

        if not (v_name and v_desc and v_finder and v_contact):
            return

        # Prevent multiple accidental submissions
        self.btn_submit_found.setEnabled(False)
        self.btn_submit_found.setText("Submitting Report...")

        try:
            item_name = self.form_found_name.text().strip()
            cat = self.form_found_category.currentText().strip()
            col = self.form_found_colour.currentText().strip()
            if col.startswith("Select"):
                col = None
            brand = self.form_found_brand.text().strip() or None
            date_str = self.form_found_date.date().toString("yyyy-MM-dd")
            loc = self.form_found_location.currentText().strip()
            desc = self.form_found_desc.toPlainText().strip()
            finder = self.form_found_finder.text().strip()
            contact = clean_mobile_number(self.form_found_contact.text().strip())

            new_id = database.insert_found_report({
                "item_name": item_name,
                "category": cat,
                "colour": col,
                "brand": brand,
                "date_found": date_str,
                "location": loc,
                "description": desc,
                "photo_path": self.selected_found_photo,
                "finder_name": finder,
                "contact_info": contact,
            })

            # Automatically compare submitted found item against existing lost items
            match_res = database.match_single_found(new_id)
            self.refresh_all_data()

            # Render live matching results section directly
            self._render_live_found_matches(match_res)

            match_cnt = match_res.get("matches_count", 0)
            if match_cnt > 0:
                self.banner_found_success.setText(
                    f"✔ Found Item Registered Successfully! Assigned ID: {new_id}.\n"
                    f"🎉 Good news! AI matching automatically identified {match_cnt} potential student owner report(s)! Review details below."
                )
            else:
                self.banner_found_success.setText(
                    f"✔ Found Item Registered Successfully! Assigned ID: {new_id}.\n"
                    f"Item placed into custody with status Searching. You will be notified when owner is matched."
                )
            self.banner_found_success.show()

            self.form_found_name.clear()
            self.form_found_brand.clear()
            self.form_found_desc.clear()
            self.form_found_finder.clear()
            self.form_found_contact.clear()
            self.selected_found_photo = None
            self.lbl_found_photo_path.setText("No photo selected")

            QMessageBox.information(
                self,
                "Found Report Submitted",
                f"The found item has been registered under ID: {new_id}.\n\n"
                f"Finder Mobile: {contact}\n"
                f"Data successfully saved to database. Records will persist after restart."
            )
        finally:
            self.btn_submit_found.setEnabled(True)
            self.btn_submit_found.setText("📥  Submit Found Report")

    # --------------------------------------------------------------------------
    # Page 3: Lodge Ownership Claim / Add Double Claim
    # --------------------------------------------------------------------------
    def _browse_claim_photo(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Proof Photograph", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file:
            dest = PHOTOS_DIR / f"claim_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{Path(file).name}"
            try:
                shutil.copy(file, dest)
                self.selected_claim_photo = str(dest)
            except Exception:
                self.selected_claim_photo = file
            self.lbl_claim_photo_path.setText(Path(file).name)

    def _build_lodge_claim_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 24, 40, 30)
        layout.setSpacing(16)

        header_box = QVBoxLayout()
        lbl_t = QLabel("Lodge Ownership Claim / Add Double Claim")
        lbl_t.setStyleSheet("font-size: 18px; font-weight: 800; color: #064e3b;")
        lbl_s = QLabel(
            "Lodge a verified ownership claim against property currently held in campus custody. "
            "If multiple students claim the same item, our automatic conflict detector flags it for Help Desk arbitration."
        )
        lbl_s.setStyleSheet("color: #64748b; font-size: 12px;")
        header_box.addWidget(lbl_t)
        header_box.addWidget(lbl_s)
        layout.addLayout(header_box)

        # Success Banner
        self.banner_claim_success = QLabel("")
        self.banner_claim_success.setStyleSheet(
            "background-color: #ecfdf5; color: #065f46; border: 1.5px solid #10b981; "
            "border-radius: 8px; padding: 14px; font-weight: 700; font-size: 13px;"
        )
        self.banner_claim_success.setWordWrap(True)
        self.banner_claim_success.hide()
        layout.addWidget(self.banner_claim_success)

        # Form Card
        form_card = QFrame()
        form_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px;")
        grid = QGridLayout(form_card)
        grid.setSpacing(14)

        # 1. Target Found Item Selector
        grid.addWidget(QLabel("Select Target Found Item *"), 0, 0)
        self.claim_found_combo = QComboBox()
        self.claim_found_combo.currentIndexChanged.connect(self._on_claim_found_changed)
        grid.addWidget(self.claim_found_combo, 0, 1, 1, 3)

        # Live Target Preview Banner
        self.claim_target_preview = QLabel("Select a found item from custody above.")
        self.claim_target_preview.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; color: #334155; font-size: 12px;")
        self.claim_target_preview.setWordWrap(True)
        grid.addWidget(self.claim_target_preview, 1, 0, 1, 4)

        # 2. Claimant Name & Student ID
        grid.addWidget(QLabel("Claimant Full Name *"), 2, 0)
        cname_box = QVBoxLayout()
        cname_box.setSpacing(2)
        self.claim_student_name = QLineEdit()
        self.claim_student_name.setPlaceholderText("Full Name")
        self.claim_student_name.textChanged.connect(self._validate_claim_student_name)
        self.err_claim_student_name = QLabel("")
        self.err_claim_student_name.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: 600;")
        self.err_claim_student_name.hide()
        cname_box.addWidget(self.claim_student_name)
        cname_box.addWidget(self.err_claim_student_name)
        grid.addLayout(cname_box, 2, 1)

        grid.addWidget(QLabel("Student ID *"), 2, 2)
        cid_box = QVBoxLayout()
        cid_box.setSpacing(2)
        self.claim_student_id = QLineEdit()
        self.claim_student_id.setPlaceholderText("e.g. CIT2026-904")
        self.claim_student_id.textChanged.connect(self._validate_claim_student_id)
        self.err_claim_student_id = QLabel("")
        self.err_claim_student_id.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: 600;")
        self.err_claim_student_id.hide()
        cid_box.addWidget(self.claim_student_id)
        cid_box.addWidget(self.err_claim_student_id)
        grid.addLayout(cid_box, 2, 3)

        # 3. Contact Info & Date Lost
        grid.addWidget(QLabel("Mobile Number *"), 3, 0)
        ccontact_box = QVBoxLayout()
        ccontact_box.setSpacing(2)
        self.claim_contact = QLineEdit()
        self.claim_contact.setPlaceholderText("Enter 10-digit mobile number")
        self.claim_contact.textChanged.connect(self._validate_claim_contact)
        self.err_claim_contact = QLabel("")
        self.err_claim_contact.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: 600;")
        self.err_claim_contact.setWordWrap(True)
        self.err_claim_contact.hide()
        ccontact_box.addWidget(self.claim_contact)
        ccontact_box.addWidget(self.err_claim_contact)
        grid.addLayout(ccontact_box, 3, 1)

        grid.addWidget(QLabel("Date Lost *"), 3, 2)
        self.claim_date_lost = QDateEdit()
        self.claim_date_lost.setCalendarPopup(True)
        self.claim_date_lost.setDate(QDate.currentDate())
        grid.addWidget(self.claim_date_lost, 3, 3)

        # 4. Description of Lost Property
        grid.addWidget(QLabel("Detailed Description *"), 4, 0)
        cdesc_box = QVBoxLayout()
        cdesc_box.setSpacing(2)
        self.claim_description = QTextEdit()
        self.claim_description.setPlaceholderText("Describe the item: colour, brand, circumstances when lost, and identifying marks...")
        self.claim_description.setFixedHeight(80)
        self.claim_description.textChanged.connect(self._validate_claim_desc)
        self.err_claim_description = QLabel("")
        self.err_claim_description.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: 600;")
        self.err_claim_description.hide()
        cdesc_box.addWidget(self.claim_description)
        cdesc_box.addWidget(self.err_claim_description)
        grid.addLayout(cdesc_box, 4, 1, 1, 3)

        # 5. Mandatory Private Identifying Proof
        grid.addWidget(QLabel("Private Identifying Proof *"), 5, 0)
        cproof_box = QVBoxLayout()
        cproof_box.setSpacing(2)
        self.claim_private_proof = QLineEdit()
        self.claim_private_proof.setPlaceholderText("Unmentioned secret detail: passcode, lock-screen wallpaper, unique scratch, inside contents, serial #...")
        self.claim_private_proof.textChanged.connect(self._validate_claim_proof)
        self.err_claim_private_proof = QLabel("")
        self.err_claim_private_proof.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: 600;")
        self.err_claim_private_proof.hide()
        cproof_box.addWidget(self.claim_private_proof)
        cproof_box.addWidget(self.err_claim_private_proof)
        grid.addLayout(cproof_box, 5, 1, 1, 3)

        # 6. Upload Photograph (Optional)
        grid.addWidget(QLabel("Upload Proof Photo"), 6, 0)
        photo_box = QHBoxLayout()
        btn_photo = QPushButton("📷 Choose Photo...")
        btn_photo.setProperty("class", "secondaryBtn")
        btn_photo.clicked.connect(self._browse_claim_photo)
        self.lbl_claim_photo_path = QLabel("No photo selected")
        self.lbl_claim_photo_path.setStyleSheet("color: #64748b; font-size: 11px;")
        photo_box.addWidget(btn_photo)
        photo_box.addWidget(self.lbl_claim_photo_path)
        photo_box.addStretch()
        grid.addLayout(photo_box, 6, 1, 1, 3)

        # Submit & Cancel Buttons
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "secondaryBtn")
        btn_cancel.clicked.connect(lambda: self.navigate_to(0))

        self.btn_submit_claim = QPushButton("⚖️  Submit Ownership Claim")
        self.btn_submit_claim.setProperty("class", "submitBtn")
        self.btn_submit_claim.setFixedHeight(44)
        self.btn_submit_claim.setCursor(Qt.PointingHandCursor)
        self.btn_submit_claim.clicked.connect(self._submit_lodge_claim)

        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(self.btn_submit_claim)
        grid.addLayout(btn_row, 7, 0, 1, 4)

        layout.addWidget(form_card)
        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def _validate_claim_student_name(self) -> bool:
        if not self.claim_student_name.text().strip():
            self.err_claim_student_name.setText("Claimant name is required.")
            self.err_claim_student_name.show()
            self.claim_student_name.setStyleSheet("border: 2px solid #ef4444;")
            return False
        self.err_claim_student_name.setText("")
        self.err_claim_student_name.hide()
        self.claim_student_name.setStyleSheet("")
        return True

    def _validate_claim_student_id(self) -> bool:
        if not self.claim_student_id.text().strip():
            self.err_claim_student_id.setText("Student ID is required.")
            self.err_claim_student_id.show()
            self.claim_student_id.setStyleSheet("border: 2px solid #ef4444;")
            return False
        self.err_claim_student_id.setText("")
        self.err_claim_student_id.hide()
        self.claim_student_id.setStyleSheet("")
        return True

    def _validate_claim_contact(self) -> bool:
        raw = self.claim_contact.text().strip()
        if not raw:
            self.err_claim_contact.setText("Invalid mobile number. Please enter a valid 10-digit number.")
            self.err_claim_contact.show()
            self.claim_contact.setStyleSheet("border: 2px solid #ef4444;")
            return False

        is_valid, msg = validate_indian_mobile(raw)
        if not is_valid:
            self.err_claim_contact.setText("Invalid mobile number. Please enter a valid 10-digit number.")
            self.err_claim_contact.show()
            self.claim_contact.setStyleSheet("border: 2px solid #ef4444;")
            return False

        if database.is_contact_number_registered(raw):
            self.err_claim_contact.setText("This mobile number is already registered. Please enter a different number.")
            self.err_claim_contact.show()
            self.claim_contact.setStyleSheet("border: 2px solid #ef4444;")
            return False

        self.err_claim_contact.setText("")
        self.err_claim_contact.hide()
        self.claim_contact.setStyleSheet("")
        return True

    def _validate_claim_desc(self) -> bool:
        if not self.claim_description.toPlainText().strip():
            self.err_claim_description.setText("Description of lost property is required.")
            self.err_claim_description.show()
            self.claim_description.setStyleSheet("border: 2px solid #ef4444;")
            return False
        self.err_claim_description.setText("")
        self.err_claim_description.hide()
        self.claim_description.setStyleSheet("")
        return True

    def _validate_claim_proof(self) -> bool:
        if not self.claim_private_proof.text().strip():
            self.err_claim_private_proof.setText("Private proof detail is required for ownership verification.")
            self.err_claim_private_proof.show()
            self.claim_private_proof.setStyleSheet("border: 2px solid #ef4444;")
            return False
        self.err_claim_private_proof.setText("")
        self.err_claim_private_proof.hide()
        self.claim_private_proof.setStyleSheet("")
        return True

    def _refresh_claim_found_combo(self):
        if not hasattr(self, "claim_found_combo"):
            return
        self.claim_found_combo.blockSignals(True)
        self.claim_found_combo.clear()
        found_items = database.get_all_found_reports()
        for f in found_items:
            label = f"[{f['id']}] {f.get('item_name', 'Item')} — Location: {f.get('location', 'campus')} (Found: {f.get('date_found', '')}) [{f.get('status', 'In Custody')}]"
            self.claim_found_combo.addItem(label, f)
        self.claim_found_combo.blockSignals(False)
        self._on_claim_found_changed()

    def _on_claim_found_changed(self):
        item_data = self.claim_found_combo.currentData()
        if not item_data:
            self.claim_target_preview.setText("Select a found item from custody above.")
            return

        f_id = item_data.get("id")
        f_name = item_data.get("item_name")
        f_loc = item_data.get("location")
        f_date = item_data.get("date_found")
        f_status = item_data.get("status")

        # Check existing claims in matches
        conflicts = database.get_double_claims_details()
        existing_conflict = next((c for c in conflicts if c["found_id"] == f_id), None)
        existing_count = existing_conflict["claim_count"] if existing_conflict else 0

        if existing_count > 0:
            preview_txt = (
                f"<b>Target: [{f_id}] {f_name}</b> &nbsp;|&nbsp; Found Date: {f_date} &nbsp;|&nbsp; Location: {f_loc} &nbsp;|&nbsp; Status: {f_status}<br>"
                f"<span style='color: #b91c1c; font-weight: bold;'>⚠️ ACTIVE CONFLICT WARNING: "
                f"This found item already has {existing_count} competing claim(s). "
                f"Lodging your claim will register an immediate DOUBLE CLAIM conflict for Help Desk arbitration.</span>"
            )
        else:
            preview_txt = (
                f"<b>Target: [{f_id}] {f_name}</b> &nbsp;|&nbsp; Found Date: {f_date} &nbsp;|&nbsp; Location: {f_loc} &nbsp;|&nbsp; Status: {f_status}<br>"
                f"<span style='color: #059669; font-weight: bold;'>ℹ️ No prior claims yet for this item in campus custody.</span>"
            )
        self.claim_target_preview.setText(preview_txt)

    def _submit_lodge_claim(self):
        item_data = self.claim_found_combo.currentData()
        if not item_data:
            QMessageBox.warning(self, "Select Found Item", "Please select a target found item from custody.")
            return

        v_name = self._validate_claim_student_name()
        v_id = self._validate_claim_student_id()
        v_contact = self._validate_claim_contact()
        v_desc = self._validate_claim_desc()
        v_proof = self._validate_claim_proof()

        if not (v_name and v_id and v_contact and v_desc and v_proof):
            return

        self.btn_submit_claim.setEnabled(False)
        self.btn_submit_claim.setText("Submitting Claim...")

        try:
            f_id = item_data["id"]
            s_name = self.claim_student_name.text().strip()
            s_id = self.claim_student_id.text().strip()
            contact = clean_mobile_number(self.claim_contact.text().strip())
            date_lost = self.claim_date_lost.date().toString("yyyy-MM-dd")
            desc = self.claim_description.toPlainText().strip()
            proof = self.claim_private_proof.text().strip()

            new_lost_id = database.add_direct_claim_for_found(
                found_id=f_id,
                claimant_name=s_name,
                student_id=s_id,
                contact_info=contact,
                description=desc,
                date_lost=date_lost,
                private_proof=proof,
                photo_path=self.selected_claim_photo or ""
            )

            self.refresh_all_data()

            self.banner_claim_success.setText(
                f"✔ Ownership Claim Registered! Assigned Lost ID: {new_lost_id} for Found Item {f_id}.\n"
                f"Automatic conflict detector identified competing claimants and updated Double Claim Management."
            )
            self.banner_claim_success.show()

            QMessageBox.information(
                self,
                "Ownership Claim Registered",
                f"Ownership claim successfully registered under Report ID: {new_lost_id} for Found Item {f_id}!\n\n"
                f"Claimant Mobile: {contact}\n"
                f"Automatic Double Claim Detection has updated the conflicts database.\n"
                f"Opening Double Claim Management for arbitration."
            )

            # Clear form
            self.claim_student_name.clear()
            self.claim_student_id.clear()
            self.claim_contact.clear()
            self.claim_description.clear()
            self.claim_private_proof.clear()
            self.selected_claim_photo = None
            self.lbl_claim_photo_path.setText("No photo selected")

            self.navigate_to(6)
        finally:
            self.btn_submit_claim.setEnabled(True)
            self.btn_submit_claim.setText("⚖️  Submit Ownership Claim")

    # --------------------------------------------------------------------------
    # Page 4: Lost Items List Page
    # --------------------------------------------------------------------------
    def _build_lost_items_page(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 20, 30, 24)
        layout.setSpacing(14)

        # Filter & Search Bar
        tb = QHBoxLayout()
        self.search_lost_edit = QLineEdit()
        self.search_lost_edit.setPlaceholderText("🔍 Search lost items by name, brand, location...")
        self.search_lost_edit.textChanged.connect(self._filter_lost_table)
        tb.addWidget(self.search_lost_edit, 2)

        self.cat_filter_lost = QComboBox()
        self.cat_filter_lost.addItem("All Categories")
        self.cat_filter_lost.addItems(sorted(list(ALLOWED_ITEMS)))
        self.cat_filter_lost.currentIndexChanged.connect(self._filter_lost_table)
        tb.addWidget(self.cat_filter_lost, 1)

        btn_new_lost = QPushButton("➕ Report Lost Item")
        btn_new_lost.setProperty("class", "primaryBtn")
        btn_new_lost.clicked.connect(lambda: self.navigate_to(1))
        tb.addWidget(btn_new_lost)
        layout.addLayout(tb)

        # Full Table
        self.table_all_lost = QTableWidget(0, 9)
        self.table_all_lost.setHorizontalHeaderLabels(["ID", "Photo", "Item Name", "Category", "Colour", "Brand", "Date Lost", "Location", "Status"])
        self.table_all_lost.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_all_lost.setColumnWidth(1, 60)
        self.table_all_lost.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_all_lost.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table_all_lost, 1)

        return container

    def _filter_lost_table(self):
        query = self.search_lost_edit.text().strip().lower()
        selected_cat = self.cat_filter_lost.currentText().lower()

        all_records = database.get_all_lost_reports()
        filtered = []
        for r in all_records:
            if selected_cat != "all categories" and r.get("category", "").lower() != selected_cat:
                continue
            text_haystack = f"{r.get('id')} {r.get('item_name')} {r.get('brand')} {r.get('location')} {r.get('description')}".lower()
            if query and query not in text_haystack:
                continue
            filtered.append(r)

        self._populate_lost_table_rows(filtered)

    def _populate_lost_table_rows(self, records: List[Dict[str, Any]]):
        self.table_all_lost.setRowCount(len(records))
        for row, r in enumerate(records):
            photo_icon = "📷 Yes" if r.get("photo_path") and Path(r.get("photo_path")).exists() else "—"
            self.table_all_lost.setItem(row, 0, QTableWidgetItem(r.get("id", "")))
            self.table_all_lost.setItem(row, 1, QTableWidgetItem(photo_icon))
            self.table_all_lost.setItem(row, 2, QTableWidgetItem(r.get("item_name", "")))
            self.table_all_lost.setItem(row, 3, QTableWidgetItem(r.get("category", "").capitalize()))
            self.table_all_lost.setItem(row, 4, QTableWidgetItem((r.get("colour") or "-").capitalize()))
            self.table_all_lost.setItem(row, 5, QTableWidgetItem(r.get("brand") or "-"))
            self.table_all_lost.setItem(row, 6, QTableWidgetItem(r.get("date_lost", "")))
            self.table_all_lost.setItem(row, 7, QTableWidgetItem(r.get("location", "")))
            self.table_all_lost.setItem(row, 8, QTableWidgetItem(r.get("status", "Reported Lost")))

    # --------------------------------------------------------------------------
    # Page 4: Found Items List Page
    # --------------------------------------------------------------------------
    def _build_found_items_page(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 20, 30, 24)
        layout.setSpacing(14)

        # Filter & Search Bar
        tb = QHBoxLayout()
        self.search_found_edit = QLineEdit()
        self.search_found_edit.setPlaceholderText("🔍 Search found items by name, brand, location...")
        self.search_found_edit.textChanged.connect(self._filter_found_table)
        tb.addWidget(self.search_found_edit, 2)

        self.cat_filter_found = QComboBox()
        self.cat_filter_found.addItem("All Categories")
        self.cat_filter_found.addItems(sorted(list(ALLOWED_ITEMS)))
        self.cat_filter_found.currentIndexChanged.connect(self._filter_found_table)
        tb.addWidget(self.cat_filter_found, 1)

        btn_new_found = QPushButton("📥 Report Found Item")
        btn_new_found.setProperty("class", "primaryBtn")
        btn_new_found.clicked.connect(lambda: self.navigate_to(2))
        tb.addWidget(btn_new_found)
        layout.addLayout(tb)

        # Full Table
        self.table_all_found = QTableWidget(0, 9)
        self.table_all_found.setHorizontalHeaderLabels(["ID", "Photo", "Item Name", "Category", "Colour", "Brand", "Date Found", "Location", "Status"])
        self.table_all_found.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_all_found.setColumnWidth(1, 60)
        self.table_all_found.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_all_found.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table_all_found, 1)

        return container

    def _filter_found_table(self):
        query = self.search_found_edit.text().strip().lower()
        selected_cat = self.cat_filter_found.currentText().lower()

        all_records = database.get_all_found_reports()
        filtered = []
        for r in all_records:
            if selected_cat != "all categories" and r.get("category", "").lower() != selected_cat:
                continue
            text_haystack = f"{r.get('id')} {r.get('item_name')} {r.get('brand')} {r.get('location')} {r.get('description')}".lower()
            if query and query not in text_haystack:
                continue
            filtered.append(r)

        self._populate_found_table_rows(filtered)

    def _populate_found_table_rows(self, records: List[Dict[str, Any]]):
        self.table_all_found.setRowCount(len(records))
        for row, r in enumerate(records):
            photo_icon = "📷 Yes" if r.get("photo_path") and Path(r.get("photo_path")).exists() else "—"
            self.table_all_found.setItem(row, 0, QTableWidgetItem(r.get("id", "")))
            self.table_all_found.setItem(row, 1, QTableWidgetItem(photo_icon))
            self.table_all_found.setItem(row, 2, QTableWidgetItem(r.get("item_name", "")))
            self.table_all_found.setItem(row, 3, QTableWidgetItem(r.get("category", "").capitalize()))
            self.table_all_found.setItem(row, 4, QTableWidgetItem((r.get("colour") or "-").capitalize()))
            self.table_all_found.setItem(row, 5, QTableWidgetItem(r.get("brand") or "-"))
            self.table_all_found.setItem(row, 6, QTableWidgetItem(r.get("date_found", "")))
            self.table_all_found.setItem(row, 7, QTableWidgetItem(r.get("location", "")))
            self.table_all_found.setItem(row, 8, QTableWidgetItem(r.get("status", "In Custody")))

    # --------------------------------------------------------------------------
    # Page 6: Double Claim Detection and Ownership Verification
    # --------------------------------------------------------------------------
    def _build_double_claims_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self.dc_layout = QVBoxLayout(container)
        self.dc_layout.setContentsMargins(30, 20, 30, 24)
        self.dc_layout.setSpacing(16)

        # Header
        lbl_t = QLabel("Double Claim Detection & Ownership Verification")
        lbl_t.setStyleSheet("font-size: 18px; font-weight: 800; color: #064e3b;")
        self.dc_layout.addWidget(lbl_t)

        lbl_s = QLabel(
            "Automatic conflict detection flags contested found items with multiple competing student claims. "
            "Help Desk staff must arbitrate and verify unmentioned private identifying proof before releasing property."
        )
        lbl_s.setStyleSheet("color: #64748b; font-size: 12px;")
        self.dc_layout.addWidget(lbl_s)

        # Quick Stats & Action Filter Bar
        action_bar = QFrame()
        action_bar.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 12px;")
        abl = QHBoxLayout(action_bar)
        abl.setSpacing(12)

        self.lbl_dc_total_badge = QLabel("Total Conflicts: 0")
        self.lbl_dc_total_badge.setStyleSheet("background-color: #f1f5f9; color: #0f172a; font-weight: 700; padding: 6px 12px; border-radius: 6px;")
        abl.addWidget(self.lbl_dc_total_badge)

        self.lbl_dc_pending_badge = QLabel("Pending Arbitration: 0")
        self.lbl_dc_pending_badge.setStyleSheet("background-color: #fee2e2; color: #b91c1c; font-weight: 700; padding: 6px 12px; border-radius: 6px;")
        abl.addWidget(self.lbl_dc_pending_badge)

        self.lbl_dc_resolved_badge = QLabel("Resolved: 0")
        self.lbl_dc_resolved_badge.setStyleSheet("background-color: #dcfce7; color: #15803d; font-weight: 700; padding: 6px 12px; border-radius: 6px;")
        abl.addWidget(self.lbl_dc_resolved_badge)

        abl.addStretch()

        self.dc_filter_combo = QComboBox()
        self.dc_filter_combo.addItems(["All Conflicts", "Pending Arbitration Only", "Resolved Conflicts Only"])
        self.dc_filter_combo.currentIndexChanged.connect(self._populate_double_claims_cards)
        abl.addWidget(self.dc_filter_combo)

        self.dc_search_edit = QLineEdit()
        self.dc_search_edit.setPlaceholderText("🔍 Search contested items or claimants...")
        self.dc_search_edit.textChanged.connect(self._populate_double_claims_cards)
        self.dc_search_edit.setFixedWidth(240)
        abl.addWidget(self.dc_search_edit)

        btn_new_claim = QPushButton("➕ Lodge New Claim")
        btn_new_claim.setProperty("class", "primaryBtn")
        btn_new_claim.clicked.connect(lambda: self.navigate_to(3))
        abl.addWidget(btn_new_claim)

        self.dc_layout.addWidget(action_bar)

        # Dynamic Cards Container
        self.dc_cards_container = QVBoxLayout()
        self.dc_cards_container.setSpacing(18)
        self.dc_layout.addLayout(self.dc_cards_container)
        self.dc_layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def _populate_double_claims_cards(self):
        if not hasattr(self, "dc_cards_container"):
            return

        while self.dc_cards_container.count():
            item = self.dc_cards_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        conflicts = database.get_double_claims_details()
        summary = database.get_double_claims_summary()

        self.lbl_dc_total_badge.setText(f"Total Conflicts: {summary['total_conflicts']}")
        self.lbl_dc_pending_badge.setText(f"Pending Arbitration: {summary['pending_verification']}")
        self.lbl_dc_resolved_badge.setText(f"Resolved: {summary['resolved_claims']}")

        filter_mode = self.dc_filter_combo.currentText()
        search_query = self.dc_search_edit.text().strip().lower()

        filtered = []
        for c in conflicts:
            if filter_mode == "Pending Arbitration Only" and c["has_verified"]:
                continue
            if filter_mode == "Resolved Conflicts Only" and not c["has_verified"]:
                continue

            if search_query:
                f_item = c["found_item"]
                haystack = f"{c['found_id']} {f_item.get('item_name', '')} {f_item.get('category', '')} {f_item.get('location', '')} ".lower()
                for cl in c["claimants"]:
                    haystack += f"{cl.get('lost_id', '')} {cl.get('student_name', '')} {cl.get('student_id', '')} {cl.get('lost_description', '')} ".lower()
                if search_query not in haystack:
                    continue

            filtered.append(c)

        if not filtered:
            no_card = QFrame()
            no_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 30px;")
            nl = QVBoxLayout(no_card)
            lbl_none = QLabel("✔ No Double Claim Conflicts In Current View")
            lbl_none.setStyleSheet("font-size: 15px; font-weight: 700; color: #065f46;")
            lbl_sub = QLabel("No contested found items matched your search/filter criteria.")
            lbl_sub.setStyleSheet("color: #64748b; font-size: 12px;")
            nl.addWidget(lbl_none)
            nl.addWidget(lbl_sub)
            self.dc_cards_container.addWidget(no_card)
            return

        for c in filtered:
            f_id = c["found_id"]
            f_item = c["found_item"]
            claimants = c["claimants"]
            is_resolved = c["has_verified"]

            card = QFrame()
            border_color = "#10b981" if is_resolved else "#f59e0b"
            bg_color = "#ffffff"
            card.setStyleSheet(f"background-color: {bg_color}; border: 1.5px solid {border_color}; border-radius: 12px; padding: 20px;")
            cl = QVBoxLayout(card)
            cl.setSpacing(14)

            # 1. Header Bar: Status Badge + Item Title
            hdr = QHBoxLayout()
            if is_resolved:
                badge = QLabel(f"✔️ CONFLICT RESOLVED • RELEASED")
                badge.setProperty("class", "badgeResolved")
            else:
                badge = QLabel(f"⚠️ CONFLICT DETECTED • {len(claimants)} COMPETING CLAIMANTS")
                badge.setProperty("class", "badgeConflict")
            hdr.addWidget(badge)

            lbl_title = QLabel(f"Contested Item: {f_item.get('item_name')}  [Found ID: {f_id}]")
            lbl_title.setStyleSheet("font-weight: 800; font-size: 15px; color: #064e3b;")
            hdr.addWidget(lbl_title)
            hdr.addStretch()

            lbl_custody = QLabel(f"Custody: <b>{f_item.get('status', 'In Custody')}</b>")
            lbl_custody.setStyleSheet("color: #475569; font-size: 12px;")
            hdr.addWidget(lbl_custody)
            cl.addLayout(hdr)

            # 2. Contested Found Item Overview Card
            found_box = QFrame()
            found_box.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px;")
            fb_layout = QHBoxLayout(found_box)
            fb_layout.setSpacing(16)

            # Photo or Placeholder
            photo_lbl = QLabel()
            photo_path = f_item.get("photo_path")
            if photo_path and Path(photo_path).exists():
                pix = QPixmap(photo_path).scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                photo_lbl.setPixmap(pix)
            else:
                photo_lbl.setText("📦\nNo Photo")
                photo_lbl.setAlignment(Qt.AlignCenter)
                photo_lbl.setStyleSheet("background-color: #e2e8f0; color: #64748b; font-weight: bold; border-radius: 6px;")
                photo_lbl.setFixedSize(80, 80)
            fb_layout.addWidget(photo_lbl)

            fb_info = QVBoxLayout()
            fb_info.setSpacing(4)
            lbl_found_details = QLabel(
                f"<b>Category:</b> {f_item.get('category', '').capitalize()} &nbsp;|&nbsp; "
                f"<b>Colour:</b> {(f_item.get('colour') or '-').capitalize()} &nbsp;|&nbsp; "
                f"<b>Brand:</b> {f_item.get('brand') or '-'} &nbsp;|&nbsp; "
                f"<b>Date Found:</b> {f_item.get('date_found')} &nbsp;|&nbsp; "
                f"<b>Found Location:</b> {f_item.get('location')}"
            )
            lbl_found_details.setStyleSheet("font-size: 12px; color: #0f172a;")
            fb_info.addWidget(lbl_found_details)

            lbl_found_desc = QLabel(f"<b>Finder Note:</b> \"{f_item.get('description', '')}\" — Reported by {f_item.get('finder_name', 'Security')} ({f_item.get('contact_info', '')})")
            lbl_found_desc.setStyleSheet("font-size: 12px; color: #475569;")
            lbl_found_desc.setWordWrap(True)
            fb_info.addWidget(lbl_found_desc)
            fb_layout.addLayout(fb_info, 1)

            cl.addWidget(found_box)

            # 3. Competing Claimants Section
            lbl_cl_header = QLabel(f"<b>Competing Student Claimants ({len(claimants)} Claims Registered):</b>")
            lbl_cl_header.setStyleSheet("color: #064e3b; font-size: 13px; margin-top: 4px;")
            cl.addWidget(lbl_cl_header)

            claimants_grid = QVBoxLayout()
            claimants_grid.setSpacing(10)

            for i, claimant in enumerate(claimants, 1):
                c_card = QFrame()
                c_status = claimant.get("claim_status", "Pending Verification")

                if c_status == "Verified & Returned":
                    c_style = "background-color: #f0fdf4; border: 1.5px solid #16a34a; border-radius: 8px; padding: 12px;"
                    status_badge = "<span style='background-color: #16a34a; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;'>🏆 WINNING CLAIMANT — VERIFIED & RETURNED</span>"
                elif c_status == "Claim Denied - Alternate Verified":
                    c_style = "background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px;"
                    status_badge = "<span style='background-color: #94a3b8; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;'>❌ CLAIM DENIED (ALTERNATE VERIFIED)</span>"
                else:
                    c_style = "background-color: #fffbeb; border: 1px solid #fcd34d; border-radius: 8px; padding: 12px;"
                    status_badge = "<span style='background-color: #f59e0b; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;'>⏳ PENDING ARBITRATION</span>"

                c_card.setStyleSheet(c_style)
                c_layout = QVBoxLayout(c_card)
                c_layout.setSpacing(6)

                ch_bar = QHBoxLayout()
                lbl_c_title = QLabel(f"<b>Claimant #{i}: {claimant.get('student_name')}</b>  (Student ID: {claimant.get('student_id', 'N/A')})")
                lbl_c_title.setStyleSheet("font-size: 13px; color: #0f172a;")
                ch_bar.addWidget(lbl_c_title)
                ch_bar.addStretch()

                lbl_c_status = QLabel(status_badge)
                ch_bar.addWidget(lbl_c_status)
                c_layout.addLayout(ch_bar)

                # Claimant Details
                score = claimant.get('match_score', 0)
                pct = claimant.get('match_percentage', 0)
                classification = claimant.get('classification', '')
                c_details = QLabel(
                    f"<b>Report ID:</b> {claimant.get('lost_id')} &nbsp;|&nbsp; "
                    f"<b>Contact:</b> {claimant.get('contact_info')} &nbsp;|&nbsp; "
                    f"<b>Date Lost:</b> {claimant.get('date_lost')} &nbsp;|&nbsp; "
                    f"<b>Reported Place:</b> {claimant.get('lost_location')}<br>"
                    f"<b>Student Description:</b> \"{claimant.get('lost_description')}\"<br>"
                    f"<b>AI Match Assessment:</b> Confidence {pct}% (Score: {score}/5) • {classification} — <i>{claimant.get('reasons', '')}</i>"
                )
                c_details.setStyleSheet("font-size: 12px; color: #334155; line-height: 1.4;")
                c_details.setWordWrap(True)
                c_layout.addWidget(c_details)

                claimants_grid.addWidget(c_card)

            cl.addLayout(claimants_grid)

            # 4. Help Desk Arbitration & Verification Panel
            if not is_resolved:
                arb_box = QFrame()
                arb_box.setStyleSheet("background-color: #fff7ed; border: 1.5px solid #fdba74; border-radius: 8px; padding: 14px;")
                arb_l = QVBoxLayout(arb_box)
                arb_l.setSpacing(10)

                lbl_arb_title = QLabel("⚖️  Campus Help Desk In-Person Arbitration & Handover Authorization")
                lbl_arb_title.setStyleSheet("font-weight: 800; font-size: 13px; color: #9a3412;")
                arb_l.addWidget(lbl_arb_title)

                lbl_arb_warn = QLabel(
                    "<b>DECISION RULE:</b> AI matching suggestions alone NEVER decide ownership. "
                    "Help Desk staff must physically interview claimants and verify an <u>unmentioned private detail</u> "
                    "(passcode, lockscreen photo, serial number, scratch, inside contents) before releasing property."
                )
                lbl_arb_warn.setStyleSheet("color: #7c2d12; font-size: 11px; line-height: 1.4;")
                lbl_arb_warn.setWordWrap(True)
                arb_l.addWidget(lbl_arb_warn)

                arb_grid = QGridLayout()
                arb_grid.setSpacing(10)

                # Select Winner Dropdown
                arb_grid.addWidget(QLabel("Select Legitimate Owner *:"), 0, 0)
                combo_winner = QComboBox()
                for claimant in claimants:
                    combo_winner.addItem(
                        f"Award to {claimant.get('student_name')} [Report: {claimant.get('lost_id')}, ID: {claimant.get('student_id')}]",
                        claimant.get("lost_id")
                    )
                arb_grid.addWidget(combo_winner, 0, 1)

                # Mandatory Private Proof
                arb_grid.addWidget(QLabel("Verified Private Identifying Proof *:"), 1, 0)
                txt_proof = QLineEdit()
                txt_proof.setPlaceholderText("e.g. Unlocked phone with PIN 8192 and showed matching student ID photo")
                arb_grid.addWidget(txt_proof, 1, 1)

                # Staff Officer Name
                arb_grid.addWidget(QLabel("Authorizing Staff Officer *:"), 2, 0)
                txt_staff = QLineEdit("Campus Help Desk Officer")
                arb_grid.addWidget(txt_staff, 2, 1)

                # Notes
                arb_grid.addWidget(QLabel("Arbitration Notes:"), 3, 0)
                txt_notes = QLineEdit()
                txt_notes.setPlaceholderText("Additional arbitration remarks and physical handoff verification notes")
                arb_grid.addWidget(txt_notes, 3, 1)

                arb_l.addLayout(arb_grid)

                # Authorize Button
                btn_resolve = QPushButton("⚖️  Authorize Handover & Resolve Conflict")
                btn_resolve.setProperty("class", "submitBtn")
                btn_resolve.setFixedHeight(40)
                btn_resolve.setCursor(Qt.PointingHandCursor)
                btn_resolve.clicked.connect(
                    lambda ch=False, target_fid=f_id, cw=combo_winner, tp=txt_proof, ts=txt_staff, tn=txt_notes:
                    self._do_resolve_conflict(target_fid, cw, tp, ts, tn)
                )
                arb_l.addWidget(btn_resolve, 0, Qt.AlignRight)

                cl.addWidget(arb_box)
            else:
                # Resolved Audit Banner
                res_box = QFrame()
                res_box.setStyleSheet("background-color: #ecfdf5; border: 1.5px solid #a7f3d0; border-radius: 8px; padding: 14px;")
                res_l = QVBoxLayout(res_box)
                res_l.setSpacing(6)

                winner = next((c for c in claimants if c.get("claim_status") == "Verified & Returned"), None)
                winner_lost_id = winner.get("lost_id") if winner else "N/A"
                winner_name = winner.get("student_name") if winner else "Verified Student"

                lbl_res_title = QLabel(f"✔️  Conflict Successfully Resolved — Property Handed Over to {winner_name} ({winner_lost_id})")
                lbl_res_title.setStyleSheet("font-weight: 800; font-size: 13px; color: #065f46;")
                res_l.addWidget(lbl_res_title)

                if winner:
                    lbl_audit = QLabel(
                        f"<b>Authorizing Officer:</b> {winner.get('verified_by', 'Campus Help Desk')} &nbsp;|&nbsp; "
                        f"<b>Date Verified:</b> {winner.get('verified_at')}<br>"
                        f"<b>Documented Private Proof:</b> {winner.get('verification_notes', 'Verified in person')}"
                    )
                    lbl_audit.setStyleSheet("font-size: 12px; color: #047857;")
                    lbl_audit.setWordWrap(True)
                    res_l.addWidget(lbl_audit)

                cl.addWidget(res_box)

            self.dc_cards_container.addWidget(card)

    def _do_resolve_conflict(self, found_id: str, combo_winner: QComboBox, txt_proof: QLineEdit, txt_staff: QLineEdit, txt_notes: QLineEdit):
        winning_lost_id = combo_winner.currentData()
        proof = txt_proof.text().strip()
        staff = txt_staff.text().strip()
        notes = txt_notes.text().strip()

        if not winning_lost_id:
            QMessageBox.warning(self, "Select Winner", "Please select the verified legitimate owner.")
            return

        if not proof:
            QMessageBox.warning(self, "Mandatory Proof Required", "Please record the verified private identifying proof (e.g. passcode, wallpaper, internal contents). AI recommendations alone cannot authorize property handoff.")
            return

        if not staff:
            QMessageBox.warning(self, "Staff Officer Required", "Please enter the authorizing Help Desk staff member name.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Handover & Resolve Conflict",
            f"Are you sure you want to award Found Item {found_id} to Claimant {winning_lost_id}?\n\n"
            f"Verified Private Proof: {proof}\n"
            f"Authorizing Officer: {staff}\n\n"
            f"This will release the item from campus custody, mark this match as Verified & Returned, "
            f"and deny competing claims.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            database.resolve_double_claim(found_id, winning_lost_id, staff, proof, notes)
            self.refresh_all_data()
            QMessageBox.information(
                self,
                "Conflict Resolved",
                f"Double claim conflict for Found Item {found_id} has been successfully resolved!\n\n"
                f"Ownership awarded to {winning_lost_id}.\n"
                f"The verified handoff has been moved to Successful Matches."
            )

    # --------------------------------------------------------------------------
    # Page 7: AI Matches (Pending / Potential Matches)
    # --------------------------------------------------------------------------
    def _build_ai_matches_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self.ai_matches_layout = QVBoxLayout(container)
        self.ai_matches_layout.setContentsMargins(30, 20, 30, 24)
        self.ai_matches_layout.setSpacing(16)

        # Header with Re-Run button
        top_bar = QHBoxLayout()
        lbl_info = QLabel("AI Potential Matches Waiting for Verification")
        lbl_info.setStyleSheet("font-size: 16px; font-weight: 800; color: #064e3b;")
        top_bar.addWidget(lbl_info)
        top_bar.addStretch()

        btn_recalculate = QPushButton("⚡ Re-Run AI Matching Engine")
        btn_recalculate.setProperty("class", "secondaryBtn")
        btn_recalculate.clicked.connect(self._recalculate_ai_matches)
        top_bar.addWidget(btn_recalculate)
        self.ai_matches_layout.addLayout(top_bar)

        self.matches_cards_container = QVBoxLayout()
        self.matches_cards_container.setSpacing(14)
        self.ai_matches_layout.addLayout(self.matches_cards_container)
        self.ai_matches_layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def _recalculate_ai_matches(self):
        database.run_database_matching()
        self.refresh_all_data()
        QMessageBox.showinfo("Matching Complete", "AI matching algorithm has re-evaluated all report pairs.")

    def _populate_ai_matches_cards(self):
        while self.matches_cards_container.count():
            item = self.matches_cards_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        pending_list = database.get_pending_matches()

        if not pending_list:
            no_card = QFrame()
            no_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 30px;")
            nl = QVBoxLayout(no_card)
            lbl_none = QLabel("✔ No Potential Matches Awaiting Verification")
            lbl_none.setStyleSheet("font-size: 15px; font-weight: 700; color: #065f46;")
            lbl_sub = QLabel("All candidate pairs have either been verified or there are no new matching items at this time.")
            lbl_sub.setStyleSheet("color: #64748b; font-size: 12px;")
            nl.addWidget(lbl_none)
            nl.addWidget(lbl_sub)
            self.matches_cards_container.addWidget(no_card)
            return

        for m in pending_list:
            card = QFrame()
            card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px;")
            cl = QVBoxLayout(card)
            cl.setSpacing(10)

            # Header row: Match Percentage & IDs
            hdr = QHBoxLayout()
            score_badge = QLabel(f"{m['match_percentage']}% MATCH  ({m['classification']})")
            score_badge.setProperty("class", "badgeLikely" if m['match_percentage'] >= 60 else "badgePossible")
            hdr.addWidget(score_badge)

            lbl_ids = QLabel(f"Lost: {m['lost_id']}  ⟷  Found: {m['found_id']}")
            lbl_ids.setStyleSheet("font-weight: 800; font-size: 14px; color: #0f172a;")
            hdr.addWidget(lbl_ids)
            hdr.addStretch()

            btn_verify = QPushButton("Verify & Confirm Match")
            btn_verify.setProperty("class", "primaryBtn")
            btn_verify.clicked.connect(lambda ch=False, match_row=m: self._open_verification_modal(match_row))
            hdr.addWidget(btn_verify)
            cl.addLayout(hdr)

            # Details Grid
            details_grid = QGridLayout()
            details_grid.setSpacing(8)

            # Left: Lost Item Information
            details_grid.addWidget(QLabel("<b>Lost Item:</b>"), 0, 0)
            details_grid.addWidget(QLabel(f"{m['lost_item_name']} ({m['lost_category']})"), 0, 1)

            details_grid.addWidget(QLabel("<b>Student / Date:</b>"), 1, 0)
            details_grid.addWidget(QLabel(f"{m['student_name']} on {m['date_lost']}"), 1, 1)

            details_grid.addWidget(QLabel("<b>Reported Location:</b>"), 2, 0)
            details_grid.addWidget(QLabel(f"{m['lost_location']}"), 2, 1)

            # Right: Found Item Information
            details_grid.addWidget(QLabel("<b>Found Item:</b>"), 0, 2)
            details_grid.addWidget(QLabel(f"{m['found_item_name']} ({m['found_category']})"), 0, 3)

            details_grid.addWidget(QLabel("<b>Finder / Date:</b>"), 1, 2)
            details_grid.addWidget(QLabel(f"{m['finder_name']} on {m['date_found']}"), 1, 3)

            details_grid.addWidget(QLabel("<b>Recovered Location:</b>"), 2, 2)
            details_grid.addWidget(QLabel(f"{m['found_location']}"), 2, 3)

            cl.addLayout(details_grid)

            # Matching Characteristics & AI Explanation
            exp_box = QFrame()
            exp_box.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px;")
            el = QVBoxLayout(exp_box)
            el.setSpacing(4)

            lbl_chars = QLabel(f"<b>Matching Characteristics:</b> {m['reasons']}")
            lbl_chars.setStyleSheet("color: #065f46; font-size: 12px;")
            el.addWidget(lbl_chars)

            lbl_expl = QLabel(f"<b>AI-Generated Explanation:</b> {m['explanation']}")
            lbl_expl.setStyleSheet("color: #334155; font-size: 12px;")
            lbl_expl.setWordWrap(True)
            el.addWidget(lbl_expl)

            lbl_conflicts = QLabel("<b>Conflicting Information:</b> None detected.")
            lbl_conflicts.setStyleSheet("color: #64748b; font-size: 11px;")
            el.addWidget(lbl_conflicts)

            cl.addWidget(exp_box)
            self.matches_cards_container.addWidget(card)

    def _open_verification_modal(self, m: Dict[str, Any]):
        """Open staff verification modal before granting official match handoff."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Help Desk Verification - Confirm Ownership")
        dialog.setFixedWidth(520)
        dialog.setStyleSheet(CIT_THEME_QSS)

        dl = QVBoxLayout(dialog)
        dl.setContentsMargins(24, 20, 24, 20)
        dl.setSpacing(14)

        lbl_head = QLabel("Confirm Match & Handover")
        lbl_head.setStyleSheet("font-size: 16px; font-weight: 800; color: #064e3b;")
        dl.addWidget(lbl_head)

        lbl_sub = QLabel(
            f"Matching Lost <b>{m['lost_id']}</b> ({m['lost_item_name']}) with "
            f"Found <b>{m['found_id']}</b> ({m['found_item_name']})."
        )
        dl.addWidget(lbl_sub)

        lbl_instruct = QLabel(
            "<b>MANDATORY SECURITY PROTOCOL:</b><br>"
            "Before marking this match successful, require the claimant to provide "
            "an unmentioned private detail (e.g. device passcode, lock-screen wallpaper, or inside contents)."
        )
        lbl_instruct.setStyleSheet("background-color: #fff7ed; color: #9a3412; border: 1px solid #fed7aa; border-radius: 6px; padding: 10px; font-size: 11px;")
        dl.addWidget(lbl_instruct)

        dl.addWidget(QLabel("Verified Private Identifying Detail *:"))
        txt_notes = QLineEdit()
        txt_notes.setPlaceholderText("e.g. Student verified 4-digit PIN 8192 and showed matching student ID")
        dl.addWidget(txt_notes)

        dl.addWidget(QLabel("Staff Member Name *:"))
        txt_staff = QLineEdit("Campus Help Desk Officer")
        dl.addWidget(txt_staff)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "secondaryBtn")
        btn_cancel.clicked.connect(dialog.reject)

        btn_confirm = QPushButton("Confirm Ownership & Handoff")
        btn_confirm.setProperty("class", "primaryBtn")

        def _do_confirm():
            notes = txt_notes.text().strip()
            staff = txt_staff.text().strip()
            if not notes or not staff:
                QMessageBox.warning(dialog, "Required", "Please record the verified private proof and staff member name.")
                return
            database.confirm_successful_match(m["lost_id"], m["found_id"], notes, staff)
            dialog.accept()
            self.refresh_all_data()
            QMessageBox.showinfo(
                "Match Confirmed",
                f"Successfully verified match between {m['lost_id']} and {m['found_id']}!\n"
                f"The record has been moved to Successful Matches."
            )

        btn_confirm.clicked.connect(_do_confirm)
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_confirm)
        dl.addLayout(btn_box)

        dialog.exec()

    # --------------------------------------------------------------------------
    # Page 8: Successful Matches (Confirmed & Verified)
    # --------------------------------------------------------------------------
    def _build_successful_matches_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self.succ_matches_layout = QVBoxLayout(container)
        self.succ_matches_layout.setContentsMargins(30, 20, 30, 24)
        self.succ_matches_layout.setSpacing(16)

        # Header
        lbl_t = QLabel("Confirmed & Successfully Returned Matches")
        lbl_t.setStyleSheet("font-size: 16px; font-weight: 800; color: #064e3b;")
        self.succ_matches_layout.addWidget(lbl_t)

        lbl_s = QLabel("Items on this page represent officially verified property handoffs. AI recommendations alone never decide ownership.")
        lbl_s.setStyleSheet("color: #64748b; font-size: 12px;")
        self.succ_matches_layout.addWidget(lbl_s)

        self.succ_cards_container = QVBoxLayout()
        self.succ_cards_container.setSpacing(14)
        self.succ_matches_layout.addLayout(self.succ_cards_container)
        self.succ_matches_layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def _populate_successful_matches_cards(self):
        while self.succ_cards_container.count():
            item = self.succ_cards_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        succ_list = database.get_successful_matches()

        if not succ_list:
            no_card = QFrame()
            no_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 30px;")
            nl = QVBoxLayout(no_card)
            lbl_none = QLabel("No Confirmed Matches Yet")
            lbl_none.setStyleSheet("font-size: 15px; font-weight: 700; color: #64748b;")
            lbl_sub = QLabel("Go to AI Matches, verify claimant private identifying details, and confirm the match to display it here.")
            lbl_sub.setStyleSheet("color: #94a3b8; font-size: 12px;")
            nl.addWidget(lbl_none)
            nl.addWidget(lbl_sub)
            self.succ_cards_container.addWidget(no_card)
            return

        for m in succ_list:
            card = QFrame()
            card.setStyleSheet("background-color: #ffffff; border: 1px solid #bbf7d0; border-radius: 12px; padding: 18px;")
            cl = QVBoxLayout(card)
            cl.setSpacing(8)

            hdr = QHBoxLayout()
            badge = QLabel("VERIFIED & RETURNED")
            badge.setProperty("class", "badgeVerified")
            hdr.addWidget(badge)

            lbl_title = QLabel(f"{m['lost_item_name']}  ({m['lost_id']} ⟷ {m['found_id']})")
            lbl_title.setStyleSheet("font-weight: 800; font-size: 14px; color: #064e3b;")
            hdr.addWidget(lbl_title)
            hdr.addStretch()

            lbl_date = QLabel(f"Verified: {m.get('verified_at', '')}")
            lbl_date.setStyleSheet("color: #64748b; font-size: 11px;")
            hdr.addWidget(lbl_date)
            cl.addLayout(hdr)

            # Details
            grid = QGridLayout()
            grid.addWidget(QLabel("<b>Student Claimant:</b>"), 0, 0)
            grid.addWidget(QLabel(f"{m.get('student_name', '')} ({m.get('student_contact', '')})"), 0, 1)

            grid.addWidget(QLabel("<b>Recovered Finder:</b>"), 0, 2)
            grid.addWidget(QLabel(f"{m.get('finder_name', '')} ({m.get('finder_contact', '')})"), 0, 3)

            grid.addWidget(QLabel("<b>Verified Identifying Proof:</b>"), 1, 0)
            grid.addWidget(QLabel(f"{m.get('verification_notes', 'Physical proof verified in person')}"), 1, 1, 1, 3)

            cl.addLayout(grid)
            self.succ_cards_container.addWidget(card)

    # --------------------------------------------------------------------------
    # Central Refresh Function
    # --------------------------------------------------------------------------
    def refresh_all_data(self):
        """Update all 5 dashboard statistic cards, tables, and AI matching views."""
        stats = database.get_dashboard_statistics()

        # Update 5 Clickable Dashboard Cards
        self.card_lost.set_value(str(stats["total_lost"]))
        self.card_found.set_value(str(stats["total_found"]))
        self.card_double.set_data(
            stats["double_claims_total"],
            stats["double_claims_pending"],
            stats["double_claims_resolved"]
        )
        self.card_success.set_value(str(stats["successful_matches"]))
        self.card_pending.set_value(str(stats["pending_matches"]))

        # Populate Dashboard Recent Lost Items (Top 5)
        all_lost = database.get_all_lost_reports()
        recent_lost = all_lost[:5]
        self.dash_table_lost.setRowCount(len(recent_lost))
        for row, r in enumerate(recent_lost):
            photo_icon = "📷 Yes" if r.get("photo_path") and Path(r.get("photo_path")).exists() else "—"
            self.dash_table_lost.setItem(row, 0, QTableWidgetItem(photo_icon))
            self.dash_table_lost.setItem(row, 1, QTableWidgetItem(r.get("item_name", "")))
            self.dash_table_lost.setItem(row, 2, QTableWidgetItem(r.get("category", "").capitalize()))
            self.dash_table_lost.setItem(row, 3, QTableWidgetItem((r.get("colour") or "-").capitalize()))
            self.dash_table_lost.setItem(row, 4, QTableWidgetItem(r.get("brand") or "-"))
            self.dash_table_lost.setItem(row, 5, QTableWidgetItem(r.get("date_lost", "")))
            self.dash_table_lost.setItem(row, 6, QTableWidgetItem(r.get("location", "")))
            self.dash_table_lost.setItem(row, 7, QTableWidgetItem(r.get("status", "Reported Lost")))

        # Populate Dashboard Recent Found Items (Top 5)
        all_found = database.get_all_found_reports()
        recent_found = all_found[:5]
        self.dash_table_found.setRowCount(len(recent_found))
        for row, r in enumerate(recent_found):
            photo_icon = "📷 Yes" if r.get("photo_path") and Path(r.get("photo_path")).exists() else "—"
            self.dash_table_found.setItem(row, 0, QTableWidgetItem(photo_icon))
            self.dash_table_found.setItem(row, 1, QTableWidgetItem(r.get("item_name", "")))
            self.dash_table_found.setItem(row, 2, QTableWidgetItem(r.get("category", "").capitalize()))
            self.dash_table_found.setItem(row, 3, QTableWidgetItem((r.get("colour") or "-").capitalize()))
            self.dash_table_found.setItem(row, 4, QTableWidgetItem(r.get("brand") or "-"))
            self.dash_table_found.setItem(row, 5, QTableWidgetItem(r.get("date_found", "")))
            self.dash_table_found.setItem(row, 6, QTableWidgetItem(r.get("location", "")))
            self.dash_table_found.setItem(row, 7, QTableWidgetItem(r.get("status", "In Custody")))

        # Populate Full Tables
        self._populate_lost_table_rows(all_lost)
        self._populate_found_table_rows(all_found)

        # Update Notifications Badge in header and sidebar
        unread_notifs = database.get_unread_notification_count()
        if hasattr(self, "btn_header_notif"):
            if unread_notifs > 0:
                self.btn_header_notif.setText(f"🔔  Notifications ({unread_notifs})")
                self.btn_header_notif.setStyleSheet(
                    "background-color: #fef3c7; color: #92400e; border: 1.5px solid #f59e0b; "
                    "border-radius: 14px; padding: 6px 14px; font-weight: 800; font-size: 12px; cursor: pointer;"
                )
            else:
                self.btn_header_notif.setText("🔔  Notifications")
                self.btn_header_notif.setStyleSheet(
                    "background-color: #f1f5f9; color: #064e3b; border: 1px solid #cbd5e1; "
                    "border-radius: 14px; padding: 6px 14px; font-weight: 700; font-size: 12px; cursor: pointer;"
                )
        if hasattr(self, "sidebar_buttons") and len(self.sidebar_buttons) > 9:
            notif_btn = self.sidebar_buttons[9]
            if unread_notifs > 0:
                notif_btn.setText(f"🔔  Notifications ({unread_notifs})")
            else:
                notif_btn.setText("🔔  Notifications")

        # Populate Double Claims, Combos, Matches Cards, and Notifications
        self._refresh_claim_found_combo()
        self._populate_double_claims_cards()
        self._populate_ai_matches_cards()
        self._populate_successful_matches_cards()
        self._populate_notifications_cards()


    # --------------------------------------------------------------------------
    # Live AI Matching Results Rendering
    # --------------------------------------------------------------------------
    def _render_live_lost_matches(self, match_res: Dict[str, Any]):
        """Render live matching results directly below the Report Lost form."""
        while self.live_lost_results_layout.count():
            item = self.live_lost_results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        matches = match_res.get("matches", [])
        lost_id = match_res.get("lost_id", "")
        item_name = match_res.get("lost_item_name", "Item")

        hdr = QLabel(f"🔍  LIVE AI MATCHING RESULTS FOR {item_name} [{lost_id}]")
        hdr.setStyleSheet("font-size: 16px; font-weight: 800; color: #064e3b;")
        self.live_lost_results_layout.addWidget(hdr)

        if matches:
            sub = QLabel(
                f"🎉  <b>Good news!</b> Automatic AI matching compared your submission against all campus custody property and found "
                f"<b>{len(matches)}</b> candidate match(es). Review details below."
            )
            sub.setStyleSheet("color: #065f46; font-size: 13px; background-color: #ecfdf5; border: 1.5px solid #10b981; border-radius: 8px; padding: 12px;")
            sub.setWordWrap(True)
            self.live_lost_results_layout.addWidget(sub)

            for m in matches:
                card = QFrame()
                card.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 10px; padding: 14px;")
                cl = QVBoxLayout(card)
                cl.setSpacing(8)

                top_row = QHBoxLayout()
                is_likely = m.get("match_percentage", 0) >= 60
                badge = QLabel(f"{m.get('match_percentage')}% MATCH  ({m.get('classification')})")
                badge.setStyleSheet(
                    "background-color: #dcfce7; color: #166534; font-weight: 800; font-size: 11px; padding: 4px 10px; border-radius: 6px;"
                    if is_likely else
                    "background-color: #fef3c7; color: #92400e; font-weight: 800; font-size: 11px; padding: 4px 10px; border-radius: 6px;"
                )
                top_row.addWidget(badge)

                lbl_fid = QLabel(f"<b>Found Item: [{m.get('found_id')}]</b> {m.get('item_name')}")
                lbl_fid.setStyleSheet("font-size: 13px; font-weight: 700; color: #0f172a;")
                top_row.addWidget(lbl_fid)
                top_row.addStretch()

                btn_view = QPushButton("View in AI Matches →")
                btn_view.setProperty("class", "primaryBtn")
                btn_view.clicked.connect(lambda: self.navigate_to(7))
                top_row.addWidget(btn_view)
                cl.addLayout(top_row)

                grid = QGridLayout()
                grid.addWidget(QLabel("<b>Category:</b>"), 0, 0)
                grid.addWidget(QLabel(f"{m.get('category', '').capitalize()}"), 0, 1)
                grid.addWidget(QLabel("<b>Colour:</b>"), 0, 2)
                grid.addWidget(QLabel(f"{str(m.get('colour', '')).capitalize() or '-'}"), 0, 3)

                grid.addWidget(QLabel("<b>Brand:</b>"), 1, 0)
                grid.addWidget(QLabel(f"{m.get('brand') or '-'}"), 1, 1)
                grid.addWidget(QLabel("<b>Date Found:</b>"), 1, 2)
                grid.addWidget(QLabel(f"{m.get('date_found')}"), 1, 3)

                grid.addWidget(QLabel("<b>Location:</b>"), 2, 0)
                grid.addWidget(QLabel(f"{m.get('location')}"), 2, 1)
                grid.addWidget(QLabel("<b>Status:</b>"), 2, 2)
                grid.addWidget(QLabel(f"{m.get('status')}"), 2, 3)
                cl.addLayout(grid)

                lbl_desc = QLabel(f"<b>Description:</b> {m.get('description')}")
                lbl_desc.setStyleSheet("color: #475569; font-size: 12px;")
                lbl_desc.setWordWrap(True)
                cl.addWidget(lbl_desc)

                lbl_reasons = QLabel(f"<b>Compatibility:</b> {m.get('reasons_str')}")
                lbl_reasons.setStyleSheet("color: #0369a1; font-size: 11px; font-style: italic;")
                lbl_reasons.setWordWrap(True)
                cl.addWidget(lbl_reasons)

                self.live_lost_results_layout.addWidget(card)
        else:
            no_card = QFrame()
            no_card.setStyleSheet("background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 16px;")
            nl = QVBoxLayout(no_card)
            l1 = QLabel("ℹ️  No matching items found yet. We will notify you when a match becomes available.")
            l1.setStyleSheet("font-size: 13px; font-weight: 700; color: #1e293b;")
            l2 = QLabel(
                "Your report is registered with status <b>Searching</b>. "
                "Our AI matching engine continuously compares all incoming found reports in real-time."
            )
            l2.setStyleSheet("font-size: 12px; color: #64748b;")
            nl.addWidget(l1)
            nl.addWidget(l2)
            self.live_lost_results_layout.addWidget(no_card)

        self.live_lost_results_card.show()

    def _render_live_found_matches(self, match_res: Dict[str, Any]):
        """Render live matching results directly below the Report Found form."""
        while self.live_found_results_layout.count():
            item = self.live_found_results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        matches = match_res.get("matches", [])
        found_id = match_res.get("found_id", "")
        item_name = match_res.get("found_item_name", "Item")

        hdr = QLabel(f"🔍  LIVE AI MATCHING RESULTS FOR {item_name} [{found_id}]")
        hdr.setStyleSheet("font-size: 16px; font-weight: 800; color: #064e3b;")
        self.live_found_results_layout.addWidget(hdr)

        if matches:
            sub = QLabel(
                f"🎉  <b>Potential Owner Identified!</b> Automatic AI matching paired this found item with "
                f"<b>{len(matches)}</b> candidate student report(s). Review details below."
            )
            sub.setStyleSheet("color: #065f46; font-size: 13px; background-color: #ecfdf5; border: 1.5px solid #10b981; border-radius: 8px; padding: 12px;")
            sub.setWordWrap(True)
            self.live_found_results_layout.addWidget(sub)

            for m in matches:
                card = QFrame()
                card.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 10px; padding: 14px;")
                cl = QVBoxLayout(card)
                cl.setSpacing(8)

                top_row = QHBoxLayout()
                is_likely = m.get("match_percentage", 0) >= 60
                badge = QLabel(f"{m.get('match_percentage')}% MATCH  ({m.get('classification')})")
                badge.setStyleSheet(
                    "background-color: #dcfce7; color: #166534; font-weight: 800; font-size: 11px; padding: 4px 10px; border-radius: 6px;"
                    if is_likely else
                    "background-color: #fef3c7; color: #92400e; font-weight: 800; font-size: 11px; padding: 4px 10px; border-radius: 6px;"
                )
                top_row.addWidget(badge)

                lbl_lid = QLabel(f"<b>Lost Report: [{m.get('lost_id')}]</b> {m.get('item_name')} ({m.get('student_name')})")
                lbl_lid.setStyleSheet("font-size: 13px; font-weight: 700; color: #0f172a;")
                top_row.addWidget(lbl_lid)
                top_row.addStretch()

                btn_view = QPushButton("View in AI Matches →")
                btn_view.setProperty("class", "primaryBtn")
                btn_view.clicked.connect(lambda: self.navigate_to(7))
                top_row.addWidget(btn_view)
                cl.addLayout(top_row)

                grid = QGridLayout()
                grid.addWidget(QLabel("<b>Category:</b>"), 0, 0)
                grid.addWidget(QLabel(f"{m.get('category', '').capitalize()}"), 0, 1)
                grid.addWidget(QLabel("<b>Colour:</b>"), 0, 2)
                grid.addWidget(QLabel(f"{str(m.get('colour', '')).capitalize() or '-'}"), 0, 3)

                grid.addWidget(QLabel("<b>Brand:</b>"), 1, 0)
                grid.addWidget(QLabel(f"{m.get('brand') or '-'}"), 1, 1)
                grid.addWidget(QLabel("<b>Date Lost:</b>"), 1, 2)
                grid.addWidget(QLabel(f"{m.get('date_lost')}"), 1, 3)

                grid.addWidget(QLabel("<b>Location:</b>"), 2, 0)
                grid.addWidget(QLabel(f"{m.get('location')}"), 2, 1)
                grid.addWidget(QLabel("<b>Student ID:</b>"), 2, 2)
                grid.addWidget(QLabel(f"{m.get('student_id')}"), 2, 3)
                cl.addLayout(grid)

                lbl_desc = QLabel(f"<b>Student Description:</b> {m.get('description')}")
                lbl_desc.setStyleSheet("color: #475569; font-size: 12px;")
                lbl_desc.setWordWrap(True)
                cl.addWidget(lbl_desc)

                lbl_reasons = QLabel(f"<b>Compatibility:</b> {m.get('reasons_str')}")
                lbl_reasons.setStyleSheet("color: #0369a1; font-size: 11px; font-style: italic;")
                lbl_reasons.setWordWrap(True)
                cl.addWidget(lbl_reasons)

                self.live_found_results_layout.addWidget(card)
        else:
            no_card = QFrame()
            no_card.setStyleSheet("background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 16px;")
            nl = QVBoxLayout(no_card)
            l1 = QLabel("ℹ️  No matching items found yet. We will notify you when a match becomes available.")
            l1.setStyleSheet("font-size: 13px; font-weight: 700; color: #1e293b;")
            l2 = QLabel(
                "Found item registered into custody with status <b>Searching</b>. "
                "Any compatible lost report submitted by students will trigger an immediate notification."
            )
            l2.setStyleSheet("font-size: 12px; color: #64748b;")
            nl.addWidget(l1)
            nl.addWidget(l2)
            self.live_found_results_layout.addWidget(no_card)

        self.live_found_results_card.show()

    # --------------------------------------------------------------------------
    # Page 9: Notifications Center
    # --------------------------------------------------------------------------
    def _build_notifications_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 20, 30, 24)
        layout.setSpacing(16)

        hdr_row = QHBoxLayout()
        left_h = QVBoxLayout()
        lbl_t = QLabel("🔔  Notification Center & Live Match Alerts")
        lbl_t.setStyleSheet("font-size: 18px; font-weight: 800; color: #064e3b;")
        lbl_s = QLabel("Real-time in-app notifications for candidate matches, dispute warnings, and item status updates.")
        lbl_s.setStyleSheet("color: #64748b; font-size: 12px;")
        left_h.addWidget(lbl_t)
        left_h.addWidget(lbl_s)
        hdr_row.addLayout(left_h)
        hdr_row.addStretch()

        btn_mark_all = QPushButton("✔️ Mark All as Read")
        btn_mark_all.setProperty("class", "secondaryBtn")
        btn_mark_all.clicked.connect(self._mark_all_notifs_read)
        hdr_row.addWidget(btn_mark_all)
        layout.addLayout(hdr_row)

        self.notif_cards_container = QVBoxLayout()
        self.notif_cards_container.setSpacing(12)
        layout.addLayout(self.notif_cards_container)
        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def _mark_all_notifs_read(self):
        database.mark_all_notifications_read()
        self.refresh_all_data()

    def _populate_notifications_cards(self):
        if not hasattr(self, "notif_cards_container"):
            return
        while self.notif_cards_container.count():
            item = self.notif_cards_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        notifs = database.get_all_notifications(limit=50)
        if not notifs:
            no_card = QFrame()
            no_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 30px;")
            nl = QVBoxLayout(no_card)
            lbl_none = QLabel("✔ All Caught Up! No notifications at this time.")
            lbl_none.setStyleSheet("font-size: 15px; font-weight: 700; color: #065f46;")
            lbl_sub = QLabel("When candidate matches are discovered or claim updates occur, alerts will appear here automatically.")
            lbl_sub.setStyleSheet("color: #64748b; font-size: 12px;")
            nl.addWidget(lbl_none)
            nl.addWidget(lbl_sub)
            self.notif_cards_container.addWidget(no_card)
            return

        for n in notifs:
            card = QFrame()
            is_unread = n.get("is_read") == 0
            border_col = "#10b981" if is_unread else "#e2e8f0"
            bg_col = "#f0fdf4" if is_unread else "#ffffff"
            card.setStyleSheet(f"background-color: {bg_col}; border: 1.5px solid {border_col}; border-radius: 10px; padding: 14px;")
            cl = QVBoxLayout(card)
            cl.setSpacing(6)

            top_row = QHBoxLayout()
            ntype = n.get("notification_type", "match_found")
            if ntype == "match_found":
                badge = QLabel("✨ AI MATCH FOUND")
                badge.setStyleSheet("background-color: #dcfce7; color: #166534; font-weight: 800; font-size: 10px; padding: 3px 8px; border-radius: 4px;")
            elif ntype == "double_claim":
                badge = QLabel("⚠️ DOUBLE CLAIM CONFLICT")
                badge.setStyleSheet("background-color: #fee2e2; color: #991b1b; font-weight: 800; font-size: 10px; padding: 3px 8px; border-radius: 4px;")
            else:
                badge = QLabel("ℹ️ STATUS UPDATE")
                badge.setStyleSheet("background-color: #e0f2fe; color: #075985; font-weight: 800; font-size: 10px; padding: 3px 8px; border-radius: 4px;")
            top_row.addWidget(badge)

            if is_unread:
                un_badge = QLabel("● NEW")
                un_badge.setStyleSheet("background-color: #10b981; color: #ffffff; font-weight: 800; font-size: 10px; padding: 3px 8px; border-radius: 4px;")
                top_row.addWidget(un_badge)

            lbl_title = QLabel(f"<b>{n.get('title')}</b>")
            lbl_title.setStyleSheet("font-size: 13px; color: #0f172a;")
            top_row.addWidget(lbl_title)
            top_row.addStretch()

            lbl_time = QLabel(f"{n.get('created_at', '')}")
            lbl_time.setStyleSheet("font-size: 11px; color: #94a3b8;")
            top_row.addWidget(lbl_time)
            cl.addLayout(top_row)

            lbl_msg = QLabel(n.get("message", ""))
            lbl_msg.setStyleSheet("font-size: 12px; color: #334155; line-height: 1.4;")
            lbl_msg.setWordWrap(True)
            cl.addWidget(lbl_msg)

            action_row = QHBoxLayout()
            if n.get("match_id"):
                btn_goto = QPushButton("View AI Match Details →")
                btn_goto.setProperty("class", "primaryBtn")
                btn_goto.clicked.connect(lambda ch=False, nid=n["id"]: (database.mark_notification_read(nid), self.navigate_to(7)))
                action_row.addWidget(btn_goto)
            elif ntype == "double_claim":
                btn_goto = QPushButton("Open Double Claim Management →")
                btn_goto.setProperty("class", "primaryBtn")
                btn_goto.clicked.connect(lambda ch=False, nid=n["id"]: (database.mark_notification_read(nid), self.navigate_to(6)))
                action_row.addWidget(btn_goto)

            if is_unread:
                btn_read = QPushButton("Mark Read")
                btn_read.setProperty("class", "secondaryBtn")
                btn_read.clicked.connect(lambda ch=False, nid=n["id"]: (database.mark_notification_read(nid), self.refresh_all_data()))
                action_row.addWidget(btn_read)

            action_row.addStretch()
            cl.addLayout(action_row)

            self.notif_cards_container.addWidget(card)


# Compatibility alias
MainWindow = CITCampusMainWindow


def launch_cit_gui():
    """Launch the CIT Campus Smart Lost & Found Portal."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = CITCampusMainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    launch_cit_gui()

