from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import User, MentorStudent
from flask_jwt_extended import jwt_required, get_jwt_identity

users_bp = Blueprint('users', __name__)

@users_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    users = User.query.all()
    return jsonify([{"id": u.id, "name": u.name, "email": u.email, "role": u.role} for u in users]), 200

@users_bp.route('/users/<int:id>', methods=['GET'])
@jwt_required()
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify({"id": user.id, "name": user.name, "email": user.email, "role": user.role}), 200

@users_bp.route('/my-students', methods=['GET'])
@jwt_required()
def get_my_students():
    current_user_id = int(get_jwt_identity())
    students = db.session.query(User).join(MentorStudent, MentorStudent.student_id == User.id).filter(MentorStudent.mentor_id == current_user_id).all()
    return jsonify([{"id": s.id, "name": s.name, "email": s.email} for s in students]), 200

@users_bp.route('/my-mentor', methods=['GET'])
@jwt_required()
def get_my_mentor():
    current_user_id = int(get_jwt_identity())
    relation = MentorStudent.query.filter_by(student_id=current_user_id).first()
    if not relation:
        return jsonify({"error": "Nenhum mentor atribuído"}), 404
    mentor = User.query.get(relation.mentor_id)
    return jsonify({"name": mentor.name, "whatsapp": mentor.whatsapp}), 200

@users_bp.route('/mentor/<int:id>/students', methods=['GET'])
@jwt_required()
def get_mentor_students(id):
    students = db.session.query(User).join(MentorStudent, MentorStudent.student_id == User.id).filter(MentorStudent.mentor_id == id).all()
    return jsonify([{"id": s.id, "name": s.name, "email": s.email} for s in students]), 200

@users_bp.route('/assign-mentor', methods=['POST'])
@jwt_required()
def assign_mentor():
    data = request.get_json()
    student_id = data.get('student_id')
    mentor_id = data.get('mentor_id')
    
    if MentorStudent.query.filter_by(student_id=student_id).first():
        return jsonify({"error": "Aluno já possui um mentor"}), 400
        
    assignment = MentorStudent(student_id=student_id, mentor_id=mentor_id)
    db.session.add(assignment)
    db.session.commit()
    return jsonify({"message": "Mentor atribuído com sucesso"}), 201