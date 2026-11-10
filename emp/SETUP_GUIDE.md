# Examination Management Portal — Complete Setup Guide

This guide walks you through setting up and running the EMP project on a **brand new Windows machine** from scratch. Follow every step in order.

---

## Prerequisites Overview

You need to install four things before anything else:

| Tool | Purpose | Version |
|------|---------|---------|
| Python | Runs the Flask backend | 3.10 or higher |
| Node.js | Runs the Vue frontend | 22 or higher |
| Redis | Caching + Celery message broker | Latest |
| Git | (Optional) Version control | Latest |

---

## Part 1 — Install Python

1. Go to **https://www.python.org/downloads/**
2. Download the latest Python 3.10+ installer (e.g., `Python 3.11.x`)
3. Run the installer
   - **IMPORTANT:** On the first screen, check **"Add Python to PATH"** before clicking Install
4. Click **Install Now**
5. Verify the install — open a new Command Prompt and run:
   ```
   python --version
   ```
   You should see something like `Python 3.11.9`

---

## Part 2 — Install Node.js

1. Go to **https://nodejs.org/**
2. Download the **LTS version** (v22 or higher)
3. Run the installer — click Next through all defaults
4. Verify — open a new Command Prompt and run:
   ```
   node --version
   npm --version
   ```
   Both should print version numbers

---

## Part 3 — Install Redis on Windows

Redis does not have an official Windows installer. Use one of these two methods:

### Method A — WSL (Windows Subsystem for Linux) — Recommended

1. Open **PowerShell as Administrator** and run:
   ```
   wsl --install
   ```
2. Restart your computer when prompted
3. After restart, open the **Ubuntu** app from Start Menu and create a Linux username/password
4. Inside the Ubuntu terminal, run:
   ```bash
   sudo apt update
   sudo apt install redis-server -y
   ```
5. Start Redis:
   ```bash
   redis-server --daemonize yes
   ```
6. Test it works:
   ```bash
   redis-cli ping
   ```
   You should see: `PONG`

### Method B — Memurai (Redis-compatible, native Windows)

1. Go to **https://www.memurai.com/get-memurai**
2. Download and install Memurai for Windows
3. It runs as a Windows Service automatically on port 6379
4. No further setup needed

---

## Part 4 — Get the Project Files

If you have the project as a zip file:
1. Extract the zip to a folder, e.g., `C:\Projects\emp\`

If you are cloning from Git:
```
git clone <your-repo-url>
cd emp
```

After this step, your folder should look like:
```
emp/
  backend/
    app.py
    model.py
    celery_worker.py
    tasks.py
    requirements.txt
    templates/
  frontend/
    package.json
    vite.config.js
    src/
  SETUP_GUIDE.md
```

---

## Part 5 — Set Up the Backend

Open a **Command Prompt** (or PowerShell) and navigate to the backend folder:

```
cd C:\Projects\emp\backend
```

### 5.1 — Create a Python virtual environment

A virtual environment keeps your project's dependencies isolated from other Python projects.

```
python -m venv env
```

This creates a folder called `env/` inside `backend/`.

### 5.2 — Activate the virtual environment

```
env\Scripts\activate
```

Your prompt will change to show `(env)` at the start — this means the virtual environment is active. **You must do this every time you open a new terminal to run the backend.**

### 5.3 — Install all Python packages

```
pip install flask flask-sqlalchemy flask-jwt-extended flask-cors flask-caching celery redis werkzeug aiosmtpd
```

This takes 1–3 minutes. Wait for it to finish.

### 5.4 — Verify the install

```
pip list
```

You should see Flask, SQLAlchemy, celery, redis, and others in the list.

---

## Part 6 — Set Up the Frontend

Open a **second Command Prompt** and navigate to the frontend folder:

```
cd C:\Projects\emp\frontend
```

### 6.1 — Install Node.js packages

```
npm install
```

This reads `package.json` and downloads all dependencies into a `node_modules/` folder. Takes 1–2 minutes.

### 6.2 — Verify

```
npm list --depth=0
```

You should see `vue`, `axios`, `bootstrap`, `vue-router`, `vue-chartjs` listed.

---

## Part 7 — Run the Application

You need **6 terminal windows** open simultaneously. Here is the exact order to start them.

> **Tip for Windows users:** Open Windows Terminal (or use `cmd`), and open multiple tabs with `Ctrl+Shift+T`.

---

### Terminal 1 — Start Redis

**If using WSL (Method A):**
```bash
# Open Ubuntu from Start Menu, then run:
redis-server
```

**If using Memurai (Method B):**
Redis is already running as a Windows service. Skip this terminal.

**Verify Redis is running** (in any terminal):
```
redis-cli ping
```
Expected output: `PONG`

---

### Terminal 2 — Start Fake SMTP Server (for email testing)

This simulates an email server locally. All emails sent by the app will appear here instead of being actually sent.

```
cd C:\Projects\emp\backend
env\Scripts\activate
python -m aiosmtpd -n -l localhost:1025
```

Leave this running. You will see email output here when emails are triggered.

---

### Terminal 3 — Start the Flask Backend

```
cd C:\Projects\emp\backend
env\Scripts\activate
python app.py
```

Expected output:
```
Admin seeded: admin / admin123
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

