# routes/dashboard_routes.py
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, flash
from utils.db import get_db_connection
from utils.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


# -------------------------------------------------
# DASHBOARD ENTRY (ROLE BASED REDIRECT)
# -------------------------------------------------
@dashboard_bp.route("/")
@login_required
def dashboard():
    role = session.get("role")

    # Admins go to admin dashboard
    if role in ["super_admin", "state_admin", "municipal_admin"]:
        return redirect(url_for("admin.admin_dashboard"))

    # Others go to issues dashboard
    return redirect(url_for("dashboard.issues_dashboard"))


# -------------------------------------------------
# ISSUES DASHBOARD (INITIAL LOAD)
# -------------------------------------------------
@dashboard_bp.route("/issues")
@login_required
def issues_dashboard():
    user_id = session["user_id"]
    role = session["role"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ---------------- USER CONTEXT ----------------
    cursor.execute("""
        SELECT state_id, city_id, ward_id, department_id
        FROM Users
        WHERE user_id=%s
    """, (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        flash("User context lost. Please login again.", "danger")
        return redirect(url_for("auth.login"))

    profile_location = {
        "state_id": user.get("state_id"),
        "city_id": user.get("city_id"),
        "ward_id": user.get("ward_id")
    }

    # ---------------- STATES ----------------
    cursor.execute("SELECT state_id, name FROM States ORDER BY name")
    states = cursor.fetchall()

    # ---------------- BASE WHERE ----------------
    where = " WHERE 1=1 "
    params = []

    # ---------------- ROLE SCOPING ----------------
    if role == "citizen":
        # Citizen sees their own issues + all issues in their ward
        conditions = ["i.reported_by = %s"]
        params.append(user_id)

        if user.get("ward_id"):
            conditions.append("i.ward_id = %s")
            params.append(user["ward_id"])

        where += " AND (" + " OR ".join(conditions) + ")"

    elif role in ["facilitator", "field_staff"] and user.get("ward_id"):
        where += " AND i.ward_id = %s"
        params.append(user["ward_id"])

    elif role == "municipal_admin" and user.get("city_id"):
        where += " AND i.city_id = %s"
        params.append(user["city_id"])

    elif role == "department_admin" and user.get("department_id"):
        where += " AND i.assigned_department = %s"
        params.append(user["department_id"])

    # ---------------- ISSUES QUERY ----------------
    issues_query = f"""
        SELECT
            i.issue_id,
            i.title,
            i.current_status AS status,
            i.deadline,
            s.name AS state_name,
            c.name AS city_name,
            w.name AS ward_name
        FROM Issues i
        LEFT JOIN States s ON i.state_id = s.state_id
        LEFT JOIN Cities c ON i.city_id = c.city_id
        LEFT JOIN Wards w ON i.ward_id = w.ward_id
        {where}
        ORDER BY i.created_at ASC
    """

    cursor.execute(issues_query, params)
    issues = cursor.fetchall()

    # ---------------- STATS ----------------
    stats_query = f"""
        SELECT
            COUNT(*) AS Total,
            COALESCE(SUM(i.current_status='Reported'),0) AS Reported,
            COALESCE(SUM(i.current_status='Assigned'),0) AS Assigned,
            COALESCE(SUM(i.current_status='In Progress'),0) AS `In Progress`,
            COALESCE(SUM(i.current_status='In Review'),0) AS `In Review`,
            COALESCE(SUM(i.current_status='Resolved'),0) AS Resolved,
            COALESCE(SUM(i.current_status='Rejected'),0) AS Rejected
        FROM Issues i
        {where}
    """

    cursor.execute(stats_query, params)
    stats = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        role=role,
        issues=issues,
        stats=stats,
        states=states,
        profile_location=profile_location
    )


# -------------------------------------------------
# FILTER ISSUES (AJAX)
# -------------------------------------------------
@dashboard_bp.route("/issues/filter")
@login_required
def filter_issues():
    user_id = session.get("user_id")
    role = session.get("role")

    state_id = request.args.get("state_id")
    city_id = request.args.get("city_id")
    ward_id = request.args.get("ward_id")
    department_id = request.args.get("department_id")
    status = request.args.get("status")
    search = request.args.get("search")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ---------------- USER CONTEXT ----------------
    cursor.execute("""
        SELECT state_id, city_id, ward_id, department_id
        FROM Users
        WHERE user_id=%s
    """, (user_id,))
    user = cursor.fetchone() or {}

    where = " WHERE 1=1 "
    params = []

    # ---------------- ROLE SCOPING ----------------
    if role == "citizen":
        # Own issues + ward issues
        conditions = ["i.reported_by = %s"]
        params.append(user_id)
        if user.get("ward_id"):
            conditions.append("i.ward_id = %s")
            params.append(user["ward_id"])
        where += " AND (" + " OR ".join(conditions) + ")"

    elif role in ["facilitator", "field_staff"] and user.get("ward_id"):
        where += " AND i.ward_id = %s"
        params.append(user["ward_id"])

    elif role == "municipal_admin" and user.get("city_id"):
        where += " AND i.city_id = %s"
        params.append(user["city_id"])

    elif role == "department_admin" and user.get("department_id"):
        where += " AND i.assigned_department = %s"
        params.append(user["department_id"])

    # ---------------- USER-APPLIED FILTERS ----------------
    if state_id:
        where += " AND i.state_id = %s"
        params.append(state_id)
    if city_id:
        where += " AND i.city_id = %s"
        params.append(city_id)
    if ward_id:
        where += " AND i.ward_id = %s"
        params.append(ward_id)
    if department_id:
        where += " AND i.assigned_department = %s"
        params.append(department_id)
    if status:
        where += " AND i.current_status = %s"
        params.append(status)
    if search:
        like = f"%{search}%"
        where += " AND (i.title LIKE %s OR i.issue_id LIKE %s)"
        params.extend([like, like])

    # ---------------- ISSUES ----------------
    issues_query = f"""
        SELECT
            i.issue_id,
            i.title,
            i.current_status AS status,
            i.deadline,
            s.name AS state_name,
            c.name AS city_name,
            w.name AS ward_name
        FROM Issues i
        LEFT JOIN States s ON i.state_id = s.state_id
        LEFT JOIN Cities c ON i.city_id = c.city_id
        LEFT JOIN Wards w ON i.ward_id = w.ward_id
        {where}
        ORDER BY i.created_at DESC
    """

    cursor.execute(issues_query, params)
    issues = cursor.fetchall()

    # ---------------- STATS ----------------
    stats_query = f"""
        SELECT
            COUNT(*) AS Total,
            COALESCE(SUM(i.current_status='Reported'),0) AS Reported,
            COALESCE(SUM(i.current_status='Assigned'),0) AS Assigned,
            COALESCE(SUM(i.current_status='In Progress'),0) AS `In Progress`,
            COALESCE(SUM(i.current_status='In Review'),0) AS `In Review`,
            COALESCE(SUM(i.current_status='Resolved'),0) AS Resolved,
            COALESCE(SUM(i.current_status='Rejected'),0) AS Rejected
        FROM Issues i
        {where}
    """

    cursor.execute(stats_query, params)
    stats = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify({"issues": issues, "stats": stats})
