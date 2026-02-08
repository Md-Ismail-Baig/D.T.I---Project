# utils/otp.py
import random
from datetime import datetime, timedelta
from utils.db import get_db_connection


def generate_otp(mobile):
    """Generates a 6-digit OTP and stores it in DB with 1 min expiry"""

    otp = f"{random.randint(100000, 999999)}"
    expires_at = datetime.now() + timedelta(minutes=1)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Clean any previous OTPs for this mobile (single active OTP rule)
    cursor.execute("""
        DELETE FROM OTP_Verification
        WHERE mobile = %s
    """, (mobile,))

    # Insert new OTP
    cursor.execute("""
        INSERT INTO OTP_Verification (mobile, otp_code, expires_at)
        VALUES (%s, %s, %s)
    """, (mobile, otp, expires_at))

    conn.commit()
    cursor.close()
    conn.close()

    return otp


def verify_otp(mobile, otp_input):
    """Verifies OTP and deletes all OTPs on success or expiry"""

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch latest OTP for this mobile
    cursor.execute("""
        SELECT *
        FROM OTP_Verification
        WHERE mobile = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (mobile,))

    record = cursor.fetchone()

    if not record:
        cursor.close()
        conn.close()
        return False, "OTP not found"

    # Expired OTP → cleanup
    if record["expires_at"] < datetime.now():
        cursor.execute("""
            DELETE FROM OTP_Verification
            WHERE mobile = %s
        """, (mobile,))
        conn.commit()
        cursor.close()
        conn.close()
        return False, "OTP expired"

    # Wrong OTP
    if record["otp_code"] != otp_input:
        cursor.close()
        conn.close()
        return False, "Invalid OTP"

    # ✅ Correct OTP → CLEANUP
    cursor.execute("""
        DELETE FROM OTP_Verification
        WHERE mobile = %s
    """, (mobile,))
    conn.commit()

    cursor.close()
    conn.close()

    return True, "OTP verified"
