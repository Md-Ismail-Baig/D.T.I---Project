
from flask import Blueprint, render_template
from utils.db import get_db_connection

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def home():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Total Issues
    cursor.execute("SELECT COUNT(*) AS total FROM Issues")
    total_issues = cursor.fetchone()["total"]

    # Resolved Issues
    cursor.execute("SELECT COUNT(*) AS total FROM Issues WHERE current_status = 'Resolved'")
    resolved_issues = cursor.fetchone()["total"]

    # In Progress Issues
    cursor.execute("""
        SELECT COUNT(*) AS total 
        FROM Issues 
        WHERE current_status IN ('Assigned', 'In Progress', 'In Review')
    """)
    in_progress_issues = cursor.fetchone()["total"]

    # Pending Issues (Reported but not yet assigned)
    cursor.execute("""
        SELECT COUNT(*) AS total 
        FROM Issues 
        WHERE current_status = 'Reported'
    """)
    pending_issues = cursor.fetchone()["total"]

    cursor.close()
    conn.close()

    # Avoid division by zero
    if total_issues > 0:
        resolution_rate = round((resolved_issues / total_issues) * 100, 1)
        active_rate = round(((in_progress_issues + pending_issues) / total_issues) * 100, 1)
    else:
        resolution_rate = 0
        active_rate = 0

    return render_template(
        "info.html",
        total_issues=total_issues,
        resolved_issues=resolved_issues,
        in_progress_issues=in_progress_issues,
        pending_issues=pending_issues,
        resolution_rate=resolution_rate,
        active_rate=active_rate
    )

