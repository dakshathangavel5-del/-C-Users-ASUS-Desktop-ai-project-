"""
Flask Web Application for CIT Campus Smart Lost and Found Management System.
Connects directly to the existing SQLite database, validation firewall, and AI matching algorithm.
Provides full-stack web interface with identical green-and-white theme and real-time form validation.
"""

from datetime import datetime
import os
from pathlib import Path
import sys
from typing import Any, Dict

from flask import Flask, jsonify, render_template, request, send_from_directory

# Ensure project root in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import ALLOWED_COLOURS, ALLOWED_ITEMS, ALLOWED_PLACES, DATA_DIR
import database
from validator import clean_mobile_number, validate_indian_mobile

app = Flask(__name__)
app.config["SECRET_KEY"] = "cit-lost-and-found-secret-2026"
app.config["UPLOAD_FOLDER"] = str(DATA_DIR / "photos")

# Ensure database and matching engine initialized
database.init_database()
database.run_database_matching()


@app.route("/")
def index():
    """Render the main web dashboard."""
    stats = database.get_dashboard_statistics()
    all_lost = database.get_all_lost_reports()
    all_found = database.get_all_found_reports()
    conflicts = database.get_double_claims_details()
    dc_summary = database.get_double_claims_summary()
    pending_matches = database.get_pending_matches()
    successful_matches = database.get_successful_matches()
    notifications = database.get_all_notifications(limit=50)
    unread_notifs = database.get_unread_notification_count()
    match_history = database.get_match_history()

    return render_template(
        "index.html",
        stats=stats,
        recent_lost=all_lost[:5],
        recent_found=all_found[:5],
        all_lost=all_lost,
        all_found=all_found,
        conflicts=conflicts,
        dc_summary=dc_summary,
        pending_matches=pending_matches,
        successful_matches=successful_matches,
        notifications=notifications,
        unread_notifs=unread_notifs,
        match_history=match_history,
        allowed_items=sorted(list(ALLOWED_ITEMS)),
        allowed_colours=sorted(list(ALLOWED_COLOURS)),
        allowed_places=sorted(list(ALLOWED_PLACES)),
    )


@app.route("/api/validate-contact", methods=["POST"])
def api_validate_contact():
    """
    Real-time API endpoint to validate 10-digit Indian mobile number
    and check for duplicate registration in existing student records.
    """
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "")
    exclude_id = data.get("exclude_id")

    if not phone or not str(phone).strip():
        return jsonify({
            "valid": False,
            "error": "Invalid mobile number. Please enter a valid 10-digit number."
        })

    is_valid, err_msg = validate_indian_mobile(phone)
    if not is_valid:
        return jsonify({
            "valid": False,
            "error": "Invalid mobile number. Please enter a valid 10-digit number."
        })

    # Check for duplicate registration in existing records
    if database.is_contact_number_registered(phone, exclude_id=exclude_id):
        return jsonify({
            "valid": False,
            "error": "This mobile number is already registered. Please enter a different number."
        })

    return jsonify({"valid": True, "error": ""})


