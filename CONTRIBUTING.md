# Contributing Guide

Thank you for your interest in contributing to  
**D.T.I — Public Issue Reporting & Tracking System**.

This project follows a structured, review-driven workflow to ensure stability, traceability, and long-term maintainability.

Please read this document before contributing.

---

## Table of Contents

1. Code of Conduct  
2. Getting Started  
3. Development Workflow  
4. Branching Strategy  
5. Pull Request Guidelines  
6. Coding Standards  
7. Frontend Contribution Guidelines  
8. Backend Contribution Guidelines  
9. Testing Requirements  
10. After Your Pull Request Is Merged  

---

## 1. Code of Conduct

- Be respectful and professional.
- Focus on improving the project.
- Accept feedback constructively.
- Keep discussions technical and solution-oriented.

---

## 2. Getting Started

### Step 1: Fork the Repository

Click **Fork** on GitHub to create your own copy.

### Step 2: Clone Your Fork

git clone https://github.com/YOUR_USERNAME/REPOSITORY_NAME.git

### Step 3: Add Upstream Remote (One-Time Setup)

git remote add upstream https://github.com/ORIGINAL_OWNER/REPOSITORY_NAME.git


## 3. Development Workflow
Before starting any new work, synchronize your fork with the main repository:

git fetch upstream
git checkout main
git merge upstream/main
git push origin main
This prevents outdated branches and merge conflicts.

## 4. Branching Strategy
- main is protected and represents stable code.
- All development must occur in feature branches.
- Never commit directly to main.
- Create a new branch for every task:

git checkout -b feature/short-description
Branch naming examples:

feature/dashboard-ui

feature/otp-validation

feature/role-permission-fix

bugfix/status-update-error

Branches are temporary and must not be reused after merge.

## 5. Pull Request Guidelines
After pushing your feature branch:

- Open a Pull Request to main.

- Provide a clear title.

- Include a detailed description explaining:

What was changed

Why it was changed

Any limitations or assumptions

Add screenshots for UI changes.

Ensure your branch is up-to-date with main.

### Responding to Review
If changes are requested:

Update the same branch.

Commit the fixes.

Push again.

Do not create a new PR for review updates.

## 6. Coding Standards
General
- Write clean, readable, and modular code.

- Avoid unnecessary complexity.

- Follow existing structure and naming patterns.

- Add comments where logic is not immediately clear.

Commit Messages
- Commit messages must be descriptive.

Good example:

Add resolution rate calculation to homepage

Bad examples:

update
fix
changes

## 7. Frontend Contribution Guidelines
- Extend base.html for layouts.

- Maintain responsive design.

- Do not use inline CSS.

- Reuse existing CSS classes where possible.

- Keep design consistent with the current theme.

- Avoid breaking existing layout structures.

- For UI updates:

- Test across multiple screen sizes.

- Provide screenshots in the Pull Request.

## 8. Backend Contribution Guidelines
- Respect role-based access control logic.

- Do not bypass permission checks.

- Preserve audit fields (timestamps, history tracking).

- Keep database queries optimized.

- Do not remove existing relationships without discussion.

If modifying the database schema:

- Clearly document the change in the PR.

- Provide migration instructions if required.

## 9. Testing Requirements
Before submitting a Pull Request:

- Verify all affected routes work.

- Ensure no template rendering errors.

- Confirm role restrictions function correctly.

- Test issue lifecycle transitions.

- Check browser console for errors (frontend updates).

- Unstable or untested changes will not be merged.

## 10. After Your Pull Request Is Merged
- Delete your feature branch.

Synchronize your local repository:

git fetch upstream
git checkout main
git merge upstream/main
git push origin main

- Create a new branch for new work.

- Every task requires a new branch.

What Is Not Allowed
- Direct pushes to main

- Working directly on main

- Reusing old feature branches

- Large unrelated changes in one PR

- Skipping synchronization before new work

### Maintainer Role
The maintainer:

- Reviews Pull Requests

- Requests revisions when necessary

- Merges stable contributions

- Protects the integrity of main

- All merges happen through review.

### Final Note
If you are unsure about an implementation:

- Open an Issue for discussion Or create a Draft Pull Request

Clarity before code.