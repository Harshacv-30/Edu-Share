# EDUSHARE – Academic Notes Sharing & Management System

EduShare is a full-stack academic notes sharing and management platform built with **Django**, **HTML5/CSS3/JavaScript**, and **SQLite/PostgreSQL**. Designed specifically for universities and colleges, it implements administrative quality control, student verification workflows, and granular role-based upload permissions.

---

## 🎨 Theme & UI Design
- **Color Palette:** Deep Violet/Purple (`#6D28D9`), Radiant Amber/Orange (`#F97316`), Crisp White (`#FFFFFF`), and Dark Slate Gray (`#0F172A`). *(Zero blue theme)*.
- **Responsive:** Mobile-first layout with responsive navigation, adaptive filter grids, and accessible data tables.
- **Unified Website URL:** All users—whether campus administrators or students across branches—access the system through the **SAME website URL**. Access levels are governed server-side.

---

## 🔐 Role-Based Access Control Architecture

| User Role | Status | Dashboard Access | Browse Approved Notes | Download Notes | Upload Notes | Admin Portal |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Guest / Public** | - | ❌ | ✅ | ✅ | ❌ | ❌ |
| **Student** | `PENDING` | ❌ (Redirects to Waiting Page) | ✅ | ✅ | ❌ | ❌ |
| **Student** | `REJECTED` | ❌ (Access Denied) | ✅ | ✅ | ❌ | ❌ |
| **Student** | `APPROVED` (`upload_perm = False`) | ✅ | ✅ | ✅ | ❌ (Hidden & Guarded) | ❌ |
| **Student** | `APPROVED` (`upload_perm = True`) | ✅ | ✅ | ✅ | ✅ (Status `PENDING`) | ❌ |
| **Campus Admin** | `STAFF / SUPERUSER` | ✅ (Full Oversight) | ✅ | ✅ | Moderate/Approve | ✅ |

> **Upload Security:** Being an approved student does **NOT** grant upload permissions. Campus administrators must explicitly grant upload privileges. Unauthorized access attempts are rejected at the Django view decorator level (`@student_upload_required`).

---

## 📋 The 16 Complete System Pages

1. **Home (`/`)**: Hero section with search bar, metrics, recent approved notes, and workflow guide.
2. **Student Registration (`/register/`)**: Registration with Name, USN, Branch, Semester, Section, and Password. Defaults to `PENDING`.
3. **Student Login / Access (`/login/`)**: Login using USN and Password.
4. **Waiting for Approval (`/waiting-approval/`)**: Live status lookup page using USN.
5. **Student Dashboard (`/student/dashboard/`)**: Filterable notes repository, welcome banner, and "+ Upload Notes" button (only visible if permission granted).
6. **Browse Notes (`/notes/`)**: Public/student directory with multi-field search (Title, Subject, Course ID, Module).
7. **Note Details (`/notes/<id>/`)**: Complete metadata, syllabus module, uploader details, and download counter.
8. **Upload Note (`/notes/upload/`)**: Gated upload form. Uploaded notes enter the review queue with status `PENDING`.
9. **My Notes (`/student/my-notes/`)**: Personal submissions dashboard with real-time moderation status badges (`PENDING`, `APPROVED`, `REJECTED`).
10. **Admin Login (`/admin-portal/login/`)**: Dedicated secure login for campus administrators.
11. **Admin Dashboard (`/admin-portal/dashboard/`)**: Overview with metrics, pending student registrations queue, and pending notes review queue.
12. **Manage Students (`/admin-portal/students/`)**: Complete directory with status tabs (All, Pending, Approved, Rejected) and 1-click Approve/Reject actions.
13. **Upload Permissions (`/admin-portal/permissions/`)**: Dedicated table (`Student Name | USN | Upload Permission | Action`) to Grant/Remove permissions.
14. **Pending Notes (`/admin-portal/notes/pending/`)**: Moderation queue allowing admins to inspect document files, approve, or reject with feedback.
15. **Approved Notes (`/admin-portal/notes/approved/`)**: Directory of live notes with option to revoke.
16. **Rejected Notes (`/admin-portal/notes/rejected/`)**: Archive of rejected submissions with feedback and re-approval option.

---

## 🚀 Local Installation & Running Instructions

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.12 and 3.14)
- Git (optional)

### 2. Create Virtual Environment
```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Database Migrations
```bash
python manage.py migrate
```

### 5. Seed Database with Admin & Test Students
```bash
python manage.py seed_data
```

### 6. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 7. Run the Development Server
```bash
python manage.py runserver 0.0.0.0:8000
```
Open **`http://127.0.0.1:8000/`** or your local IP address in any web browser.

---

## 🔑 Pre-Seeded Accounts for Testing

### Administrator Account
- **URL:** `http://127.0.0.1:8000/admin-portal/login/` (or via Top Nav "Admin Login")
- **Username:** `admin`
- **Password:** `adminpassword123`

### Test Student Accounts (Login with USN)
- **URL:** `http://127.0.0.1:8000/login/`
1. **Approved Student with Upload Permission:**
   - **USN:** `1RV21CS001`
   - **Password:** `password123`
   - *Status:* Approved, can browse, download, and upload notes.
2. **Approved Student WITHOUT Upload Permission:**
   - **USN:** `1RV21CS042`
   - **Password:** `password123`
   - *Status:* Approved, can browse and download notes, upload button is hidden and upload view is guarded.
3. **Pending Student:**
   - **USN:** `1RV21EC015`
   - **Password:** `password123`
   - *Status:* Pending admin approval, redirected to Waiting Approval page.
4. **Rejected Student:**
   - **USN:** `1RV21ME099`
   - **Password:** `password123`
   - *Status:* Rejected, denied dashboard access.

---

## 🧪 Automated Testing
Run the automated integration test suite verifying the end-to-end 16-step student-to-admin workflow:
```bash
python manage.py test core
```

---

## 🌐 Permanent Public Deployment Guide

EduShare is configured out of the box for permanent deployment on cloud platforms with persistent PostgreSQL and HTTPS:

### Option A: Render.com (Recommended Free/Standard Tier)
1. Push your repository to GitHub or GitLab.
2. In [Render.com](https://render.com), click **New +** &rarr; **Blueprint**.
3. Select your repository. Render detects `render.yaml` automatically:
   - Sets up a **Python Web Service** with `gunicorn`.
   - Provisions a persistent **PostgreSQL Database**.
   - Runs `collectstatic`, `migrate`, and `seed_data`.
4. Your site will be live at `https://<your-service-name>.onrender.com` with full HTTPS, persistent database, and file storage.

### Option B: Railway.app
1. Create a project on [Railway.app](https://railway.app).
2. Connect your GitHub repository.
3. Add a PostgreSQL plugin.
4. Set environment variable `DJANGO_DEBUG=False`.
5. Railway automatically builds using the provided `Dockerfile` or `Procfile`.

### Option C: PythonAnywhere
1. Create a Python 3.12 Web App (Manual Configuration).
2. Set up virtualenv and install `requirements.txt`.
3. Set WSGI configuration file pointing to `edushare_project/wsgi.py`.
4. Configure `/static/` pointing to `staticfiles/` and `/media/` pointing to `media/`.
