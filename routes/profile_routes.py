# routes/profile_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from utils.db import get_db_connection
from utils.auth import login_required

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


# -----------------------------
# VIEW PROFILE
# -----------------------------
@profile_bp.route("/")
@login_required
def profile_page():
    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT u.*,
               s.name AS state_name,
               c.name AS city_name,
               w.name AS ward_name
        FROM Users u
        LEFT JOIN States s ON u.state_id = s.state_id
        LEFT JOIN Cities c ON u.city_id = c.city_id
        LEFT JOIN Wards w ON u.ward_id = w.ward_id
        WHERE u.user_id=%s
    """, (user_id,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("profile/profile.html", user=user)


# -----------------------------
# UPDATE PROFILE
# -----------------------------
@profile_bp.route("/update", methods=["GET", "POST"])
@login_required
def update_profile():
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        mobile = request.form.get("mobile", "").strip()

        state_id = request.form.get("state_id") or None
        city_id = request.form.get("city_id") or None
        ward_id = request.form.get("ward_id") or None

        cursor.execute("""
            UPDATE Users
            SET name=%s,
                email=%s,
                mobile=%s,
                state_id=%s,
                city_id=%s,
                ward_id=%s
            WHERE user_id=%s
        """, (name, email, mobile, state_id, city_id, ward_id, user_id))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile.profile_page"))

    # ---------- GET ----------
    cursor.execute("SELECT * FROM Users WHERE user_id=%s", (user_id,))
    user = cursor.fetchone()

    cursor.execute("SELECT state_id, name FROM States ORDER BY name")
    states = cursor.fetchall()

    cursor.close()
    conn.close()

    # Note: cities and wards are no longer fetched from backend
    # JS will dynamically load them based on selected state/city
    return render_template(
        "profile/update_profile.html",
        user=user,
        states=states
    )


# -----------------------------
# API: GET CITIES BY STATE
# -----------------------------
@profile_bp.route("/api/cities")
@login_required
def get_cities():
    state_id = request.args.get("state_id")
    if not state_id:
        return jsonify({"cities": []})

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT city_id, name FROM Cities WHERE state_id=%s ORDER BY name",
        (state_id,)
    )
    cities = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"cities": cities})


# -----------------------------
# API: GET WARDS BY CITY
# -----------------------------
@profile_bp.route("/api/wards")
@login_required
def get_wards():
    city_id = request.args.get("city_id")
    if not city_id:
        return jsonify({"wards": []})

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT ward_id, name FROM Wards WHERE city_id=%s ORDER BY name",
        (city_id,)
    )
    wards = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"wards": wards})
