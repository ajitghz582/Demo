# Examination Management Portal — Beginner-Friendly End-to-End Build Plan

## Context

You have been given a project specification (`mad2_requirement.txt`) for an **Examination Management Portal (EMP)** — a web app where an Admin manages exams, Examiners create time slots, and Students book those slots and view results.

A reference codebase for a *different* project (a Parking Management System) lives in `referenceCode/`. This is there to show you the **exact same tech stack and patterns** you must follow — just adapted to the exam portal domain. Study it carefully before writing a single line of code.

---

## Tech Stack Summary

| Layer | Technology | Reference File |
|-------|-----------|----------------|
| Backend API | Python + Flask | `referenceCode/backend/app.py` |
| Database ORM | Flask-SQLAlchemy → SQLite | `referenceCode/backend/model.py` |
| Authentication | Flask-JWT-Extended (JWT tokens) | `app.py` — `/login` route |
| Caching | Redis via Flask-Caching | `app.py` — `Cache(app)` setup |
| Background Jobs | Celery + Redis broker | `referenceCode/backend/celery_worker.py` |
| Scheduled Tasks | Celery Beat | `celery_worker.py` — `beat_schedule` |
| Email (dev) | Python smtplib → local SMTP:1025 | `referenceCode/backend/tasks.py` |
| Email Templates | Jinja2 HTML templates | `referenceCode/backend/templates/` |
| Frontend | Vue 3 + Vite | `referenceCode/vp-frontend/src/` |
| Routing (SPA) | Vue Router 5 | `vp-frontend/src/router/index.js` |
| Styling | Bootstrap 5 | `package.json` → imported in `main.js` |
| Charts (optional) | vue-chartjs (Chart.js) | `package.json` |
| HTTP Client | Axios | `package.json` |

---

## Phase 1 — Set Up Your Development Environment

**Goal:** Get all tools installed before writing a single line of code.

### 1.1 Python virtual environment and packages
```bash
python -m venv env
# Windows:
env\Scripts\activate
# Mac/Linux:
source env/bin/activate

pip install flask flask-sqlalchemy flask-jwt-extended flask-cors flask-caching celery redis werkzeug
```

### 1.2 Node.js and Vue project
```bash
# Install Node.js v22+ from nodejs.org, then:
npm create vue@latest emp-frontend
cd emp-frontend
npm install
npm install axios bootstrap vue-router vue-chartjs chart.js
```

### 1.3 Install and start Redis
- **Windows:** Use WSL (`sudo apt install redis-server && redis-server`) or download Redis for Windows
- Verify: `redis-cli ping` → should print `PONG`
- Redis is used on **three channels simultaneously**: `/0` for caching, `/1` as Celery broker, `/2` as Celery result backend

### 1.4 Local SMTP server for email testing
```bash
pip install aiosmtpd
python -m aiosmtpd -n -l localhost:1025
```
Keep this running in its own terminal. All emails sent during development will appear here instead of actually being sent.

---

## Phase 2 — Backend: Database Models (`model.py`)

**Goal:** Define all database tables as Python classes — SQLAlchemy handles all SQL for you. This is exactly the pattern in `referenceCode/backend/model.py`.

**How it works:** You define a class → SQLAlchemy generates the table. Call `db.create_all()` once at startup and the database is ready.

Create these models:

| Model | Key Fields | Notes |
|-------|-----------|-------|
| `User` | id, username, email, password (hashed), role, active | Unified model for all 3 roles |
| `Course` | id, course_code, course_name, description, status | Admin creates these |
| `Examination` | id, course_id (FK), name, type, duration, max_marks, slot_creation_start/end, booking_start/end, status | Status drives what actions are allowed |
| `ExaminationRubric` | id, exam_id (FK), criterion_name, max_marks, weightage, description | Grading criteria |
| `ExaminerProfile` | id, user_id (FK), department, contact | Linked to User with role='examiner' |
| `ExaminationSlot` | id, exam_id (FK), examiner_id (FK), date, start_time, end_time, capacity, available_seats, status, meeting_link | Created by Examiner |
| `Booking` | id, student_id (FK), slot_id (FK), booking_date, status | Student books a slot |
| `Evaluation` | id, booking_id (FK), student_id (FK), examiner_id (FK), total_marks, remarks, eval_date, status | Examiner fills this |

