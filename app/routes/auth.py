from flask import Blueprint, render_template, redirect, url_for, request, flash
from app.models import User, Patient, Doctor, Department
from app import db
from flask_login import login_user, logout_user, login_required, current_user

bp = Blueprint('auth', __name__)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    # if already logged-in, send to appropriate dashboard
    if current_user.is_authenticated:
        if getattr(current_user, "role", None) == 'admin':
            return redirect(url_for('admin.dashboard'))
        if getattr(current_user, "role", None) == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        return redirect(url_for('patient.dashboard'))

    # load departments for the form (used when registering doctor)
    departments = Department.query.all()

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', '').strip()
        dept_id = request.form.get('department_id')  # may be None

        errors = []
        if not username:
            errors.append("Username required")
        if not email or '@' not in email:
            errors.append("Valid email required")
        if not password or len(password) < 4:
            errors.append("Password required (min 4 characters)")
        if role not in ['patient', 'doctor', 'admin']:
            errors.append("Please select a valid role")

        # if doctor, department must be chosen
        if role == 'doctor':
            if not dept_id:
                errors.append("Please select a department for the doctor")

        if User.query.filter_by(username=username).first():
            errors.append("Username already exists")
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered")

        if errors:
            # return departments again so the form can repopulate the dropdown
            return render_template('auth/register.html', errors=errors, form=request.form, departments=departments)

        # create user and related profile
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        if role == 'patient':
            p = Patient(user_id=user.id)
            db.session.add(p)
            db.session.commit()
        elif role == 'doctor':
            # create doctor with department assignment if provided
            d = Doctor(user_id=user.id, department_id=int(dept_id) if dept_id else None)
            db.session.add(d)
            db.session.commit()

        flash("Registration successful. Please log in.")
        return redirect(url_for('auth.login'))

    # GET -> render form with departments
    return render_template('auth/register.html', departments=departments)

@bp.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('patient.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            return render_template('auth/login.html', error='Invalid credentials')
        login_user(user)
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        if user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        return redirect(url_for('patient.dashboard'))
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
