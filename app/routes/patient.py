from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user
from app.models import Patient, Department, Doctor, Appointment, Availability, PatientHistory
from app import db
from datetime import datetime
from flask import abort

bp = Blueprint('patient', __name__)

def patient_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*a, **k):
        if not current_user.is_authenticated or current_user.role != 'patient':
            return redirect(url_for('auth.login'))
        return fn(*a, **k)
    return wrapper

@bp.route('/')
@patient_required
def dashboard():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    appts = []
    if patient:
        appts = Appointment.query.filter_by(patient_id=patient.id).all()
    departments = Department.query.all()
    return render_template('patient/dashboard.html', appointments=appts, departments=departments)

@bp.route('/book', methods=['GET','POST'])
@patient_required
def book():
    departments = Department.query.all()
    if request.method == 'POST':
        dept_id = request.form.get('department_id')
        doctor_id = request.form.get('doctor_id')
        avail_id = request.form.get('availability_id')
        errors = []
        if not dept_id:
            errors.append('Department required')
        if not doctor_id:
            errors.append('Doctor required')
        if not avail_id:
            errors.append('Availability slot required')
        if errors:
            return render_template('patient/book.html', errors=errors, departments=departments)
        avail = Availability.query.get(int(avail_id))
        if not avail or avail.is_booked:
            errors.append('Selected slot no longer available')
            return render_template('patient/book.html', errors=errors, departments=departments)
        patient = Patient.query.filter_by(user_id=current_user.id).first()
        appt = Appointment(patient_id=patient.id, doctor_id=avail.doctor_id, department_id=int(dept_id),
                           date=avail.date, start_time=avail.start_time, end_time=avail.end_time, status='scheduled')
        avail.is_booked = True
        db.session.add(appt)
        db.session.commit()
        flash('Appointment booked')
        return redirect(url_for('patient.dashboard'))
    return render_template('patient/book.html', departments=departments)

@bp.route('/history')
@patient_required
def history():
    """
    Show the logged-in patient's treatment / visit history.
    Works even if PatientHistory fields vary across your model.
    """
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        return redirect(url_for('auth.login'))

    # Try to order by created_at if it exists, otherwise by id desc
    # Use getattr checks to avoid attribute errors if model differs.
    try:
        histories = PatientHistory.query.filter_by(patient_id=patient.id).order_by(PatientHistory.created_at.desc()).all()
    except Exception:
        histories = PatientHistory.query.filter_by(patient_id=patient.id).order_by(PatientHistory.id.desc()).all()

    return render_template('patient/history.html', histories=histories, patient=patient)


@bp.route('/appointments/<int:appt_id>/reschedule', methods=['GET','POST'])
@patient_required
def reschedule_appointment(appt_id):
    """
    Patient reschedules by selecting an available slot for a chosen doctor.
    """
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        return abort(403)

    appt = Appointment.query.get_or_404(appt_id)
    # ensure this appointment belongs to the logged-in patient
    if appt.patient_id != patient.id:
        return abort(403)

    departments = Department.query.all()
    doctors = Doctor.query.all()

    # If POST -> user submitted chosen availability_id
    if request.method == 'POST':
        avail_id = request.form.get('availability_id')
        if not avail_id:
            flash('Please select an available slot.')
            return render_template('patient/reschedule.html', appt=appt, departments=departments, doctors=doctors, slots=[])

        avail = Availability.query.get(int(avail_id))
        if not avail or avail.is_booked:
            flash('Selected slot is no longer available. Choose another.')
            return render_template('patient/reschedule.html', appt=appt, departments=departments, doctors=doctors, slots=[])

        # ensure we have doctor object for this availability
        avail_doctor = Doctor.query.get(avail.doctor_id)
        # Free previous availability if we can find it (match by doctor/date/start_time)
        try:
            prev_avail = Availability.query.filter_by(doctor_id=appt.doctor_id, date=appt.date, start_time=appt.start_time).first()
            if prev_avail:
                prev_avail.is_booked = False
                db.session.add(prev_avail)
        except Exception:
            # ignore if previous slot not found
            pass

        # Book new availability
        avail.is_booked = True

        # update appointment fields using avail + avail_doctor
        appt.doctor_id = avail.doctor_id
        if avail_doctor:
            appt.department_id = avail_doctor.department_id if hasattr(avail_doctor, 'department_id') else appt.department_id
        appt.date = avail.date
        appt.start_time = avail.start_time
        appt.end_time = avail.end_time
        appt.status = 'scheduled'

        db.session.add(avail)
        db.session.add(appt)
        db.session.commit()

        flash('Appointment rescheduled to selected available slot.')
        return redirect(url_for('patient.dashboard'))

    # GET -> need to show departments/doctors and (optionally) slots for the currently selected doctor
    # If the page receives query params doctor_id, we will show slots for that doctor; otherwise show none.
    selected_doc_id = request.args.get('doctor_id', type=int)
    slots = []
    if selected_doc_id:
        slots = Availability.query.filter_by(doctor_id=selected_doc_id, is_booked=False).order_by(Availability.date, Availability.start_time).all()
        # attach doctor object to each slot so template can use slot.doctor safely
        for s in slots:
            s.doctor = Doctor.query.get(s.doctor_id)

    return render_template('patient/reschedule.html',
                           appt=appt, doctors=doctors, departments=departments, slots=slots, selected_doc_id=selected_doc_id)
