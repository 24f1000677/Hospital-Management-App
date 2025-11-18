from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import current_user
from app.models import User, Department, Doctor
from app import db
# --- Admin: Manage Appointments ---
from flask import jsonify
from app.models import Appointment, Patient, Doctor, Department, Availability
from datetime import datetime, time

bp = Blueprint('admin', __name__)

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*a, **k):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return redirect(url_for('auth.login'))
        return fn(*a, **k)
    return wrapper

@bp.route('/')
@admin_required
def dashboard():
    users = User.query.all()
    departments = Department.query.all()
    doctors = Doctor.query.all()
    return render_template('admin/dashboard.html', users=users, departments=departments, doctors=doctors)

@bp.route('/departments/add', methods=['POST'])
@admin_required
def add_department():
    name = request.form.get('name','').strip()
    if not name:
        flash('Department name required')
        return redirect(url_for('admin.dashboard'))
    if Department.query.filter_by(name=name).first():
        flash('Department already exists')
        return redirect(url_for('admin.dashboard'))
    d = Department(name=name, description=request.form.get('description',''))
    db.session.add(d)
    db.session.commit()
    flash('Department added')
    return redirect(url_for('admin.dashboard'))


@bp.route('/doctors/add', methods=['POST'])
@admin_required
def add_doctor():
    username = request.form.get('username','').strip()
    email = request.form.get('email','').strip()
    password = request.form.get('password','').strip()
    department_id = request.form.get('department_id')
    specialization = request.form.get('specialization','').strip()
    exp = request.form.get('experience_years','').strip()

    errors = []
    if not username:
        errors.append('Username required for doctor.')
    if not email or '@' not in email:
        errors.append('Valid email required.')
    if not password or len(password) < 4:
        errors.append('Password min length 4 required.')
    if not department_id:
        errors.append('Department must be selected.')

    if User.query.filter_by(username=username).first():
        errors.append('Username already exists.')
    if User.query.filter_by(email=email).first():
        errors.append('Email already registered.')

    if errors:
        for e in errors:
            flash(e)
        return redirect(url_for('admin.dashboard'))

    # create the user and doctor profile
    user = User(username=username, email=email, role='doctor')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    doctor = Doctor(user_id=user.id,
                    department_id=int(department_id),
                    specialization=specialization or None,
                    experience_years=int(exp) if exp.isdigit() else None)
    db.session.add(doctor)
    db.session.commit()

    flash('Doctor account created.')
    return redirect(url_for('admin.dashboard'))