@app.route("/api/report-lost", methods=["POST"])
def api_report_lost():
    """Submit and save a lost item report with strict validation."""
    data = request.form if request.form else (request.get_json(silent=True) or {})
    
    item_name = data.get("item_name", "").strip()
    category = data.get("category", "").strip().lower()
    colour = data.get("colour", "").strip().lower() or None
    brand = data.get("brand", "").strip() or None
    date_lost = data.get("date_lost", "").strip() or datetime.now().strftime("%Y-%m-%d")
    location = data.get("location", "").strip().lower()
    description = data.get("description", "").strip()
    student_name = data.get("student_name", "").strip()
    student_id = data.get("student_id", "").strip()
    contact_raw = data.get("contact_info", "").strip()

    # Validation checks
    errors = {}
    if not item_name:
        errors["item_name"] = "Item name is required."
    if not category:
        errors["category"] = "Category is required."
    if not location:
        errors["location"] = "Location is required."
    if not description:
        errors["description"] = "Detailed description is required."
    if not student_name:
        errors["student_name"] = "Student name is required."
    if not student_id:
        errors["student_id"] = "Student ID is required."

    # Mobile validation
    is_valid, msg = validate_indian_mobile(contact_raw)
    if not is_valid:
        errors["contact_info"] = "Invalid mobile number. Please enter a valid 10-digit number."
    elif database.is_contact_number_registered(contact_raw):
        errors["contact_info"] = "This mobile number is already registered. Please enter a different number."

    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    clean_contact = clean_mobile_number(contact_raw)

    # Handle photo upload if present
    photo_path = None
    if "photo" in request.files:
        photo_file = request.files["photo"]
        if photo_file and photo_file.filename:
            dest = Path(app.config["UPLOAD_FOLDER"]) / f"lost_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo_file.filename}"
            photo_file.save(str(dest))
            photo_path = str(dest)

    new_id = database.insert_lost_report({
        "item_name": item_name,
        "category": category,
        "colour": colour,
        "brand": brand,
        "date_lost": date_lost,
        "location": location,
        "description": description,
        "photo_path": photo_path,
        "student_name": student_name,
        "student_id": student_id,
        "contact_info": clean_contact,
    })

    # Trigger automatic matching for this item
    match_res = database.match_single_lost(new_id)

    return jsonify({
        "success": True,
        "id": new_id,
        "message": match_res["message"],
        "contact": clean_contact,
        "matches": match_res["matches"],
        "matches_count": match_res["matches_count"],
        "status": match_res["status"],
        "notifications": match_res["notifications"]
    })


@app.route("/api/report-found", methods=["POST"])
def api_report_found():
    """Submit and save a found item report."""
    data = request.form if request.form else (request.get_json(silent=True) or {})
    
    item_name = data.get("item_name", "").strip()
    category = data.get("category", "").strip().lower()
    colour = data.get("colour", "").strip().lower() or None
    brand = data.get("brand", "").strip() or None
    date_found = data.get("date_found", "").strip() or datetime.now().strftime("%Y-%m-%d")
    location = data.get("location", "").strip().lower()
    description = data.get("description", "").strip()
    finder_name = data.get("finder_name", "").strip()
    contact_raw = data.get("contact_info", "").strip()

    errors = {}
    if not item_name:
        errors["item_name"] = "Item name is required."
    if not category:
        errors["category"] = "Category is required."
    if not location:
        errors["location"] = "Location is required."
    if not description:
        errors["description"] = "Detailed description is required."
    if not finder_name:
        errors["finder_name"] = "Finder name is required."

    is_valid, msg = validate_indian_mobile(contact_raw)
    if not is_valid:
        errors["contact_info"] = "Invalid mobile number. Please enter a valid 10-digit number."

    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    clean_contact = clean_mobile_number(contact_raw)

    photo_path = None
    if "photo" in request.files:
        photo_file = request.files["photo"]
        if photo_file and photo_file.filename:
            dest = Path(app.config["UPLOAD_FOLDER"]) / f"found_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo_file.filename}"
            photo_file.save(str(dest))
            photo_path = str(dest)

    new_id = database.insert_found_report({
        "item_name": item_name,
        "category": category,
        "colour": colour,
        "brand": brand,
        "date_found": date_found,
        "location": location,
        "description": description,
        "photo_path": photo_path,
        "finder_name": finder_name,
        "contact_info": clean_contact,
    })

    # Trigger automatic matching for this item
    match_res = database.match_single_found(new_id)

    return jsonify({
        "success": True,
        "id": new_id,
        "message": match_res["message"],
        "contact": clean_contact,
        "matches": match_res["matches"],
        "matches_count": match_res["matches_count"],
        "status": match_res["status"],
        "is_double_claim": match_res.get("is_double_claim", False),
        "notifications": match_res["notifications"]
    })


