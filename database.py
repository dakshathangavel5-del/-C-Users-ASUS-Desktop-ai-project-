"""
Database module for CIT Campus Smart Lost & Found Portal.
Uses SQLite for persistent storage of lost reports, found reports, and verified matches.
"""

from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from config import DATA_DIR, FOUND_CSV_PATH, LOST_CSV_PATH
from file_handler import read_report

DB_PATH = DATA_DIR / "cit_campus.db"


def get_db_connection(timeout: float = 30.0) -> sqlite3.Connection:
    """Establish and return SQLite database connection with row dictionary access and WAL mode."""
    conn = sqlite3.connect(str(DB_PATH), timeout=timeout)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception:
        pass
    return conn


def init_database():
    """Create tables and initialize with existing CSV dataset if empty."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Lost Reports Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lost_reports (
            id TEXT PRIMARY KEY,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            colour TEXT,
            brand TEXT,
            date_lost TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT,
            photo_path TEXT,
            student_name TEXT,
            student_id TEXT,
            contact_info TEXT,
            status TEXT DEFAULT 'Reported Lost',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Found Reports Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS found_reports (
            id TEXT PRIMARY KEY,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            colour TEXT,
            brand TEXT,
            date_found TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT,
            photo_path TEXT,
            finder_name TEXT,
            contact_info TEXT,
            status TEXT DEFAULT 'In Custody',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Matches Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lost_id TEXT NOT NULL,
            found_id TEXT NOT NULL,
            match_score INTEGER NOT NULL,
            match_percentage INTEGER NOT NULL,
            classification TEXT NOT NULL,
            reasons TEXT,
            explanation TEXT,
            status TEXT DEFAULT 'Pending Verification',
            verified_at TEXT,
            verified_by TEXT,
            verification_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(lost_id, found_id),
            FOREIGN KEY (lost_id) REFERENCES lost_reports(id),
            FOREIGN KEY (found_id) REFERENCES found_reports(id)
        )
    """)

    # 4. Notifications Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_type TEXT NOT NULL,
            recipient_name TEXT,
            recipient_contact TEXT,
            report_id TEXT NOT NULL,
            match_id INTEGER,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (match_id) REFERENCES matches(id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notif_report ON notifications(report_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notif_read ON notifications(is_read)")

    # Normalize legacy statuses to canonical 5 statuses
    cursor.execute("UPDATE lost_reports SET status = 'Returned to Owner' WHERE status = 'Matched & Returned'")
    cursor.execute("UPDATE found_reports SET status = 'Returned to Owner' WHERE status = 'Claimed & Released'")
    cursor.execute("UPDATE lost_reports SET status = 'Closed' WHERE status = 'Claim Closed (Alternate Winner)'")
    cursor.execute("UPDATE lost_reports SET status = 'Searching' WHERE status = 'Reported Lost'")
    cursor.execute("UPDATE found_reports SET status = 'Searching' WHERE status = 'In Custody'")

    conn.commit()

    # Seed with existing CSV records if lost_reports is empty
    cursor.execute("SELECT COUNT(*) FROM lost_reports")
    count_lost = cursor.fetchone()[0]

    if count_lost == 0 and LOST_CSV_PATH.exists() and FOUND_CSV_PATH.exists():
        _seed_from_csv(cursor)
        conn.commit()

    conn.close()


def _seed_from_csv(cursor: sqlite3.Cursor):
    """Seed SQLite database with existing 12 lost and 11 found reports from CSV."""
    from extractor import extract_information

    lost_records = read_report(LOST_CSV_PATH)
    for r in lost_records:
        ext = extract_information(r["report"])
        col_str = (ext.get("colour") or "").capitalize()
        brand_str = ext.get("brand") or ""
        item_str = (ext.get("item") or "Item").capitalize()
        name_parts = [p for p in (col_str, brand_str, item_str) if p]
        item_name = " ".join(name_parts) or r["report"][:30]
        cursor.execute("""
            INSERT OR IGNORE INTO lost_reports 
            (id, item_name, category, colour, brand, date_lost, location, description, student_name, student_id, contact_info, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r["id"],
            item_name,
            ext.get("item", "other"),
            ext.get("colour"),
            ext.get("brand"),
            r["date"],
            ext.get("place", "Campus Grounds") or "Campus Grounds",
            r["report"],
            "CIT Student",
            f"CIT{r['id']}",
            "student@cit.edu",
            "Reported Lost",
        ))

    found_records = read_report(FOUND_CSV_PATH)
    for r in found_records:
        ext = extract_information(r["report"])
        col_str = (ext.get("colour") or "").capitalize()
        brand_str = ext.get("brand") or ""
        item_str = (ext.get("item") or "Item").capitalize()
        name_parts = [p for p in (col_str, brand_str, item_str) if p]
        item_name = " ".join(name_parts) or r["report"][:30]
        cursor.execute("""
            INSERT OR IGNORE INTO found_reports 
            (id, item_name, category, colour, brand, date_found, location, description, finder_name, contact_info, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r["id"],
            item_name,
            ext.get("item", "other"),
            ext.get("colour"),
            ext.get("brand"),
            r["date"],
            ext.get("place", "Campus Grounds") or "Campus Grounds",
            r["report"],
            "Campus Security / Student",
            "security@cit.edu",
            "In Custody",
        ))


def get_all_lost_reports() -> List[Dict[str, Any]]:
    """Retrieve all lost reports sorted by date descending."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lost_reports ORDER BY date_lost DESC, id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_all_found_reports() -> List[Dict[str, Any]]:
    """Retrieve all found reports sorted by date descending."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM found_reports ORDER BY date_found DESC, id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def is_contact_number_registered(phone_raw: str, exclude_id: Optional[str] = None) -> bool:
    """
    Check existing student records in lost_reports to verify if the 10-digit mobile number
    is already registered to prevent duplicate submissions.
    """
    from validator import clean_mobile_number
    target_digits = clean_mobile_number(phone_raw)
    if not target_digits or len(target_digits) != 10:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()

    if exclude_id:
        cursor.execute("SELECT id, contact_info FROM lost_reports WHERE id != ?", (exclude_id,))
    else:
        cursor.execute("SELECT id, contact_info FROM lost_reports")

    rows = cursor.fetchall()
    conn.close()

    for r in rows:
        existing_contact = r["contact_info"] or ""
        existing_digits = clean_mobile_number(existing_contact)
        if existing_digits and existing_digits == target_digits:
            return True

    return False


def insert_lost_report(data: Dict[str, Any]) -> str:
    """Insert a new lost report into SQLite and return its new ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Generate new ID
    cursor.execute("SELECT id FROM lost_reports WHERE id LIKE 'L%' ORDER BY rowid DESC LIMIT 1")
    last = cursor.fetchone()
    if last and last[0].startswith("L"):
        try:
            num = int(last[0][1:]) + 1
            new_id = f"L{num:02d}"
        except ValueError:
            new_id = f"L{datetime.now().strftime('%M%S')}"
    else:
        new_id = "L01"

    cursor.execute("""
        INSERT INTO lost_reports 
        (id, item_name, category, colour, brand, date_lost, location, description, photo_path, student_name, student_id, contact_info, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        new_id,
        data.get("item_name", "Untitled Item"),
        data.get("category", "other"),
        data.get("colour"),
        data.get("brand"),
        data.get("date_lost", datetime.now().strftime("%Y-%m-%d")),
        data.get("location", "Campus Grounds"),
        data.get("description", ""),
        data.get("photo_path"),
        data.get("student_name", "Anonymous Student"),
        data.get("student_id", ""),
        data.get("contact_info", ""),
        "Searching",
    ))
    conn.commit()
    conn.close()
    return new_id


def insert_found_report(data: Dict[str, Any]) -> str:
    """Insert a new found report into SQLite and return its new ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Generate new ID
    cursor.execute("SELECT id FROM found_reports WHERE id LIKE 'F%' ORDER BY rowid DESC LIMIT 1")
    last = cursor.fetchone()
    if last and last[0].startswith("F"):
        try:
            num = int(last[0][1:]) + 1
            new_id = f"F{num:02d}"
        except ValueError:
            new_id = f"F{datetime.now().strftime('%M%S')}"
    else:
        new_id = "F01"

    cursor.execute("""
        INSERT INTO found_reports 
        (id, item_name, category, colour, brand, date_found, location, description, photo_path, finder_name, contact_info, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        new_id,
        data.get("item_name", "Untitled Item"),
        data.get("category", "other"),
        data.get("colour"),
        data.get("brand"),
        data.get("date_found", datetime.now().strftime("%Y-%m-%d")),
        data.get("location", "Campus Grounds"),
        data.get("description", ""),
        data.get("photo_path"),
        data.get("finder_name", "Anonymous Finder"),
        data.get("contact_info", ""),
        "Searching",
    ))
    conn.commit()
    conn.close()
    return new_id


