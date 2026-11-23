"""
CET Campus - Smart Lost & Found Portal
Clean, professional, fully functional Windows desktop application.
Uses PySide6, SQLite, existing LLM extraction, and deterministic matching engine.
"""

from datetime import datetime
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QDate, QSize, Qt, QTimer
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
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
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

from config import ALLOWED_COLOURS, ALLOWED_ITEMS, ALLOWED_PLACES
import database

# ------------------------------------------------------------------------------
# Professional Green and White Modern Theme (QSS)
# ------------------------------------------------------------------------------
CET_THEME_QSS = """
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
    font-size: 17px;
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
    padding: 12px 28px;
}

#headerTitle {
    font-size: 20px;
    font-weight: bold;
    color: #064e3b;
}

#headerSubtitle {
    font-size: 12px;
    color: #64748b;
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
    padding: 20px;
}

QFrame.reportOptionCard:hover {
    border: 2px solid #10b981;
    background-color: #f0fdf4;
}

/* Standard Buttons */
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

        lbl_hint = QLabel(hint_text)
        lbl_hint.setProperty("class", "statHint")
        layout.addWidget(lbl_hint)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.callback:
            self.callback()
        super().mousePressEvent(event)

    def set_value(self, val: str):
        self.lbl_value.setText(val)


# ------------------------------------------------------------------------------
# Main Application Window
# ------------------------------------------------------------------------------
class CETCampusMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CET CAMPUS – Smart Lost & Found Portal")
        self.resize(1260, 820)
        self.setMinimumSize(1040, 680)

        # Initialize SQLite database and run initial matching
        database.init_database()
        database.run_database_matching()

        # Temporary photo storage
        self.selected_lost_photo: Optional[str] = None
        self.selected_found_photo: Optional[str] = None

        # Apply Global Styling
        self.setStyleSheet(CET_THEME_QSS)

        # Build Main Frame
        self._build_ui()

        # Refresh all data on startup
        self.refresh_all_data()

    def _build_ui(self):
        root_widget = QWidget()
        self.setCentralWidget(root_widget)

        root_layout = QHBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Left Sidebar
        self._build_sidebar(root_layout)

        # 2. Main Area (Top Header + Stacked Pages)
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._build_header(main_layout)

        self.pages_stack = QStackedWidget()
        main_layout.addWidget(self.pages_stack, 1)

        # Build Pages (Only the 7 essential navigation views)
        self.page_dashboard = self._build_dashboard_page()          # 0
        self.page_report_lost = self._build_report_lost_page()      # 1
        self.page_report_found = self._build_report_found_page()    # 2
        self.page_lost_items = self._build_lost_items_page()        # 3
        self.page_found_items = self._build_found_items_page()      # 4
        self.page_ai_matches = self._build_ai_matches_page()        # 5
        self.page_successful = self._build_successful_matches_page()# 6

        self.pages_stack.addWidget(self.page_dashboard)
        self.pages_stack.addWidget(self.page_report_lost)
        self.pages_stack.addWidget(self.page_report_found)
        self.pages_stack.addWidget(self.page_lost_items)
        self.pages_stack.addWidget(self.page_found_items)
        self.pages_stack.addWidget(self.page_ai_matches)
        self.pages_stack.addWidget(self.page_successful)

        root_layout.addWidget(main_container, 1)

    # --------------------------------------------------------------------------
    # Left Sidebar Navigation (7 Options Only)
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

        lbl_top = QLabel("CET CAMPUS")
        lbl_top.setObjectName("portalTitle")
        tb_l.addWidget(lbl_top)

        lbl_sub = QLabel("Smart Lost & Found")
        lbl_sub.setObjectName("portalSub")
        tb_l.addWidget(lbl_sub)
        layout.addWidget(title_box)

        # Navigation Options
        self.sidebar_buttons: List[QPushButton] = []
        nav_items = [
            ("📊  Dashboard", 0),
            ("➕  Report Lost Item", 1),
            ("📥  Report Found Item", 2),
            ("📋  Lost Items", 3),
            ("📦  Found Items", 4),
            ("🤖  AI Matches", 5),
            ("✔️  Successful Matches", 6),
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
        lbl_foot = QLabel("Campus Services\nDecision Support System")
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

        # Update Header Title
        titles = [
            ("Dashboard", "Campus property overview and real-time statistics"),
            ("Report Lost Item", "Submit a lost property incident report with detailed characteristics"),
            ("Report Found Item", "Register recovered campus property for owner verification"),
            ("Lost Items", "All student-submitted lost property incident reports"),
            ("Found Items", "All turned-in recovered items currently in campus custody"),
            ("AI Matches", "Pending candidate pairs awaiting Help Desk verification"),
            ("Successful Matches", "Officially confirmed and verified property handoffs"),
        ]
        if page_index < len(titles):
            title, subtitle = titles[page_index]
            self.header_page_title.setText(title)
            self.header_page_sub.setText(subtitle)

        # Refresh page data on navigation
        if page_index in (0, 3, 4, 5, 6):
            self.refresh_all_data()

    # --------------------------------------------------------------------------
    # Application Header
    # --------------------------------------------------------------------------
    def _build_header(self, parent_layout: QVBoxLayout):
        header = QFrame()
        header.setObjectName("topHeaderBar")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(28, 14, 28, 14)

        left_box = QVBoxLayout()
        self.header_page_title = QLabel("Dashboard")
        self.header_page_title.setObjectName("headerTitle")
        self.header_page_sub = QLabel("Campus property overview and real-time statistics")
        self.header_page_sub.setObjectName("headerSubtitle")
        left_box.addWidget(self.header_page_title)
        left_box.addWidget(self.header_page_sub)
        layout.addLayout(left_box)

        layout.addStretch()

        # Campus System Badge
        portal_badge = QLabel("CET CAMPUS  |  Smart Lost & Found Portal")
        portal_badge.setStyleSheet(
            "background-color: #ecfdf5; color: #065f46; border: 1px solid #10b981; "
            "border-radius: 14px; padding: 6px 16px; font-weight: 700; font-size: 12px;"
        )
        layout.addWidget(portal_badge)

        parent_layout.addWidget(header)

    # --------------------------------------------------------------------------
    # Page 0: Main Dashboard (4 Cards, 2 Options, 2 Recent Tables Only)
    # --------------------------------------------------------------------------
    def _build_dashboard_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 20, 28, 24)
        layout.setSpacing(22)

        # 1. FOUR STATISTIC CARDS (Clickable)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(14)

        self.card_lost = ClickableStatCard(
            "TOTAL LOST REPORTS",
            "0",
            "Click to view all lost items →",
            lambda: self.navigate_to(3),
        )
        self.card_found = ClickableStatCard(
            "TOTAL FOUND REPORTS",
            "0",
            "Click to view all found items →",
            lambda: self.navigate_to(4),
        )
        self.card_success = ClickableStatCard(
            "SUCCESSFUL MATCHES",
            "0",
            "Click to view verified matches →",
            lambda: self.navigate_to(6),
        )
        self.card_pending = ClickableStatCard(
            "PENDING MATCHES",
            "0",
            "Click to view AI candidate matches →",
            lambda: self.navigate_to(5),
        )

        stats_layout.addWidget(self.card_lost)
        stats_layout.addWidget(self.card_found)
        stats_layout.addWidget(self.card_success)
        stats_layout.addWidget(self.card_pending)
        layout.addLayout(stats_layout)

        # 2. REPORTING SECTION: TWO LARGE ATTRACTIVE OPTIONS
        rep_box = QFrame()
        rep_l = QHBoxLayout(rep_box)
        rep_l.setContentsMargins(0, 0, 0, 0)
        rep_l.setSpacing(16)

        # Option 1: Report Lost Item Card
        opt_lost_card = QFrame()
        opt_lost_card.setProperty("class", "reportOptionCard")
        opt_lost_card.setCursor(QCursor(Qt.PointingHandCursor))
        opt_lost_card.mousePressEvent = lambda e: self.navigate_to(1)

        ol_layout = QVBoxLayout(opt_lost_card)
        ol_layout.setSpacing(8)

        lbl_ol_title = QLabel("➕  REPORT LOST ITEM")
        lbl_ol_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #064e3b;")
        ol_layout.addWidget(lbl_ol_title)

        lbl_ol_desc = QLabel(
            "Misplaced something on campus? Submit a lost report with category, colour, "
            "brand, date, location, and photograph. Our AI matching engine will automatically compare "
            "it against all turned-in found property."
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

        lbl_of_title = QLabel("📥  REPORT FOUND ITEM")
        lbl_of_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #064e3b;")
        of_layout.addWidget(lbl_of_title)

        lbl_of_desc = QLabel(
            "Found an item on campus grounds? Register the recovered item with location, "
            "description, and photograph to help Campus Services verify and return it "
            "to its rightful student owner."
        )
        lbl_of_desc.setStyleSheet("color: #475569; font-size: 12px; line-height: 1.4;")
        lbl_of_desc.setWordWrap(True)
        of_layout.addWidget(lbl_of_desc)

        btn_open_found = QPushButton("Open Found Item Form →")
        btn_open_found.setProperty("class", "primaryBtn")
        btn_open_found.clicked.connect(lambda: self.navigate_to(2))
        of_layout.addWidget(btn_open_found, 0, Qt.AlignLeft)
        rep_l.addWidget(opt_found_card, 1)

        layout.addWidget(rep_box)

        # 3. RECENT ITEMS: EXACTLY TWO SECTIONS AT THE BOTTOM
        # Section A: Recently Lost Items
        sec_lost_header = QHBoxLayout()
        lbl_sec_lost = QLabel("📋  RECENTLY LOST ITEMS")
        lbl_sec_lost.setStyleSheet("font-size: 15px; font-weight: 800; color: #0f172a;")
        sec_lost_header.addWidget(lbl_sec_lost)
        sec_lost_header.addStretch()

        btn_view_lost = QPushButton("View All Lost Items →")
        btn_view_lost.setProperty("class", "secondaryBtn")
        btn_view_lost.clicked.connect(lambda: self.navigate_to(3))
        sec_lost_header.addWidget(btn_view_lost)
        layout.addLayout(sec_lost_header)

        self.dash_table_lost = QTableWidget(0, 7)
        self.dash_table_lost.setHorizontalHeaderLabels(["Item Name", "Category", "Colour", "Brand", "Date Lost", "Location", "Status"])
        self.dash_table_lost.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.dash_table_lost.setFixedHeight(180)
        self.dash_table_lost.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dash_table_lost.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.dash_table_lost)

        # Section B: Recently Found Items
        sec_found_header = QHBoxLayout()
        lbl_sec_found = QLabel("📦  RECENTLY FOUND ITEMS")
        lbl_sec_found.setStyleSheet("font-size: 15px; font-weight: 800; color: #0f172a;")
        sec_found_header.addWidget(lbl_sec_found)
        sec_found_header.addStretch()

        btn_view_found = QPushButton("View All Found Items →")
        btn_view_found.setProperty("class", "secondaryBtn")
        btn_view_found.clicked.connect(lambda: self.navigate_to(4))
        sec_found_header.addWidget(btn_view_found)
        layout.addLayout(sec_found_header)

        self.dash_table_found = QTableWidget(0, 7)
        self.dash_table_found.setHorizontalHeaderLabels(["Item Name", "Category", "Colour", "Brand", "Date Found", "Location", "Status"])
        self.dash_table_found.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.dash_table_found.setFixedHeight(180)
        self.dash_table_found.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dash_table_found.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.dash_table_found)

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
        lbl_t = QLabel("Report a Lost Item")
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

        # Row 0: Item Name & Category
        grid.addWidget(QLabel("Item Name *"), 0, 0)
        self.form_lost_name = QLineEdit()
        self.form_lost_name.setPlaceholderText("e.g. Black Samsung Galaxy Phone")
        grid.addWidget(self.form_lost_name, 0, 1)

        grid.addWidget(QLabel("Category *"), 0, 2)
        self.form_lost_category = QComboBox()
        self.form_lost_category.addItems(sorted(list(ALLOWED_ITEMS)))
        grid.addWidget(self.form_lost_category, 0, 3)

        # Row 1: Colour & Brand
        grid.addWidget(QLabel("Colour"), 1, 0)
        self.form_lost_colour = QComboBox()
        self.form_lost_colour.addItem("Select colour...")
        self.form_lost_colour.addItems(sorted(list(ALLOWED_COLOURS)))
        grid.addWidget(self.form_lost_colour, 1, 1)

        grid.addWidget(QLabel("Brand"), 1, 2)
        self.form_lost_brand = QLineEdit()
        self.form_lost_brand.setPlaceholderText("e.g. Samsung, Apple, Sony, Nike")
        grid.addWidget(self.form_lost_brand, 1, 3)

        # Row 2: Date Lost & Location
        grid.addWidget(QLabel("Date Lost *"), 2, 0)
        self.form_lost_date = QDateEdit()
        self.form_lost_date.setCalendarPopup(True)
        self.form_lost_date.setDate(QDate.currentDate())
        grid.addWidget(self.form_lost_date, 2, 1)

        grid.addWidget(QLabel("Location Lost *"), 2, 2)
        self.form_lost_location = QComboBox()
        self.form_lost_location.addItems(sorted(list(ALLOWED_PLACES)))
        grid.addWidget(self.form_lost_location, 2, 3)

        # Row 3: Detailed Description
        grid.addWidget(QLabel("Detailed Description *"), 3, 0)
        self.form_lost_desc = QTextEdit()
        self.form_lost_desc.setPlaceholderText("Provide specific details: scratches, lock-screen wallpaper, stickers, accessories, etc.")
        self.form_lost_desc.setFixedHeight(85)
        grid.addWidget(self.form_lost_desc, 3, 1, 1, 3)

        # Row 4: Upload Photograph
        grid.addWidget(QLabel("Photograph"), 4, 0)
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

        # Row 6: Student Info
        grid.addWidget(QLabel("Student Name *"), 6, 0)
        self.form_lost_student_name = QLineEdit()
        self.form_lost_student_name.setPlaceholderText("Full Name")
        grid.addWidget(self.form_lost_student_name, 6, 1)

        grid.addWidget(QLabel("Student ID *"), 6, 2)
        self.form_lost_student_id = QLineEdit()
        self.form_lost_student_id.setPlaceholderText("e.g. CET2026-891")
        grid.addWidget(self.form_lost_student_id, 6, 3)

        # Row 7: Contact Information
        grid.addWidget(QLabel("Contact Info *"), 7, 0)
        self.form_lost_contact = QLineEdit()
        self.form_lost_contact.setPlaceholderText("Phone or university email")
        grid.addWidget(self.form_lost_contact, 7, 1, 1, 3)

        # Row 8: Submit Button
        btn_submit = QPushButton("Submit Lost Report")
        btn_submit.setProperty("class", "primaryBtn")
        btn_submit.setFixedHeight(40)
        btn_submit.clicked.connect(self._submit_lost_report)
        grid.addWidget(btn_submit, 8, 1, 1, 2)

        layout.addWidget(form_card)
        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def _browse_lost_photo(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Item Photograph", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file:
            self.selected_lost_photo = file
            self.lbl_lost_photo_path.setText(Path(file).name)

    def _submit_lost_report(self):
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
        contact = self.form_lost_contact.text().strip()

        if not item_name or not desc or not s_name or not contact:
            QMessageBox.warning(self, "Required Fields Missing", "Please fill in all required fields (Item Name, Description, Student Name, Contact).")
            return

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

        # Initiate matching against all found reports
        database.run_database_matching()
        self.refresh_all_data()

        QMessageBox.showinfo(
            "Lost Report Submitted",
            f"Your lost report has been registered under ID: {new_id}.\n\n"
            f"The AI matching algorithm has evaluated your submission against all campus found property."
        )

        # Clear form and navigate to Lost Items
        self.form_lost_name.clear()
        self.form_lost_brand.clear()
        self.form_lost_desc.clear()
        self.form_lost_student_name.clear()
        self.form_lost_student_id.clear()
        self.form_lost_contact.clear()
        self.selected_lost_photo = None
        self.lbl_lost_photo_path.setText("No photo selected")
        self.navigate_to(3)

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
        lbl_t = QLabel("Report a Found Item")
        lbl_t.setStyleSheet("font-size: 18px; font-weight: 800; color: #064e3b;")
        lbl_s = QLabel("Register recovered campus property. The AI matching algorithm will check for matching student lost reports.")
        lbl_s.setStyleSheet("color: #64748b; font-size: 12px;")
        header_box.addWidget(lbl_t)
        header_box.addWidget(lbl_s)
        layout.addLayout(header_box)

        # Form Card
        form_card = QFrame()
        form_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px;")
        grid = QGridLayout(form_card)
        grid.setSpacing(14)

        # Row 0: Item Name & Category
        grid.addWidget(QLabel("Item Name *"), 0, 0)
        self.form_found_name = QLineEdit()
        self.form_found_name.setPlaceholderText("e.g. Silver Apple MacBook Air")
        grid.addWidget(self.form_found_name, 0, 1)

        grid.addWidget(QLabel("Category *"), 0, 2)
        self.form_found_category = QComboBox()
        self.form_found_category.addItems(sorted(list(ALLOWED_ITEMS)))
        grid.addWidget(self.form_found_category, 0, 3)

        # Row 1: Colour & Brand
        grid.addWidget(QLabel("Colour"), 1, 0)
        self.form_found_colour = QComboBox()
        self.form_found_colour.addItem("Select colour...")
        self.form_found_colour.addItems(sorted(list(ALLOWED_COLOURS)))
        grid.addWidget(self.form_found_colour, 1, 1)

        grid.addWidget(QLabel("Brand"), 1, 2)
        self.form_found_brand = QLineEdit()
        self.form_found_brand.setPlaceholderText("e.g. Apple, Samsung, Sony")
        grid.addWidget(self.form_found_brand, 1, 3)

        # Row 2: Date Found & Location
        grid.addWidget(QLabel("Date Found *"), 2, 0)
        self.form_found_date = QDateEdit()
        self.form_found_date.setCalendarPopup(True)
        self.form_found_date.setDate(QDate.currentDate())
        grid.addWidget(self.form_found_date, 2, 1)

        grid.addWidget(QLabel("Location Found *"), 2, 2)
        self.form_found_location = QComboBox()
        self.form_found_location.addItems(sorted(list(ALLOWED_PLACES)))
        grid.addWidget(self.form_found_location, 2, 3)

        # Row 3: Detailed Description
        grid.addWidget(QLabel("Detailed Description *"), 3, 0)
        self.form_found_desc = QTextEdit()
        self.form_found_desc.setPlaceholderText("Describe where it was found, table/room number, condition, accessories...")
        self.form_found_desc.setFixedHeight(85)
        grid.addWidget(self.form_found_desc, 3, 1, 1, 3)

        # Row 4: Upload Photograph
        grid.addWidget(QLabel("Photograph"), 4, 0)
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

        # Row 6: Finder Name
        grid.addWidget(QLabel("Finder Name *"), 6, 0)
        self.form_found_finder = QLineEdit()
        self.form_found_finder.setPlaceholderText("Student / Security Officer Name")
        grid.addWidget(self.form_found_finder, 6, 1)

        grid.addWidget(QLabel("Contact Info *"), 6, 2)
        self.form_found_contact = QLineEdit()
        self.form_found_contact.setPlaceholderText("Phone or email")
        grid.addWidget(self.form_found_contact, 6, 3)

        # Row 7: Submit Button
        btn_submit = QPushButton("Submit Found Report")
        btn_submit.setProperty("class", "primaryBtn")
        btn_submit.setFixedHeight(40)
        btn_submit.clicked.connect(self._submit_found_report)
        grid.addWidget(btn_submit, 7, 1, 1, 2)

        layout.addWidget(form_card)
        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def _browse_found_photo(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Item Photograph", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file:
            self.selected_found_photo = file
            self.lbl_found_photo_path.setText(Path(file).name)

    def _submit_found_report(self):
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
        contact = self.form_found_contact.text().strip()

        if not item_name or not desc or not finder or not contact:
            QMessageBox.warning(self, "Required Fields Missing", "Please fill in all required fields (Item Name, Description, Finder Name, Contact).")
            return

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

        # Run AI matching against lost items
        database.run_database_matching()
        self.refresh_all_data()

        QMessageBox.showinfo(
            "Found Report Submitted",
            f"The found item has been registered under ID: {new_id}.\n\n"
            f"The AI matching algorithm has evaluated your submission against all student lost reports."
        )

        self.form_found_name.clear()
        self.form_found_brand.clear()
        self.form_found_desc.clear()
        self.form_found_finder.clear()
        self.form_found_contact.clear()
        self.selected_found_photo = None
        self.lbl_found_photo_path.setText("No photo selected")
        self.navigate_to(4)

    # --------------------------------------------------------------------------
    # Page 3: Lost Items List Page
    # --------------------------------------------------------------------------
    def _build_lost_items_page(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 20, 28, 24)
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
        self.table_all_lost = QTableWidget(0, 8)
        self.table_all_lost.setHorizontalHeaderLabels(["ID", "Item Name", "Category", "Colour", "Brand", "Date Lost", "Location", "Status"])
        self.table_all_lost.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
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
            self.table_all_lost.setItem(row, 0, QTableWidgetItem(r.get("id", "")))
            self.table_all_lost.setItem(row, 1, QTableWidgetItem(r.get("item_name", "")))
            self.table_all_lost.setItem(row, 2, QTableWidgetItem(r.get("category", "").capitalize()))
            self.table_all_lost.setItem(row, 3, QTableWidgetItem((r.get("colour") or "-").capitalize()))
            self.table_all_lost.setItem(row, 4, QTableWidgetItem(r.get("brand") or "-"))
            self.table_all_lost.setItem(row, 5, QTableWidgetItem(r.get("date_lost", "")))
            self.table_all_lost.setItem(row, 6, QTableWidgetItem(r.get("location", "")))
            self.table_all_lost.setItem(row, 7, QTableWidgetItem(r.get("status", "Reported Lost")))

    # --------------------------------------------------------------------------
    # Page 4: Found Items List Page
    # --------------------------------------------------------------------------
    def _build_found_items_page(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 20, 28, 24)
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
        self.table_all_found = QTableWidget(0, 8)
        self.table_all_found.setHorizontalHeaderLabels(["ID", "Item Name", "Category", "Colour", "Brand", "Date Found", "Location", "Status"])
        self.table_all_found.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
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
            self.table_all_found.setItem(row, 0, QTableWidgetItem(r.get("id", "")))
            self.table_all_found.setItem(row, 1, QTableWidgetItem(r.get("item_name", "")))
            self.table_all_found.setItem(row, 2, QTableWidgetItem(r.get("category", "").capitalize()))
            self.table_all_found.setItem(row, 3, QTableWidgetItem((r.get("colour") or "-").capitalize()))
            self.table_all_found.setItem(row, 4, QTableWidgetItem(r.get("brand") or "-"))
            self.table_all_found.setItem(row, 5, QTableWidgetItem(r.get("date_found", "")))
            self.table_all_found.setItem(row, 6, QTableWidgetItem(r.get("location", "")))
            self.table_all_found.setItem(row, 7, QTableWidgetItem(r.get("status", "In Custody")))

    # --------------------------------------------------------------------------
    # Page 5: AI Matches (Pending Candidate Pairs)
    # --------------------------------------------------------------------------
    def _build_ai_matches_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self.ai_matches_layout = QVBoxLayout(container)
        self.ai_matches_layout.setContentsMargins(28, 20, 28, 24)
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
        # Clear existing match cards
        while self.matches_cards_container.count():
            item = self.matches_cards_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        pending_list = database.get_pending_matches()

        if not pending_list:
            no_card = QFrame()
            no_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 30px;")
            nl = QVBoxLayout(no_card)
            lbl_none = QLabel("✔ No Pending Matches Awaiting Verification")
            lbl_none.setStyleSheet("font-size: 15px; font-weight: 700; color: #065f46;")
            lbl_sub = QLabel("All candidate matches have either been verified or there are no new matching items at this time.")
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

            lbl_expl = QLabel(f"<b>AI Explanation:</b> {m['explanation']}")
            lbl_expl.setStyleSheet("color: #334155; font-size: 12px;")
            lbl_expl.setWordWrap(True)
            el.addWidget(lbl_expl)

            cl.addWidget(exp_box)
            self.matches_cards_container.addWidget(card)

    def _open_verification_modal(self, m: Dict[str, Any]):
        """Open staff verification modal before granting official match handoff."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Help Desk Verification - Confirm Ownership")
        dialog.setFixedWidth(520)
        dialog.setStyleSheet(CET_THEME_QSS)

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
    # Page 6: Successful Matches (Confirmed & Verified)
    # --------------------------------------------------------------------------
    def _build_successful_matches_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self.succ_matches_layout = QVBoxLayout(container)
        self.succ_matches_layout.setContentsMargins(28, 20, 28, 24)
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
        """Update all 4 dashboard statistic cards, tables, and AI matching views."""
        stats = database.get_dashboard_statistics()

        # Update 4 Clickable Dashboard Cards
        self.card_lost.set_value(str(stats["total_lost"]))
        self.card_found.set_value(str(stats["total_found"]))
        self.card_success.set_value(str(stats["successful_matches"]))
        self.card_pending.set_value(str(stats["pending_matches"]))

        # Populate Dashboard Recent Lost Items (Top 5)
        all_lost = database.get_all_lost_reports()
        recent_lost = all_lost[:5]
        self.dash_table_lost.setRowCount(len(recent_lost))
        for row, r in enumerate(recent_lost):
            self.dash_table_lost.setItem(row, 0, QTableWidgetItem(r.get("item_name", "")))
            self.dash_table_lost.setItem(row, 1, QTableWidgetItem(r.get("category", "").capitalize()))
            self.dash_table_lost.setItem(row, 2, QTableWidgetItem((r.get("colour") or "-").capitalize()))
            self.dash_table_lost.setItem(row, 3, QTableWidgetItem(r.get("brand") or "-"))
            self.dash_table_lost.setItem(row, 4, QTableWidgetItem(r.get("date_lost", "")))
            self.dash_table_lost.setItem(row, 5, QTableWidgetItem(r.get("location", "")))
            self.dash_table_lost.setItem(row, 6, QTableWidgetItem(r.get("status", "Reported Lost")))

        # Populate Dashboard Recent Found Items (Top 5)
        all_found = database.get_all_found_reports()
        recent_found = all_found[:5]
        self.dash_table_found.setRowCount(len(recent_found))
        for row, r in enumerate(recent_found):
            self.dash_table_found.setItem(row, 0, QTableWidgetItem(r.get("item_name", "")))
            self.dash_table_found.setItem(row, 1, QTableWidgetItem(r.get("category", "").capitalize()))
            self.dash_table_found.setItem(row, 2, QTableWidgetItem((r.get("colour") or "-").capitalize()))
            self.dash_table_found.setItem(row, 3, QTableWidgetItem(r.get("brand") or "-"))
            self.dash_table_found.setItem(row, 4, QTableWidgetItem(r.get("date_found", "")))
            self.dash_table_found.setItem(row, 5, QTableWidgetItem(r.get("location", "")))
            self.dash_table_found.setItem(row, 6, QTableWidgetItem(r.get("status", "In Custody")))

        # Populate Full Tables
        self._populate_lost_table_rows(all_lost)
        self._populate_found_table_rows(all_found)

        # Populate AI Matches Cards and Successful Matches Cards
        self._populate_ai_matches_cards()
        self._populate_successful_matches_cards()


def launch_cet_gui():
    """Launch the CET Campus Smart Lost & Found Portal."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = CETCampusMainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    launch_cet_gui()
