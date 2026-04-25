from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import User, Meeting, Class, ClassEnrollment
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

academic_bp = Blueprint('academic', __name__)

@academic_bp.route('/meetings', methods=['POST', 'GET'])
@jwt_required()
def handle_meetings():
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    role = claims.get('role')

    if request.method == 'POST':
        if role not in ['mentor', 'teacher']:
            return jsonify({"error": "Apenas mentores ou professores podem criar reuniões"}), 403
            
        data = request.get_json()
        new_meeting = Meeting(
            mentor_id=current_user_id,
            student_id=data.get('student_id'),
            datetime=data.get('datetime'),
            description=data.get('description'),
            link=data.get('link')
        )
        db.session.add(new_meeting)
        db.session.commit()
        return jsonify({"message": "Reunião criada com sucesso"}), 201

    if request.method == 'GET':
        if role in ['mentor', 'teacher']:
            meetings = Meeting.query.filter_by(mentor_id=current_user_id).all()
        elif role == 'student':
            meetings = Meeting.query.filter_by(student_id=current_user_id).all()
        else:
            meetings = []
        return jsonify([{"id": m.id, "datetime": m.datetime, "description": m.description, "link": m.link} for m in meetings]), 200

@academic_bp.route('/classes', methods=['POST', 'GET'])
@jwt_required()
def handle_classes():
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    role = claims.get('role')
    
    if request.method == 'POST':
        if role not in ['teacher', 'mentor']:
            return jsonify({"error": "Acesso negado para criação de aulas"}), 403
            
        data = request.get_json()
        new_class = Class(
            teacher_id=current_user_id,
            title=data.get('title'),
            description=data.get('description'),
            datetime=data.get('datetime'),
            link=data.get('link')
        )
        db.session.add(new_class)
        db.session.commit()
        return jsonify({"message": "Aula criada com sucesso"}), 201
        
    if request.method == 'GET':
        classes = db.session.query(Class, User.name.label('teacher_name')).join(User, Class.teacher_id == User.id).all()
        return jsonify([{"id": c.Class.id, "title": c.Class.title, "datetime": c.Class.datetime, "link": c.Class.link, "teacher_name": c.teacher_name} for c in classes]), 200

@academic_bp.route('/classes/<int:id>/enroll', methods=['POST'])
@jwt_required()
def enroll_class(id):
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    
    if claims.get('role') != 'student':
        return jsonify({"error": "Apenas alunos podem se inscrever"}), 403

    if ClassEnrollment.query.filter_by(class_id=id, student_id=current_user_id).first():
        return jsonify({"error": "Você já está inscrito nesta aula"}), 400

    enrollment = ClassEnrollment(class_id=id, student_id=current_user_id)
    db.session.add(enrollment)
    db.session.commit()
    return jsonify({"message": "Inscrição realizada com sucesso"}), 201