def save_or_update_match(match_data: Dict[str, Any]):
    """Insert or update potential match record in SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()

    score = match_data.get("match_score", 0)
    pct = min(100, int((score / 5.0) * 100))

    reasons_str = "; ".join(match_data.get("reasons", [])) if isinstance(match_data.get("reasons"), list) else str(match_data.get("reasons", ""))

    cursor.execute("""
        INSERT INTO matches (lost_id, found_id, match_score, match_percentage, classification, reasons, explanation, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending Verification')
        ON CONFLICT(lost_id, found_id) DO UPDATE SET
            match_score=excluded.match_score,
            match_percentage=excluded.match_percentage,
            classification=excluded.classification,
            reasons=excluded.reasons,
            explanation=excluded.explanation
    """, (
        match_data.get("lost_id"),
        match_data.get("found_id"),
        score,
        pct,
        match_data.get("classification"),
        reasons_str,
        match_data.get("explanation", reasons_str),
    ))
    conn.commit()
    conn.close()


def confirm_successful_match(lost_id: str, found_id: str, notes: str, verified_by: str = "Campus Help Desk"):
    """Mark a match as verified & successful in SQLite, updating item statuses."""
    conn = get_db_connection()
    cursor = conn.cursor()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE matches SET
            status = 'Verified & Returned',
            verified_at = ?,
            verified_by = ?,
            verification_notes = ?
        WHERE lost_id = ? AND found_id = ?
    """, (now_str, verified_by, notes, lost_id, found_id))

    cursor.execute("UPDATE lost_reports SET status = 'Returned to Owner' WHERE id = ?", (lost_id,))
    cursor.execute("UPDATE found_reports SET status = 'Returned to Owner' WHERE id = ?", (found_id,))

    conn.commit()
    conn.close()

    add_notification_if_not_exists(
        recipient_type="student",
        title="Match Confirmed & Property Returned",
        message=f"Ownership for your lost item {lost_id} has been verified and confirmed. Handover authorized by {verified_by}.",
        report_id=lost_id,
        notification_type="status_update"
    )
    add_notification_if_not_exists(
        recipient_type="finder",
        title="Found Property Returned to Owner",
        message=f"Found item {found_id} has been successfully returned to its verified owner by {verified_by}. Thank you!",
        report_id=found_id,
        notification_type="status_update"
    )


