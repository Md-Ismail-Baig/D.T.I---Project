# routes/dashboard_routes.py
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
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

    if role in ["super_admin", "state_admin", "municipal_admin"]:
        return redirect(url_for("admin.admin_dashboard"))

    return redirect(url_for("dashboard.issues_dashboard"))


# -------------------------------------------------
# ISSUES DASHBOARD (MAIN PAGE)
# -------------------------------------------------
@dashboard_bp.route("/issues")
@login_required
def issues_dashboard():
    user_id = session.get("user_id")
    role = session.get("role")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ---------------- STATES (FILTER DROPDOWN) ----------------
    cursor.execute("SELECT state_id, name FROM States ORDER BY name")
    states = cursor.fetchall()

    # ---------------- STATS (CARDS) ----------------
    cursor.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(current_status='Reported') AS reported,
            SUM(current_status='Assigned') AS assigned,
            SUM(current_status='In Progress') AS in_progress,
            SUM(current_status='In Review') AS in_review,
            SUM(current_status='Resolved') AS resolved,
            SUM(current_status='Rejected') AS rejected
        FROM Issues
    """)
    row = cursor.fetchone()

    stats = {
        "Total": row["total"],
        "Reported": row["reported"],
        "Assigned": row["assigned"],
        "In Progress": row["in_progress"],
        "In Review": row["in_review"],
        "Resolved": row["resolved"],
        "Rejected": row["rejected"]
    }

    # ---------------- BASE QUERY ----------------
    query = """
        SELECT i.issue_id, i.title, i.current_status AS status,
               i.deadline,
               w.name AS ward_name,
               c.name AS city_name,
               s.name AS state_name
        FROM Issues i
        LEFT JOIN Wards w ON i.ward_id = w.ward_id
        LEFT JOIN Cities c ON i.city_id = c.city_id
        LEFT JOIN States s ON i.state_id = s.state_id
        WHERE 1=1
    """
    params = []

    # ---------------- ROLE VISIBILITY ----------------
    if role == "citizen":
        query += " AND i.reported_by = %s"
        params.append(user_id)

    elif role in ["facilitator", "field_staff"]:
        cursor.execute("SELECT ward_id FROM Users WHERE user_id=%s", (user_id,))
        ward = cursor.fetchone()
        if ward and ward["ward_id"]:
            query += " AND i.ward_id = %s"
            params.append(ward["ward_id"])

    elif role == "municipal_admin":
        cursor.execute("SELECT city_id FROM Users WHERE user_id=%s", (user_id,))
        city = cursor.fetchone()
        if city and city["city_id"]:
            query += " AND i.city_id = %s"
            params.append(city["city_id"])

    elif role == "department_admin":
        query += " AND i.assigned_department IS NOT NULL"

    query += " ORDER BY i.created_at DESC"

    cursor.execute(query, params)
    issues = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        issues=issues,
        states=states,
        role=role,
        stats=stats
    )


# -------------------------------------------------
# FILTER ISSUES (AJAX)
# -------------------------------------------------
@dashboard_bp.route("/issues/filter")
@login_required
def filter_issues():
    role = session.get("role")
    user_id = session.get("user_id")

    state_id = request.args.get("state_id")
    city_id = request.args.get("city_id")
    ward_id = request.args.get("ward_id")
    department_id = request.args.get("department_id")
    status = request.args.get("status")
    search = request.args.get("search")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    where = " WHERE 1=1 "
    params = []

    # =================================================
    # ROLE-BASED VISIBILITY (HARD CONSTRAINTS)
    # =================================================

    if role == "citizen":
        where += " AND i.reported_by = %s"
        params.append(user_id)

    elif role == "facilitator":
        cursor.execute(
            "SELECT ward_id FROM Users WHERE user_id=%s",
            (user_id,)
        )
        user = cursor.fetchone()
        if user and user["ward_id"]:
            where += " AND i.ward_id = %s"
            params.append(user["ward_id"])

    elif role == "field_staff":
        cursor.execute("""
            SELECT ward_id, department_id
            FROM Users
            WHERE user_id=%s
        """, (user_id,))
        user = cursor.fetchone()

        if user:
            where += " AND i.ward_id = %s"
            params.append(user["ward_id"])

            where += " AND i.assigned_department = %s"
            params.append(user["department_id"])

        # 🔒 Enforce valid statuses for field staff
        allowed_statuses = ["Assigned", "In Progress", "Resolved"]
        if status and status not in allowed_statuses:
            status = None  # silently ignore invalid status

    elif role == "municipal_admin":
        cursor.execute(
            "SELECT city_id FROM Users WHERE user_id=%s",
            (user_id,)
        )
        user = cursor.fetchone()
        if user and user["city_id"]:
            where += " AND i.city_id = %s"
            params.append(user["city_id"])

    elif role == "department_admin":
        cursor.execute(
            "SELECT department_id FROM Users WHERE user_id=%s",
            (user_id,)
        )
        user = cursor.fetchone()
        if user and user["department_id"]:
            where += " AND i.assigned_department = %s"
            params.append(user["department_id"])

    # super_admin & state_admin → unrestricted

    # =================================================
    # USER FILTERS (SAFE TO APPLY NOW)
    # =================================================

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
        where += " AND (i.title LIKE %s OR i.issue_id LIKE %s)"
        like = f"%{search}%"
        params.extend([like, like])

    # =================================================
    # ISSUES QUERY
    # =================================================

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

    # =================================================
    # STATS QUERY (MUST MATCH EXACT SAME WHERE)
    # =================================================

    stats_query = f"""
        SELECT
            COUNT(*) AS total,
            SUM(i.current_status='Reported') AS Reported,
            SUM(i.current_status='Assigned') AS Assigned,
            SUM(i.current_status='In Progress') AS `In Progress`,
            SUM(i.current_status='In Review') AS `In Review`,
            SUM(i.current_status='Resolved') AS Resolved,
            SUM(i.current_status='Rejected') AS Rejected

        FROM Issues i
        {where}
    """

    cursor.execute(stats_query, params)
    stats = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify({
        "issues": issues,
        "stats": stats
    })
