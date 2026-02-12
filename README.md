# D.T.I — Public Issue Reporting & Tracking System

> A structured, role-based civic governance platform for transparent public issue reporting, tracking, and resolution.

---

## 📌 Overview

Cities and local communities face recurring public issues such as damaged roads, sanitation problems, water leakage, and safety hazards.  

Reporting mechanisms are often fragmented, opaque, or inaccessible to non-technical citizens.

This project digitizes civic issue reporting while respecting real-world municipal hierarchies and enabling assisted and offline participation.

The system is designed as a scalable governance tool — not just a complaint form.

---

## 🎯 Objectives

- Provide structured issue reporting and tracking
- Ensure transparency through status history and auditability
- Support assisted and offline submissions
- Enforce strict role-based access control
- Reflect real municipal governance workflow
- Maintain long-term extensibility and maintainability

---

## 👥 User Roles

The system models real governance layers:

- **Citizen** – Reports and tracks personal issues
- **Facilitator** – Assists citizens in offline/verbal reporting
- **Field Staff** – Reports and verifies issues on-site
- **Department Admin** – Manages department-level issues
- **Municipal Admin** – Assigns departments and deadlines
- **State Admin** – Oversees municipalities
- **Super Admin** – System-wide visibility and oversight

Each role has enforced permission boundaries at the backend.

---

## 🔁 Issue Lifecycle

1. Issue is reported (Citizen / Facilitator / Field Staff)
2. Municipal Admin reviews submission
3. Department is assigned with a deadline
4. Status progresses through controlled stages
5. Resolution is recorded
6. Citizen can track complete issue history

No issue is deleted.  
All actions are timestamped and traceable.

---

## 🧩 Current Features

- Mobile-based authentication with OTP verification
- Role-based and location-based access control
- Hierarchical location model (State → City → Ward)
- Assisted signup and assisted issue reporting
- Image uploads for issue evidence
- Status history tracking
- Dashboard filtering and search
- Administrative monitoring interfaces

---

## 🛠 Technology Stack

- **Backend**: Python (Flask)
- **Frontend**: HTML, CSS, Jinja2, JavaScript
- **Database**: MySQL
- **Authentication**: Session-based with OTP
- **Version Control**: Git & GitHub

The stack is intentionally simple, readable, and maintainable.

---

## 📂 Project Structure

app.py # Application entry point
routes/ # Flask blueprints and route logic
templates/ # Jinja2 templates
static/ # CSS, JS, uploads
utils/ # Helpers and authentication utilities


Sensitive configuration files (`config.py`, `.env`) are excluded from version control.

---

## 🚀 Getting Started (Development)

1. Clone the repository
2. Create a virtual environment
3. Install dependencies
4. Configure database in `config.py`
5. Run database schema
6. Start the Flask server

Detailed setup instructions may expand as the system stabilizes.

---

## 🤝 Collaboration Model

- `main` is protected
- All changes happen via feature branches
- Every update requires a Pull Request
- Code review is mandatory
- Stability over speed

See `CONTRIBUTING.md` for full workflow.

---

## 🔮 Planned Enhancements

- Password hashing and improved security
- OTP rate limiting
- Notification system (SMS/Email)
- Audit logs
- Analytics dashboard
- Performance optimization
- Accessibility improvements

Enhancements will be incremental and controlled.

---

## 🏛 Project Philosophy

This is not just a web application.

It is an attempt to:

- Respect governance structures
- Include offline and non-technical citizens
- Encourage accountability through visibility
- Build software aligned with real-world workflows

We are not building something flashy.  
We are building something correct.

---

## 📌 Status

🟡 Active Development

The system is functional but evolving.  
Expect refinement, iteration, and structural improvement.