def get_pending_matches() -> List[Dict[str, Any]]:
    """Retrieve all potential matches awaiting verification with joined lost & found details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            m.id as match_id,
            m.lost_id,
            m.found_id,
            m.match_score,
            m.match_percentage,
            m.classification,
            m.reasons,
            m.explanation,
            m.status as match_status,
            l.item_name as lost_item_name,
            l.category as lost_category,
            l.colour as lost_colour,
            l.brand as lost_brand,
            l.date_lost,
            l.location as lost_location,
            l.description as lost_description,
            l.student_name,
            l.contact_info as student_contact,
            f.item_name as found_item_name,
            f.category as found_category,
            f.colour as found_colour,
            f.brand as found_brand,
            f.date_found,
            f.location as found_location,
            f.description as found_description,
            f.finder_name,
            f.contact_info as finder_contact
        FROM matches m
        JOIN lost_reports l ON m.lost_id = l.id
        JOIN found_reports f ON m.found_id = f.id
        WHERE m.status = 'Pending Verification'
        ORDER BY m.match_score DESC, m.id DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_successful_matches() -> List[Dict[str, Any]]:
    """Retrieve all confirmed and verified matches."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            m.id as match_id,
            m.lost_id,
            m.found_id,
            m.match_score,
            m.match_percentage,
            m.classification,
            m.reasons,
            m.explanation,
            m.status as match_status,
            m.verified_at,
            m.verified_by,
            m.verification_notes,
            l.item_name as lost_item_name,
            l.student_name,
            l.contact_info as student_contact,
            f.item_name as found_item_name,
            f.finder_name,
            f.contact_info as finder_contact
        FROM matches m
        JOIN lost_reports l ON m.lost_id = l.id
        JOIN found_reports f ON m.found_id = f.id
        WHERE m.status = 'Verified & Returned'
        ORDER BY m.verified_at DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def run_database_matching():
    """Run deterministic matching across all lost and found reports, generate notifications, and synchronize item statuses."""
    from matcher import score_pair

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM lost_reports")
    lost_list = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM found_reports")
    found_list = [dict(r) for r in cursor.fetchall()]

    for lost in lost_list:
        l_obj = {
            "id": lost["id"],
            "date": lost["date_lost"],
            "report": lost["description"] or lost["item_name"],
            "extracted": {
                "item": lost["category"],
                "colour": lost["colour"],
                "brand": lost["brand"],
                "place": lost["location"],
                "summary": lost["item_name"],
            }
        }
        for found in found_list:
            f_obj = {
                "id": found["id"],
                "date": found["date_found"],
                "report": found["description"] or found["item_name"],
                "extracted": {
                    "item": found["category"],
                    "colour": found["colour"],
                    "brand": found["brand"],
                    "place": found["location"],
                    "summary": found["item_name"],
                }
            }
            score, classification, reasons = score_pair(l_obj, f_obj)
            if score >= 1 and classification != "DO NOT DISPLAY":
                pct = min(100, int((score / 5.0) * 100))
                reasons_str = "; ".join(reasons)
                expl = (
                    f"AI Match Confidence: {pct}% ({classification}). "
                    f"Compatibility: {reasons_str}. "
                    f"Both reports involve a {lost['category']}."
                )

                # Check if already verified
                cursor.execute("SELECT id, status FROM matches WHERE lost_id = ? AND found_id = ?", (lost["id"], found["id"]))
                existing = cursor.fetchone()
                if not existing:
                    cursor.execute("""
                        INSERT INTO matches (lost_id, found_id, match_score, match_percentage, classification, reasons, explanation, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending Verification')
                    """, (lost["id"], found["id"], score, pct, classification, reasons_str, expl))
                    match_id = cursor.lastrowid
                else:
                    match_id = existing["id"]
                    if existing["status"] != "Verified & Returned":
                        cursor.execute("""
                            UPDATE matches SET
                                match_score = ?,
                                match_percentage = ?,
                                classification = ?,
                                reasons = ?,
                                explanation = ?
                            WHERE id = ?
                        """, (score, pct, classification, reasons_str, expl, match_id))

                # Notifications (avoids sending duplicate notifications for the same match)
                student_msg = f"Good news! We found a {classification.lower()} ({pct}%) for your lost item '{lost['item_name']}'. Matching Found Item: {found['id']}."
                add_notification_if_not_exists(
                    recipient_type="student",
                    title="Good news! Possible Match Found",
                    message=student_msg,
                    report_id=lost["id"],
                    match_id=match_id,
                    recipient_name=lost.get("student_name"),
                    recipient_contact=lost.get("contact_info"),
                    notification_type="match_found",
                    conn=conn
                )

                finder_msg = f"Good news! A student has reported a matching item for '{found['item_name']}' that you found. Lost Item: {lost['id']} ({pct}% compatibility)."
                add_notification_if_not_exists(
                    recipient_type="finder",
                    title="Good news! Potential Owner Identified",
                    message=finder_msg,
                    report_id=found["id"],
                    match_id=match_id,
                    recipient_name=found.get("finder_name"),
                    recipient_contact=found.get("contact_info"),
                    notification_type="match_found",
                    conn=conn
                )

    # Synchronize item statuses:
    cursor.execute("""
        SELECT l.id, COUNT(m.id) as match_cnt
        FROM lost_reports l
        LEFT JOIN matches m ON l.id = m.lost_id AND m.status = 'Pending Verification'
        WHERE l.status NOT IN ('Returned to Owner', 'Closed', 'Match Confirmed')
        GROUP BY l.id
    """)
    for row in cursor.fetchall():
        new_st = "Possible Match Found" if row["match_cnt"] > 0 else "Searching"
        cursor.execute("UPDATE lost_reports SET status = ? WHERE id = ?", (new_st, row["id"]))

    cursor.execute("""
        SELECT f.id, COUNT(m.id) as match_cnt
        FROM found_reports f
        LEFT JOIN matches m ON f.id = m.found_id AND m.status = 'Pending Verification'
        WHERE f.status NOT IN ('Returned to Owner', 'Closed', 'Match Confirmed')
        GROUP BY f.id
    """)
    for row in cursor.fetchall():
        new_st = "Possible Match Found" if row["match_cnt"] > 0 else "Searching"
        cursor.execute("UPDATE found_reports SET status = ? WHERE id = ?", (new_st, row["id"]))

    # Double Claim Detection alerts for Help Desk
    cursor.execute("""
        SELECT found_id, COUNT(*) as claim_cnt
        FROM matches
        WHERE status = 'Pending Verification'
        GROUP BY found_id
        HAVING COUNT(*) > 1
    """)
    for dc in cursor.fetchall():
        f_id = dc["found_id"]
        cursor.execute("SELECT item_name FROM found_reports WHERE id = ?", (f_id,))
        fn_row = cursor.fetchone()
        fn_name = fn_row[0] if fn_row else "Item"
        dc_msg = f"⚠️ Double claim detected for Found Item {f_id} ('{fn_name}'). {dc['claim_cnt']} competing student claims registered. In-person Help Desk arbitration required."
        add_notification_if_not_exists(
            recipient_type="help_desk",
            title="⚠️ Double Claim Conflict Detected!",
            message=dc_msg,
            report_id=f_id,
            notification_type="double_claim",
            conn=conn
        )

    conn.commit()
    conn.close()


