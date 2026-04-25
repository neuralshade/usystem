import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.extensions import db, bcrypt
from app.models.models import User, MentorStudent, Meeting, Class, ClassEnrollment, File
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from app.models.models import StudyPlan, StudyTask, ExamResult

api_bp = Blueprint('api', __name__)

@api_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
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
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role, "name": user.name})
        # Correção: Enviar 'role' e 'name' diretamente na resposta da API
        return jsonify({"access_token": token, "role": user.role, "name": user.name}), 200
    return jsonify({"error": "Credenciais inválidas"}), 401

@api_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    users = User.query.all()
    return jsonify([{"id": u.id, "name": u.name, "email": u.email, "role": u.role} for u in users]), 200

@api_bp.route('/users/<int:id>', methods=['GET'])
@jwt_required()
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify({"id": user.id, "name": user.name, "email": user.email, "role": user.role}), 200

@api_bp.route('/assign-mentor', methods=['POST'])
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

@api_bp.route('/mentor/<int:id>/students', methods=['GET'])
@jwt_required()
def get_mentor_students(id):
    students = db.session.query(User).join(MentorStudent, MentorStudent.student_id == User.id).filter(MentorStudent.mentor_id == id).all()
    return jsonify([{"id": s.id, "name": s.name, "email": s.email} for s in students]), 200

@api_bp.route('/meetings', methods=['POST', 'GET'])
@jwt_required()
def handle_meetings():
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    role = claims.get('role')

    if request.method == 'POST':
        if role != 'mentor':
            return jsonify({"error": "Apenas mentores podem criar reuniões"}), 403
            
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
        if role == 'mentor':
            meetings = Meeting.query.filter_by(mentor_id=current_user_id).all()
        elif role == 'student':
            meetings = Meeting.query.filter_by(student_id=current_user_id).all()
        else:
            meetings = []
        return jsonify([{"id": m.id, "datetime": m.datetime, "description": m.description, "link": m.link} for m in meetings]), 200

@api_bp.route('/classes', methods=['POST', 'GET'])
@jwt_required()
def handle_classes():
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    role = claims.get('role')
    
    if request.method == 'POST':
        if role != 'teacher':
            return jsonify({"error": "Apenas professores podem criar aulas"}), 403
            
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
        classes = Class.query.all()
        return jsonify([{"id": c.id, "title": c.title, "datetime": c.datetime, "link": c.link} for c in classes]), 200

@api_bp.route('/classes/<int:id>/enroll', methods=['POST'])
@jwt_required()
def enroll_class(id):
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    role = claims.get('role')

    if role != 'student':
        return jsonify({"error": "Apenas alunos podem se inscrever"}), 403

    if ClassEnrollment.query.filter_by(class_id=id, student_id=current_user_id).first():
        return jsonify({"error": "Você já está inscrito nesta aula"}), 400

    enrollment = ClassEnrollment(class_id=id, student_id=current_user_id)
    db.session.add(enrollment)
    db.session.commit()
    return jsonify({"message": "Inscrição realizada com sucesso"}), 201

@api_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    current_user_id = int(get_jwt_identity())
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400
        
    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    class_id = request.form.get('class_id')
    if not class_id or class_id == 'null':
        class_id = None

    new_file = File(
        filename=filename,
        path=filepath,
        owner_id=current_user_id,
        class_id=class_id
    )
    db.session.add(new_file)
    db.session.commit()
    
    return jsonify({"message": "Arquivo enviado com sucesso", "filename": filename}), 201

@api_bp.route('/files', methods=['GET'])
@jwt_required()
def get_files():
    files = File.query.all()
    return jsonify([{"id": f.id, "filename": f.filename} for f in files]), 200

@api_bp.route('/my-mentor', methods=['GET'])
@jwt_required()
def get_my_mentor():
    current_user_id = int(get_jwt_identity())
    relation = MentorStudent.query.filter_by(student_id=current_user_id).first()
    if not relation:
        return jsonify({"error": "Nenhum mentor atribuído"}), 404
    mentor = User.query.get(relation.mentor_id)
    return jsonify({"name": mentor.name, "whatsapp": mentor.whatsapp}), 200

# Gerenciamento de Cronogramas e Metas (Acesso pelo Mentor e Aluno)
@api_bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    current_user_id = int(get_jwt_identity())
    # Simplificação: buscando as metas atreladas aos planos do aluno
    plans = StudyPlan.query.filter_by(student_id=current_user_id).all()
    plan_ids = [p.id for p in plans]
    tasks = StudyTask.query.filter(StudyTask.plan_id.in_(plan_ids)).all()
    return jsonify([{"id": t.id, "week_number": t.week_number, "description": t.description, "is_completed": t.is_completed} for t in tasks]), 200

@api_bp.route('/tasks/<int:id>/toggle', methods=['POST'])
@jwt_required()
def toggle_task(id):
    task = StudyTask.query.get_or_404(id)
    task.is_completed = not task.is_completed
    db.session.commit()
    return jsonify({"message": "Status da meta atualizado", "is_completed": task.is_completed}), 200

# Resultados de Simulados (Acompanhamento de Desempenho)
@api_bp.route('/exam-results', methods=['GET', 'POST'])
@jwt_required()
def handle_exam_results():
    current_user_id = int(get_jwt_identity())
    
    if request.method == 'POST':
        data = request.get_json()
        student_id = data.get('student_id', current_user_id) # Mentor pode postar para o aluno
        new_result = ExamResult(
            student_id=student_id,
            exam_title=data.get('exam_title'),
            score=data.get('score'),
            date=data.get('date')
        )
        db.session.add(new_result)
        db.session.commit()
        return jsonify({"message": "Resultado salvo com sucesso"}), 201

    # GET
    results = ExamResult.query.filter_by(student_id=current_user_id).all()
    return jsonify([{"id": r.id, "exam_title": r.exam_title, "score": r.score, "date": r.date} for r in results]), 200