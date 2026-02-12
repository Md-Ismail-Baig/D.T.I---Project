# routes/auth_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.db import get_db_connection
from utils.auth import login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ---------------------------------
# ENTRY
# ---------------------------------
@auth_bp.route("/")
def entry():
    return redirect(url_for("auth.login"))


# ---------------------------------
# SIGNUP
# ---------------------------------
@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        mobile = request.form.get("mobile")
        password = request.form.get("password")
        state_id = request.form.get("state_id")
        city_id = request.form.get("city_id")
        ward_id = request.form.get("ward_id")
        assisted = request.form.get("assisted_signup") == "on"

        if not all([name, mobile, password]):
            flash("All required fields must be filled.", "danger")
            return redirect(url_for("auth.signup"))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT user_id FROM Users WHERE mobile=%s", (mobile,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            flash("Mobile already registered. Please login.", "warning")
            return redirect(url_for("auth.login"))

        cursor.execute("""
            INSERT INTO Users
            (name, mobile, password, role, state_id, city_id, ward_id, verified, assisted_signup)
            VALUES (%s,%s,%s,'citizen',%s,%s,%s,0,%s)
        """, (name, mobile, password, state_id, city_id, ward_id, assisted))

        conn.commit()
        cursor.close()
        conn.close()

        # OTP intent
        session["otp_mobile"] = mobile
        session["otp_purpose"] = "signup"

        flash("Signup successful. Verify your mobile number.", "success")
        return redirect(url_for("otp_bp.request_otp"))

    return render_template("otp/signup.html")


# ---------------------------------
# LOGIN
# ---------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    mobile = request.form.get("mobile")
    password = request.form.get("password")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT user_id, role, verified
        FROM Users
        WHERE mobile=%s AND password=%s
    """, (mobile, password))

    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        flash("Invalid mobile number or password.", "danger")
        return redirect(url_for("auth.login"))

    if not user["verified"]:
        flash("Account not verified. Please complete signup.", "warning")
        return redirect(url_for("auth.login"))

    # ✅ Clean login
    session.clear()
    session["user_id"] = user["user_id"]
    session["role"] = user["role"]

    flash("Login successful.", "success")
    return redirect(url_for("dashboard.dashboard"))



# ---------------------------------
# LOGOUT
# ---------------------------------
@auth_bp.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("auth.login"))


# ---------------------------------
# FORGOT PASSWORD (ENTRY)
# ---------------------------------
@auth_bp.route("/forgot_password")
def forgot_password():
    session.clear()
    session["otp_purpose"] = "reset_password"
    return redirect(url_for("otp_bp.request_otp"))


# ---------------------------------
# PROFILE PASSWORD RESET (LOGGED IN)
# ---------------------------------
@auth_bp.route("/profile/reset_password", methods=["GET", "POST"])
@login_required
def profile_reset_password():
    user_id = session["user_id"]

    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not all([current_password, new_password, confirm_password]):
            flash("All fields are required.", "danger")
            return redirect(url_for("auth.profile_reset_password"))

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.profile_reset_password"))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT password FROM Users WHERE user_id=%s",
            (user_id,)
        )
        user = cursor.fetchone()

        if not user or user["password"] != current_password:
            cursor.close()
            conn.close()
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("auth.profile_reset_password"))

        if new_password == current_password:
            cursor.close()
            conn.close()
            flash("New password must be different.", "danger")
            return redirect(url_for("auth.profile_reset_password"))

        cursor.execute(
            "UPDATE Users SET password=%s WHERE user_id=%s",
            (new_password, user_id)
        )

        conn.commit()
        cursor.close()
        conn.close()

        flash("Password updated successfully.", "success")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("profile/reset_password.html")
