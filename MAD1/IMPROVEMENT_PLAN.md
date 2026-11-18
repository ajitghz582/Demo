# Examination Management Portal — Fix & Completion Plan

## Context

This is a student-level Flask/SQLite project (IIT Madras MAD-1) for an Examination Management Portal with three roles: Admin, Examiner, Student. The codebase has 2 Python files (`app.py`, `model.py`) and 23 Jinja2 templates. The core structure is in place but there are crash-level bugs, broken template bindings, and missing workflow routes that make large parts of the app non-functional.

---

## Priority 1 — Crash-Level Bugs

These cause 500 errors, 405 errors, or Jinja2 `UndefinedError` on normal use.

### 1.1 `datetime()` misuse — slot creation and exam edit crash on every POST
- **File:** `app.py` → `create_slot` and `edit_exam`
- **Problem:** `datetime(request.form["field"])` passes a string to `datetime()` which expects integers → `TypeError`
- **Fix:** Replace with `datetime.strptime(request.form["field"], "%Y-%m-%d")` for date fields and `"%H:%M"` for time fields. Add `from datetime import datetime` at the top.

### 1.2 Approve/Reject examiner buttons are GET links but routes require POST → 405
- **File:** `templates/admin_dashboard.html`
- **Problem:** Approve/Reject are `<a href>` links; the backend routes are `methods=["POST"]` only
- **Fix:** Wrap each in a `<form method="POST"><button type="submit">` tag

### 1.3 `student_dashboard.html` crashes on page load
- **File:** `templates/student_dashboard.html`
- **Problem:** Cancel button references `{{ booking.id }}` but `booking` is never passed to this template → Jinja2 `UndefinedError`
- **Fix:** Remove the Cancel column from the dashboard (cancellations live on the My Bookings page only)

### 1.4 `student_view_exam.html` — loop never executes, page shows no data
- **File:** `templates/student_view_exam.html`
- **Problem:** Route passes `examination` (singular) but template iterates `{% for exam in examinations %}` — loop body never runs; also missing `{% endfor %}`
- **Fix:** Remove the loop; use `examination` directly; add missing `{% endfor %}`

### 1.5 `student_profile.html` — updates silently do nothing
- **File:** `templates/student_profile.html`
- **Problem:** Field names (`name`, `contact_num`) don't match what the backend reads (`username`, `contact_no`); form action `/student_profile` has no student ID
- **Fix:** Rename fields to `username` and `contact_no`; change action to `"/student_profile/{{ student.id }}"`

### 1.6 `admin_registered_student.html` — results table is static/empty
- **File:** `templates/admin_registered_student.html`
- **Problem:** Table body has static empty `<td>` cells — no Jinja loop, so search results never appear
- **Fix:** Add `{% for booking in bookings %}...{% endfor %}` loop in `<tbody>`

### 1.7 Cancel booking → 405 on every click
- **Files:** `templates/student_booking.html`, `templates/student_dashboard.html`
- **Problem:** Cancel is an `<a href>` (GET) but route is `methods=["POST"]` only
- **Fix:** Wrap in `<form method="POST" action="/cancel_booking/{{ booking.id }}"><button type="submit">Cancel</button></form>`

### 1.8 `student_history` always returns an error string
- **File:** `app.py` → `/student_history`
- **Problem:** Route uses `request.form.get("student_id")` on a GET-only route — always `None`; returns a plain error string instead of a page
- **Fix:** Change URL to `/student_history/<int:student_id>`, read the ID from the URL param, query evaluations via the student's bookings

### 1.9 Broken navigation hrefs
- `templates/wrong.html`: `href="login.html"` → `href="/login"`
- `templates/invalid.html`: empty `href=""` → `href="/home"`

---

## Priority 2 — Slot Creation Workflow

### 2.1 Add date-window fields to `Examination` model
The spec requires four date fields on each Examination to control when slots can be created and when students can book:

```python
# In model.py → Examination class
slot_creation_start_date = db.Column(db.Date)
slot_creation_end_date   = db.Column(db.Date)
slot_booking_start_date  = db.Column(db.Date)
slot_booking_end_date    = db.Column(db.Date)
```

- Also change `Examination.date` from `db.Column(db.String)` to `db.Column(db.Date)` for type consistency
- Add all five fields to `admin_examination.html` with `type="date"` inputs

