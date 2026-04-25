import os

from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app.extensions import db
from app.models import File, Class
from app.services.files import save_uploaded_file
from app.services.permissions import can_manage_student


files_bp = Blueprint('files', __name__)


@files_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    current_user_id = int(get_jwt_identity())
    current_role = get_jwt().get('role')
    if current_role not in ('mentor', 'teacher'):
        return jsonify({"error": "Apenas mentores ou professores podem enviar arquivos"}), 403

    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400

    try:
        filename, filepath = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    class_id = request.form.get('class_id')
    student_id = request.form.get('student_id')
    if not class_id or class_id == 'null':
        class_id = None
    else:
        try:
            class_id = int(class_id)
        except ValueError:
            return jsonify({"error": "class_id inválido"}), 400

        if not Class.query.get(class_id):
            return jsonify({"error": "Turma não encontrada"}), 404

    if not student_id or student_id == 'null':
        student_id = None
    else:
        try:
            student_id = int(student_id)
        except ValueError:
            return jsonify({"error": "student_id inválido"}), 400

        if not can_manage_student(current_user_id, current_role, student_id):
            return jsonify({"error": "Sem permissão para compartilhar material com este aluno"}), 403

    new_file = File(
        filename=filename,
        path=filepath,
        owner_id=current_user_id,
        student_id=student_id,
        class_id=class_id
    )
    db.session.add(new_file)
    db.session.commit()

    return jsonify({"message": "Arquivo enviado com sucesso", "filename": filename}), 201


@files_bp.route('/files', methods=['GET'])
@jwt_required()
def get_files():
    current_user_id = int(get_jwt_identity())
    current_role = get_jwt().get('role')
    requested_student_id = request.args.get('student_id', type=int)

    if current_role == 'student':
        files = File.query.filter_by(student_id=current_user_id).all()
    elif requested_student_id:
        if not can_manage_student(current_user_id, current_role, requested_student_id):
            return jsonify({"error": "Sem permissão para ver os materiais deste aluno"}), 403
        files = File.query.filter_by(student_id=requested_student_id, owner_id=current_user_id).all()
    else:
        files = File.query.filter_by(owner_id=current_user_id, student_id=None).all()

    return jsonify([{"id": f.id, "filename": f.filename} for f in files]), 200


@files_bp.route('/files/download/<int:id>', methods=['GET'])
@jwt_required()
def download_file(id):
    file = File.query.get_or_404(id)
    directory, filename = os.path.split(file.path)
    return send_from_directory(directory, filename, as_attachment=True)