**What happens on first run:**
- SQLite database file `instance/emp.db` is created automatically
- All database tables are created
- An admin user (`admin` / `admin123`) is seeded

> **Keep this terminal open.** The backend must be running for the app to work.

---

### Terminal 4 — Start Celery Worker

The worker processes background tasks like sending emails and exporting data.

```
cd C:\Projects\emp\backend
env\Scripts\activate
celery -A celery_worker.celery_app worker --loglevel=info
```

Expected output includes:
```
[tasks]
  . tasks.send_daily_reminder
  . tasks.send_monthly_report
  . tasks.export_exam_history

[celery@hostname] ready.
```

---

### Terminal 5 — Start Celery Beat (Scheduler)

The beat scheduler fires scheduled tasks (daily reminder at 8am, monthly report on 1st of month).

```
cd C:\Projects\emp\backend
env\Scripts\activate
celery -A celery_worker.celery_app beat --loglevel=info
```

Expected output:
```
beat: Starting...
beat: Ticking with max interval of 5.00 seconds
```

---

### Terminal 6 — Start the Vue Frontend

```
cd C:\Projects\emp\frontend
npm run dev
```

Expected output:
```
  VITE v5.x  ready in 300ms

  ➜  Local:   http://localhost:5173/
```

---

## Part 8 — Open the App in Your Browser

Go to: **http://localhost:5173**

You should see the EMP login page.

---

## Part 9 — First-Time Usage Walkthrough

### Step 1 — Log in as Admin
- Username: `admin`
- Password: `admin123`

### Step 2 — Create a Course
1. Click the **Courses** tab
2. Click **+ New Course**
3. Fill in: Code = `CS101`, Name = `Computer Science`, Description = any text
4. Click **Save**

### Step 3 — Create an Examination
1. Click the **Examinations** tab
2. Click **+ New Examination**
3. Fill in: Name, select course CS101, Type = Viva, Duration = 30, Max Marks = 100
4. Set dates (Slot Creation Start/End, Booking Start/End)
5. Set Status = `Slot Creation`
6. Click **Save**

### Step 4 — Add Rubric Criteria
1. Find your exam in the list → click **Rubrics**
2. Add criteria like: "Communication Skills" (Max: 40), "Technical Knowledge" (Max: 60)

### Step 5 — Add an Examiner
1. Click the **Examiners** tab
2. Click **+ Add Examiner**
3. Fill in username, email, password, department
4. Click **Save**

### Step 6 — Examiner Creates Slots
1. Log out (click Logout)
2. Log in with the examiner credentials you just created
3. Click **+ Create Slot**
4. Select the examination, set a date and time, set capacity
5. Click **Save**

### Step 7 — Open Student Booking (Admin)
1. Log out and log in as `admin`
2. Go to Examinations → find your exam → click **Edit**
3. Change Status to `Booking Open`
4. Click **Save**

