# Examination Management Portal (EMP)

A full-stack web application for managing examinations involving Admins, Examiners, and Students.

## Tech Stack

- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Redis, Celery
- **Frontend:** Vue 3, Vite, Bootstrap 5, Axios
- **Database:** SQLite (created programmatically)
- **Background Jobs:** Celery + Redis (scheduled reminders, monthly reports, async CSV export)

## Roles

| Role | Access |
|------|--------|
| Admin | Manage courses, exams, rubrics, examiners; publish results |
| Examiner | Create slots, evaluate students |
| Student | Register, book slots, view results |

## Quick Start

See **[SETUP_GUIDE.md](SETUP_GUIDE.md)** for complete step-by-step setup instructions.

**Default admin credentials:** `admin` / `admin123`

## Project Structure

```
emp/
  backend/         Flask API, models, Celery tasks
  frontend/        Vue 3 SPA
  SETUP_GUIDE.md   Full setup instructions
```
