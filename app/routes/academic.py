from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app.extensions import db
from app.models import User, Meeting, Class, ClassEnrollment
from app.services.permissions import can_manage_student


academic_bp = Blueprint('academic', __name__)


def serialize_meeting(meeting):
    return {
        "id": meeting.id,
        "title": meeting.title,
        "datetime": meeting.datetime,
        "description": meeting.description,
        "link": meeting.link,
        "student_id": meeting.student_id,
        "mentor_id": meeting.mentor_id,
    }


@academic_bp.route('/meetings', methods=['POST', 'GET'])
@jwt_required()
def handle_meetings():
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    role = claims.get('role')

    if request.method == 'POST':
        if role != 'mentor':
            return jsonify({"error": "Apenas mentores podem criar reuniões"}), 403

        data = request.get_json(silent=True) or {}
        if not data.get('student_id') or not data.get('datetime') or not data.get('title'):
            return jsonify({"error": "student_id, title e datetime são obrigatórios"}), 400

        if not can_manage_student(current_user_id, role, int(data['student_id'])):
            return jsonify({"error": "Você só pode criar sessões para seus próprios alunos"}), 403

        new_meeting = Meeting(
            mentor_id=current_user_id,
            student_id=data.get('student_id'),
            title=data.get('title'),
            datetime=data.get('datetime'),
            description=data.get('description'),
            link=data.get('link')
        )
        db.session.add(new_meeting)
        db.session.commit()
        return jsonify({"message": "Reunião criada com sucesso", "meeting": serialize_meeting(new_meeting)}), 201

    if role == 'mentor':
        meetings_query = Meeting.query.filter_by(mentor_id=current_user_id)
        student_id = request.args.get('student_id', type=int)
        if student_id:
            meetings_query = meetings_query.filter_by(student_id=student_id)
        meetings = meetings_query.all()
    elif role == 'student':
        meetings = Meeting.query.filter_by(student_id=current_user_id).all()
    else:
        meetings = []
    return jsonify([serialize_meeting(meeting) for meeting in meetings]), 200


@academic_bp.route('/meetings/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_meeting(id):
    current_user_id = int(get_jwt_identity())
    role = get_jwt().get('role')

    if role != 'mentor':
        return jsonify({"error": "Apenas mentores podem excluir reuniões"}), 403

    meeting = Meeting.query.get_or_404(id)
    if meeting.mentor_id != current_user_id:
        return jsonify({"error": "Sem permissão para excluir esta reunião"}), 403

    db.session.delete(meeting)
    db.session.commit()
    return jsonify({"message": "Reunião excluída com sucesso"}), 200


@academic_bp.route('/classes', methods=['POST', 'GET'])
@jwt_required()
def handle_classes():
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    role = claims.get('role')

    if request.method == 'POST':
        if role != 'mentor':
            return jsonify({"error": "Apenas mentores podem criar aulas"}), 403

        data = request.get_json(silent=True) or {}
        if not data.get('title') or not data.get('datetime'):
            return jsonify({"error": "title e datetime são obrigatórios"}), 400
        event_type = data.get('event_type', 'collective_class')
        if event_type not in ('collective_class', 'office_hours'):
            return jsonify({"error": "event_type inválido"}), 400

        new_class = Class(
            mentor_id=current_user_id,
            title=data.get('title'),
            description=data.get('description'),
            datetime=data.get('datetime'),
            link=data.get('link'),
            event_type=event_type
        )
        db.session.add(new_class)
        db.session.commit()
        return jsonify({
            "message": "Aula criada com sucesso",
            "class": {
                "id": new_class.id,
                "title": new_class.title,
                "description": new_class.description,
                "datetime": new_class.datetime,
                "link": new_class.link,
                "event_type": new_class.event_type,
                "mentor_id": new_class.mentor_id,
            }
        }), 201

    classes = db.session.query(Class, User.name.label('mentor_name')).join(User, Class.mentor_id == User.id).all()
    return jsonify([{"id": c.Class.id, "title": c.Class.title, "description": c.Class.description, "datetime": c.Class.datetime, "link": c.Class.link, "mentor_name": c.mentor_name, "event_type": c.Class.event_type, "mentor_id": c.Class.mentor_id} for c in classes]), 200


@academic_bp.route('/classes/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_class(id):
    current_user_id = int(get_jwt_identity())
    role = get_jwt().get('role')

    if role != 'mentor':
        return jsonify({"error": "Apenas mentores podem excluir aulas ou plantões"}), 403

    class_event = Class.query.get_or_404(id)
    if class_event.mentor_id != current_user_id:
        return jsonify({"error": "Sem permissão para excluir este evento"}), 403

    ClassEnrollment.query.filter_by(class_id=id).delete(synchronize_session=False)
    db.session.delete(class_event)
    db.session.commit()
    return jsonify({"message": "Evento excluído com sucesso"}), 200


@academic_bp.route('/classes/<int:id>/enroll', methods=['POST'])
@jwt_required()
def enroll_class(id):
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())

    if claims.get('role') != 'student':
        return jsonify({"error": "Apenas alunos podem se inscrever"}), 403

    Class.query.get_or_404(id)

    if ClassEnrollment.query.filter_by(class_id=id, student_id=current_user_id).first():
        return jsonify({"error": "Você já está inscrito nesta aula"}), 400

    enrollment = ClassEnrollment(class_id=id, student_id=current_user_id)
    db.session.add(enrollment)
    db.session.commit()
    return jsonify({"message": "Inscrição realizada com sucesso"}), 201