**Pattern to follow** (from `referenceCode/backend/model.py`):
```python
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    role = db.Column(db.String(20), default='student')  # 'admin', 'examiner', 'student'
    # ... etc
```

---

## Phase 3 — Backend: Flask App (`app.py`)

**Goal:** Build all REST API endpoints. Follow the pattern in `referenceCode/backend/app.py` exactly.

### 3.1 App setup (top of `app.py`)
```python
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_caching import Cache
from model import db  # import your models too

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///emp.db"
app.config["SECRET_KEY"] = "your-secret-key"
app.config["JWT_SECRET_KEY"] = "your-jwt-key"
app.config["CACHE_TYPE"] = "RedisCache"
app.config["CACHE_REDIS_URL"] = "redis://localhost:6379/0"

CORS(app)
JWTManager(app)
cache = Cache(app)
db.init_app(app)
```

### 3.2 Auto-create DB and seed Admin on first run
```python
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # creates all tables from your model classes
        if not User.query.filter_by(username='admin').first():
            admin = User(username="admin", email="admin@emp.com",
                        password=generate_password_hash("admin123"), role="admin")
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)
```

### 3.3 JWT auth pattern (copy from reference — this exact pattern is required)
```python
# In every protected route:
@app.route("/api/admin/courses", methods=["GET"])
@jwt_required()
def get_courses():
    role = get_jwt().get("role")  # check role from JWT
    if role != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    # ... your logic
```

### 3.4 API endpoints to build

**Public (no JWT):**
- `POST /register` — student self-registration
- `POST /login` — returns JWT token with `role` claim embedded

**Admin endpoints** (require `role == "admin"` check):
- `GET/POST /api/admin/courses` — list / create
- `PUT/DELETE /api/admin/courses/<id>` — update / remove
- `GET/POST /api/admin/examinations` — list / create
- `PUT /api/admin/examinations/<id>` — update (including status changes to open/close slots and booking)
- `POST /api/admin/examinations/<id>/rubrics` — add rubric criteria
- `POST /api/admin/examiners` — create examiner (User with role='examiner')
- `GET /api/admin/slots` — view all examiner slots
- `GET /api/admin/bookings` — view all bookings + search/filter by query param
- `PUT /api/admin/bookings/<id>/reschedule` — move student to new slot
- `POST /api/admin/examinations/<id>/publish` — publish results
- `GET /api/admin/dashboard` — counts (courses, exams, students, examiners, slots, bookings)

**Examiner endpoints** (require `role == "examiner"` check):
- `GET /api/examiner/examinations` — their assigned exams
- `POST /api/examiner/slots` — create a slot (validate: exam must be in "Slot Creation" status)
- `PUT /api/examiner/slots/<id>` — update slot (validate: booking must not have started yet)
- `GET /api/examiner/slots/<id>/students` — booked students for their slot
- `POST /api/examiner/evaluate/<booking_id>` — submit marks and remarks per rubric criterion

**Student endpoints** (require `role == "student"` check):
- `GET /api/student/examinations` — available exams (add `@cache.cached(timeout=60)` here)
- `GET /api/student/slots/<exam_id>` — slots for an exam with available seats
- `POST /api/student/bookings` — book a slot (validate: not already booked, seats > 0, booking period open)
- `DELETE /api/student/bookings/<id>` — cancel before deadline
- `GET /api/student/bookings` — booking history
- `GET /api/student/results` — published evaluations for the student
- `GET /api/student/export` — trigger async CSV export job

**Caching example** (follow the commented-out line in `referenceCode/backend/app.py` line 255):
```python
@app.route("/api/student/examinations")
@jwt_required()
@cache.cached(timeout=60)   # cache for 60 seconds
def get_examinations():
    ...
```

---

## Phase 4 — Background Jobs (`celery_worker.py` + `tasks.py`)

**Goal:** Mirror exactly what `referenceCode/backend/celery_worker.py` and `tasks.py` do.

### 4.1 `celery_worker.py` — setup (copy this structure exactly)
```python
from celery import Celery, Task
from celery.schedules import crontab
from app import app  # import your Flask app

celery_app = Celery('tasks',
                    broker='redis://localhost:6379/1',
                    backend='redis://localhost:6379/2',
                    include=['tasks'])

class FlaskTask(Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():       # CRITICAL: gives tasks access to db/models
            return self.run(*args, **kwargs)

celery_app.Task = FlaskTask
celery_app.conf.timezone = 'Asia/Kolkata'

celery_app.conf.beat_schedule = {
    'daily-exam-reminder': {
        'task': 'tasks.send_daily_reminder',
        'schedule': crontab(hour=8, minute=0),
    },
    'monthly-exam-report': {
        'task': 'tasks.send_monthly_report',
        'schedule': crontab(hour=0, minute=1, day_of_month=1),
    },
}
```

