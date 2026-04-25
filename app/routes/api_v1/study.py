from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import StudyPlan, StudyTask, ExamResult
from flask_jwt_extended import jwt_required, get_jwt_identity

study_bp = Blueprint('study', __name__)

@study_bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    current_user_id = int(get_jwt_identity())
    plans = StudyPlan.query.filter_by(student_id=current_user_id).all()
    plan_ids = [p.id for p in plans]
    tasks = StudyTask.query.filter(StudyTask.plan_id.in_(plan_ids)).all()
    return jsonify([{"id": t.id, "week_number": t.week_number, "description": t.description, "is_completed": t.is_completed} for t in tasks]), 200

@study_bp.route('/tasks/<int:id>/toggle', methods=['POST'])
@jwt_required()
def toggle_task(id):
    task = StudyTask.query.get_or_404(id)
    task.is_completed = not task.is_completed
    db.session.commit()
    return jsonify({"message": "Status da meta atualizado", "is_completed": task.is_completed}), 200

@study_bp.route('/exam-results', methods=['GET', 'POST'])
@jwt_required()
def handle_exam_results():
    current_user_id = int(get_jwt_identity())
    
    if request.method == 'POST':
        data = request.get_json()
        student_id = data.get('student_id', current_user_id) 
        new_result = ExamResult(
            student_id=student_id,
            exam_title=data.get('exam_title'),
            score=data.get('score'),
            date=data.get('date')
        )
        db.session.add(new_result)
        db.session.commit()
        return jsonify({"message": "Resultado salvo com sucesso"}), 201

    results = ExamResult.query.filter_by(student_id=current_user_id).all()
    return jsonify([{"id": r.id, "exam_title": r.exam_title, "score": r.score, "date": r.date} for r in results]), 200