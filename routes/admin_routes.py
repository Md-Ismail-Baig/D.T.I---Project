# routes/admin_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session,jsonify
from utils.db import get_db_connection
from utils.auth import login_required, role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# -----------------------------
# FILTER USERS (AJAX)
# -----------------------------
@admin_bp.route("/users/filter")
@login_required
@role_required("super_admin", "state_admin", "municipal_admin")
def filter_users():

    role = session.get("role")
    session_state_id = session.get("state_id")
    session_city_id = session.get("city_id")

    state_id = request.args.get("state_id")
    city_id = request.args.get("city_id")
    ward_id = request.args.get("ward_id")
    search = request.args.get("search")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT 
            u.user_id, u.name, u.mobile, u.email, u.role,
            u.verified, u.assisted_signup, u.created_at,
            s.name AS state_name,
            c.name AS city_name,
            w.name AS ward_name
        FROM Users u
        LEFT JOIN States s ON u.state_id = s.state_id
        LEFT JOIN Cities c ON u.city_id = c.city_id
        LEFT JOIN Wards w ON u.ward_id = w.ward_id
        WHERE 1=1
    """
    params = []

    # ---------------- ROLE VISIBILITY ----------------
    if role == "state_admin":
        query += " AND (u.state_id = %s OR u.assisted_signup = TRUE)"
        params.append(session_state_id)

    elif role == "municipal_admin":
        query += " AND (u.city_id = %s OR u.assisted_signup = TRUE)"
        params.append(session_city_id)

    elif role == "super_admin":
        pass  # full access

    # ---------------- PROGRESSIVE FILTERS ----------------
    if state_id:
        query += " AND u.state_id = %s"
        params.append(state_id)

    if city_id:
        query += " AND u.city_id = %s"
        params.append(city_id)

    if ward_id:
        query += " AND u.ward_id = %s"
        params.append(ward_id)

    # ---------------- SEARCH ----------------
    if search:
        like = f"%{search}%"
        query += " AND (u.name LIKE %s OR u.mobile LIKE %s)"
        params.extend([like, like])

    query += " ORDER BY u.created_at ASC"

    cursor.execute(query, params)
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"users": users})



# GET CITIES FOR STATE
@admin_bp.route("/get_cities")
def get_cities():
    state_id = request.args.get("state_id")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Cities WHERE state_id=%s", (state_id,))
    cities = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"cities": cities}

# GET WARDS FOR CITY
@admin_bp.route("/get_wards")
def get_wards():
    city_id = request.args.get("city_id")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Wards WHERE city_id=%s", (city_id,))
    wards = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"wards": wards}

@admin_bp.route("/get_departments")
@login_required
def get_departments():
    city_id = request.args.get("city_id")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT department_id, name FROM Departments WHERE city_id=%s",
        (city_id,)
    )
    departments = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"departments": departments})


# -----------------------------
# ADMIN DASHBOARD
# -----------------------------
@admin_bp.route("/dashboard")
@login_required
@role_required("super_admin", "state_admin", "municipal_admin")
def admin_dashboard():
    # OTP/login check
    if not session.get("user_id"):
        flash("Please login first using OTP.", "warning")
        return redirect(url_for("otp.request_otp"))

    return render_template("admin/admin_dashboard.html", role=session["role"])


# -----------------------------
# VIEW USERS PAGE
# -----------------------------
@admin_bp.route("/users")
@login_required
@role_required("super_admin", "state_admin", "municipal_admin")
def view_users():

    role = session["role"]
    state_id = session.get("state_id")
    city_id = session.get("city_id")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM States")
    states = cursor.fetchall()

    base_query = """
        SELECT u.user_id, u.name, u.mobile, u.email, u.role,
               u.verified, u.assisted_signup, u.created_at,
               s.name AS state_name,
               c.name AS city_name,
               w.name AS ward_name
        FROM Users u
        LEFT JOIN States s ON u.state_id = s.state_id
        LEFT JOIN Cities c ON u.city_id = c.city_id
        LEFT JOIN Wards w ON u.ward_id = w.ward_id
    """

    params = []

    if role == "state_admin":
        base_query += " WHERE (u.state_id = %s OR u.assisted_signup = TRUE)"
        params.append(state_id)

    elif role == "municipal_admin":
        base_query += " WHERE (u.city_id = %s OR u.assisted_signup = TRUE)"
        params.append(city_id)

    base_query += " ORDER BY u.user_id ASC"

    cursor.execute(base_query, params)
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin/user.html", users=users, states=states)



# -----------------------------
# CREATE NEW USER
# -----------------------------
@admin_bp.route("/create_user", methods=["GET", "POST"])
@login_required
@role_required("super_admin", "state_admin", "municipal_admin")
def create_user():
    if not session.get("user_id"):
        flash("Please login first using OTP.", "warning")
        return redirect(url_for("otp.request_otp"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch states, cities, wards
    cursor.execute("SELECT * FROM States")
    states = cursor.fetchall()

    cursor.execute("SELECT * FROM Cities")
    cities = cursor.fetchall()

    cursor.execute("SELECT * FROM Wards")
    wards = cursor.fetchall()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role")

        state_id = int(request.form.get("state_id")) if request.form.get("state_id") else None
        city_id = int(request.form.get("city_id")) if request.form.get("city_id") else None
        ward_id = int(request.form.get("ward_id")) if request.form.get("ward_id") else None

        # ✅ FIX: mark assisted signup explicitly
        assisted_signup = True

        cursor.execute("""
            INSERT INTO Users (
                name, email, mobile, password, role,
                state_id, city_id, ward_id,
                verified, assisted_signup
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,TRUE,%s)
        """, (
            name, email, mobile, password, role,
            state_id, city_id, ward_id,
            assisted_signup
        ))

        conn.commit()
        cursor.close()
        conn.close()

        flash("User created successfully (Assisted Signup).", "success")
        return redirect(url_for("admin.view_users"))

    cursor.close()
    conn.close()
    return render_template(
        "admin/admin_create_user.html",
        states=states,
        cities=cities,
        wards=wards
    )

