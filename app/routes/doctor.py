from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import current_user
from datetime import datetime
from app.models import Patient, Department, Doctor, Appointment, Availability, PatientHistory
from app import db

bp = Blueprint('doctor', __name__)

def doctor_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*a, **k):
        if not current_user.is_authenticated or current_user.role != 'doctor':
            return redirect(url_for('auth.login'))
        return fn(*a, **k)
    return wrapper

@bp.route('/')
@doctor_required
def dashboard():
    # get doctor by logged-in user's id (user.id)
    doc = Doctor.query.filter_by(user_id=current_user.id).first()
    appts = []
    if doc:
        appts = Appointment.query.filter_by(doctor_id=doc.id).order_by(
            Appointment.date.desc(), Appointment.start_time
        ).all()
    return render_template('doctor/dashboard.html', appointments=appts)

@bp.route('/availability', methods=['GET', 'POST'])
@doctor_required
def availability():
    doc = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doc:
        return abort(403)

    if request.method == 'POST':
        date_str = request.form.get('date')
        start_str = request.form.get('start_time')
        end_str = request.form.get('end_time')

        errors = []
        if not date_str:
            errors.append('Date required')
        if not start_str or not end_str:
            errors.append('Start and end time required')

        if errors:
            avails = Availability.query.filter_by(doctor_id=doc.id).all()
            return render_template('doctor/availability.html', errors=errors, avails=avails)

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_obj = datetime.strptime(start_str, "%H:%M").time()
            end_obj = datetime.strptime(end_str, "%H:%M").time()
        except ValueError:
            avails = Availability.query.filter_by(doctor_id=doc.id).all()
            return render_template(
                'doctor/availability.html',
                errors=["Invalid date or time format"],
                avails=avails,
            )

        a = Availability(
            doctor_id=doc.id,
            date=date_obj,
            start_time=start_obj,
            end_time=end_obj,
            is_booked=False,
        )
        db.session.add(a)
        db.session.commit()

        flash('Availability saved')
        return redirect(url_for('doctor.availability'))

    avails = Availability.query.filter_by(doctor_id=doc.id).order_by(
        Availability.date, Availability.start_time
    ).all()
    return render_template('doctor/availability.html', avails=avails)


@bp.route('/appointments/<int:appt_id>/complete', methods=['GET', 'POST'])
@doctor_required
def complete_appointment(appt_id):
    """
    Doctor completes an appointment: enter visit type, tests, diagnosis, prescription, medicines.
    Saves a PatientHistory record and marks appointment completed.
    Also shows previous history for this patient.
    """
    appt = Appointment.query.get_or_404(appt_id)
    doc = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doc:
        return abort(403)

    # ensure appointment belongs to this doctor
    if appt.doctor_id != doc.id:
        return abort(403)

    patient = Patient.query.get(appt.patient_id)

    # fetch previous history for this patient (most recent first)
    histories = []
    if patient:
        histories = (
            PatientHistory.query
            .filter_by(patient_id=patient.id)
            .order_by(PatientHistory.visit_date.desc())
            .all()
        )

    if request.method == 'POST':
        visit_type   = request.form.get('visit_type', '').strip()
        tests_done   = request.form.get('tests_done', '').strip()
        diagnosis    = request.form.get('diagnosis', '').strip()
        prescription = request.form.get('prescription', '').strip()
        medicines    = request.form.get('medicines', '').strip()
        notes        = request.form.get('notes', '').strip()

        errors = []
        if not visit_type:
            errors.append('Visit type is required.')
        if not diagnosis:
            errors.append('Diagnosis is required.')

        if errors:
            for e in errors:
                flash(e)
            return render_template(
                'doctor/complete_appointment.html',
                appt=appt,
                patient=patient,
                histories=histories,
            )

        # create patient history entry — store each field in its own column
        try:
            ph = PatientHistory(
                patient_id  = patient.id if patient else None,
                doctor_id   = doc.id,
                visit_date  = appt.date if getattr(appt, 'date', None) else datetime.utcnow(),
                visit_type  = visit_type,
                diagnosis   = diagnosis,
                prescription= prescription or None,
                tests_done  = tests_done or None,
                medicines   = medicines or None,
                notes       = notes or None,
            )

            db.session.add(ph)

            # mark appointment completed
            appt.status = 'completed'
            db.session.add(appt)

            db.session.commit()

            return render_template(
                'doctor/complete_success.html',
                appt=appt,
                history=ph,
                patient=patient,
            )

        except Exception as ex:
            db.session.rollback()
            flash('Error saving record: {}'.format(str(ex)))
            return render_template(
                'doctor/complete_appointment.html',
                appt=appt,
                patient=patient,
                histories=histories,
            )

    # GET: render form
    return render_template(
        'doctor/complete_appointment.html',
        appt=appt,
        patient=patient,
        histories=histories,
    )


# NEW: doctor view of a patient's full history
@bp.route('/patients/<int:patient_id>/history')
@doctor_required
def patient_history(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    histories = (
        PatientHistory.query
        .filter_by(patient_id=patient.id)
        .order_by(PatientHistory.visit_date.desc())
        .all()
    )
    return render_template(
        'doctor/patient_history.html',
        patient=patient,
        histories=histories,
    )
