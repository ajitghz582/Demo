import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

from celery_worker import celery_app
from flask import render_template
from model import User, Booking, ExaminationSlot, Examination, Course, Evaluation

SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "1025"))
SENDER = os.environ.get("SMTP_SENDER", "noreply@emp.com")


def send_email(to_address, subject, message, content="text"):
    msg = MIMEMultipart()
    msg['To'] = to_address
    msg['From'] = SENDER
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'html' if content == "html" else 'plain'))
    try:
        s = smtplib.SMTP(host=SMTP_HOST, port=SMTP_PORT)
        s.send_message(msg)
        s.quit()
    except Exception as e:
        print(f"[Email error] {e}")
    return True


@celery_app.task
def send_daily_reminder():
    now = datetime.utcnow().date()
    bookings = Booking.query.filter_by(status='Booked').all()
    sent = 0
    for b in bookings:
        slot = ExaminationSlot.query.get(b.slot_id)
        if not slot or slot.date != now:
            continue
        student = User.query.get(b.student_id)
        exam = Examination.query.get(slot.exam_id)
        examiner = User.query.get(slot.examiner_id)
        if not student or not exam:
            continue
        body = f"""
        <h2>Examination Reminder</h2>
        <p>Dear {student.username},</p>
        <p>You have an examination today:</p>
        <ul>
          <li><strong>Exam:</strong> {exam.name}</li>
          <li><strong>Date:</strong> {slot.date}</li>
          <li><strong>Time:</strong> {slot.start_time} – {slot.end_time}</li>
          <li><strong>Examiner:</strong> {examiner.username if examiner else 'TBA'}</li>
          {'<li><strong>Meeting Link:</strong> ' + slot.meeting_link + '</li>' if slot.meeting_link else ''}
        </ul>
        <p>Good luck!</p>
        """
        send_email(student.email, f"Reminder: {exam.name} today", body, content="html")
        sent += 1
    return f"Daily reminders sent: {sent}"


@celery_app.task
def send_monthly_report():
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        return "No admin found"

    exams = Examination.query.all()
    total_evaluated = Evaluation.query.filter_by(status='Published').count()
    total_completed = Booking.query.filter_by(status='Completed').count()
    pending_evals = Evaluation.query.filter_by(status='Pending').count()

    exam_rows = []
    for e in exams:
        course = Course.query.get(e.course_id)
        bookings_count = db_count_bookings_for_exam(e.id)
        exam_rows.append({
            "name": e.name,
            "course": course.course_name if course else "",
            "type": e.exam_type,
            "bookings": bookings_count,
            "status": e.status,
        })

    # Active examiners
    examiners = User.query.filter_by(role='examiner').all()
    active_examiners = []
    for ex in examiners:
        slots = ExaminationSlot.query.filter_by(examiner_id=ex.id).all()
        evaluated = Evaluation.query.filter_by(examiner_id=ex.id).count()
        active_examiners.append({
            "name": ex.username,
            "slots": len(slots),
            "evaluated": evaluated,
        })
    active_examiners.sort(key=lambda x: x["evaluated"], reverse=True)

    html = render_template(
        'monthly_report.html',
        generated_on=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        stats={
            "total_exams": len(exams),
            "total_evaluated": total_evaluated,
            "total_completed": total_completed,
            "pending_evaluations": pending_evals,
        },
        active_examiners=active_examiners[:5],
        exams=exam_rows,
    )
    send_email(admin.email, "Monthly Examination Report", html, content="html")
    return "Monthly report sent"


def db_count_bookings_for_exam(exam_id):
    slots = ExaminationSlot.query.filter_by(exam_id=exam_id).all()
    slot_ids = [s.id for s in slots]
    if not slot_ids:
        return 0
    return Booking.query.filter(Booking.slot_id.in_(slot_ids)).count()


@celery_app.task
def export_exam_history(user_id):
    student = User.query.get(user_id)
    if not student:
        return "Student not found"

    bookings = Booking.query.filter_by(student_id=user_id).all()
    records = []
    for b in bookings:
        slot = ExaminationSlot.query.get(b.slot_id)
        exam = Examination.query.get(slot.exam_id) if slot else None
        course = Course.query.get(exam.course_id) if exam else None
        examiner = User.query.get(slot.examiner_id) if slot else None
        ev = Evaluation.query.filter_by(booking_id=b.id).first()
        records.append({
            "exam_name": exam.name if exam else "N/A",
            "course": course.course_name if course else "N/A",
            "exam_type": exam.exam_type if exam else "N/A",
            "date": str(slot.date) if slot else "N/A",
            "examiner": examiner.username if examiner else "N/A",
            "marks": ev.total_marks if ev else None,
            "max_marks": exam.max_marks if exam else "N/A",
            "booking_status": b.status,
        })

    html = render_template(
        'export.html',
        username=student.username,
        total_records=len(records),
        records=records,
    )
    send_email(student.email, "Your Examination History Export", html, content="html")
    return f"Export sent to {student.email}"
