from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.extensions import db
from app.models import ChatMessage, ChatThread, User
from app.services.permissions import get_student_assignment


chat_bp = Blueprint('chat', __name__)


def serialize_message(message, current_user_id):
    sender = User.query.get(message.sender_id)
    return {
        "id": message.id,
        "thread_id": message.thread_id,
        "sender_id": message.sender_id,
        "sender_name": sender.name if sender else 'Usuário',
        "sender_role": sender.role if sender else None,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
        "read_at": message.read_at.isoformat() if message.read_at else None,
        "is_mine": message.sender_id == current_user_id,
    }


def get_thread_unread_count(thread_id, current_user_id):
    return ChatMessage.query.filter(
        ChatMessage.thread_id == thread_id,
        ChatMessage.sender_id != current_user_id,
        ChatMessage.read_at.is_(None),
    ).count()


def resolve_chat_access(current_user_id, current_role, requested_student_id=None):
    if current_role == 'mentor':
        student_id = requested_student_id
        try:
            student_id = int(student_id)
        except (TypeError, ValueError):
            return None, None, "student_id é obrigatório"

        assignment = get_student_assignment(student_id)
        if not assignment or assignment.mentor_id != current_user_id:
            return None, None, "Sem permissão para acessar o chat deste aluno"

        student = User.query.get(student_id)
        mentor = User.query.get(current_user_id)
        if not student or student.role != 'student':
            return None, None, "Aluno inválido"
        if not mentor or mentor.role != 'mentor':
            return None, None, "Apenas mentores podem usar este chat"

        return mentor, student, None

    if current_role == 'student':
        assignment = get_student_assignment(current_user_id)
        if not assignment:
            return None, None, "Nenhum mentor responsável vinculado"

        mentor = User.query.get(assignment.mentor_id)
        student = User.query.get(current_user_id)
        if not mentor or mentor.role != 'mentor':
            return None, None, "Chat disponível apenas com mentor responsável"
        if not student or student.role != 'student':
            return None, None, "Aluno inválido"

        return mentor, student, None

    return None, None, "Somente mentor e aluno podem usar o chat"


def get_or_create_thread(mentor_id, student_id):
    thread = ChatThread.query.filter_by(mentor_id=mentor_id, student_id=student_id).first()
    if thread:
        return thread

    thread = ChatThread(mentor_id=mentor_id, student_id=student_id)
    db.session.add(thread)
    db.session.commit()
    return thread


@chat_bp.route('/chat/thread', methods=['GET'])
@jwt_required()
def get_chat_thread():
    current_user_id = int(get_jwt_identity())
    current_role = get_jwt().get('role')
    mentor, student, error = resolve_chat_access(current_user_id, current_role, request.args.get('student_id'))
    if error:
        return jsonify({"error": error}), 403 if current_role != 'student' or error != "Nenhum mentor responsável vinculado" else 404

    thread = get_or_create_thread(mentor.id, student.id)
    counterpart = student if current_role == 'mentor' else mentor
    return jsonify({
        "thread": {
            "id": thread.id,
            "mentor_id": mentor.id,
            "student_id": student.id,
            "created_at": thread.created_at.isoformat(),
        },
        "counterpart": {
            "id": counterpart.id,
            "name": counterpart.name,
            "role": counterpart.role,
        },
        "unread_count": get_thread_unread_count(thread.id, current_user_id),
    }), 200


@chat_bp.route('/chat/messages', methods=['GET', 'POST'])
@jwt_required()
def chat_messages():
    current_user_id = int(get_jwt_identity())
    current_role = get_jwt().get('role')
    requested_student_id = request.args.get('student_id')
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        requested_student_id = data.get('student_id')

    mentor, student, error = resolve_chat_access(current_user_id, current_role, requested_student_id)
    if error:
        return jsonify({"error": error}), 403 if current_role != 'student' or error != "Nenhum mentor responsável vinculado" else 404

    thread = get_or_create_thread(mentor.id, student.id)

    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        content = (data.get('content') or '').strip()
        if not content:
            return jsonify({"error": "content é obrigatório"}), 400

        message = ChatMessage(
            thread_id=thread.id,
            sender_id=current_user_id,
            content=content,
        )
        db.session.add(message)
        db.session.commit()
        return jsonify({"message": "Mensagem enviada com sucesso", "chat_message": serialize_message(message, current_user_id)}), 201

    after_id = request.args.get('after_id', type=int)
    query = ChatMessage.query.filter_by(thread_id=thread.id).order_by(ChatMessage.id.asc())
    if after_id:
        query = query.filter(ChatMessage.id > after_id)

    messages = query.all()
    return jsonify({
        "thread_id": thread.id,
        "messages": [serialize_message(message, current_user_id) for message in messages],
        "unread_count": get_thread_unread_count(thread.id, current_user_id),
    }), 200


@chat_bp.route('/chat/read', methods=['POST'])
@jwt_required()
def mark_chat_as_read():
    current_user_id = int(get_jwt_identity())
    current_role = get_jwt().get('role')
    data = request.get_json(silent=True) or {}
    mentor, student, error = resolve_chat_access(current_user_id, current_role, data.get('student_id'))
    if error:
        return jsonify({"error": error}), 403 if current_role != 'student' or error != "Nenhum mentor responsável vinculado" else 404

    thread = get_or_create_thread(mentor.id, student.id)
    unread_messages = ChatMessage.query.filter(
        ChatMessage.thread_id == thread.id,
        ChatMessage.sender_id != current_user_id,
        ChatMessage.read_at.is_(None),
    ).all()

    now = datetime.utcnow()
    for message in unread_messages:
        message.read_at = now

    db.session.commit()
    return jsonify({"message": "Mensagens marcadas como lidas", "unread_count": 0}), 200


@chat_bp.route('/chat/unread-summary', methods=['GET'])
@jwt_required()
def get_chat_unread_summary():
    current_user_id = int(get_jwt_identity())
    current_role = get_jwt().get('role')

    if current_role == 'mentor':
        threads = ChatThread.query.filter_by(mentor_id=current_user_id).all()
        return jsonify([
            {
                "student_id": thread.student_id,
                "unread_count": get_thread_unread_count(thread.id, current_user_id),
            }
            for thread in threads
            if get_thread_unread_count(thread.id, current_user_id) > 0
        ]), 200

    if current_role == 'student':
        mentor, student, error = resolve_chat_access(current_user_id, current_role)
        if error:
            return jsonify([]), 200

        thread = ChatThread.query.filter_by(mentor_id=mentor.id, student_id=student.id).first()
        if not thread:
            return jsonify([]), 200

        return jsonify([{
            "student_id": student.id,
            "mentor_id": mentor.id,
            "unread_count": get_thread_unread_count(thread.id, current_user_id),
        }]), 200

    return jsonify([]), 200