### Step 8 — Student Registers and Books
1. Log out
2. On the login page click **Register here**
3. Register a new student account
4. Log in as the student
5. Click **Book Exam** tab → find your examination → click **View Slots & Book**
6. Click **Book** next to an available slot

### Step 9 — Examiner Evaluates
1. Log in as the examiner
2. Click **Evaluate Students** tab
3. Select the slot from the dropdown
4. Enter marks and remarks → click **Submit**

### Step 10 — Publish Results (Admin)
1. Log in as `admin`
2. Go to Examinations → find your exam → click **Publish**
3. Confirm

### Step 11 — Student Views Results
1. Log in as the student
2. Click the **Results** tab
3. You should see marks and remarks

---

## Part 10 — Testing Background Jobs Manually

### Test the CSV Export
1. Log in as a student who has bookings
2. Go to **My Bookings** tab
3. Click **Export History (Email)**
4. Switch to **Terminal 2** (fake SMTP) — you will see the email content printed

### Test Daily Reminder Manually
In a new terminal with the virtual environment active:
```
cd C:\Projects\emp\backend
env\Scripts\activate
python -c "from celery_worker import celery_app; from tasks import send_daily_reminder; send_daily_reminder.delay()"
```
Check Terminal 2 for the email output.

---

## Part 11 — Stopping the Application

Stop each terminal in this order:

1. **Terminal 6** (Vue) — press `Ctrl+C`
2. **Terminal 5** (Celery Beat) — press `Ctrl+C`
3. **Terminal 4** (Celery Worker) — press `Ctrl+C`
4. **Terminal 3** (Flask) — press `Ctrl+C`
5. **Terminal 2** (SMTP) — press `Ctrl+C`
6. **Terminal 1** (Redis) — press `Ctrl+C` (or leave running)

---

## Part 12 — Restarting After a Shutdown

Each time you want to run the app again after shutting down:

1. Make sure Redis is running (Terminal 1)
2. Start SMTP server (Terminal 2) — only needed if testing emails
3. Start Flask backend (Terminal 3) — **activate venv first**
4. Start Celery worker (Terminal 4) — **activate venv first**
5. Start Celery beat (Terminal 5) — **activate venv first**
6. Start frontend (Terminal 6)

> The database (`instance/emp.db`) persists between restarts — your data is saved.

---

## Troubleshooting

### "Module not found" or "No module named flask"
You forgot to activate the virtual environment. Run:
```
env\Scripts\activate
```
Then try again.

### "Address already in use" on port 5000
Something else is using port 5000. Either kill that process or change the Flask port:
In `app.py`, change the last line to:
```python
app.run(debug=True, port=5001)
```
And update `vite.config.js` proxy to point to `http://localhost:5001`.

### "Connection refused" on Redis
Redis is not running. Start it in Terminal 1 and verify with `redis-cli ping`.

### Celery worker crashes immediately
Make sure the Flask backend (Terminal 3) is running first — Celery imports `app.py` on startup.

### Frontend shows blank page or 404
Make sure the frontend dev server is running (`npm run dev`) and you are visiting `http://localhost:5173`, not `http://localhost:5000`.

### "CORS error" in browser console
Make sure Flask is running and `flask-cors` is installed (`pip list | findstr flask-cors`).

### Database needs to be reset
Delete the file `backend/instance/emp.db` and restart Flask — the database will be recreated fresh with the admin user.

---

## Quick Reference — Ports

| Service | Port | URL |
|---------|------|-----|
| Vue frontend | 5173 | http://localhost:5173 |
| Flask backend | 5000 | http://localhost:5000 |
| Redis (caching) | 6379/0 | redis://localhost:6379/0 |
| Redis (Celery broker) | 6379/1 | redis://localhost:6379/1 |
| Redis (Celery results) | 6379/2 | redis://localhost:6379/2 |
| Fake SMTP | 1025 | localhost:1025 |

## Quick Reference — Default Credentials

| Role | Username | Password |
|------|---------|---------|
| Admin | `admin` | `admin123` |
| Examiner | (created by admin) | (set by admin) |
| Student | (self-registered) | (set during registration) |
