# routes/otp_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.db import get_db_connection
from datetime import datetime, timedelta
import random

otp_bp = Blueprint("otp_bp", __name__)


# ---------------------------------
# OTP GENERATOR
# ---------------------------------
def generate_otp():
    return str(random.randint(100000, 999999))


# ---------------------------------
# REQUEST OTP
# ---------------------------------
@otp_bp.route("/request_otp", methods=["GET", "POST"])
def request_otp():
    if request.method == "POST":
        mobile = request.form.get("mobile")

        otp_code = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=1)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Allow only ONE active OTP per mobile
        cursor.execute(
            "DELETE FROM OTP_Verification WHERE mobile=%s",
            (mobile,)
        )

        cursor.execute("""
            INSERT INTO OTP_Verification (mobile, otp_code, expires_at)
            VALUES (%s, %s, %s)
        """, (mobile, otp_code, expires_at))

        conn.commit()
        cursor.close()
        conn.close()

        session["otp_mobile"] = mobile
        flash(f"Your OTP is {otp_code} (valid for 1 minute)", "success")

        return redirect(url_for("otp_bp.verify_otp"))

    return render_template("otp/request_otp.html")


# ---------------------------------
# VERIFY OTP
# ---------------------------------
@otp_bp.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if "otp_mobile" not in session:
        flash("Enter mobile number first.", "warning")
        return redirect(url_for("otp_bp.request_otp"))

    if request.method == "POST":
        otp_input = request.form.get("otp")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM OTP_Verification
            WHERE mobile=%s
            ORDER BY expires_at DESC
            LIMIT 1
        """, (session["otp_mobile"],))
        record = cursor.fetchone()

        if not record or datetime.now() > record["expires_at"]:
            flash("OTP expired.", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for("otp_bp.request_otp"))

        if otp_input != record["otp_code"]:
            flash("Incorrect OTP.", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for("otp_bp.verify_otp"))

        # ✅ OTP verified → CLEAN DB
        cursor.execute(
            "DELETE FROM OTP_Verification WHERE mobile=%s",
            (session["otp_mobile"],)
        )
        conn.commit()
        cursor.close()
        conn.close()

        session["otp_verified"] = True
        return redirect(url_for("otp_bp.change_password"))

    return render_template("otp/verify_otp.html")

# ---------------------------------
# CHANGE PASSWORD (AFTER OTP)
# ---------------------------------
@otp_bp.route("/change_password", methods=["GET", "POST"])
def change_password():
    if not session.get("otp_verified") or "otp_mobile" not in session:
        flash("OTP verification required.", "warning")
        return redirect(url_for("otp_bp.request_otp"))

    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("otp_bp.change_password"))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE Users SET password=%s WHERE mobile=%s",
            (new_password, session["otp_mobile"])
        )
        conn.commit()
        cursor.close()
        conn.close()

        # 🔐 full logout — non-negotiable
        session.clear()

        flash("Password updated. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("otp/change_password.html")
