from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os, secrets

db = SQLAlchemy()
login = LoginManager()
login.login_view = "auth.login"


def create_app():
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    template_dir = os.path.join(BASE_DIR, 'templates')
    static_dir = os.path.join(BASE_DIR, 'static')

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    if os.environ.get('FLASK_SECRET'):
        app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET')
    else:
        # new random secret on each start -> forces logout after restart
        app.config['SECRET_KEY'] = secrets.token_urlsafe(32)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    print("Database path:", app.config['SQLALCHEMY_DATABASE_URI'])
    print("Instance path:", app.instance_path)

    db.init_app(app)
    login.init_app(app)

    from app.routes.auth import bp as auth_bp
    from app.routes.admin import bp as admin_bp
    from app.routes.doctor import bp as doctor_bp
    from app.routes.patient import bp as patient_bp
    from app.routes.api import bp as api_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(patient_bp, url_prefix='/patient')
    app.register_blueprint(api_bp, url_prefix='/api')

     # 🔽🔽🔽 ADD THIS BLOCK HERE 🔽🔽🔽
    @app.route('/')
    def index():
        from flask_login import current_user
        from flask import redirect, url_for

        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            if current_user.role == 'doctor':
                return redirect(url_for('doctor.dashboard'))
            return redirect(url_for('patient.dashboard'))
        
        return redirect(url_for('auth.login'))
    # 🔼🔼🔼 END BLOCK 🔼🔼🔼

    # friendly 403 handler: redirect anonymous -> login, show helpful page to logged-in users
    @app.errorhandler(403)
    def handle_403(err):
        from flask import render_template, redirect, url_for
        from flask_login import current_user
        # anonymous users -> send to login
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        # logged-in but wrong role -> show helpful page with logout/dashboard links
        return render_template('errors/403.html', user=current_user), 403


    with app.app_context():
        from app import models
        db.create_all()

        from app.models import User, Department
        if not User.query.filter_by(username='admin').first():
            u = User(username='admin', email='admin@example.com')
            u.set_password('adminpass')
            u.role = 'admin'
            db.session.add(u)
        if Department.query.count() == 0:
            for name in ['Cardiology','Oncology','General']:
                db.session.add(Department(name=name, description=f'{name} department'))
        db.session.commit()
    # inside create_app(), after app initialization and config
    app.jinja_env.globals['getattr'] = getattr

    return app