def get_dashboard_statistics() -> Dict[str, int]:
    """Calculate the exact statistics required by CET Campus Portal."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lost_reports")
    total_lost = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM found_reports")
    total_found = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM matches WHERE status = 'Verified & Returned'")
    successful_matches = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM matches WHERE status = 'Pending Verification'")
    pending_matches = cursor.fetchone()[0]

    conn.close()

    double_summary = get_double_claims_summary()

    return {
        "total_lost": total_lost,
        "total_found": total_found,
        "successful_matches": successful_matches,
        "pending_matches": pending_matches,
        "double_claims_total": double_summary["total_conflicts"],
        "double_claims_pending": double_summary["pending_verification"],
        "double_claims_resolved": double_summary["resolved_claims"],
        "unread_notifications": get_unread_notification_count(),
    }


def get_double_claims_summary() -> Dict[str, int]:
    """
    Summarize double claim conflicts in the database.
    A double claim conflict occurs when 2 or more lost reports claim the same found item.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Find all found_id with more than one match claim
    cursor.execute("""
        SELECT found_id, 
               COUNT(*) as claim_count,
               SUM(CASE WHEN status = 'Verified & Returned' THEN 1 ELSE 0 END) as verified_count
        FROM matches
        GROUP BY found_id
        HAVING COUNT(*) > 1
    """)
    rows = cursor.fetchall()
    conn.close()

    total_conflicts = len(rows)
    resolved_count = 0
    pending_count = 0

    for r in rows:
        if r["verified_count"] > 0:
            resolved_count += 1
        else:
            pending_count += 1

    return {
        "total_conflicts": total_conflicts,
        "pending_verification": pending_count,
        "resolved_claims": resolved_count,
    }


