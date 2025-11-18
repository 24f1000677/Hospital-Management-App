from flask import Blueprint, request, jsonify
from app.models import Appointment, db, Doctor, Availability, Department, User
from datetime import datetime

bp = Blueprint('api', __name__)

@bp.route('/appointments', methods=['GET', 'POST'])
def appointments():
    if request.method == 'GET':
        appts = Appointment.query.all()
        data = []
        for a in appts:
            data.append({
                "id": a.id,
                "patient_id": a.patient_id,
                "doctor_id": a.doctor_id,
                "department_id": a.department_id,
                "date": a.date.isoformat() if a.date else None,
                "status": a.status
            })
        return jsonify(data), 200

    if request.method == 'POST':
        payload = request.get_json() or {}
        required = ['patient_id', 'doctor_id', 'date']
        for k in required:
            if k not in payload:
                return jsonify({"error": f"{k} is required"}), 400
        try:
            date = datetime.fromisoformat(payload['date']).date()
        except Exception:
            return jsonify({"error": "Invalid date format; use ISO YYYY-MM-DD"}), 400
        a = Appointment(
            patient_id=int(payload['patient_id']),
            doctor_id=int(payload['doctor_id']),
            department_id=int(payload.get('department_id')) if payload.get('department_id') else None,
            date=date,
            status=payload.get('status','scheduled')
        )
        db.session.add(a)
        db.session.commit()
        return jsonify({"id": a.id}), 201

@bp.route('/appointments/<int:id>', methods=['PUT', 'DELETE'])
def appointment_detail(id):
    a = Appointment.query.get_or_404(id)
    if request.method == 'PUT':
        payload = request.get_json() or {}
        if 'status' in payload:
            a.status = payload['status']
        db.session.commit()
        return jsonify({"msg":"updated"}), 200
    if request.method == 'DELETE':
        db.session.delete(a)
        db.session.commit()
        return jsonify({"msg":"deleted"}), 200

@bp.route('/departments/<int:dept_id>/doctors', methods=['GET'])
def dept_doctors(dept_id):
    docs = Doctor.query.filter_by(department_id=dept_id).all()
    out = []
    for d in docs:
        u = User.query.get(d.user_id)
        out.append({"id": d.id, "username": u.username if u else None})
    return jsonify(out), 200

@bp.route('/doctors/<int:doc_id>/availability', methods=['GET'])
def doctor_availability(doc_id):
    avs = Availability.query.filter_by(doctor_id=doc_id, is_booked=False).all()
    out = []
    for a in avs:
        out.append({"id": a.id, "date": str(a.date), "start_time": str(a.start_time) if a.start_time else None})
    return jsonify(out), 200
