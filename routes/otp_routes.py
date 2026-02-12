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
    # OTP must always have a purpose
    if "otp_purpose" not in session:
        flash("Invalid OTP request.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        mobile = request.form.get("mobile")

        if not mobile:
            flash("Mobile number is required.", "danger")
            return redirect(url_for("otp_bp.request_otp"))

        otp_code = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=1)

        conn = get_db_connection()
        cursor = conn.cursor()

        # enforce single active OTP
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

        # (DEV ONLY — replace with SMS in prod)
        flash(f"Your OTP is {otp_code} (valid for 1 minute)", "success")

        return redirect(url_for("otp_bp.verify_otp"))

    return render_template("otp/request_otp.html")


# ---------------------------------
# VERIFY OTP
# ---------------------------------
@otp_bp.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    mobile = session.get("otp_mobile")
    purpose = session.get("otp_purpose")

    if not mobile or not purpose:
        flash("OTP session expired. Please start again.", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        otp_input = request.form.get("otp")

        if not otp_input:
            flash("OTP is required.", "danger")
            return redirect(url_for("otp_bp.verify_otp"))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT otp_code, expires_at
            FROM OTP_Verification
            WHERE mobile=%s
            ORDER BY expires_at DESC
            LIMIT 1
        """, (mobile,))

        record = cursor.fetchone()

        if not record or datetime.now() > record["expires_at"]:
            cursor.close()
            conn.close()
            flash("OTP expired. Please request a new one.", "danger")
            return redirect(url_for("otp_bp.request_otp"))

        if otp_input != record["otp_code"]:
            cursor.close()
            conn.close()
            flash("Incorrect OTP.", "danger")
            return redirect(url_for("otp_bp.verify_otp"))

        # OTP VALID → destroy it
        cursor.execute(
            "DELETE FROM OTP_Verification WHERE mobile=%s",
            (mobile,)
        )
        conn.commit()
        cursor.close()
        conn.close()

        # -------------------------
        # PURPOSE HANDLING
        # -------------------------

        if purpose in ("signup", "login"):
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE Users SET verified=1 WHERE mobile=%s",
                (mobile,)
            )

            conn.commit()
            cursor.close()
            conn.close()

            # full OTP cleanup
            session.pop("otp_mobile", None)
            session.pop("otp_purpose", None)

            flash("Mobile verified successfully. Please login.", "success")
            return redirect(url_for("auth.login"))

        if purpose == "reset_password":
            session["otp_verified"] = True
            return redirect(url_for("otp_bp.change_password"))

        # fallback
        session.clear()
        flash("Invalid OTP flow.", "danger")
        return redirect(url_for("auth.login"))

    return render_template("otp/verify_otp.html")


# ---------------------------------
# CHANGE PASSWORD (OTP VERIFIED)
# ---------------------------------
@otp_bp.route("/change_password", methods=["GET", "POST"])
def change_password():
    if session.get("otp_purpose") != "reset_password" or not session.get("otp_verified"):
        flash("Unauthorized access.", "danger")
        return redirect(url_for("auth.login"))

    mobile = session.get("otp_mobile")

    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not new_password or not confirm_password:
            flash("All fields are required.", "danger")
            return redirect(url_for("otp_bp.change_password"))

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("otp_bp.change_password"))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE Users SET password=%s WHERE mobile=%s",
            (new_password, mobile)
        )

        conn.commit()
        cursor.close()
        conn.close()

        # hard reset session
        session.clear()

        flash("Password updated successfully. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("otp/change_password.html")
