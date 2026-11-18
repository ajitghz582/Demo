from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)
    contact_no = db.Column(db.String, nullable=False)
    department = db.Column(db.String, nullable=True)
    status = db.Column(db.String, nullable=False)

class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    code = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String, nullable=False)

class Examination(db.Model):
    __tablename__ = "examinations"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    date = db.Column(db.String, nullable=False)
    type = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    slot_creation_start_date = db.Column(db.String, nullable=True)
    slot_creation_end_date = db.Column(db.String, nullable=True)
    slot_booking_start_date = db.Column(db.String, nullable=True)
    slot_booking_end_date = db.Column(db.String, nullable=True)
    course = db.relationship("Course", backref="examinations")

class Examination_Rubric(db.Model):
    __tablename__ = "examination_rubrics"
    id = db.Column(db.Integer, primary_key=True)
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.id'), nullable=False)
    criteria_name = db.Column(db.String, nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    weightage = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    examination = db.relationship("Examination", backref="examination_rubrics")

class Slot(db.Model):
    __tablename__ = "slots"
    id = db.Column(db.Integer, primary_key=True)
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.id'), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exam_date = db.Column(db.DateTime, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    max_students = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String, nullable=False)
    examination = db.relationship("Examination", backref="slots")
    examiner = db.relationship("User", foreign_keys=[examiner_id])

class Booking(db.Model):
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('slots.id'), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String, nullable=False)
    slot = db.relationship("Slot", backref="bookings")
    student = db.relationship("User", foreign_keys=[student_id])

class ExaminerAssignment(db.Model):
    __tablename__ = "examiner_assignments"
    id = db.Column(db.Integer, primary_key=True)
    examiner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    examination_id = db.Column(db.Integer, db.ForeignKey("examinations.id"), nullable=False)
    examiner = db.relationship("User", foreign_keys=[examiner_id])
    examination = db.relationship("Examination", backref="assignments")

class Evaluation(db.Model):
    __tablename__ = "evaluations"
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    feedback = db.Column(db.Text)
    result = db.Column(db.String, nullable=False)
    booking = db.relationship("Booking", backref="evaluation")
    examiner = db.relationship("User", foreign_keys=[examiner_id])