### 4.2 `tasks.py` — three tasks to implement

The `send_email()` helper function in `referenceCode/backend/tasks.py` can be **copied directly** into your project.

| Task | Trigger | What it does |
|------|---------|-------------|
| `send_daily_reminder()` | Scheduled daily | Query upcoming booked exams → email each student |
| `send_monthly_report()` | 1st of month | Compile stats → render `monthly_report.html` → email Admin |
| `export_exam_history(user_id)` | Student clicks button | Query student's bookings + evaluations → render `export.html` → email student |

### 4.3 Email templates
Create `templates/monthly_report.html` and `templates/export.html` as Jinja2 templates.
The reference files in `referenceCode/backend/templates/` show the exact pattern — use `{{ variable }}` and `{% for item in items %}` loops.

Render them with:
```python
from flask import render_template
html = render_template('monthly_report.html', data=your_data)
```

### 4.4 Running Celery (two additional terminals)
```bash
# Terminal A — the worker (processes tasks)
celery -A celery_worker.celery_app worker --loglevel=info

# Terminal B — beat (fires scheduled tasks)
celery -A celery_worker.celery_app beat --loglevel=info
```

---

## Phase 5 — Frontend: Vue 3 App

**Goal:** Build the UI following the component and routing structure in `referenceCode/vp-frontend/src/`.

### 5.1 Folder structure to create
```
src/
  router/index.js          <- 4 routes (see pattern below)
  main.js                  <- imports Vue, router, Bootstrap
  App.vue                  <- root component with <RouterView />
  views/
    LandingPage.vue        <- login/register choice screen
    AdminView.vue          <- full admin SPA area
    ExaminerView.vue       <- examiner area
    StudentView.vue        <- student area
  components/
    admin/
      AdminDash.vue        <- tab-based dashboard (tab per feature)
      ManageCourses.vue
      ManageExams.vue
      ManageExaminers.vue
      ViewBookings.vue
      AdminRubrics.vue
    examiner/
      ExaminerDash.vue
      CreateSlot.vue
      EvaluateStudent.vue
    student/
      StudentDash.vue
      BookSlot.vue
      MyBookings.vue
      ViewResults.vue
      ExportHistory.vue
```

### 5.2 `main.js` — Bootstrap and router setup (follow reference pattern)
```javascript
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'

createApp(App).use(router).mount('#app')
```

### 5.3 Router (`src/router/index.js`) — follow the reference pattern exactly
```javascript
import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from '../views/LandingPage.vue'
import AdminView from '../views/AdminView.vue'
// ...

const routes = [
  { path: '/', component: LandingPage },
  { path: '/admin', component: AdminView },
  { path: '/examiner', component: ExaminerView },
  { path: '/student', component: StudentView },
  { path: '/:pathMatch(.*)*', redirect: '/' }  // catch-all
]
export default createRouter({ history: createWebHistory(), routes })
```

### 5.4 Auth flow (follow `referenceCode` pattern)
1. `LandingPage.vue` has buttons to route to `/admin`, `/examiner`, or `/student`
2. Each view shows a Login form first; after successful login, shows the dashboard
3. Store the JWT: `localStorage.setItem('token', response.data.access_token)`
4. Store the role: `localStorage.setItem('role', response.data.role)`
5. On logout: `localStorage.removeItem('token')` then redirect to `/`

**Note:** The reference uses `'admin_token'` for admin and `'token'` for users — you can simplify to just `'token'` and `'role'` for all three roles.

### 5.5 Axios pattern for protected calls (use in every component)
```javascript
import axios from 'axios'
const BASE_URL = 'http://localhost:5000'

async function fetchExaminations() {
  const token = localStorage.getItem('token')
  const response = await axios.get(`${BASE_URL}/api/student/examinations`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}
```

### 5.6 Tab-based dashboard pattern (from `referenceCode/vp-frontend/src/components/AdminDash.vue`)
The reference uses Bootstrap's nav-tabs to switch between features within one dashboard view — keep all your admin/examiner/student feature components in one dashboard using this pattern to avoid complex routing.

