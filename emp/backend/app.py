import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (JWTManager, create_access_token,
                                jwt_required, get_jwt_identity, get_jwt)
from flask_caching import Cache
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, time

from model import (db, User, ExaminerProfile, Course, Examination,
                   ExaminationRubric, ExaminationSlot, Booking, Evaluation)

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///emp.db")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-jwt-key-change-in-prod")
app.config["CACHE_TYPE"] = "RedisCache"
app.config["CACHE_REDIS_URL"] = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
app.config["CACHE_DEFAULT_TIMEOUT"] = 60

CORS(app)
JWTManager(app)
cache = Cache(app)
db.init_app(app)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def require_role(*roles):
    role = get_jwt().get("role")
    if role not in roles:
        return jsonify({"error": "Unauthorized"}), 403
    return None


def fmt_date(d):
    return d.isoformat() if d else None


def fmt_time(t):
    return t.strftime("%H:%M") if t else None


def slot_to_dict(slot):
    examiner = User.query.get(slot.examiner_id)
    return {
        "id": slot.id,
        "exam_id": slot.exam_id,
        "examiner_id": slot.examiner_id,
        "examiner_name": examiner.username if examiner else None,
        "date": fmt_date(slot.date),
        "start_time": fmt_time(slot.start_time),
        "end_time": fmt_time(slot.end_time),
        "capacity": slot.capacity,
        "available_seats": slot.available_seats,
        "status": slot.status,
        "meeting_link": slot.meeting_link,
    }


def booking_to_dict(b):
    slot = ExaminationSlot.query.get(b.slot_id)
    exam = Examination.query.get(slot.exam_id) if slot else None
    course = Course.query.get(exam.course_id) if exam else None
    examiner = User.query.get(slot.examiner_id) if slot else None
    return {
        "id": b.id,
        "slot_id": b.slot_id,
        "student_id": b.student_id,
        "booking_date": b.booking_date.isoformat(),
        "status": b.status,
        "exam_name": exam.name if exam else None,
        "exam_type": exam.exam_type if exam else None,
        "course": course.course_name if course else None,
        "date": fmt_date(slot.date) if slot else None,
        "start_time": fmt_time(slot.start_time) if slot else None,
        "end_time": fmt_time(slot.end_time) if slot else None,
        "examiner": examiner.username if examiner else None,
        "meeting_link": slot.meeting_link if slot else None,
    }


