# routes/auth_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.db import get_db_connection
from utils.auth import login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ---------------------------------
# DEFAULT ENTRY (OPEN SIGNUP FIRST)
# ---------------------------------
@auth_bp.route("/")
def entry():
    return redirect(url_for("auth.signup"))


# ---------------------------------
# SIGNUP (Citizen / Assisted)
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

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if mobile already exists
        cursor.execute("SELECT user_id FROM Users WHERE mobile=%s", (mobile,))
        if cursor.fetchone():
            flash("Mobile number already registered. Please login.", "warning")
            cursor.close()
            conn.close()
            return redirect(url_for("auth.login"))

        # Create unverified citizen
        cursor.execute("""
            INSERT INTO Users
            (name, mobile, password, role, state_id, city_id, ward_id, verified, assisted_signup)
            VALUES (%s,%s,%s,'citizen',%s,%s,%s,0,%s)
        """, (name, mobile, password, state_id, city_id, ward_id, assisted))

        conn.commit()
        cursor.close()
        conn.close()

        # Store mobile for OTP flow
        session["otp_mobile"] = mobile
        flash("Signup successful! Please verify your mobile number.", "success")
        return redirect(url_for("otp_bp.request_otp"))

    return render_template("otp/signup.html")


# ---------------------------------
# LOGIN
# ---------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        session.pop("user_id", None)
        session.pop("role", None)

    if request.method == "POST":
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
            session["otp_mobile"] = mobile
            flash("Please verify your mobile number first.", "warning")
            return redirect(url_for("otp_bp.request_otp"))

        session["user_id"] = user["user_id"]
        session["role"] = user["role"]

        flash("Login successful!", "success")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("login.html")


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
    session["otp_purpose"] = "reset_password"
    return redirect(url_for("otp_bp.request_otp"))

@auth_bp.route("/profile/change_password", methods=["GET", "POST"])
@login_required
def profile_change_password():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not current_password or not new_password or not confirm_password:
            flash("All fields are required.", "danger")
            return redirect(url_for("auth.profile_change_password"))

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.profile_change_password"))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT password FROM Users WHERE user_id=%s",
            (session["user_id"],)
        )
        user = cursor.fetchone()

        if not user or user["password"] != current_password:
            flash("Current password is incorrect.", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for("auth.profile_change_password"))

        cursor.execute(
            "UPDATE Users SET password=%s WHERE user_id=%s",
            (new_password, session["user_id"])
        )
        conn.commit()
        cursor.close()
        conn.close()

        # 🚫 DO NOT CLEAR SESSION HERE
        flash("Password updated successfully.", "success")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("profile/change_password.html")
