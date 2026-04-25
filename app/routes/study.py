from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app.extensions import db
from app.models import StudyPlan, StudyTask, ExamResult, SharedLink, User
from app.services.permissions import can_manage_student


study_bp = Blueprint('study', __name__)


VALID_PLAN_DURATIONS = (6, 9, 12)


def serialize_plan(plan):
    tasks = StudyTask.query.filter_by(plan_id=plan.id).order_by(StudyTask.week_number.asc(), StudyTask.id.asc()).all()
    return {
        "id": plan.id,
        "student_id": plan.student_id,
        "mentor_id": plan.mentor_id,
        "title": plan.title,
        "duration_months": plan.duration_months,
        "status": plan.status,
        "notes": plan.notes,
        "tasks": [serialize_task(task) for task in tasks],
    }


def serialize_task(task):
    return {
        "id": task.id,
        "plan_id": task.plan_id,
        "week_number": task.week_number,
        "description": task.description,
        "subject": task.subject,
        "due_date": task.due_date,
        "is_completed": task.is_completed,
    }


def serialize_exam_result(result):
    return {
        "id": result.id,
        "student_id": result.student_id,
        "exam_title": result.exam_title,
        "score": result.score,
        "date": result.date,
        "exam_type": result.exam_type,
        "correct_answers": result.correct_answers,
        "total_questions": result.total_questions,
        "notes": result.notes,
    }


def serialize_shared_link(link):
    return {
        "id": link.id,
        "student_id": link.student_id,
        "mentor_id": link.mentor_id,
        "title": link.title,
        "url": link.url,
    }


def resolve_student_scope(current_user_id, current_role, requested_student_id=None):
    if current_role == 'student':
        return current_user_id

    if requested_student_id is None:
        return None

    try:
        student_id = int(requested_student_id)
    except (TypeError, ValueError):
        return None

    if can_manage_student(current_user_id, current_role, student_id):
        return student_id

    return None


@study_bp.route('/plans', methods=['GET', 'POST'])
@jwt_required()
def handle_plans():
    current_user_id = int(get_jwt_identity())
    current_role = get_jwt().get('role')

    if request.method == 'POST':
        if current_role not in ('mentor', 'teacher'):
            return jsonify({"error": "Apenas mentores ou professores podem criar cronogramas"}), 403

        data = request.get_json(silent=True) or {}
        student_id = resolve_student_scope(current_user_id, current_role, data.get('student_id'))
        if not student_id:
            return jsonify({"error": "Aluno inválido ou sem permissão"}), 403

        duration_months = data.get('duration_months')
        if duration_months not in VALID_PLAN_DURATIONS:
            return jsonify({"error": "duration_months deve ser 6, 9 ou 12"}), 400

        if not data.get('title'):
            return jsonify({"error": "title é obrigatório"}), 400

        plan = StudyPlan(
            student_id=student_id,
            mentor_id=current_user_id,
            title=data['title'],
            duration_months=duration_months,
            status=data.get('status', 'active'),
            notes=data.get('notes'),
        )
        db.session.add(plan)
        db.session.commit()
        return jsonify({"message": "Cronograma criado com sucesso", "plan": serialize_plan(plan)}), 201

    requested_student_id = request.args.get('student_id')
    student_id = resolve_student_scope(current_user_id, current_role, requested_student_id)
    if current_role in ('mentor', 'teacher') and requested_student_id and not student_id:
        return jsonify({"error": "Aluno inválido ou sem permissão"}), 403

    if current_role == 'student':
        plans = StudyPlan.query.filter_by(student_id=current_user_id).order_by(StudyPlan.id.desc()).all()
    elif student_id:
        plans = StudyPlan.query.filter_by(student_id=student_id).order_by(StudyPlan.id.desc()).all()
    else:
        plans = StudyPlan.query.order_by(StudyPlan.id.desc()).all() if current_role == 'teacher' else StudyPlan.query.filter_by(mentor_id=current_user_id).order_by(StudyPlan.id.desc()).all()

    return jsonify([serialize_plan(plan) for plan in plans]), 200