# ─────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    if not username or not email or not password:
        return jsonify({"error": "username, email and password are required"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409
    user = User(username=username, email=email,
                password=generate_password_hash(password), role="student")
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Registered successfully"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400
    username = data.get("username", "")
    password = data.get("password", "")
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials"}), 401
    if not user.active:
        return jsonify({"error": "Account is inactive"}), 403
    token = create_access_token(identity=user.id,
                                additional_claims={"role": user.role})
    return jsonify({
        "access_token": token,
        "role": user.role,
        "username": user.username,
        "id": user.id
    }), 200


# ─────────────────────────────────────────────────────────────
# Admin — Dashboard
# ─────────────────────────────────────────────────────────────

@app.route("/api/admin/dashboard", methods=["GET"])
@jwt_required()
def admin_dashboard():
    err = require_role("admin")
    if err:
        return err
    return jsonify({
        "courses": Course.query.count(),
        "examinations": Examination.query.count(),
        "students": User.query.filter_by(role="student").count(),
        "examiners": User.query.filter_by(role="examiner").count(),
        "slots": ExaminationSlot.query.count(),
        "bookings": Booking.query.count(),
    }), 200


# ─────────────────────────────────────────────────────────────
# Admin — Courses
# ─────────────────────────────────────────────────────────────

@app.route("/api/admin/courses", methods=["GET", "POST"])
@jwt_required()
def admin_courses():
    err = require_role("admin")
    if err:
        return err
    if request.method == "GET":
        q = request.args.get("q", "")
        query = Course.query
        if q:
            query = query.filter(
                (Course.course_name.ilike(f"%{q}%")) |
                (Course.course_code.ilike(f"%{q}%"))
            )
        courses = query.all()
        return jsonify([{
            "id": c.id, "course_code": c.course_code,
            "course_name": c.course_name, "description": c.description,
            "status": c.status
        } for c in courses]), 200

    data = request.get_json()
    if not data.get("course_code") or not data.get("course_name"):
        return jsonify({"error": "course_code and course_name required"}), 400
    if Course.query.filter_by(course_code=data["course_code"]).first():
        return jsonify({"error": "Course code already exists"}), 409
    c = Course(course_code=data["course_code"], course_name=data["course_name"],
               description=data.get("description", ""), status="active")
    db.session.add(c)
    db.session.commit()
    return jsonify({"message": "Course created", "id": c.id}), 201


@app.route("/api/admin/courses/<int:cid>", methods=["PUT", "DELETE"])
@jwt_required()
def admin_course_detail(cid):
    err = require_role("admin")
    if err:
        return err
    c = Course.query.get_or_404(cid)
    if request.method == "DELETE":
        db.session.delete(c)
        db.session.commit()
        return jsonify({"message": "Course deleted"}), 200
    data = request.get_json()
    c.course_name = data.get("course_name", c.course_name)
    c.course_code = data.get("course_code", c.course_code)
    c.description = data.get("description", c.description)
    c.status = data.get("status", c.status)
    db.session.commit()
    return jsonify({"message": "Course updated"}), 200


# ─────────────────────────────────────────────────────────────
# Admin — Examinations
# ─────────────────────────────────────────────────────────────

def parse_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


@app.route("/api/admin/examinations", methods=["GET", "POST"])
@jwt_required()
def admin_examinations():
    err = require_role("admin")
    if err:
        return err
    if request.method == "GET":
        q = request.args.get("q", "")
        query = Examination.query
        if q:
            query = query.filter(Examination.name.ilike(f"%{q}%"))
        exams = query.all()
        return jsonify([exam_to_dict(e) for e in exams]), 200

    data = request.get_json()
    required = ["course_id", "name", "exam_type", "duration", "max_marks"]
    if not all(data.get(f) for f in required):
        return jsonify({"error": f"Required fields: {required}"}), 400
    e = Examination(
        course_id=data["course_id"],
        name=data["name"],
        exam_type=data["exam_type"],
        duration=int(data["duration"]),
        max_marks=float(data["max_marks"]),
        slot_creation_start=parse_dt(data.get("slot_creation_start")),
        slot_creation_end=parse_dt(data.get("slot_creation_end")),
        booking_start=parse_dt(data.get("booking_start")),
        booking_end=parse_dt(data.get("booking_end")),
        status="Draft"
    )
    db.session.add(e)
    db.session.commit()
    return jsonify({"message": "Examination created", "id": e.id}), 201


def exam_to_dict(e):
    course = Course.query.get(e.course_id)
    return {
        "id": e.id,
        "course_id": e.course_id,
        "course_name": course.course_name if course else None,
        "name": e.name,
        "exam_type": e.exam_type,
        "duration": e.duration,
        "max_marks": e.max_marks,
        "slot_creation_start": fmt_date(e.slot_creation_start),
        "slot_creation_end": fmt_date(e.slot_creation_end),
        "booking_start": fmt_date(e.booking_start),
        "booking_end": fmt_date(e.booking_end),
        "status": e.status,
    }


@app.route("/api/admin/examinations/<int:eid>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def admin_examination_detail(eid):
    err = require_role("admin")
    if err:
        return err
    e = Examination.query.get_or_404(eid)
    if request.method == "GET":
        return jsonify(exam_to_dict(e)), 200
    if request.method == "DELETE":
        # Guard: prevent deletion if bookings exist
        slot_ids = [s.id for s in ExaminationSlot.query.filter_by(exam_id=eid).all()]
        if slot_ids and Booking.query.filter(Booking.slot_id.in_(slot_ids)).count() > 0:
            return jsonify({"error": "Cannot delete examination with existing bookings"}), 409
        db.session.delete(e)
        db.session.commit()
        return jsonify({"message": "Examination deleted"}), 200
    data = request.get_json()
    e.name = data.get("name", e.name)
    e.exam_type = data.get("exam_type", e.exam_type)
    e.duration = int(data.get("duration", e.duration))
    e.max_marks = float(data.get("max_marks", e.max_marks))
    e.slot_creation_start = parse_dt(data.get("slot_creation_start")) or e.slot_creation_start
    e.slot_creation_end = parse_dt(data.get("slot_creation_end")) or e.slot_creation_end
    e.booking_start = parse_dt(data.get("booking_start")) or e.booking_start
    e.booking_end = parse_dt(data.get("booking_end")) or e.booking_end
    if "status" in data:
        e.status = data["status"]
    db.session.commit()
    return jsonify({"message": "Examination updated"}), 200


@app.route("/api/admin/examinations/<int:eid>/publish", methods=["POST"])
@jwt_required()
def admin_publish_results(eid):
    err = require_role("admin")
    if err:
        return err
    e = Examination.query.get_or_404(eid)
    # Mark all Pending evaluations for this exam's bookings as Published
    slots = ExaminationSlot.query.filter_by(exam_id=eid).all()
    count = 0
    for slot in slots:
        for booking in slot.bookings:
            if booking.evaluation and booking.evaluation.status == "Pending":
                booking.evaluation.status = "Published"
                count += 1
    e.status = "Completed"
    db.session.commit()
    return jsonify({"message": f"Results published for {count} evaluations"}), 200


# ─────────────────────────────────────────────────────────────
# Admin — Rubrics
# ─────────────────────────────────────────────────────────────

@app.route("/api/admin/examinations/<int:eid>/rubrics", methods=["GET", "POST"])
@jwt_required()
def admin_rubrics(eid):
    err = require_role("admin")
    if err:
        return err
    Examination.query.get_or_404(eid)
    if request.method == "GET":
        rubrics = ExaminationRubric.query.filter_by(exam_id=eid).all()
        return jsonify([{
            "id": r.id, "criterion_name": r.criterion_name,
            "max_marks": r.max_marks, "weightage": r.weightage,
            "description": r.description
        } for r in rubrics]), 200
    data = request.get_json()
    if not data.get("criterion_name") or not data.get("max_marks"):
        return jsonify({"error": "criterion_name and max_marks required"}), 400
    r = ExaminationRubric(
        exam_id=eid,
        criterion_name=data["criterion_name"],
        max_marks=float(data["max_marks"]),
        weightage=float(data.get("weightage", 1.0)),
        description=data.get("description", "")
    )
    db.session.add(r)
    db.session.commit()
    return jsonify({"message": "Rubric created", "id": r.id}), 201


@app.route("/api/admin/rubrics/<int:rid>", methods=["PUT", "DELETE"])
@jwt_required()
def admin_rubric_detail(rid):
    err = require_role("admin")
    if err:
        return err
    r = ExaminationRubric.query.get_or_404(rid)
    if request.method == "DELETE":
        db.session.delete(r)
        db.session.commit()
        return jsonify({"message": "Rubric deleted"}), 200
    data = request.get_json()
    r.criterion_name = data.get("criterion_name", r.criterion_name)
    r.max_marks = float(data.get("max_marks", r.max_marks))
    r.weightage = float(data.get("weightage", r.weightage))
    r.description = data.get("description", r.description)
    db.session.commit()
    return jsonify({"message": "Rubric updated"}), 200


# ─────────────────────────────────────────────────────────────
# Admin — Examiners
# ─────────────────────────────────────────────────────────────

@app.route("/api/admin/examiners", methods=["GET", "POST"])
@jwt_required()
def admin_examiners():
    err = require_role("admin")
    if err:
        return err
    if request.method == "GET":
        q = request.args.get("q", "")
        query = User.query.filter_by(role="examiner")
        if q:
            query = query.filter(User.username.ilike(f"%{q}%"))
        examiners = query.all()
        result = []
        for u in examiners:
            ep = ExaminerProfile.query.filter_by(user_id=u.id).first()
            result.append({
                "id": u.id, "username": u.username, "email": u.email,
                "active": u.active,
                "department": ep.department if ep else None,
                "contact": ep.contact if ep else None,
            })
        return jsonify(result), 200

    data = request.get_json()
    if not data.get("username") or not data.get("email") or not data.get("password"):
        return jsonify({"error": "username, email and password required"}), 400
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already taken"}), 409
    u = User(username=data["username"], email=data["email"],
             password=generate_password_hash(data["password"]), role="examiner")
    db.session.add(u)
    db.session.flush()
    ep = ExaminerProfile(user_id=u.id,
                         department=data.get("department", ""),
                         contact=data.get("contact", ""))
    db.session.add(ep)
    db.session.commit()
    return jsonify({"message": "Examiner created", "id": u.id}), 201


@app.route("/api/admin/examiners/<int:uid>", methods=["PUT", "DELETE"])
@jwt_required()
def admin_examiner_detail(uid):
    err = require_role("admin")
    if err:
        return err
    u = User.query.filter_by(id=uid, role="examiner").first()
    if not u:
        return jsonify({"error": "Examiner not found"}), 404
    if request.method == "DELETE":
        u.active = False
        db.session.commit()
        return jsonify({"message": "Examiner deactivated"}), 200
    data = request.get_json()
    u.email = data.get("email", u.email)
    u.active = data.get("active", u.active)
    ep = ExaminerProfile.query.filter_by(user_id=uid).first()
    if ep:
        ep.department = data.get("department", ep.department)
        ep.contact = data.get("contact", ep.contact)
    db.session.commit()
    return jsonify({"message": "Examiner updated"}), 200


# ─────────────────────────────────────────────────────────────
# Admin — Students
# ─────────────────────────────────────────────────────────────

@app.route("/api/admin/students", methods=["GET"])
@jwt_required()
def admin_students():
    err = require_role("admin")
    if err:
        return err
    q = request.args.get("q", "")
    query = User.query.filter_by(role="student")
    if q:
        query = query.filter(User.username.ilike(f"%{q}%"))
    students = query.all()
    return jsonify([{
        "id": u.id, "username": u.username, "email": u.email, "active": u.active
    } for u in students]), 200


# ─────────────────────────────────────────────────────────────
# Admin — Slots & Bookings
# ─────────────────────────────────────────────────────────────

@app.route("/api/admin/slots", methods=["GET"])
@jwt_required()
def admin_slots():
    err = require_role("admin")
    if err:
        return err
    exam_id = request.args.get("exam_id")
    query = ExaminationSlot.query
    if exam_id:
        query = query.filter_by(exam_id=int(exam_id))
    slots = query.all()
    return jsonify([slot_to_dict(s) for s in slots]), 200


@app.route("/api/admin/bookings", methods=["GET"])
@jwt_required()
def admin_bookings():
    err = require_role("admin")
    if err:
        return err
    q = request.args.get("q", "")
    bookings = Booking.query.all()
    result = []
    for b in bookings:
        d = booking_to_dict(b)
        student = User.query.get(b.student_id)
        d["student_name"] = student.username if student else None
        if q and q.lower() not in (d.get("student_name") or "").lower() \
                and q.lower() not in (d.get("exam_name") or "").lower():
            continue
        result.append(d)
    return jsonify(result), 200


@app.route("/api/admin/bookings/<int:bid>/reschedule", methods=["PUT"])
@jwt_required()
def admin_reschedule(bid):
    err = require_role("admin")
    if err:
        return err
    b = Booking.query.get_or_404(bid)
    data = request.get_json()
    new_slot_id = data.get("new_slot_id")
    if not new_slot_id:
        return jsonify({"error": "new_slot_id required"}), 400
    new_slot = ExaminationSlot.query.get_or_404(new_slot_id)
    if new_slot.available_seats <= 0:
        return jsonify({"error": "New slot has no available seats"}), 400

    # Free old slot
    old_slot = ExaminationSlot.query.get(b.slot_id)
    if old_slot and b.status == "Booked":
        old_slot.available_seats += 1
        if old_slot.status == "Full":
            old_slot.status = "Available"

    # Assign new slot
    b.slot_id = new_slot_id
    new_slot.available_seats -= 1
    if new_slot.available_seats == 0:
        new_slot.status = "Full"
    db.session.commit()
    return jsonify({"message": "Booking rescheduled"}), 200


@app.route("/api/admin/bookings/<int:bid>/reassign", methods=["PUT"])
@jwt_required()
def admin_reassign_examiner(bid):
    err = require_role("admin")
    if err:
        return err
    b = Booking.query.get_or_404(bid)
    data = request.get_json()
    new_examiner_id = data.get("examiner_id")
    if not new_examiner_id:
        return jsonify({"error": "examiner_id required"}), 400
    slot = ExaminationSlot.query.get(b.slot_id)
    if not slot:
        return jsonify({"error": "Slot not found"}), 404
    slot.examiner_id = new_examiner_id
    db.session.commit()
    return jsonify({"message": "Examiner reassigned"}), 200


# ─────────────────────────────────────────────────────────────
# Examiner — Endpoints
# ─────────────────────────────────────────────────────────────

@app.route("/api/examiner/examinations", methods=["GET"])
@jwt_required()
def examiner_examinations():
    err = require_role("examiner")
    if err:
        return err
    examiner_id = get_jwt_identity()
    # Return exams with existing slots + all "Slot Creation" exams (so examiner can create new slots)
    slot_exam_ids = db.session.query(ExaminationSlot.exam_id)\
        .filter_by(examiner_id=examiner_id).distinct().all()
    existing_ids = [r[0] for r in slot_exam_ids]
    slot_creation_exams = Examination.query.filter_by(status="Slot Creation").all()
    slot_creation_ids = [e.id for e in slot_creation_exams]
    all_ids = list(set(existing_ids + slot_creation_ids))
    exams = Examination.query.filter(Examination.id.in_(all_ids)).all() if all_ids else []
    return jsonify([exam_to_dict(e) for e in exams]), 200


@app.route("/api/examiner/slots", methods=["GET", "POST"])
@jwt_required()
def examiner_slots():
    err = require_role("examiner")
    if err:
        return err
    examiner_id = get_jwt_identity()
    if request.method == "GET":
        slots = ExaminationSlot.query.filter_by(examiner_id=examiner_id).all()
        result = []
        for s in slots:
            d = slot_to_dict(s)
            d["booked_count"] = Booking.query.filter_by(slot_id=s.id, status="Booked").count()
            result.append(d)
        return jsonify(result), 200

    data = request.get_json()
    exam = Examination.query.get(data.get("exam_id"))
    if not exam:
        return jsonify({"error": "Examination not found"}), 404
    if exam.status != "Slot Creation":
        return jsonify({"error": "Slot creation is not open for this examination"}), 403

    try:
        slot_date = date.fromisoformat(data["date"])
        start_t = time.fromisoformat(data["start_time"])
        end_t = time.fromisoformat(data["end_time"])
    except (KeyError, ValueError) as ex:
        return jsonify({"error": f"Invalid date/time format: {ex}"}), 400

    capacity = int(data.get("capacity", 1))
    s = ExaminationSlot(
        exam_id=data["exam_id"],
        examiner_id=examiner_id,
        date=slot_date,
        start_time=start_t,
        end_time=end_t,
        capacity=capacity,
        available_seats=capacity,
        status="Available",
        meeting_link=data.get("meeting_link", "")
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({"message": "Slot created", "id": s.id}), 201


@app.route("/api/examiner/slots/<int:sid>", methods=["PUT", "DELETE"])
@jwt_required()
def examiner_slot_detail(sid):
    err = require_role("examiner")
    if err:
        return err
    examiner_id = get_jwt_identity()
    s = ExaminationSlot.query.filter_by(id=sid, examiner_id=examiner_id).first()
    if not s:
        return jsonify({"error": "Slot not found or not yours"}), 404
    exam = Examination.query.get(s.exam_id)

    if request.method == "DELETE":
        if exam and exam.status == "Booking Open":
            return jsonify({"error": "Cannot delete slot after booking has opened"}), 403
        db.session.delete(s)
        db.session.commit()
        return jsonify({"message": "Slot deleted"}), 200

    if exam and exam.status == "Booking Open":
        return jsonify({"error": "Cannot update slot after booking has opened"}), 403
    data = request.get_json()
    if "date" in data:
        s.date = date.fromisoformat(data["date"])
    if "start_time" in data:
        s.start_time = time.fromisoformat(data["start_time"])
    if "end_time" in data:
        s.end_time = time.fromisoformat(data["end_time"])
    if "capacity" in data:
        new_cap = int(data["capacity"])
        booked = s.capacity - s.available_seats
        s.capacity = new_cap
        s.available_seats = max(0, new_cap - booked)
        s.status = "Full" if s.available_seats == 0 else "Available"
    s.meeting_link = data.get("meeting_link", s.meeting_link)
    db.session.commit()
    return jsonify({"message": "Slot updated"}), 200


@app.route("/api/examiner/slots/<int:sid>/students", methods=["GET"])
@jwt_required()
def examiner_slot_students(sid):
    err = require_role("examiner")
    if err:
        return err
    examiner_id = get_jwt_identity()
    slot = ExaminationSlot.query.filter_by(id=sid, examiner_id=examiner_id).first()
    if not slot:
        return jsonify({"error": "Slot not found or not yours"}), 404
    bookings = Booking.query.filter_by(slot_id=sid).all()
    result = []
    for b in bookings:
        student = User.query.get(b.student_id)
        ev = Evaluation.query.filter_by(booking_id=b.id).first()
        result.append({
            "booking_id": b.id,
            "student_id": b.student_id,
            "student_name": student.username if student else None,
            "student_email": student.email if student else None,
            "booking_status": b.status,
            "evaluated": ev is not None,
            "marks": ev.total_marks if ev else None,
        })
    return jsonify(result), 200


@app.route("/api/examiner/evaluate/<int:booking_id>", methods=["POST"])
@jwt_required()
def examiner_evaluate(booking_id):
    err = require_role("examiner")
    if err:
        return err
    examiner_id = get_jwt_identity()
    b = Booking.query.get_or_404(booking_id)
    slot = ExaminationSlot.query.get(b.slot_id)
    if not slot or slot.examiner_id != examiner_id:
        return jsonify({"error": "You are not the examiner for this booking"}), 403
    if b.status == "Cancelled":
        return jsonify({"error": "Cannot evaluate a cancelled booking"}), 400
    data = request.get_json()
    ev = Evaluation.query.filter_by(booking_id=booking_id).first()
    if ev:
        ev.total_marks = float(data.get("total_marks", ev.total_marks))
        ev.remarks = data.get("remarks", ev.remarks)
        ev.eval_date = datetime.utcnow()
    else:
        ev = Evaluation(
            booking_id=booking_id,
            student_id=b.student_id,
            examiner_id=examiner_id,
            total_marks=float(data.get("total_marks", 0)),
            remarks=data.get("remarks", ""),
            status="Pending"
        )
        db.session.add(ev)
        b.status = "Completed"
    db.session.commit()
    return jsonify({"message": "Evaluation saved"}), 200


@app.route("/api/examiner/dashboard", methods=["GET"])
@jwt_required()
def examiner_dashboard():
    err = require_role("examiner")
    if err:
        return err
    examiner_id = get_jwt_identity()
    slots = ExaminationSlot.query.filter_by(examiner_id=examiner_id).all()
    slot_ids = [s.id for s in slots]
    booked = Booking.query.filter(Booking.slot_id.in_(slot_ids), Booking.status == "Booked").count()
    pending_evals = Booking.query.filter(
        Booking.slot_id.in_(slot_ids),
        Booking.status == "Completed"
    ).outerjoin(Evaluation, Booking.id == Evaluation.booking_id)\
     .filter(Evaluation.id == None).count()

    slot_exam_ids = list({s.exam_id for s in slots})
    return jsonify({
        "assigned_exams": len(slot_exam_ids),
        "total_slots": len(slots),
        "booked_students": booked,
        "pending_evaluations": pending_evals,
    }), 200


# ─────────────────────────────────────────────────────────────
# Student — Endpoints
# ─────────────────────────────────────────────────────────────

@app.route("/api/student/examinations", methods=["GET"])
@jwt_required()
def student_examinations():
    err = require_role("student")
    if err:
        return err
    q = request.args.get("q", "")
    exam_type = request.args.get("type", "")
    query = Examination.query.filter(
        Examination.status.in_(["Booking Open", "Slot Creation", "Closed", "Completed"])
    )
    if q:
        query = query.filter(Examination.name.ilike(f"%{q}%"))
    if exam_type:
        query = query.filter(Examination.exam_type == exam_type)
    return jsonify([exam_to_dict(e) for e in query.all()]), 200


@app.route("/api/student/slots/<int:exam_id>", methods=["GET"])
@jwt_required()
def student_slots(exam_id):
    err = require_role("student")
    if err:
        return err
    exam = Examination.query.get_or_404(exam_id)
    if exam.status != "Booking Open":
        return jsonify({"error": "Booking is not open for this examination"}), 403
    slots = ExaminationSlot.query.filter_by(exam_id=exam_id, status="Available").all()
    return jsonify([slot_to_dict(s) for s in slots]), 200


@app.route("/api/student/bookings", methods=["GET", "POST"])
@jwt_required()
def student_bookings():
    err = require_role("student")
    if err:
        return err
    student_id = get_jwt_identity()

    if request.method == "GET":
        bookings = Booking.query.filter_by(student_id=student_id).all()
        return jsonify([booking_to_dict(b) for b in bookings]), 200

    data = request.get_json()
    slot_id = data.get("slot_id")
    if not slot_id:
        return jsonify({"error": "slot_id required"}), 400

    slot = ExaminationSlot.query.get_or_404(slot_id)
    exam = Examination.query.get(slot.exam_id)

    # Validate booking period
    if not exam or exam.status != "Booking Open":
        return jsonify({"error": "Booking is not open for this examination"}), 403
    now = datetime.utcnow()
    if exam.booking_end and now > exam.booking_end:
        return jsonify({"error": "Booking period has ended"}), 403

    # Prevent duplicate booking for same exam
    existing_exam_booking = db.session.query(Booking).join(
        ExaminationSlot, Booking.slot_id == ExaminationSlot.id
    ).filter(
        ExaminationSlot.exam_id == exam.id,
        Booking.student_id == student_id,
        Booking.status == "Booked"
    ).first()
    if existing_exam_booking:
        return jsonify({"error": "You have already booked a slot for this examination"}), 409

    # Check capacity
    if slot.available_seats <= 0 or slot.status == "Full":
        return jsonify({"error": "No available seats in this slot"}), 400

    b = Booking(student_id=student_id, slot_id=slot_id)
    db.session.add(b)
    slot.available_seats -= 1
    if slot.available_seats == 0:
        slot.status = "Full"
    db.session.commit()
    return jsonify({"message": "Slot booked successfully", "booking_id": b.id}), 201


@app.route("/api/student/bookings/<int:bid>", methods=["DELETE"])
@jwt_required()
def student_cancel_booking(bid):
    err = require_role("student")
    if err:
        return err
    student_id = get_jwt_identity()
    b = Booking.query.filter_by(id=bid, student_id=student_id).first()
    if not b:
        return jsonify({"error": "Booking not found"}), 404
    if b.status != "Booked":
        return jsonify({"error": "Only active bookings can be cancelled"}), 400
    slot = ExaminationSlot.query.get(b.slot_id)
    exam = Examination.query.get(slot.exam_id) if slot else None
    now = datetime.utcnow()
    if exam and exam.booking_end and now > exam.booking_end:
        return jsonify({"error": "Cancellation deadline has passed"}), 403
    b.status = "Cancelled"
    if slot:
        slot.available_seats += 1
        if slot.status == "Full":
            slot.status = "Available"
    db.session.commit()
    return jsonify({"message": "Booking cancelled"}), 200


@app.route("/api/student/results", methods=["GET"])
@jwt_required()
def student_results():
    err = require_role("student")
    if err:
        return err
    student_id = get_jwt_identity()
    evals = Evaluation.query.filter_by(student_id=student_id, status="Published").all()
    result = []
    for ev in evals:
        b = Booking.query.get(ev.booking_id)
        slot = ExaminationSlot.query.get(b.slot_id) if b else None
        exam = Examination.query.get(slot.exam_id) if slot else None
        course = Course.query.get(exam.course_id) if exam else None
        examiner = User.query.get(ev.examiner_id)
        result.append({
            "evaluation_id": ev.id,
            "exam_name": exam.name if exam else None,
            "course": course.course_name if course else None,
            "total_marks": ev.total_marks,
            "max_marks": exam.max_marks if exam else None,
            "remarks": ev.remarks,
            "eval_date": ev.eval_date.isoformat() if ev.eval_date else None,
            "examiner": examiner.username if examiner else None,
        })
    return jsonify(result), 200


@app.route("/api/student/profile", methods=["GET", "PUT"])
@jwt_required()
def student_profile():
    err = require_role("student")
    if err:
        return err
    student_id = get_jwt_identity()
    u = User.query.get_or_404(student_id)
    if request.method == "GET":
        return jsonify({"id": u.id, "username": u.username, "email": u.email}), 200
    data = request.get_json()
    if "email" in data:
        u.email = data["email"]
    if "password" in data and data["password"]:
        u.password = generate_password_hash(data["password"])
    db.session.commit()
    return jsonify({"message": "Profile updated"}), 200


@app.route("/api/student/export", methods=["GET"])
@jwt_required()
def student_export():
    err = require_role("student")
    if err:
        return err
    student_id = get_jwt_identity()
    from tasks import export_exam_history
    export_exam_history.delay(student_id)
    return jsonify({"message": "Export started — you will receive an email when ready"}), 200


@app.route("/api/student/dashboard", methods=["GET"])
@jwt_required()
def student_dashboard():
    err = require_role("student")
    if err:
        return err
    student_id = get_jwt_identity()
    bookings = Booking.query.filter_by(student_id=student_id).all()
    upcoming = [b for b in bookings if b.status == "Booked"]
    published_results = Evaluation.query.filter_by(
        student_id=student_id, status="Published"
    ).count()
    return jsonify({
        "total_bookings": len(bookings),
        "upcoming_exams": len(upcoming),
        "published_results": published_results,
    }), 200


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            admin = User(
                username="admin",
                email="admin@emp.com",
                password=generate_password_hash("admin123"),
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin seeded: admin / admin123")
    app.run(debug=True, port=5000)
