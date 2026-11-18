from datetime import datetime
from flask import Flask, redirect, render_template, request
from model import *

app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///MAD_1_PROJECT_SEPT2026.db'
app.secret_key = 'emp_mad1_secret'
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/home", methods=["GET"])
def home():
    return render_template("home.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form.get("password")
        user_type = request.form.get("usertype")
        if user_type == "admin":
            admin = User.query.filter_by(username=username, password=password, role="admin").first()
            if admin:
                return redirect("/admin_dashboard")
            else:
                return render_template('invalid.html')

        if user_type == "student":
            student = User.query.filter_by(username=username, password=password, role="student").first()
            if student:
                return redirect(f"/student_dashboard/{student.id}")
            else:
                return render_template('invalid.html')

        if user_type == "examiner":
            examiner = User.query.filter_by(username=username, password=password, role="examiner").first()
            if examiner:
                if examiner.status != "Approved":
                    return render_template('invalid.html')
                return redirect(f"/examiner_dashboard/{examiner.id}")
            else:
                return render_template('invalid.html')
        else:
            return render_template("login.html")
    else:
        return render_template("login.html")

@app.route('/register_admin', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        contact_no = request.form.get("contact_no")
        admin_name = User.query.filter_by(username=username).first()
        if admin_name:
            return render_template("already.html")
        new_user = User(username=username, password=password, email=email, contact_no=contact_no, role="admin", status="Approved")
        db.session.add(new_user)
        db.session.commit()
        return render_template("register_admin.html", success=True)
    else:
        return render_template("register_admin.html", success=False)

@app.route('/register_examiner', methods=['GET', 'POST'])
def register_examiner():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        contact_no = request.form.get("contact_no")
        department = request.form.get("department")
        e_name = User.query.filter_by(username=username).first()
        if e_name:
            return render_template("already.html")
        new_examiner = User(username=username, password=password, email=email, contact_no=contact_no, department=department, role="examiner", status="pending")
        db.session.add(new_examiner)
        db.session.commit()
        return render_template("register_examiner.html", success=True)
    else:
        return render_template("register_examiner.html")

@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        contact_no = request.form.get("contact_no")
        stu_name = User.query.filter_by(username=username).first()
        if stu_name:
            return render_template("already.html")
        new_student = User(username=username, password=password, email=email, contact_no=contact_no, role="student", status="Approved")
        db.session.add(new_student)
        db.session.commit()
        return render_template("register_student.html", success=True)
    else:
        return render_template("register_student.html")

# ─── ADMIN ───────────────────────────────────────────────────────────────────

@app.route("/admin_dashboard")
def admin_dashboard():
    courses = Course.query.all()
    examinations = Examination.query.all()
    examiners = User.query.filter_by(role="examiner").all()
    approved_examiners = User.query.filter_by(role="examiner", status="Approved").all()
    return render_template("admin_dashboard.html",
                           courses=courses,
                           examinations=examinations,
                           examiners=examiners,
                           approved_examiners=approved_examiners)

@app.route("/course", methods=["GET", "POST"])
def add_course():
    if request.method == "POST":
        code = request.form["code"]
        name = request.form["name"]
        description = request.form["description"]
        course = Course(code=code, name=name, description=description, status="active")
        db.session.add(course)
        db.session.commit()
        return redirect("/admin_dashboard")
    return render_template("admin_course.html", editing=False)

@app.route("/course/edit/<int:course_id>", methods=["GET", "POST"])
def edit_course(course_id):
    course = Course.query.get(course_id)
    if request.method == "POST":
        course.code = request.form["code"]
        course.name = request.form["name"]
        course.description = request.form["description"]
        db.session.commit()
        return redirect("/admin_dashboard")
    return render_template("admin_course.html", course=course, editing=True)

@app.route("/course/delete/<int:course_id>")
def delete_course(course_id):
    course = Course.query.get(course_id)
    db.session.delete(course)
    db.session.commit()
    return redirect("/admin_dashboard")

@app.route("/examination", methods=["GET", "POST"])
def add_exam():
    courses = Course.query.all()
    if request.method == "POST":
        exam = Examination(
            course_id=int(request.form["course_id"]),
            name=request.form["name"],
            type=request.form["type"],
            duration=int(request.form["duration"]),
            max_marks=float(request.form["max_marks"]),
            date=request.form["exam_date"],
            status="Draft",
            slot_creation_start_date=request.form.get("slot_creation_start_date") or None,
            slot_creation_end_date=request.form.get("slot_creation_end_date") or None,
            slot_booking_start_date=request.form.get("slot_booking_start_date") or None,
            slot_booking_end_date=request.form.get("slot_booking_end_date") or None)
        db.session.add(exam)
        db.session.commit()
        return redirect("/admin_dashboard")
    return render_template("admin_examination.html", courses=courses, editing=False)

@app.route("/examination/edit/<int:exam_id>", methods=["GET", "POST"])
def edit_exam(exam_id):
    exam = Examination.query.get(exam_id)
    courses = Course.query.all()
    if request.method == "POST":
        exam.course_id = int(request.form["course_id"])
        exam.name = request.form["name"]
        exam.type = request.form["type"]
        exam.duration = int(request.form["duration"])
        exam.max_marks = float(request.form["max_marks"])
        exam.date = request.form["exam_date"]
        exam.slot_creation_start_date = request.form.get("slot_creation_start_date") or None
        exam.slot_creation_end_date = request.form.get("slot_creation_end_date") or None
        exam.slot_booking_start_date = request.form.get("slot_booking_start_date") or None
        exam.slot_booking_end_date = request.form.get("slot_booking_end_date") or None
        db.session.commit()
        return redirect("/admin_dashboard")
    return render_template("admin_examination.html", exam=exam, courses=courses, editing=True)

@app.route("/examination/delete/<int:exam_id>")
def delete_exam(exam_id):
    exam = Examination.query.get(exam_id)
    db.session.delete(exam)
    db.session.commit()
    return redirect("/admin_dashboard")

@app.route("/exam/set_status/<int:exam_id>", methods=["POST"])
def set_exam_status(exam_id):
    exam = Examination.query.get(exam_id)
    exam.status = request.form["status"]
    db.session.commit()
    return redirect("/admin_dashboard")

@app.route("/rubrics/<int:exam_id>", methods=["GET", "POST"])
def rubrics(exam_id):
    exam = Examination.query.get(exam_id)
    if request.method == "POST":
        rubric = Examination_Rubric(
            examination_id=exam_id,
            criteria_name=request.form["criteria_name"],
            max_marks=float(request.form["max_marks"]),
            weightage=float(request.form["weightage"]),
            description=request.form["description"])
        db.session.add(rubric)
        db.session.commit()
        return redirect(f"/rubrics/{exam_id}")
    rubrics_list = Examination_Rubric.query.filter_by(examination_id=exam_id).all()
    return render_template("admin_rubrics.html", exam=exam, rubrics=rubrics_list)

@app.route("/registered_student", methods=["GET", "POST"])
def registered_student():
    exam_id = request.args.get("id", type=int) or request.form.get("id", type=int)
    student_id = request.args.get("student_id", type=int) or request.form.get("student_id", type=int)
    query = Booking.query.join(Slot)
    if exam_id:
        query = query.filter(Slot.examination_id == exam_id)
    if student_id:
        query = query.filter(Booking.student_id == student_id)
    bookings = query.order_by(Booking.booking_date.desc()).all()
    slots_for_reschedule = Slot.query.filter(Slot.available_seats > 0).all()
    return render_template("admin_registered_student.html",
                           bookings=bookings,
                           exam_id=exam_id,
                           student_id=student_id,
                           slots_for_reschedule=slots_for_reschedule)

@app.route("/booking/reschedule/<int:booking_id>", methods=["POST"])
def reschedule_booking(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking or not request.form.get("new_slot_id"):
        return redirect("/registered_student")
    new_slot_id = int(request.form["new_slot_id"])
    old_slot = Slot.query.get(booking.slot_id)
    new_slot = Slot.query.get(new_slot_id)
    if new_slot.available_seats <= 0:
        return redirect("/registered_student")
    old_slot.available_seats += 1
    if old_slot.status == "Full":
        old_slot.status = "Available"
    new_slot.available_seats -= 1
    if new_slot.available_seats == 0:
        new_slot.status = "Full"
    booking.slot_id = new_slot_id
    db.session.commit()
    return redirect("/registered_student")

@app.route("/slot/reassign/<int:slot_id>", methods=["POST"])
def reassign_slot(slot_id):
    slot = Slot.query.get(slot_id)
    if not slot or not request.form.get("new_examiner_id"):
        return redirect("/admin_dashboard")
    new_examiner_id = int(request.form["new_examiner_id"])
    old_assignment = ExaminerAssignment.query.filter_by(
        examiner_id=slot.examiner_id, examination_id=slot.examination_id).first()
    if old_assignment:
        old_assignment.examiner_id = new_examiner_id
    slot.examiner_id = new_examiner_id
    db.session.commit()
    return redirect("/admin_dashboard")

@app.route("/assign_examiner", methods=["POST"])
def assign_examiner():
    if not request.form.get("examiner_id") or not request.form.get("examination_id"):
        return redirect("/admin_dashboard")
    examiner_id = int(request.form["examiner_id"])
    examination_id = int(request.form["examination_id"])
    existing = ExaminerAssignment.query.filter_by(
        examiner_id=examiner_id, examination_id=examination_id).first()
    if not existing:
        assignment = ExaminerAssignment(examiner_id=examiner_id, examination_id=examination_id)
        db.session.add(assignment)
        db.session.commit()
    return redirect("/admin_dashboard")

# ─── EXAMINERS ────────────────────────────────────────────────────────────────

@app.route("/examiner_dashboard")
def examiner_dashboard():
    examiners = User.query.filter_by(role="examiner").all()
    return render_template("examiner_list.html", examiners=examiners)

@app.route("/examiner_dashboard/<int:examiner_id>")
def examiners_dashboard(examiner_id):
    examiner = User.query.get(examiner_id)
    if not examiner:
        return render_template("invalid.html")
    examinations = Examination.query.join(ExaminerAssignment).filter(
        ExaminerAssignment.examiner_id == examiner_id).all()
    slots = Slot.query.filter_by(examiner_id=examiner_id).all()
    bookings = Booking.query.join(Slot).filter(Slot.examiner_id == examiner_id).all()
    return render_template("examiner_dashboard.html",
                           examiner=examiner,
                           examinations=examinations,
                           slots=slots,
                           bookings=bookings)

@app.route("/examiner/approve/<int:examiner_id>", methods=["POST"])
def approve_examiner(examiner_id):
    examiner = User.query.filter_by(id=examiner_id, role="examiner").first()
    if not examiner:
        return redirect("/admin_dashboard")
    examiner.status = "Approved"
    db.session.commit()
    return redirect("/admin_dashboard")

@app.route("/examiner/reject/<int:examiner_id>", methods=["POST"])
def reject_examiner(examiner_id):
    examiner = User.query.filter_by(id=examiner_id, role="examiner").first()
    if not examiner:
        return redirect("/admin_dashboard")
    examiner.status = "Rejected"
    db.session.commit()
    return redirect("/admin_dashboard")

@app.route("/admin/examiner/<int:examiner_id>")
def admin_view_examiner(examiner_id):
    examiner = User.query.get(examiner_id)
    assignments = ExaminerAssignment.query.filter_by(examiner_id=examiner_id).all()
    return render_template("admin_view_examiner.html", examiner=examiner, assignments=assignments)

@app.route("/examiner_slots/<int:examiner_id>")
def examiner_slots(examiner_id):
    examiner = User.query.get(examiner_id)
    slots = Slot.query.filter_by(examiner_id=examiner_id).all()
    examinations = Examination.query.join(ExaminerAssignment).filter(
        ExaminerAssignment.examiner_id == examiner_id).all()
    return render_template("examiner_availability.html",
                           slots=slots,
                           examiner_id=examiner_id,
                           examiner=examiner,
                           examinations=examinations)

@app.route("/slot/create", methods=["GET", "POST"])
def create_slot():
    if request.method == "POST":
        raw_eid = request.form.get("examiner_id", "")
        if not raw_eid.isdigit():
            return redirect("/examiner_dashboard")
        examiner_id = int(raw_eid)
        exam_id = int(request.form["examination_id"])
        max_students = int(request.form["max_students"])
        exam_date_str = request.form["exam_date"]
        start_time_str = request.form["start_time"]
        end_time_str = request.form["end_time"]
        exam_date = datetime.strptime(exam_date_str + " 00:00", "%Y-%m-%d %H:%M")
        start_time = datetime.strptime(exam_date_str + " " + start_time_str, "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(exam_date_str + " " + end_time_str, "%Y-%m-%d %H:%M")
        slot = Slot(
            examination_id=exam_id,
            examiner_id=examiner_id,
            exam_date=exam_date,
            start_time=start_time,
            end_time=end_time,
            max_students=max_students,
            available_seats=max_students,
            status="Available")
        db.session.add(slot)
        db.session.commit()
        return redirect(f"/examiner_slots/{examiner_id}")
    examiner_id = request.args.get("examiner_id", type=int)
    examiner = User.query.get(examiner_id) if examiner_id else None
    examinations = Examination.query.all()
    if examiner_id:
        examinations = Examination.query.join(ExaminerAssignment).filter(
            ExaminerAssignment.examiner_id == examiner_id).all()
    return render_template("examiner_availability.html",
                           slots=[],
                           examiner_id=examiner_id,
                           examiner=examiner,
                           examinations=examinations,
                           create_mode=True)

@app.route("/slot/edit/<int:slot_id>", methods=["GET", "POST"])
def edit_slot(slot_id):
    slot = Slot.query.get(slot_id)
    if request.method == "POST":
        exam_date_str = request.form["exam_date"]
        start_time_str = request.form["start_time"]
        end_time_str = request.form["end_time"]
        slot.exam_date = datetime.strptime(exam_date_str + " 00:00", "%Y-%m-%d %H:%M")
        slot.start_time = datetime.strptime(exam_date_str + " " + start_time_str, "%Y-%m-%d %H:%M")
        slot.end_time = datetime.strptime(exam_date_str + " " + end_time_str, "%Y-%m-%d %H:%M")
        slot.max_students = int(request.form["max_students"])
        db.session.commit()
        return redirect(f"/examiner_slots/{slot.examiner_id}")
    return render_template("slot_edit.html", slot=slot)

@app.route("/slot/delete/<int:slot_id>", methods=["POST"])
def delete_slot(slot_id):
    slot = Slot.query.get(slot_id)
    examiner_id = slot.examiner_id
    db.session.delete(slot)
    db.session.commit()
    return redirect(f"/examiner_slots/{examiner_id}")

@app.route("/evaluate/<int:booking_id>", methods=["GET", "POST"])
def evaluate(booking_id):
    booking = Booking.query.get(booking_id)
    if request.method == "POST":
        marks = float(request.form["marks_obtained"])
        feedback = request.form.get("feedback", "")
        result = request.form["result"]
        existing = Evaluation.query.filter_by(booking_id=booking_id).first()
        if existing:
            existing.marks_obtained = marks
            existing.feedback = feedback
            existing.result = result
        else:
            evaluation = Evaluation(
                booking_id=booking_id,
                examiner_id=booking.slot.examiner_id,
                marks_obtained=marks,
                feedback=feedback,
                result=result)
            db.session.add(evaluation)
        booking.status = "Completed"
        db.session.commit()
        return redirect(f"/examiner_dashboard/{booking.slot.examiner_id}")
    rubrics = Examination_Rubric.query.filter_by(
        examination_id=booking.slot.examination_id).all()
    return render_template("examiner_rubrics.html",
                           booking=booking,
                           rubrics=rubrics,
                           booking_id=booking_id)

# ─── STUDENTS ─────────────────────────────────────────────────────────────────

@app.route("/student_dashboard/<int:student_id>")
def student_dashboard(student_id):
    slots = Slot.query.filter(Slot.available_seats > 0).all()
    examinations = Examination.query.all()
    my_bookings = Booking.query.filter_by(student_id=student_id).all()
    return render_template("student_dashboard.html",
                           slots=slots,
                           examinations=examinations,
                           student_id=student_id,
                           my_bookings=my_bookings)

@app.route("/student_view_exam/<int:exam_id>/<int:student_id>")
def student_view_exam(exam_id, student_id):
    examination = Examination.query.get(exam_id)
    slots = Slot.query.filter_by(examination_id=exam_id).filter(Slot.available_seats > 0).all()
    return render_template("student_view_exam.html",
                           examination=examination,
                           slots=slots,
                           student_id=student_id)

@app.route("/book/<int:id>/<int:student_id>")
def book_slot(id, student_id):
    slot = Slot.query.get(id)
    if slot.available_seats <= 0:
        return redirect(f"/student_dashboard/{student_id}")
    # Prevent duplicate bookings for the same examination
    existing = Booking.query.join(Slot).filter(
        Booking.student_id == student_id,
        Slot.examination_id == slot.examination_id,
        Booking.status == "Booked").first()
    if existing:
        return redirect(f"/student_dashboard/{student_id}")
    booking = Booking(student_id=student_id, slot_id=id,
                      booking_date=datetime.now(), status="Booked")
    slot.available_seats -= 1
    if slot.available_seats == 0:
        slot.status = "Full"
    db.session.add(booking)
    db.session.commit()
    return redirect(f"/student_dashboard/{student_id}")

@app.route("/cancel_booking/<int:booking_id>", methods=["POST"])
def cancel_booking(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return redirect("/login")
    student_id = booking.student_id
    booking.status = "Cancelled"
    slot = Slot.query.get(booking.slot_id)
    slot.available_seats += 1
    if slot.status == "Full":
        slot.status = "Available"
    db.session.commit()
    return redirect(f"/student_bookings/{student_id}")

@app.route("/student_history/<int:student_id>")
def student_history(student_id):
    evaluations = Evaluation.query.join(Booking).filter(
        Booking.student_id == student_id).all()
    return render_template("student_history.html",
                           evaluations=evaluations,
                           student_id=student_id)

@app.route("/student_bookings/<int:student_id>")
def student_bookings(student_id):
    bookings = Booking.query.filter_by(student_id=student_id).all()
    return render_template("student_booking.html",
                           bookings=bookings,
                           student_id=student_id)

@app.route("/student_profile/<int:student_id>", methods=["GET", "POST"])
def student_profile(student_id):
    user = User.query.get(student_id)
    if request.method == "POST":
        user.username = request.form["username"]
        user.email = request.form["email"]
        user.contact_no = request.form["contact_no"]
        db.session.commit()
        return redirect(f"/student_dashboard/{student_id}")
    return render_template("student_profile.html", user=user, student_id=student_id)

@app.route("/logout")
def logout():
    return redirect("/login")

if __name__ == '__main__':
    app.run()
