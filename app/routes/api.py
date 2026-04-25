import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.extensions import db, bcrypt
from app.models.models import User, MentorStudent, Meeting, Class, ClassEnrollment, File
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

api_bp = Blueprint('api', __name__)

@api_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    # Verifica se o email já existe
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({"error": "Email já cadastrado"}), 400

    hashed_pw = bcrypt.generate_password_hash(data.get('password')).decode('utf-8')
    new_user = User(
        name=data.get('name'),
        email=data.get('email'),
        password_hash=hashed_pw,
        role=data.get('role')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Usuário registrado com sucesso"}), 201

@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if user and bcrypt.check_password_hash(user.password_hash, data.get('password')):
        token = create_access_token(identity={"id": user.id, "role": user.role})
        return jsonify({"access_token": token}), 200
    return jsonify({"error": "Credenciais inválidas"}), 401

@api_bp.route('/assign-mentor', methods=['POST'])
@jwt_required()
def assign_mentor():
    data = request.get_json()
    student_id = data.get('student_id')
    mentor_id = data.get('mentor_id')
    
    # Previne que um aluno tenha mais de um mentor
    if MentorStudent.query.filter_by(student_id=student_id).first():
        return jsonify({"error": "Aluno já possui um mentor"}), 400
        
    assignment = MentorStudent(student_id=student_id, mentor_id=mentor_id)
    db.session.add(assignment)
    db.session.commit()
    return jsonify({"message": "Mentor atribuído com sucesso"}), 201

@api_bp.route('/classes', methods=['POST', 'GET'])
@jwt_required()
def handle_classes():
    current_user = get_jwt_identity()
    
    if request.method == 'POST':
        if current_user['role'] != 'teacher':
            return jsonify({"error": "Apenas professores podem criar aulas"}), 403
            
        data = request.get_json()
        new_class = Class(
            teacher_id=current_user['id'],
            title=data.get('title'),
            description=data.get('description'),
            datetime=data.get('datetime'), # Ex: '2026-04-25T10:00:00'
            link=data.get('link')
        )
        db.session.add(new_class)
        db.session.commit()
        return jsonify({"message": "Aula criada com sucesso"}), 201
        
    if request.method == 'GET':
        classes = Class.query.all()
        return jsonify([{"id": c.id, "title": c.title, "link": c.link} for c in classes]), 200

@api_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    current_user = get_jwt_identity()
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400
        
    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    new_file = File(
        filename=filename,
        path=filepath,
        owner_id=current_user['id'],
        class_id=request.form.get('class_id')
    )
    db.session.add(new_file)
    db.session.commit()
    
    return jsonify({"message": "Arquivo enviado com sucesso", "path": filepath}), 201