@app.route("/api/lodge-claim", methods=["POST"])
def api_lodge_claim():
    """Lodge direct ownership claim against a found item."""
    data = request.form if request.form else (request.get_json(silent=True) or {})
    found_id = data.get("found_id", "").strip()
    claimant_name = data.get("claimant_name", "").strip()
    student_id = data.get("student_id", "").strip()
    contact_raw = data.get("contact_info", "").strip()
    date_lost = data.get("date_lost", "").strip() or datetime.now().strftime("%Y-%m-%d")
    description = data.get("description", "").strip()
    private_proof = data.get("private_proof", "").strip()

    errors = {}
    if not found_id:
        errors["found_id"] = "Please select a target found item."
    if not claimant_name:
        errors["claimant_name"] = "Claimant name is required."
    if not student_id:
        errors["student_id"] = "Student ID is required."
    if not description:
        errors["description"] = "Description is required."
    if not private_proof:
        errors["private_proof"] = "Private proof detail is required."

    is_valid, msg = validate_indian_mobile(contact_raw)
    if not is_valid:
        errors["contact_info"] = "Invalid mobile number. Please enter a valid 10-digit number."
    elif database.is_contact_number_registered(contact_raw):
        errors["contact_info"] = "This mobile number is already registered. Please enter a different number."

    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    clean_contact = clean_mobile_number(contact_raw)

    new_lost_id = database.add_direct_claim_for_found(
        found_id=found_id,
        claimant_name=claimant_name,
        student_id=student_id,
        contact_info=clean_contact,
        description=description,
        date_lost=date_lost,
        private_proof=private_proof
    )

    database.run_database_matching()

    return jsonify({
        "success": True,
        "id": new_lost_id,
        "message": f"Ownership claim registered under ID {new_lost_id} for Found Item {found_id}!"
    })


@app.route("/api/resolve-double-claim", methods=["POST"])
def api_resolve_double_claim():
    """Arbitrate and resolve a double claim conflict."""
    data = request.get_json(silent=True) or request.form
    found_id = data.get("found_id")
    winning_lost_id = data.get("winning_lost_id")
    staff_name = data.get("staff_name", "Campus Help Desk Officer")
    private_proof = data.get("private_proof", "")
    notes = data.get("notes", "")

    if not found_id or not winning_lost_id:
        return jsonify({"success": False, "error": "Found ID and winning claimant are required."}), 400
    if not private_proof:
        return jsonify({"success": False, "error": "Mandatory private identifying proof is required."}), 400

    database.resolve_double_claim(found_id, winning_lost_id, staff_name, private_proof, notes)
    database.run_database_matching()

    return jsonify({"success": True, "message": f"Conflict for {found_id} successfully resolved in favor of {winning_lost_id}!"})


@app.route("/api/stats")
def api_stats():
    """Return live database statistics."""
    return jsonify(database.get_dashboard_statistics())


@app.route("/api/notifications")
def api_get_notifications():
    """Retrieve all notifications and unread count."""
    notifs = database.get_all_notifications()
    unread = database.get_unread_notification_count()
    return jsonify({"notifications": notifs, "unread_count": unread})


@app.route("/api/notifications/<int:notif_id>/read", methods=["POST"])
def api_mark_notification_read(notif_id):
    """Mark a notification as read."""
    database.mark_notification_read(notif_id)
    return jsonify({"success": True})


@app.route("/api/notifications/mark-all-read", methods=["POST"])
def api_mark_all_notifications_read():
    """Mark all notifications as read."""
    count = database.mark_all_notifications_read()
    return jsonify({"success": True, "count": count})


@app.route("/api/match-history")
def api_match_history():
    """Retrieve full history of previous matches."""
    history = database.get_match_history()
    return jsonify({"match_history": history})


@app.route("/photos/<filename>")
def serve_photo(filename):
    """Serve uploaded photos."""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


def run_web_server(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    """Run the Flask web server."""
    print(f"[*] Starting CIT Campus Lost & Found Web Portal on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_web_server()