### 2.2 Fix `create_slot` route
- **File:** `app.py` → `create_slot` route
- Fix `datetime()` crash (see 1.1 above)
- Fix POST redirect — currently goes to unparameterized `/examiner_dashboard` → change to `/examiner_dashboard/<examiner_id>`
- Fix GET handler — currently renders `examiner_availability.html` without `examiner_id` or `slots` → pass them to avoid Jinja2 `UndefinedError`

### 2.3 Fix `examiner_availability.html` form
- Form POSTs to `/examiner_slots/<id>` which is GET-only → 405
- **Fix:** Change `action` to `"/slot/create"` with `method="POST"`
- Fix input types: date field → `type="date"`, time fields → `type="time"` (currently `type="number"`)
- Add missing `max_students` input field (required by backend but absent from form)

### 2.4 Add slot edit and delete routes
- Spec: examiners can update or delete their own slots before the booking window opens
- Add `/slot/edit/<slot_id>` (GET/POST) — renders a pre-filled slot form, saves changes
- Add `/slot/delete/<slot_id>` (POST) — deletes the slot
- Add Edit/Delete buttons to the slot table in `examiner_availability.html`

### 2.5 Admin: open/close slot creation and booking windows
- Spec: admin explicitly opens and closes these phases via Examination status
- Add a `/exam/set_status/<exam_id>` POST route accepting a `status` field (values: Draft / Slot Creation / Booking Open / Closed / Completed)
- Add status-change buttons next to each examination on `admin_dashboard.html`

---

## Priority 3 — Booking Workflow

### 3.1 Prevent duplicate bookings
- **File:** `app.py` → `book_slot` route
- Add a check: query whether the student already has an active `Booking` for any slot of the same `examination_id`; if yes, redirect with an error message

### 3.2 Fix `student_view_exam.html` navigation
- All nav links (`Home`, `Profile`, My Bookings) are missing the `student_id` parameter → broken links
- Fix: `/student_dashboard/{{ student_id }}`, `/student_bookings/{{ student_id }}`, `/student_profile/{{ student_id }}`
- Fix copy-paste "Welcome Admin" navbar label → "Welcome Student"

### 3.3 Fix `student_booking.html`
- Cancel `<a>` tag is a direct child of `<tr>` (invalid HTML) → move inside a `<td>`
- Wrap in `<form method="POST">` (see 1.7)
- Fix Bootstrap CDN version from `6.0.0-alpha.1` to `5.0.2` (mismatched with rest of app)

### 3.4 Fix `student_history.html` navigation
- Nav links to `/student_history` and `/student_profile` are missing `student_id` — add it

### 3.5 Admin: reschedule booking
- Spec: admin can move a student's booking to a different slot
- Add `/booking/reschedule/<booking_id>` (POST) — accepts `new_slot_id`, updates `booking.slot_id`, adjusts `available_seats` on the old and new slots
- Add a Reschedule action on `admin_registered_student.html` (a dropdown of available slots + submit)

### 3.6 Admin: reassign examiner on a slot
- Spec: admin can change which examiner covers a slot
- Add `/slot/reassign/<slot_id>` (POST) — accepts `new_examiner_id`, updates `slot.examiner_id`
- Add a Reassign Examiner dropdown to the admin slot view

---

## Priority 4 — Evaluation Workflow (Examiner Grades Students)

### 4.1 Add `/evaluate/<booking_id>` route — currently linked but missing
- `examiner_dashboard.html` links to `/evaluate/<booking_id>` which returns 404
- Add a GET + POST route:
  - **GET:** render `examiner_rubrics.html` with the booking, student name, and all `Examination_Rubric` records for that exam
  - **POST:** create an `Evaluation` record (`marks_obtained`, `feedback`, `result`)

### 4.2 Fix `examiner_rubrics.html`
- `action=""` and `method=""` — form does nothing on submit
- Fix: `action="/evaluate/{{ booking_id }}"`, `method="POST"`
- Loop over rubric criteria dynamically from the database instead of hardcoded "Criteria 1"
- Add `marks_obtained`, `feedback`, and `result` fields

---

## Priority 5 — Remaining Broken Connections

### 5.1 Wire `admin_view_examiner.html` to a real route
- Template POSTs to `/admin/examiner/<id>` which doesn't exist → 404
- Fix: add a `/admin/examiner/<int:id>` route, or repoint the template to the existing `/examiner_dashboard/<id>`