# ----------------------------
# Edit doctor
# ----------------------------
@bp.route('/doctors/<int:doctor_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_doctor(doctor_id):
    doc = Doctor.query.get_or_404(doctor_id)
    user = User.query.get(doc.user_id)
    departments = Department.query.all()

    if request.method == 'POST':
        # gather fields
        username = request.form.get('username','').strip()
        email = request.form.get('email','').strip()
        password = request.form.get('password','').strip()
        department_id = request.form.get('department_id')
        specialization = request.form.get('specialization','').strip()
        exp = request.form.get('experience_years','').strip()

        errors = []
        if not username:
            errors.append('Username required.')
        if not email or '@' not in email:
            errors.append('Valid email required.')
        if not department_id:
            errors.append('Department must be selected.')

        # check unique username/email (skip current user's own record)
        u_conflict = User.query.filter(User.username==username, User.id!=user.id).first()
        if u_conflict:
            errors.append('Username already taken by another user.')
        e_conflict = User.query.filter(User.email==email, User.id!=user.id).first()
        if e_conflict:
            errors.append('Email already registered to another user.')

        if errors:
            for e in errors:
                flash(e)
            return render_template('admin/edit_doctor.html', doc=doc, user=user, departments=departments)

        # update user
        user.username = username
        user.email = email
        if password:
            user.set_password(password)
        db.session.add(user)

        # update doctor record
        doc.department_id = int(department_id)
        doc.specialization = specialization or None
        doc.experience_years = int(exp) if exp.isdigit() else None
        db.session.add(doc)

        db.session.commit()
        flash('Doctor updated.')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/edit_doctor.html', doc=doc, user=user, departments=departments)


# ----------------------------
# Delete doctor (removes doctor row and corresponding user account)
# ----------------------------
@bp.route('/doctors/<int:doctor_id>/delete', methods=['POST'])
@admin_required
def delete_doctor(doctor_id):
    doc = Doctor.query.get_or_404(doctor_id)
    user = User.query.get(doc.user_id)

    # remove doctor row
    db.session.delete(doc)
    # remove user row
    if user:
        db.session.delete(user)
    db.session.commit()
    flash('Doctor account deleted.')
    return redirect(url_for('admin.dashboard'))

# ---------- PATIENT: EDIT ----------
@bp.route('/patients/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_patient(user_id):
    """Admin edits a patient user's basic info."""
    user = User.query.get_or_404(user_id)

    # Only allow editing real patients
    if user.role != 'patient':
        abort(404)

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()

        errors = []
        if not username:
            errors.append('Username is required.')
        if not email or '@' not in email:
            errors.append('A valid email is required.')

        # uniqueness checks (ignore current user)
        existing_username = User.query.filter(
            User.username == username,
            User.id != user.id
        ).first()
        if existing_username:
            errors.append('Username is already taken.')

        existing_email = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()
        if existing_email:
            errors.append('Email is already registered.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            # re-render form with previous values
            return render_template('admin/edit_patient.html', user=user)

        # apply changes
        user.username = username
        user.email = email
        db.session.commit()
        flash('Patient details updated.', 'success')
        return redirect(url_for('admin.dashboard'))

    # GET – show form
    return render_template('admin/edit_patient.html', user=user)


# ---------- PATIENT: DELETE ----------
@bp.route('/patients/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_patient(user_id):
    """Admin deletes a patient (user + patient record + their appointments)."""
    user = User.query.get_or_404(user_id)

    if user.role != 'patient':
        abort(404)

    # find patient profile
    patient = Patient.query.filter_by(user_id=user.id).first()

    if patient:
        # delete this patient's appointments
        Appointment.query.filter_by(patient_id=patient.id).delete()
        # delete patient profile
        db.session.delete(patient)

    # finally delete user account
    db.session.delete(user)
    db.session.commit()
    flash('Patient deleted successfully.', 'success')
    return redirect(url_for('admin.dashboard'))

# ---------- DOCTOR APPOINTMENTS (ADMIN VIEW) ----------

@bp.route('/doctors/<int:doctor_id>/appointments')
@admin_required
def manage_doctor_appointments(doctor_id):
    """Admin view of all appointments for a given doctor."""
    doctor = Doctor.query.get_or_404(doctor_id)
    appts = (
        Appointment.query
        .filter_by(doctor_id=doctor.id)
        .order_by(Appointment.date, Appointment.start_time)
        .all()
    )
    return render_template(
        'admin/manage_appointments.html',
        doctor=doctor,
        appointments=appts
    )


@bp.route('/appointments/<int:appt_id>/cancel_by_admin', methods=['POST'])
@admin_required
def admin_cancel_appointment(appt_id):
    """Admin cancels an appointment for any doctor."""
    appt = Appointment.query.get_or_404(appt_id)

    # keep doctor_id before we change anything, for redirect
    doctor_id = appt.doctor_id

    appt.status = 'cancelled'
    db.session.commit()
    flash('Appointment cancelled.', 'success')

    return redirect(url_for('admin.manage_doctor_appointments',
                            doctor_id=doctor_id))

@bp.route('/appointments')
@admin_required
def appointments_list():
    # show all appointments with related user info
    appts = Appointment.query.order_by(Appointment.date.desc(), Appointment.start_time).all()
    # eager fetch helper via templates
    return render_template('admin/appointments.html', appointments=appts)

@bp.route('/appointments/<int:appt_id>/edit', methods=['GET','POST'])
@admin_required
def edit_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    patients = Patient.query.all()
    doctors = Doctor.query.all()
    departments = Department.query.all()

    if request.method == 'POST':
        # gather fields
        patient_id = request.form.get('patient_id')
        doctor_id = request.form.get('doctor_id')
        department_id = request.form.get('department_id')
        date_str = request.form.get('date')
        start_str = request.form.get('start_time')
        end_str = request.form.get('end_time')
        status = request.form.get('status','scheduled')

        errors = []
        if not patient_id:
            errors.append('Patient required.')
        if not doctor_id:
            errors.append('Doctor required.')
        if not department_id:
            errors.append('Department required.')
        if not date_str:
            errors.append('Date required.')
        if not start_str or not end_str:
            errors.append('Start and end time required.')

        # parse date/time
        date_obj = None
        start_obj = None
        end_obj = None
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_obj = datetime.strptime(start_str, "%H:%M").time()
            end_obj = datetime.strptime(end_str, "%H:%M").time()
        except Exception:
            errors.append('Invalid date/time format.')

        if errors:
            for e in errors:
                flash(e)
            return render_template('admin/edit_appointment.html',
                                   appt=appt, patients=patients, doctors=doctors, departments=departments)

        # apply updates
        appt.patient_id = int(patient_id)
        appt.doctor_id = int(doctor_id)
        appt.department_id = int(department_id)
        appt.date = date_obj
        appt.start_time = start_obj
        appt.end_time = end_obj
        appt.status = status

        db.session.add(appt)
        db.session.commit()
        flash('Appointment updated.')
        return redirect(url_for('admin.appointments_list'))

    return render_template('admin/edit_appointment.html',
                           appt=appt, patients=patients, doctors=doctors, departments=departments)


@bp.route('/appointments/<int:appt_id>/delete', methods=['POST'])
@admin_required
def delete_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    db.session.delete(appt)
    db.session.commit()
    flash('Appointment deleted.')
    return redirect(url_for('admin.appointments_list'))