@study_bp.route('/plans/<int:id>', methods=['PATCH'])
@jwt_required()
def update_plan(id):
    current_user_id = int(get_jwt_identity())
    current_role = get_jwt().get('role')
    plan = StudyPlan.query.get_or_404(id)
    if not can_manage_student(current_user_id, current_role, plan.student_id):
        return jsonify({"error": "Sem permissão para alterar este cronograma"}), 403

    data = request.get_json(silent=True) or {}
    if data.get('title'):
        plan.title = data['title']
    if data.get('notes') is not None:
        plan.notes = data.get('notes')
    if data.get('status'):
        plan.status = data['status']
    if data.get('duration_months') in VALID_PLAN_DURATIONS:
        plan.duration_months = data['duration_months']

    db.session.commit()
    return jsonify({"message": "Cronograma atualizado com sucesso", "plan": serialize_plan(plan)}), 200


@study_bp.route('/plans/<int:id>/tasks', methods=['POST'])
@jwt_required()
def create_plan_task(id):
    current_user_id = int(get_jwt_identity())
    current_role = get_jwt().get('role')
    plan = StudyPlan.query.get_or_404(id)
    if not can_manage_student(current_user_id, current_role, plan.student_id):
        return jsonify({"error": "Sem permissão para adicionar metas"}), 403

    data = request.get_json(silent=True) or {}
    if not data.get('description') or not data.get('week_number'):
        return jsonify({"error": "description e week_number são obrigatórios"}), 400

    task = StudyTask(
        plan_id=plan.id,
        week_number=data['week_number'],
        description=data['description'],
        subject=data.get('subject'),
        due_date=data.get('due_date'),
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({"message": "Meta adicionada com sucesso", "task": serialize_task(task)}), 201


@study_bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    current_user_id = int(get_jwt_identity())
    plans = StudyPlan.query.filter_by(student_id=current_user_id).all()
    plan_ids = [p.id for p in plans]
    tasks = StudyTask.query.filter(StudyTask.plan_id.in_(plan_ids)).all()
    return jsonify([serialize_task(t) for t in tasks]), 200


@study_bp.route('/tasks/<int:id>/toggle', methods=['POST'])
@jwt_required()
def toggle_task(id):
    current_user_id = int(get_jwt_identity())
    current_role = get_jwt().get('role')
    task = StudyTask.query.get_or_404(id)
    plan = StudyPlan.query.get_or_404(task.plan_id)
    if current_role == 'student' and plan.student_id != current_user_id:
        return jsonify({"error": "Sem permissão para alterar esta meta"}), 403
    if current_role in ('mentor', 'teacher') and not can_manage_student(current_user_id, current_role, plan.student_id):
        return jsonify({"error": "Sem permissão para alterar esta meta"}), 403
    task.is_completed = not task.is_completed
    db.session.commit()
    return jsonify({"message": "Status da meta atualizado", "is_completed": task.is_completed}), 200


@study_bp.route('/exam-results', methods=['GET', 'POST'])
@jwt_required()
def handle_exam_results():
    current_user_id = int(get_jwt_identity())
    current_role = get_jwt().get('role')

    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        if not data.get('exam_title') or data.get('score') is None or not data.get('date'):
            return jsonify({"error": "exam_title, score e date são obrigatórios"}), 400

        student_id = resolve_student_scope(current_user_id, current_role, data.get('student_id', current_user_id))
        if not student_id:
            return jsonify({"error": "Aluno inválido ou sem permissão"}), 403

        new_result = ExamResult(
            student_id=student_id,
            exam_title=data.get('exam_title'),
            score=data.get('score'),
            date=data.get('date'),
            exam_type=data.get('exam_type', 'mock_exam'),
            correct_answers=data.get('correct_answers'),
            total_questions=data.get('total_questions'),
            notes=data.get('notes'),
        )
        db.session.add(new_result)
        db.session.commit()
        return jsonify({"message": "Resultado salvo com sucesso", "result": serialize_exam_result(new_result)}), 201

    student_id = resolve_student_scope(current_user_id, current_role, request.args.get('student_id'))
    if current_role in ('mentor', 'teacher') and request.args.get('student_id') and not student_id:
        return jsonify({"error": "Aluno inválido ou sem permissão"}), 403

    if current_role == 'student':
        results = ExamResult.query.filter_by(student_id=current_user_id).order_by(ExamResult.id.desc()).all()
    elif student_id:
        results = ExamResult.query.filter_by(student_id=student_id).order_by(ExamResult.id.desc()).all()
    else:
        results = ExamResult.query.order_by(ExamResult.id.desc()).all() if current_role == 'teacher' else ExamResult.query.join(User, ExamResult.student_id == User.id).order_by(ExamResult.id.desc()).all()
    return jsonify([serialize_exam_result(r) for r in results]), 200


@study_bp.route('/progress', methods=['GET'])
@jwt_required()
def get_progress():
    current_user_id = int(get_jwt_identity())
    current_role = get_jwt().get('role')
    student_id = resolve_student_scope(current_user_id, current_role, request.args.get('student_id'))
    if current_role in ('mentor', 'teacher') and request.args.get('student_id') and not student_id:
        return jsonify({"error": "Aluno inválido ou sem permissão"}), 403

    if current_role == 'student' or student_id:
        student_ids = [student_id or current_user_id]
    elif current_role == 'teacher':
        student_ids = [user.id for user in User.query.filter_by(role='student').all()]
    else:
        student_ids = [plan.student_id for plan in StudyPlan.query.filter_by(mentor_id=current_user_id).all()]
        student_ids = list(dict.fromkeys(student_ids))

    plans = StudyPlan.query.filter(StudyPlan.student_id.in_(student_ids)).all() if student_ids else []
    plan_ids = [plan.id for plan in plans]
    tasks = StudyTask.query.filter(StudyTask.plan_id.in_(plan_ids)).all() if plan_ids else []
    results = ExamResult.query.filter(ExamResult.student_id.in_(student_ids)).all() if student_ids else []

    completed_tasks = sum(1 for task in tasks if task.is_completed)
    total_tasks = len(tasks)
    average_score = round(sum(result.score for result in results) / len(results), 2) if results else 0

    return jsonify({
        "student_id": student_id or (current_user_id if current_role == 'student' else None),
        "students_count": len(student_ids),
        "plans_count": len(plans),
        "tasks_total": total_tasks,
        "tasks_completed": completed_tasks,
        "task_completion_rate": round((completed_tasks / total_tasks) * 100, 2) if total_tasks else 0,
        "exam_results_count": len(results),
        "average_score": average_score,
    }), 200


@study_bp.route('/student-links', methods=['GET', 'POST'])
@jwt_required()
def handle_student_links():
    current_user_id = int(get_jwt_identity())
    current_role = get_jwt().get('role')

    if request.method == 'POST':
        if current_role not in ('mentor', 'teacher'):
            return jsonify({"error": "Apenas mentores ou professores podem compartilhar links"}), 403

        data = request.get_json(silent=True) or {}
        student_id = resolve_student_scope(current_user_id, current_role, data.get('student_id'))
        if not student_id:
            return jsonify({"error": "Aluno inválido ou sem permissão"}), 403
        if not data.get('title') or not data.get('url'):
            return jsonify({"error": "title e url são obrigatórios"}), 400

        link = SharedLink(
            student_id=student_id,
            mentor_id=current_user_id,
            title=data['title'],
            url=data['url'],
        )
        db.session.add(link)
        db.session.commit()
        return jsonify({"message": "Link compartilhado com sucesso", "link": serialize_shared_link(link)}), 201

    student_id = resolve_student_scope(current_user_id, current_role, request.args.get('student_id'))
    if current_role in ('mentor', 'teacher') and request.args.get('student_id') and not student_id:
        return jsonify({"error": "Aluno inválido ou sem permissão"}), 403

    if current_role == 'student':
        links = SharedLink.query.filter_by(student_id=current_user_id).order_by(SharedLink.id.desc()).all()
    elif student_id:
        links = SharedLink.query.filter_by(student_id=student_id, mentor_id=current_user_id).order_by(SharedLink.id.desc()).all()
    else:
        links = SharedLink.query.filter_by(mentor_id=current_user_id).order_by(SharedLink.id.desc()).all()

    return jsonify([serialize_shared_link(link) for link in links]), 200


@study_bp.route('/student-links/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_student_link(id):
    current_user_id = int(get_jwt_identity())
    current_role = get_jwt().get('role')

    if current_role not in ('mentor', 'teacher'):
        return jsonify({"error": "Apenas mentores ou professores podem excluir links"}), 403

    link = SharedLink.query.get_or_404(id)
    if link.mentor_id != current_user_id:
        return jsonify({"error": "Sem permissão para excluir este link"}), 403

    db.session.delete(link)
    db.session.commit()
    return jsonify({"message": "Link excluído com sucesso"}), 200