### 5.2 Fix orphaned `admin_create_edit_slot.html`
- Template exists but no route renders it; `create_slot` renders `examiner_availability.html` instead
- Fix field names to match the backend (`id` → `examination_id`, `date` → `exam_date`)
- Fix input types to `type="date"` / `type="time"` (currently `type="number"`)
- Add missing `examiner_id` and `max_students` fields
- Wire `/slot/create` GET to render this template

### 5.3 Add ExaminerAssignment creation
- Examiner dashboard queries `ExaminerAssignment` but no route creates them → examiner always sees an empty exam list
- Add an "Assign Examiner" form on `admin_dashboard.html` next to each examination (select from approved examiners, POST to `/assign_examiner`)
- Add `/assign_examiner` POST route that creates the `ExaminerAssignment` record

### 5.4 Add `Slot → User` SQLAlchemy relationship
- **File:** `model.py` → `Slot` class
- Add `examiner = db.relationship("User", foreign_keys=[examiner_id])` so templates can display `slot.examiner.username`

### 5.5 Minor template / UI fixes
- `admin_course.html` submit button always says "Update" → pass an `editing` flag and use `{% if editing %}Update{% else %}Add Course{% endif %}`
- `admin_examination.html` course code is a free-text field → change to a `<select>` dropdown populated from courses
- `admin_rubrics.html` Exam ID is editable → change to `type="hidden"`, display exam name as text
- `already.html`, `invalid.html` → fix `<title>Document</title>` to something meaningful
- Add `<meta name="viewport" content="width=device-width, initial-scale=1">` to all templates that are missing it
- `static/style.css` → remove `greenyellow` border and fixed `600px`/`800px` heights (placeholder dev styling)

---

## Files to Modify

| File | Key Changes |
|---|---|
| `app.py` | Fix datetime parsing, fix `student_history` URL, fix `create_slot` redirect + GET handler, add `/evaluate`, `/slot/edit`, `/slot/delete`, `/booking/reschedule`, `/slot/reassign`, `/assign_examiner`, `/exam/set_status`, `/admin/examiner/<id>` routes, add duplicate booking check |
| `model.py` | Add 4 date-window columns, change `Examination.date` → `db.Date`, add `Slot.examiner` relationship |
| `admin_dashboard.html` | Wrap approve/reject in POST forms, add assign-examiner UI, add status-change buttons |
| `admin_course.html` | Fix submit label (Add vs Update) |
| `admin_examination.html` | Course `<select>` dropdown, 4 new `type="date"` fields |
| `admin_rubrics.html` | Make exam_id `type="hidden"` |
| `admin_registered_student.html` | Add Jinja loop, add Reschedule action |
| `admin_view_examiner.html` | Fix route reference |
| `admin_create_edit_slot.html` | Fix field names, input types, add missing fields, wire to route |
| `examiner_availability.html` | Fix form action/method, fix input types, add max_students, add Edit/Delete buttons |
| `examiner_rubrics.html` | Fix action/method, loop rubrics from DB, add evaluation fields |
| `student_dashboard.html` | Remove broken `booking.id` Cancel, fix nav Slots link |
| `student_booking.html` | Wrap Cancel in POST form, fix `<td>` nesting, fix Bootstrap version |
| `student_history.html` | Fix nav links with student_id |
| `student_profile.html` | Fix field names and action URL |
| `student_view_exam.html` | Use `examination` directly, fix loop/endfor, fix nav label and links |
| `wrong.html` | Fix `href="login.html"` → `href="/login"` |
| `invalid.html` | Fix empty `href` |
| `already.html` | Fix page title |
| `static/style.css` | Remove placeholder styling |
| All templates | Add viewport meta tag where missing |

---

## Verification Checklist

1. **Run the app:** `flask run` from the `examination_management_portal_mad1/` subdirectory — no startup errors.
2. **Admin flow:**
   - Login → add course → add examination (with date window fields) → assign examiner to exam → open slot creation window → open booking window
   - Search registered students → results appear in table
   - Reschedule a booking, reassign examiner on a slot
3. **Examiner flow:**
   - Register as examiner → admin approves (Approve button works without 405) → login
   - Sees assigned examinations → creates a slot (form submits without crash) → edits/deletes slot
   - After booking window opens: views booked students → submits evaluation (rubrics form works)
4. **Student flow:**
   - Register → login → browse available exams → book a slot
   - Try to book the same exam again → blocked (duplicate booking error)
   - Cancel a booking (Cancel button works without 405)
   - View history page (shows data, doesn't return error string)
   - Update profile (changes actually save)
5. **Crash check:** Edit an exam, create a slot, update profile → no 500/TypeError/UndefinedError
