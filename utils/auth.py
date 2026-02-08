# utils/auth.py
from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "role" not in session or session["role"] not in roles:
                flash("Unauthorized access", "danger")
                return redirect(url_for("dashboard.dashboard"))
            return f(*args, **kwargs)
        return wrapper
    return decorator