---

## Phase 6 — Run Everything Together

### Complete startup checklist (run in this order):

| Order | What | Command | Terminal # |
|-------|------|---------|-----------|
| 1 | Redis server | `redis-server` | 1 |
| 2 | Fake SMTP | `python -m aiosmtpd -n -l localhost:1025` | 2 |
| 3 | Flask backend | `python app.py` (from `backend/` folder) | 3 |
| 4 | Celery worker | `celery -A celery_worker.celery_app worker --loglevel=info` | 4 |
| 5 | Celery beat | `celery -A celery_worker.celery_app beat --loglevel=info` | 5 |
| 6 | Vue frontend | `npm run dev` (from frontend folder) | 6 |

- Backend runs at: `http://localhost:5000`
- Frontend runs at: `http://localhost:5173`
- CORS is handled by `CORS(app)` in `app.py` — no extra config needed

---

## Phase 7 — Verification Checklist

Test these flows end-to-end after building:

**Auth:**
- [ ] Student registers → logs in → sees student dashboard
- [ ] Admin logs in with `admin` / `admin123` (seeded on first run)
- [ ] Invalid credentials → error message shown

**Admin flow:**
- [ ] Admin creates a Course
- [ ] Admin creates an Examination under that Course
- [ ] Admin adds rubric criteria to the Examination
- [ ] Admin creates an Examiner (adds a user with `role=examiner`)
- [ ] Admin opens slot creation (sets exam status to "Slot Creation")

**Examiner flow:**
- [ ] Examiner logs in → sees their assigned exam
- [ ] Examiner creates 2 available time slots
- [ ] Admin opens student booking (sets exam status to "Booking Open")

**Student flow:**
- [ ] Student searches exams, finds the open one
- [ ] Student books a slot → sees booking confirmation
- [ ] Student tries to book same exam again → blocked with error
- [ ] Another student books, slot shows fewer available seats
- [ ] Slot fills up → status auto-changes to "Full"

**Evaluation and results:**
- [ ] Examiner views booked students for their slot
- [ ] Examiner submits marks + remarks using the rubric
- [ ] Admin publishes results
- [ ] Student sees their marks and examiner feedback

**Background jobs:**
- [ ] Student clicks "Export History" → check fake SMTP terminal for email
- [ ] Manually trigger `send_daily_reminder` via Celery → check SMTP terminal

**Caching:**
- [ ] Call `/api/student/examinations` twice — second call should be faster (Flask logs show cache hit)

---

## Key Differences: Reference Code vs Your Project

| Reference (Parking Portal) | Your Project (Exam Portal) |
|---------------------------|--------------------------|
| `ParkingLot` | `Examination` |
| `ParkingSpot` | `ExaminationSlot` |
| `Reservation` | `Booking` |
| No evaluation | `Evaluation` model (rubric-based marking) |
| 2 roles: `admin` / `user` | 3 roles: `admin` / `examiner` / `student` |
| No time-window control | Exam status machine controls when slots/bookings are allowed |
| No rubrics | `ExaminationRubric` table with per-criterion marks |
| `export_reservations` task | `export_exam_history` task (CSV with exam details) |

---

## Recommended Build Order

Build in this sequence to avoid blockers:

1. **`model.py`** — get all tables and relationships right first; run `python app.py` once to verify tables are created
2. **`app.py` auth routes** — `/register` and `/login`; test with curl or Postman that JWT is returned
3. **Admin API routes** — courses, exams, rubrics, examiner creation
4. **Examiner API routes** — slot creation with status validation
5. **Student API routes** — bookings with seat/duplicate/period validations
6. **`celery_worker.py` + `tasks.py`** — background jobs last (needs everything else working)
7. **Vue frontend** — build after all backend APIs are verified working
8. **Wire frontend to backend** — connect each Vue component to its API endpoint
9. **Polish** — Bootstrap styling, search/filter, charts (optional)

---

## Submission Checklist (from requirements)

- [ ] Project zip file uploaded to portal
- [ ] 5-page report with: student details, problem approach, AI/LLM declaration, frameworks list, ER diagram, API endpoints list, video drive link
- [ ] Video (5-10 minutes): intro, approach, key features demo, additional features
- [ ] Video uploaded to Google Drive with "anyone with link" access
