from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app.extensions import db
from app.models import User, MentorStudent, StudyPlan, StudyTask, ExamResult, Meeting, SharedLink, File, ChatThread, ChatMessage
from app.services.permissions import get_student_assignment, can_access_student


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


@users_bp.route('/my-mentor', methods=['GET'])
@jwt_required()
def get_my_mentor():
    current_user_id = int(get_jwt_identity())
    relation = MentorStudent.query.filter_by(student_id=current_user_id).first()
    if not relation:
        return jsonify({"error": "Nenhum mentor atribuído"}), 404
    mentor = User.query.get(relation.mentor_id)
    return jsonify({"id": mentor.id, "name": mentor.name, "whatsapp": mentor.whatsapp, "role": mentor.role}), 200


@users_bp.route('/assign-mentor', methods=['POST'])
@jwt_required()
def assign_mentor():
    current_user_id = int(get_jwt_identity())
    current_role = get_jwt().get('role')
    data = request.get_json(silent=True) or {}
    student_id = data.get('student_id')
    mentor_id = data.get('mentor_id')
    if not student_id or not mentor_id:
        return jsonify({"error": "student_id e mentor_id são obrigatórios"}), 400

    if current_role not in ('mentor', 'teacher'):
        return jsonify({"error": "Apenas mentores ou professores podem vincular alunos"}), 403

    if int(mentor_id) != current_user_id:
        return jsonify({"error": "Você só pode vincular alunos a si mesmo"}), 403

    student = User.query.get(student_id)
    mentor = User.query.get(mentor_id)
    if not student or student.role != 'student':
        return jsonify({"error": "Aluno inválido"}), 400
    if not mentor or mentor.role not in ('mentor', 'teacher'):
        return jsonify({"error": "Mentor/professor inválido"}), 400

    existing_assignment = MentorStudent.query.filter_by(student_id=student_id).first()
    if existing_assignment:
        existing_mentor = User.query.get(existing_assignment.mentor_id)
        responsible_name = existing_mentor.name if existing_mentor else 'outro responsável'
        return jsonify({"error": f"Aluno já está vinculado a {responsible_name}"}), 400

    assignment = MentorStudent(student_id=student_id, mentor_id=mentor_id)
    db.session.add(assignment)
    db.session.commit()
    return jsonify({"message": "Aluno vinculado com sucesso"}), 201


@users_bp.route('/assign-mentor/<int:student_id>', methods=['DELETE'])
@jwt_required()
def unassign_mentor(student_id):
    current_user_id = int(get_jwt_identity())
    current_role = get_jwt().get('role')
    if current_role not in ('mentor', 'teacher'):
        return jsonify({"error": "Apenas mentores ou professores podem desfazer vínculos"}), 403

    assignment = MentorStudent.query.filter_by(student_id=student_id, mentor_id=current_user_id).first()
    if not assignment:
        return jsonify({"error": "Vínculo não encontrado para este aluno"}), 404

    plans = StudyPlan.query.filter_by(student_id=student_id, mentor_id=current_user_id).all()
    plan_ids = [plan.id for plan in plans]
    if plan_ids:
        StudyTask.query.filter(StudyTask.plan_id.in_(plan_ids)).delete(synchronize_session=False)
        StudyPlan.query.filter(StudyPlan.id.in_(plan_ids)).delete(synchronize_session=False)

    ExamResult.query.filter_by(student_id=student_id).delete(synchronize_session=False)
    SharedLink.query.filter_by(student_id=student_id, mentor_id=current_user_id).delete(synchronize_session=False)
    Meeting.query.filter_by(student_id=student_id, mentor_id=current_user_id).delete(synchronize_session=False)
    File.query.filter_by(student_id=student_id, owner_id=current_user_id).delete(synchronize_session=False)
    chat_threads = ChatThread.query.filter_by(student_id=student_id, teacher_id=current_user_id).all()
    thread_ids = [thread.id for thread in chat_threads]
    if thread_ids:
        ChatMessage.query.filter(ChatMessage.thread_id.in_(thread_ids)).delete(synchronize_session=False)
        ChatThread.query.filter(ChatThread.id.in_(thread_ids)).delete(synchronize_session=False)
    db.session.delete(assignment)
    db.session.commit()

    return jsonify({"message": "Vínculo removido e histórico relacionado apagado"}), 200


@users_bp.route('/student-options', methods=['GET'])
@jwt_required()
def get_student_options():
    current_user_id = int(get_jwt_identity())
    current_role = get_jwt().get('role')
    if current_role not in ('mentor', 'teacher'):
        return jsonify({"error": "Apenas mentores ou professores podem acessar alunos"}), 403

    students = User.query.filter_by(role='student').order_by(User.name.asc()).all()
    options = []
    for student in students:
        assignment = get_student_assignment(student.id)
        assigned_to_self = assignment and assignment.mentor_id == current_user_id
        if assignment and not assigned_to_self:
            continue

        options.append({
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "status": "managed" if assigned_to_self else "available",
        })

    return jsonify({
        "assignable_students": [student for student in options if student["status"] == "available"],
        "managed_students": [student for student in options if student["status"] == "managed"],
    }), 200


@users_bp.route('/student-overview/<int:id>', methods=['GET'])
@jwt_required()
def get_student_overview(id):
    current_user_id = int(get_jwt_identity())
    current_role = get_jwt().get('role')
    if current_role not in ('mentor', 'teacher'):
        return jsonify({"error": "Apenas mentores ou professores podem acessar este resumo"}), 403

    student = User.query.get_or_404(id)
    if student.role != 'student':
        return jsonify({"error": "Usuário informado não é um aluno"}), 400

    if not can_access_student(current_user_id, current_role, id):
        return jsonify({"error": "Sem permissão para acessar este aluno"}), 403

    assignment = get_student_assignment(id)
    mentor = User.query.get(assignment.mentor_id) if assignment else None
    plans = StudyPlan.query.filter_by(student_id=id).all()
    plan_ids = [plan.id for plan in plans]
    tasks = StudyTask.query.filter(StudyTask.plan_id.in_(plan_ids)).all() if plan_ids else []
    results = ExamResult.query.filter_by(student_id=id).all()
    meetings = Meeting.query.filter_by(student_id=id).all()

    return jsonify({
        "student": {"id": student.id, "name": student.name, "email": student.email},
        "assignment_status": "managed" if mentor and mentor.id == current_user_id else ("assigned" if mentor else "available"),
        "mentor": {"id": mentor.id, "name": mentor.name, "role": mentor.role} if mentor else None,
        "plans_count": len(plans),
        "tasks_total": len(tasks),
        "tasks_completed": sum(1 for task in tasks if task.is_completed),
        "exam_results_count": len(results),
        "average_score": round(sum(result.score for result in results) / len(results), 2) if results else 0,
        "meetings_count": len(meetings),
        "plans": [{"id": plan.id, "title": plan.title, "status": plan.status} for plan in plans],
    }), 200