def get_double_claims_details() -> List[Dict[str, Any]]:
    """
    Retrieve full details for each contested found item along with all competing claimants.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Find contested found_ids
    cursor.execute("""
        SELECT found_id, COUNT(*) as claim_count
        FROM matches
        GROUP BY found_id
        HAVING COUNT(*) > 1
        ORDER BY found_id ASC
    """)
    contested_founds = cursor.fetchall()

    conflicts = []
    for cf in contested_founds:
        f_id = cf["found_id"]

        # Fetch found item details
        cursor.execute("SELECT * FROM found_reports WHERE id = ?", (f_id,))
        found_row = cursor.fetchone()
        if not found_row:
            continue
        found_data = dict(found_row)

        # Fetch all competing claimants for this found item
        cursor.execute("""
            SELECT 
                m.id as match_id,
                m.lost_id,
                m.found_id,
                m.match_score,
                m.match_percentage,
                m.classification,
                m.reasons,
                m.explanation,
                m.status as claim_status,
                m.verified_at,
                m.verified_by,
                m.verification_notes,
                m.created_at as claim_timestamp,
                l.item_name as lost_item_name,
                l.category as lost_category,
                l.colour as lost_colour,
                l.brand as lost_brand,
                l.date_lost,
                l.location as lost_location,
                l.description as lost_description,
                l.photo_path as lost_photo,
                l.student_name,
                l.student_id,
                l.contact_info,
                l.status as lost_status
            FROM matches m
            JOIN lost_reports l ON m.lost_id = l.id
            WHERE m.found_id = ?
            ORDER BY 
                CASE WHEN m.status = 'Verified & Returned' THEN 0 
                     WHEN m.status = 'Pending Verification' THEN 1 
                     ELSE 2 END,
                m.match_score DESC
        """, (f_id,))
        claimants = [dict(r) for r in cursor.fetchall()]

        # Determine conflict level status
        has_verified = any(c["claim_status"] == "Verified & Returned" for c in claimants)
        conflict_status = "Resolved & Verified" if has_verified else "Pending Arbitration"

        conflicts.append({
            "found_id": f_id,
            "found_item": found_data,
            "claim_count": len(claimants),
            "conflict_status": conflict_status,
            "has_verified": has_verified,
            "claimants": claimants,
        })

    conn.close()
    return conflicts


def resolve_double_claim(found_id: str, winning_lost_id: str, verified_by: str, private_proof: str, notes: str = "") -> bool:
    """
    Arbitrate and resolve a double claim conflict:
    1. Mark winning claimant's match as 'Verified & Returned' with proof details.
    2. Mark competing claimants as 'Claim Denied - Alternate Verified'.
    3. Update found_reports to 'Claimed & Released'.
    4. Update winning lost_reports to 'Matched & Returned'.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_notes = f"Private Proof: {private_proof}. Staff notes: {notes}".strip()

    # 1. Update winning match
    cursor.execute("""
        UPDATE matches SET
            status = 'Verified & Returned',
            verified_at = ?,
            verified_by = ?,
            verification_notes = ?
        WHERE found_id = ? AND lost_id = ?
    """, (now_str, verified_by, full_notes, found_id, winning_lost_id))

    # 2. Update competing matches for this found item
    alt_notes = f"Claim denied during arbitration. Ownership was verified and released to {winning_lost_id} by {verified_by}."
    cursor.execute("""
        UPDATE matches SET
            status = 'Claim Denied - Alternate Verified',
            verified_at = ?,
            verified_by = ?,
            verification_notes = ?
        WHERE found_id = ? AND lost_id != ?
    """, (now_str, verified_by, alt_notes, found_id, winning_lost_id))

    # 3. Update Found item status
    cursor.execute("UPDATE found_reports SET status = 'Returned to Owner' WHERE id = ?", (found_id,))

    # 4. Update Lost items status
    cursor.execute("UPDATE lost_reports SET status = 'Returned to Owner' WHERE id = ?", (winning_lost_id,))
    cursor.execute("""
        UPDATE lost_reports 
        SET status = 'Closed' 
        WHERE id IN (SELECT lost_id FROM matches WHERE found_id = ? AND lost_id != ?)
    """, (found_id, winning_lost_id))

    conn.commit()
    conn.close()

    add_notification_if_not_exists(
        recipient_type="student",
        title="Double Claim Arbitration Resolved",
        message=f"Help Desk arbitration for Found Item {found_id} resolved. Ownership verified and awarded to {winning_lost_id} by {verified_by}.",
        report_id=winning_lost_id,
        notification_type="status_update"
    )
    return True


