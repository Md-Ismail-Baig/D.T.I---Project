# routes/profile_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.db import get_db_connection
from utils.auth import login_required
from werkzeug.security import generate_password_hash, check_password_hash

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")

# -----------------------------
# VIEW PROFILE
# -----------------------------
@profile_bp.route("/")
@login_required
def profile_page():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please login first.", "warning")
        return redirect(url_for("auth.login"))

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
        WHERE u.user_id = %s
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
    user_id = session.get("user_id")
    if not user_id:
        flash("Please login first.", "warning")
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        mobile = request.form.get("mobile", "").strip()
        state_id = request.form.get("state_id") or None
        city_id = request.form.get("city_id") or None
        ward_id = request.form.get("ward_id") or None

        try: state_id = int(state_id)
        except: state_id = None
        try: city_id = int(city_id)
        except: city_id = None
        try: ward_id = int(ward_id)
        except: ward_id = None

        cursor.execute("""
            UPDATE Users
            SET name=%s, email=%s, mobile=%s,
                state_id=%s, city_id=%s, ward_id=%s
            WHERE user_id=%s
        """, (name, email, mobile, state_id, city_id, ward_id, user_id))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile.profile_page"))

    cursor.execute("SELECT * FROM Users WHERE user_id=%s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template("profile/update_profile.html", user=user)


