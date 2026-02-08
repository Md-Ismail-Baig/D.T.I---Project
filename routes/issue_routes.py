# routes/issue_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.db import get_db_connection
from utils.auth import login_required, role_required
from werkzeug.utils import secure_filename
import os
from datetime import datetime

# -----------------------------
# CONFIGURATION
# -----------------------------
issue_bp = Blueprint("issues", __name__, url_prefix="/issues")
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------------
# CREATE NEW ISSUE
# -----------------------------
@issue_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required("citizen", "facilitator")
def create_issue():
    user_id = session["user_id"]
    role = session["role"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        # Read form data
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category")
        deadline = request.form.get("deadline") or None
        assisted = role == "facilitator"
        source = role

        if not title or not description or not category:
            flash("All required fields must be filled.", "danger")
            return redirect(url_for("issues.create_issue"))

        # Get user location
        cursor.execute("SELECT state_id, city_id, ward_id FROM Users WHERE user_id=%s", (user_id,))
        location = cursor.fetchone()
        if not location or not all([location["state_id"], location["city_id"], location["ward_id"]]):
            flash("Your location details are incomplete. Please update your profile.", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for("profile.profile_page"))

        # Insert new issue
        cursor.execute("""
            INSERT INTO Issues (
                title, description, category,
                state_id, city_id, ward_id,
                reported_by, source, assisted,
                current_status, deadline
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            title, description, category,
            location["state_id"], location["city_id"], location["ward_id"],
            user_id, source, assisted,
            "Reported", deadline
        ))
        issue_id = cursor.lastrowid

        # Insert initial status
        cursor.execute("""
            INSERT INTO Status_Updates (issue_id, status, remarks, updated_by)
            VALUES (%s,%s,%s,%s)
        """, (issue_id, "Reported", "Issue reported", user_id))

        # Handle image uploads
        images = request.files.getlist("images")
        for img in images:
            if img and img.filename:
                filename = secure_filename(img.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                img.save(filepath)
                cursor.execute("""
                    INSERT INTO Issue_Images (issue_id, image_file, uploaded_by)
                    VALUES (%s,%s,%s)
                """, (issue_id, filepath, user_id))

        conn.commit()
        cursor.close()
        conn.close()
        flash("Issue reported successfully!", "success")
        return redirect(url_for("dashboard.dashboard"))

    cursor.close()
    conn.close()
    return render_template("issue_create.html")


# -----------------------------
# ISSUE DETAIL
# -----------------------------
@issue_bp.route("/<int:issue_id>")
@login_required
def issue_detail(issue_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch issue with location names
    cursor.execute("""
        SELECT i.*, 
               s.name AS state_name, 
               c.name AS city_name, 
               w.name AS ward_name
        FROM Issues i
        LEFT JOIN States s ON i.state_id = s.state_id
        LEFT JOIN Cities c ON i.city_id = c.city_id
        LEFT JOIN Wards w ON i.ward_id = w.ward_id
        WHERE i.issue_id=%s
    """, (issue_id,))
    issue = cursor.fetchone()
    if not issue:
        cursor.close()
        conn.close()
        return "Issue not found", 404

    # Fetch status timeline
    cursor.execute("""
        SELECT su.status, su.remarks, su.updated_at, u.name
        FROM Status_Updates su
        JOIN Users u ON su.updated_by = u.user_id
        WHERE su.issue_id=%s
        ORDER BY su.updated_at ASC
    """, (issue_id,))
    timeline = cursor.fetchall()

    # Fetch images
    cursor.execute("SELECT image_file AS file_path FROM Issue_Images WHERE issue_id=%s", (issue_id,))
    images = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("issue_detail.html", issue=issue, timeline=timeline, images=images)


# -----------------------------
# UPDATE ISSUE STATUS
# -----------------------------
@issue_bp.route("/<int:issue_id>/update", methods=["POST"])
@login_required
@role_required("department_admin", "field_staff", "municipal_admin")
def update_issue_status(issue_id):
    user_id = session["user_id"]
    new_status = request.form.get("status")
    remarks = request.form.get("remarks")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Issues SET current_status=%s, updated_at=NOW() WHERE issue_id=%s
    """, (new_status, issue_id))

    cursor.execute("""
        INSERT INTO Status_Updates (issue_id, status, remarks, updated_by)
        VALUES (%s,%s,%s,%s)
    """, (issue_id, new_status, remarks, user_id))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Issue status updated!", "success")
    return redirect(url_for("issues.issue_detail", issue_id=issue_id))


# -----------------------------
# ASSIGN ISSUE
# -----------------------------
@issue_bp.route("/<int:issue_id>/assign", methods=["GET", "POST"])
@login_required
@role_required("municipal_admin")
def assign_issue(issue_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Issues WHERE issue_id=%s", (issue_id,))
    issue = cursor.fetchone()
    if not issue:
        cursor.close()
        conn.close()
        return "Issue not found", 404

    if request.method == "POST":
        department_id = request.form.get("department_id")
        deadline = request.form.get("deadline")
        remarks = request.form.get("remarks")

        cursor.execute("""
            UPDATE Issues SET assigned_department=%s, deadline=%s, current_status='In Progress'
            WHERE issue_id=%s
        """, (department_id, deadline, issue_id))

        cursor.execute("""
            INSERT INTO Status_Updates (issue_id, status, remarks, updated_by)
            VALUES (%s,'In Progress',%s,%s)
        """, (issue_id, remarks, session["user_id"]))

        conn.commit()
        cursor.close()
        conn.close()
        flash("Issue assigned successfully!", "success")
        return redirect(url_for("issues.issue_detail", issue_id=issue_id))

    # GET: departments in city
    cursor.execute("""
        SELECT department_id, name FROM Departments WHERE city_id=%s
    """, (issue["city_id"],))
    departments = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("issue_assign.html", issue=issue, departments=departments)