def add_direct_claim_for_found(
    found_id: str,
    claimant_name: str,
    student_id: str,
    contact_info: str,
    description: str,
    date_lost: str,
    private_proof: str = "",
    photo_path: str = ""
) -> str:
    """
    Add a new student claim directly for a specific found item.
    Creates a new lost report and attaches it directly to the found item in matches.
    If the found item already has an existing claim, this immediately triggers a Double Claim!
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Fetch found item details for category/colour/brand
    cursor.execute("SELECT * FROM found_reports WHERE id = ?", (found_id,))
    found_row = cursor.fetchone()
    if not found_row:
        conn.close()
        raise ValueError(f"Found item {found_id} does not exist.")

    f_dict = dict(found_row)

    # 2. Generate next Lost ID
    cursor.execute("SELECT id FROM lost_reports WHERE id LIKE 'L%'")
    rows = cursor.fetchall()
    max_num = 0
    for r in rows:
        try:
            num = int(r["id"][1:])
            if num > max_num:
                max_num = num
        except Exception:
            pass
    next_id = f"L{max_num + 1:02d}"

    item_name = f_dict.get("item_name") or f"Claimed {f_dict.get('category', 'Item')}"

    # 3. Insert into lost_reports
    cursor.execute("""
        INSERT INTO lost_reports (
            id, item_name, category, colour, brand, date_lost, location,
            description, photo_path, student_name, student_id, contact_info, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Reported Lost')
    """, (
        next_id,
        item_name,
        f_dict.get("category", "other"),
        f_dict.get("colour", ""),
        f_dict.get("brand", ""),
        date_lost or datetime.now().strftime("%Y-%m-%d"),
        f_dict.get("location", "Campus Grounds"),
        description,
        photo_path,
        claimant_name,
        student_id,
        contact_info
    ))

    # 4. Insert into matches table
    expl = f"Direct claim submitted by {claimant_name} for Found Item {found_id}."
    if private_proof:
        expl += f" Private proof provided: {private_proof}"

    cursor.execute("""
        INSERT INTO matches (
            lost_id, found_id, match_score, match_percentage, classification,
            reasons, explanation, status
        ) VALUES (?, ?, 5, 100, 'DIRECT_CLAIM', 'Direct Ownership Claim Submitted', ?, 'Pending Verification')
    """, (next_id, found_id, expl))

    conn.commit()
    conn.close()
    return next_id


# ------------------------------------------------------------------------------
# Notification System & Real-Time Item Matching Engine
# ------------------------------------------------------------------------------

def add_notification_if_not_exists(
    recipient_type: str,
    title: str,
    message: str,
    report_id: str,
    match_id: Optional[int] = None,
    recipient_name: Optional[str] = None,
    recipient_contact: Optional[str] = None,
    notification_type: str = "match_found",
    conn: Optional[sqlite3.Connection] = None
) -> Optional[int]:
    """Insert a notification if one does not already exist for this report, match, and type."""
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    cursor = conn.cursor()

    if match_id is not None:
        cursor.execute("""
            SELECT id FROM notifications 
            WHERE report_id = ? AND match_id = ? AND notification_type = ?
        """, (report_id, match_id, notification_type))
    else:
        cursor.execute("""
            SELECT id FROM notifications 
            WHERE report_id = ? AND match_id IS NULL AND notification_type = ?
        """, (report_id, notification_type))

    existing = cursor.fetchone()
    if existing:
        if should_close:
            conn.close()
        return None

    cursor.execute("""
        INSERT INTO notifications (
            recipient_type, recipient_name, recipient_contact,
            report_id, match_id, title, message, notification_type, is_read
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (
        recipient_type,
        recipient_name,
        recipient_contact,
        report_id,
        match_id,
        title,
        message,
        notification_type
    ))
    notif_id = cursor.lastrowid
    if should_close:
        conn.commit()
        conn.close()
    return notif_id


def get_all_notifications(limit: int = 50, unread_only: bool = False) -> List[Dict[str, Any]]:
    """Retrieve all notifications with optional unread filter, ordered newest first."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT n.*, m.match_score, m.match_percentage, m.classification, m.lost_id, m.found_id
        FROM notifications n
        LEFT JOIN matches m ON n.match_id = m.id
    """
    params = []
    if unread_only:
        query += " WHERE n.is_read = 0"
    query += " ORDER BY n.id DESC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_unread_notification_count() -> int:
    """Return count of unread notifications."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM notifications WHERE is_read = 0")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def mark_notification_read(notification_id: int) -> bool:
    """Mark a specific notification as read."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
    conn.commit()
    conn.close()
    return True


def mark_all_notifications_read() -> int:
    """Mark all unread notifications as read."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE is_read = 0")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count


def get_notifications_for_report(report_id: str) -> List[Dict[str, Any]]:
    """Get all notifications linked to a specific lost or found report."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM notifications 
        WHERE report_id = ? 
        ORDER BY id DESC
    """, (report_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def update_item_status(item_type: str, item_id: str, new_status: str) -> bool:
    """Update status of a lost or found report ('lost' or 'found')."""
    conn = get_db_connection()
    cursor = conn.cursor()
    table = "lost_reports" if item_type.lower() == "lost" else "found_reports"
    cursor.execute(f"UPDATE {table} SET status = ? WHERE id = ?", (new_status, item_id))
    conn.commit()
    conn.close()
    return True


def get_match_history() -> List[Dict[str, Any]]:
    """Retrieve full match history including pending, confirmed, returned, and closed matches."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            m.id as match_id,
            m.lost_id,
            m.found_id,
            m.match_score,
            m.match_percentage,
            m.classification,
            m.reasons,
            m.explanation,
            m.status as match_status,
            m.verified_at,
            m.verified_by,
            m.verification_notes,
            m.created_at as match_created_at,
            l.item_name as lost_item_name,
            l.category as lost_category,
            l.colour as lost_colour,
            l.brand as lost_brand,
            l.date_lost,
            l.location as lost_location,
            l.description as lost_description,
            l.photo_path as lost_photo,
            l.student_name,
            l.student_id,
            l.contact_info as student_contact,
            l.status as lost_status,
            f.item_name as found_item_name,
            f.category as found_category,
            f.colour as found_colour,
            f.brand as found_brand,
            f.date_found,
            f.location as found_location,
            f.description as found_description,
            f.photo_path as found_photo,
            f.finder_name,
            f.contact_info as finder_contact,
            f.status as found_status
        FROM matches m
        JOIN lost_reports l ON m.lost_id = l.id
        JOIN found_reports f ON m.found_id = f.id
        ORDER BY m.id DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def match_single_lost(lost_id: str) -> Dict[str, Any]:
    """
    Automatically compare a single submitted lost item against all available found items.
    Updates matches, generates notifications, updates item statuses, and returns live matching results.
    """
    from matcher import score_pair

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM lost_reports WHERE id = ?", (lost_id,))
    lost_row = cursor.fetchone()
    if not lost_row:
        conn.close()
        return {
            "lost_id": lost_id,
            "lost_item_name": "Item",
            "matches_count": 0,
            "matches": [],
            "status": "Searching",
            "notifications": [],
            "message": "No matching items found yet. We will notify you when a match becomes available."
        }

    lost = dict(lost_row)
    l_obj = {
        "id": lost["id"],
        "date": lost["date_lost"],
        "report": lost["description"] or lost["item_name"],
        "extracted": {
            "item": lost["category"],
            "colour": lost["colour"],
            "brand": lost["brand"],
            "place": lost["location"],
            "summary": lost["item_name"],
        }
    }

    cursor.execute("SELECT * FROM found_reports WHERE status NOT IN ('Returned to Owner', 'Closed')")
    found_list = [dict(r) for r in cursor.fetchall()]

    matched_found_items = []
    generated_notifications = []

    for found in found_list:
        f_obj = {
            "id": found["id"],
            "date": found["date_found"],
            "report": found["description"] or found["item_name"],
            "extracted": {
                "item": found["category"],
                "colour": found["colour"],
                "brand": found["brand"],
                "place": found["location"],
                "summary": found["item_name"],
            }
        }
        score, classification, reasons = score_pair(l_obj, f_obj)
        if score >= 1 and classification != "DO NOT DISPLAY":
            pct = min(100, int((score / 5.0) * 100))
            reasons_str = "; ".join(reasons)
            expl = (
                f"AI Match Confidence: {pct}% ({classification}). "
                f"Compatibility: {reasons_str}. "
                f"Both reports involve a {lost['category']}."
            )

            # Insert or update match
            cursor.execute("SELECT id, status FROM matches WHERE lost_id = ? AND found_id = ?", (lost["id"], found["id"]))
            existing_match = cursor.fetchone()
            if not existing_match:
                cursor.execute("""
                    INSERT INTO matches (lost_id, found_id, match_score, match_percentage, classification, reasons, explanation, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending Verification')
                """, (lost["id"], found["id"], score, pct, classification, reasons_str, expl))
                match_id = cursor.lastrowid
            else:
                match_id = existing_match["id"]
                if existing_match["status"] != "Verified & Returned":
                    cursor.execute("""
                        UPDATE matches SET
                            match_score = ?,
                            match_percentage = ?,
                            classification = ?,
                            reasons = ?,
                            explanation = ?
                        WHERE id = ?
                    """, (score, pct, classification, reasons_str, expl, match_id))

            # Student Notification
            student_msg = f"Good news! We found a {classification.lower()} ({pct}%) for your lost item '{lost['item_name']}'. Matching Found Item: {found['id']} ({found['item_name']})."
            s_notif = add_notification_if_not_exists(
                recipient_type="student",
                title="Good news! Possible Match Found",
                message=student_msg,
                report_id=lost["id"],
                match_id=match_id,
                recipient_name=lost.get("student_name"),
                recipient_contact=lost.get("contact_info"),
                notification_type="match_found",
                conn=conn
            )
            if s_notif:
                generated_notifications.append({"id": s_notif, "title": "Good news! Possible Match Found", "message": student_msg})

            # Finder Notification
            finder_msg = f"Good news! A student has reported a matching item for '{found['item_name']}' that you found. Lost Item: {lost['id']} ({pct}% compatibility)."
            f_notif = add_notification_if_not_exists(
                recipient_type="finder",
                title="Good news! Potential Owner Identified",
                message=finder_msg,
                report_id=found["id"],
                match_id=match_id,
                recipient_name=found.get("finder_name"),
                recipient_contact=found.get("contact_info"),
                notification_type="match_found",
                conn=conn
            )
            if f_notif:
                generated_notifications.append({"id": f_notif, "title": "Good news! Potential Owner Identified", "message": finder_msg})

            # Update found report status
            if found.get("status") in ("Searching", "In Custody", "Reported"):
                cursor.execute("UPDATE found_reports SET status = 'Possible Match Found' WHERE id = ?", (found["id"],))

            # Check double claim for this found item
            cursor.execute("SELECT COUNT(*) FROM matches WHERE found_id = ? AND status = 'Pending Verification'", (found["id"],))
            claims_count = cursor.fetchone()[0]
            if claims_count > 1:
                dc_msg = f"⚠️ Double claim detected for Found Item {found['id']} ('{found['item_name']}'). Multiple students ({claims_count} claimants) have registered claims. Help Desk arbitration required."
                dc_notif = add_notification_if_not_exists(
                    recipient_type="help_desk",
                    title="⚠️ Double Claim Conflict Detected!",
                    message=dc_msg,
                    report_id=found["id"],
                    notification_type="double_claim",
                    conn=conn
                )
                if dc_notif:
                    generated_notifications.append({"id": dc_notif, "title": "⚠️ Double Claim Conflict Detected!", "message": dc_msg})

            matched_found_items.append({
                "match_id": match_id,
                "score": score,
                "match_percentage": pct,
                "classification": classification,
                "reasons": reasons,
                "reasons_str": reasons_str,
                "explanation": expl,
                "found_id": found["id"],
                "item_name": found["item_name"],
                "category": found["category"],
                "colour": found["colour"],
                "brand": found["brand"],
                "date_found": found["date_found"],
                "location": found["location"],
                "description": found["description"],
                "photo_path": found.get("photo_path"),
                "finder_name": found["finder_name"],
                "contact_info": found["contact_info"],
                "status": "Possible Match Found",
            })

    # Update lost item status
    new_status = "Possible Match Found" if matched_found_items else "Searching"
    cursor.execute("UPDATE lost_reports SET status = ? WHERE id = ?", (new_status, lost_id))

    conn.commit()
    conn.close()

    matched_found_items.sort(key=lambda x: x["score"], reverse=True)

    return {
        "lost_id": lost_id,
        "lost_item_name": lost["item_name"],
        "matches_count": len(matched_found_items),
        "matches": matched_found_items,
        "status": new_status,
        "notifications": generated_notifications,
        "message": (
            f"Good news! We found a possible match for your lost item ({len(matched_found_items)} candidate(s) found)."
            if matched_found_items
            else "No matching items found yet. We will notify you when a match becomes available."
        )
    }


def match_single_found(found_id: str) -> Dict[str, Any]:
    """
    Automatically compare a single submitted found item against all existing lost items.
    Updates matches, generates notifications, updates item statuses, and returns live matching results.
    """
    from matcher import score_pair

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM found_reports WHERE id = ?", (found_id,))
    found_row = cursor.fetchone()
    if not found_row:
        conn.close()
        return {
            "found_id": found_id,
            "found_item_name": "Item",
            "matches_count": 0,
            "matches": [],
            "status": "Searching",
            "is_double_claim": False,
            "notifications": [],
            "message": "No matching items found yet. We will notify you when a match becomes available."
        }

    found = dict(found_row)
    f_obj = {
        "id": found["id"],
        "date": found["date_found"],
        "report": found["description"] or found["item_name"],
        "extracted": {
            "item": found["category"],
            "colour": found["colour"],
            "brand": found["brand"],
            "place": found["location"],
            "summary": found["item_name"],
        }
    }

    cursor.execute("SELECT * FROM lost_reports WHERE status NOT IN ('Returned to Owner', 'Closed')")
    lost_list = [dict(r) for r in cursor.fetchall()]

    matched_lost_items = []
    generated_notifications = []

    for lost in lost_list:
        l_obj = {
            "id": lost["id"],
            "date": lost["date_lost"],
            "report": lost["description"] or lost["item_name"],
            "extracted": {
                "item": lost["category"],
                "colour": lost["colour"],
                "brand": lost["brand"],
                "place": lost["location"],
                "summary": lost["item_name"],
            }
        }
        score, classification, reasons = score_pair(l_obj, f_obj)
        if score >= 1 and classification != "DO NOT DISPLAY":
            pct = min(100, int((score / 5.0) * 100))
            reasons_str = "; ".join(reasons)
            expl = (
                f"AI Match Confidence: {pct}% ({classification}). "
                f"Compatibility: {reasons_str}. "
                f"Both reports involve a {found['category']}."
            )

            # Insert or update match
            cursor.execute("SELECT id, status FROM matches WHERE lost_id = ? AND found_id = ?", (lost["id"], found["id"]))
            existing_match = cursor.fetchone()
            if not existing_match:
                cursor.execute("""
                    INSERT INTO matches (lost_id, found_id, match_score, match_percentage, classification, reasons, explanation, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending Verification')
                """, (lost["id"], found["id"], score, pct, classification, reasons_str, expl))
                match_id = cursor.lastrowid
            else:
                match_id = existing_match["id"]
                if existing_match["status"] != "Verified & Returned":
                    cursor.execute("""
                        UPDATE matches SET
                            match_score = ?,
                            match_percentage = ?,
                            classification = ?,
                            reasons = ?,
                            explanation = ?
                        WHERE id = ?
                    """, (score, pct, classification, reasons_str, expl, match_id))

            # Student Notification
            student_msg = f"Good news! We found a {classification.lower()} ({pct}%) for your lost item '{lost['item_name']}'. Matching Found Item: {found['id']} ({found['item_name']})."
            s_notif = add_notification_if_not_exists(
                recipient_type="student",
                title="Good news! Possible Match Found",
                message=student_msg,
                report_id=lost["id"],
                match_id=match_id,
                recipient_name=lost.get("student_name"),
                recipient_contact=lost.get("contact_info"),
                notification_type="match_found",
                conn=conn
            )
            if s_notif:
                generated_notifications.append({"id": s_notif, "title": "Good news! Possible Match Found", "message": student_msg})

            # Finder Notification
            finder_msg = f"Good news! A student has reported a matching item for '{found['item_name']}' that you found. Lost Item: {lost['id']} ({pct}% compatibility)."
            f_notif = add_notification_if_not_exists(
                recipient_type="finder",
                title="Good news! Potential Owner Identified",
                message=finder_msg,
                report_id=found["id"],
                match_id=match_id,
                recipient_name=found.get("finder_name"),
                recipient_contact=found.get("contact_info"),
                notification_type="match_found",
                conn=conn
            )
            if f_notif:
                generated_notifications.append({"id": f_notif, "title": "Good news! Potential Owner Identified", "message": finder_msg})

            # Update lost report status
            if lost.get("status") in ("Searching", "Reported Lost", "Reported"):
                cursor.execute("UPDATE lost_reports SET status = 'Possible Match Found' WHERE id = ?", (lost["id"],))

            matched_lost_items.append({
                "match_id": match_id,
                "score": score,
                "match_percentage": pct,
                "classification": classification,
                "reasons": reasons,
                "reasons_str": reasons_str,
                "explanation": expl,
                "lost_id": lost["id"],
                "item_name": lost["item_name"],
                "category": lost["category"],
                "colour": lost["colour"],
                "brand": lost["brand"],
                "date_lost": lost["date_lost"],
                "location": lost["location"],
                "description": lost["description"],
                "photo_path": lost.get("photo_path"),
                "student_name": lost["student_name"],
                "student_id": lost["student_id"],
                "contact_info": lost["contact_info"],
                "status": "Possible Match Found",
            })

    # Double claim detection check
    cursor.execute("SELECT COUNT(*) FROM matches WHERE found_id = ? AND status = 'Pending Verification'", (found["id"],))
    claims_count = cursor.fetchone()[0]
    if claims_count > 1:
        dc_msg = f"⚠️ Double claim detected for Found Item {found['id']} ('{found['item_name']}'). Multiple students ({claims_count} claimants) have registered claims. Help Desk arbitration required."
        dc_notif = add_notification_if_not_exists(
            recipient_type="help_desk",
            title="⚠️ Double Claim Conflict Detected!",
            message=dc_msg,
            report_id=found["id"],
            notification_type="double_claim",
            conn=conn
        )
        if dc_notif:
            generated_notifications.append({"id": dc_notif, "title": "⚠️ Double Claim Conflict Detected!", "message": dc_msg})

    new_status = "Possible Match Found" if matched_lost_items else "Searching"
    cursor.execute("UPDATE found_reports SET status = ? WHERE id = ?", (new_status, found_id))

    conn.commit()
    conn.close()

    matched_lost_items.sort(key=lambda x: x["score"], reverse=True)

    return {
        "found_id": found_id,
        "found_item_name": found["item_name"],
        "matches_count": len(matched_lost_items),
        "matches": matched_lost_items,
        "status": new_status,
        "is_double_claim": claims_count > 1,
        "notifications": generated_notifications,
        "message": (
            f"Good news! We found a possible match for this recovered item ({len(matched_lost_items)} candidate(s) matched)."
            if matched_lost_items
            else "No matching items found yet. We will notify you when a match becomes available."
        )
    }

