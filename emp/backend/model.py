from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='student')  # 'admin', 'examiner', 'student'
    active = db.Column(db.Boolean, default=True)

    examiner_profile = db.relationship('ExaminerProfile', backref='user', uselist=False)
    bookings = db.relationship('Booking', backref='student', lazy=True,
                               foreign_keys='Booking.student_id')
    slots = db.relationship('ExaminationSlot', backref='slot_examiner', lazy=True,
                            foreign_keys='ExaminationSlot.examiner_id')
    evaluations_given = db.relationship('Evaluation', backref='eval_examiner', lazy=True,
                                        foreign_keys='Evaluation.examiner_id')


class ExaminerProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    department = db.Column(db.String(100))
    contact = db.Column(db.String(100))


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    course_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # 'active', 'inactive'

    examinations = db.relationship('Examination', backref='course', lazy=True)


class Examination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)  # Viva / Practical / Project Demo / Assessment
    duration = db.Column(db.Integer, nullable=False)       # minutes
    max_marks = db.Column(db.Float, nullable=False)
    slot_creation_start = db.Column(db.DateTime)
    slot_creation_end = db.Column(db.DateTime)
    booking_start = db.Column(db.DateTime)
    booking_end = db.Column(db.DateTime)
    # Draft / Slot Creation / Booking Open / Closed / Completed
    status = db.Column(db.String(30), default='Draft')

    rubrics = db.relationship('ExaminationRubric', backref='examination', lazy=True,
                              cascade='all, delete-orphan')
    slots = db.relationship('ExaminationSlot', backref='examination', lazy=True)


class ExaminationRubric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('examination.id'), nullable=False)
    criterion_name = db.Column(db.String(150), nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    weightage = db.Column(db.Float, default=1.0)
    description = db.Column(db.Text)


class ExaminationSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('examination.id'), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Available')  # Available / Full / Cancelled / Completed
    meeting_link = db.Column(db.String(300))

    bookings = db.relationship('Booking', backref='slot', lazy=True)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('examination_slot.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Booked')  # Booked / Cancelled / Completed

    evaluation = db.relationship('Evaluation', backref='booking', uselist=False)


class Evaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False, unique=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_marks = db.Column(db.Float)
    remarks = db.Column(db.Text)
    eval_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending')  # Pending / Published
