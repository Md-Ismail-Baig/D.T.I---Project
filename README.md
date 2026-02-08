# D.T.I---Project
Public Issue Reporting &amp; Tracking System for inclusive, role-based civic governance

# Public Issue Reporting & Tracking System

> A role-based, inclusive civic issue management platform that combines digital tracking with assisted and offline reporting.

---

## 📌 Overview

Cities and local communities face recurring public issues such as damaged roads, sanitation problems, water leakage, and safety hazards.  
While these issues are common, reporting and resolution are often unstructured, opaque, and inaccessible to many citizens.

This project aims to **digitize public issue reporting and tracking** while respecting real-world municipal hierarchies and supporting **offline, assisted, and non-technical users** through human facilitation.

The system is designed as a **collaborative, evolving platform**, developed incrementally by a team and refined over time.

---

## 🎯 Key Objectives

- Provide a structured platform for reporting and tracking public issues
- Ensure transparency and accountability through status tracking and timelines
- Support both online and offline (assisted) complaint submission
- Enforce role-based and location-based access control
- Reflect real municipal governance workflows
- Build an extensible foundation for future enhancements

---

## 👥 User Roles

The system supports multiple roles aligned with real governance structures:

- **Citizen** – Reports and tracks own issues
- **Community Facilitator** – Assists citizens with offline or verbal reporting
- **Field Staff / Inspector** – Reports and verifies issues on the ground
- **Department Admin** – Manages department-assigned issues
- **Municipal Admin** – Assigns departments, sets deadlines, monitors progress
- **State Admin** – Oversees municipalities within a state
- **Super Admin** – System-wide oversight and monitoring

Each role has **strict visibility and permission boundaries** enforced at the backend.

---

## 🔁 Issue Lifecycle

1. Issue is reported (Citizen / Facilitator / Field Staff)
2. Issue is reviewed by Municipal Admin
3. Department is assigned with a deadline
4. Issue progresses through status updates
5. Resolution is verified and recorded
6. Citizen can track the complete history

No issue is deleted.  
All actions are timestamped and traceable.

---

## 🧩 Core Features (Current)

- Mobile-based authentication with OTP verification
- Role-based access control and route protection
- Location hierarchy (State → City → Ward)
- Assisted and offline issue reporting
- Issue dashboard with filters and search
- Status timeline with remarks and updates
- Image uploads for issue evidence
- Admin dashboards for monitoring and assignment

> ⚠️ Note: This project is under active development. Features and flows will continue to evolve.

---

## 🛠 Technology Stack

- **Backend**: Python (Flask)
- **Frontend**: HTML, CSS, Jinja2, JavaScript
- **Database**: MySQL
- **Authentication**: Session-based with OTP verification
- **Version Control**: Git & GitHub


The stack is intentionally simple, readable, and beginner-friendly while remaining scalable.

---

## 📂 Project Structure (High Level)

- `app.py` – Application entry point  
- `routes/` – Flask blueprints and route logic  
- `utils/` – Authentication and helper utilities  
- `templates/` – HTML templates (Jinja2)  
- `static/` – CSS, JavaScript, and uploaded files  
 

Sensitive configuration files (`config.py`, `.env`) are excluded from version control.

---

## 🚀 Getting Started (Development)

1. Clone the repository
2. Create a virtual environment
3. Install dependencies
4. Create `config.py` using `config.example.py`
5. Set up the database schema
6. Run the Flask application

> Detailed setup instructions will be expanded as the project stabilizes.

---

## 🤝 Team Collaboration

This is a **team project**.

- Development happens collaboratively via GitHub
- Features are added incrementally
- README and documentation will be updated as the system matures
- Code reviews and refactoring are expected parts of the workflow

We prioritize **clarity, correctness, and maintainability** over rushed features.

---

## 🔮 Planned Enhancements

- Password hashing and enhanced security controls
- OTP resend limits and rate limiting
- Audit logs and activity tracking
- Notifications (SMS / Email)
- Advanced analytics and reports
- Accessibility and usability improvements
- Performance optimization and pagination

These will be implemented progressively.

---

## 🧭 Philosophy

This project is not just a web application.

It is an attempt to:
- Respect existing governance structures
- Include citizens who are offline or non-technical
- Encourage accountability through visibility
- Build software that reflects real-world constraints

We are not trying to build something flashy.  
We are trying to build something **right**.

---

## 📌 Status

🟡 **In Active Development**

The system is functional but evolving.  
Expect regular changes, improvements, and refinements.

---

