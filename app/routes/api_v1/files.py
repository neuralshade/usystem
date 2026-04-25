import os
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import File
from flask_jwt_extended import jwt_required, get_jwt_identity

files_bp = Blueprint('files', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'ppt', 'pptx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@files_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    current_user_id = int(get_jwt_identity())
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400
        
    if not allowed_file(file.filename):
        return jsonify({"error": "Tipo de arquivo não permitido"}), 400
        
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

@files_bp.route('/files', methods=['GET'])
@jwt_required()
def get_files():
    files = File.query.all()
    return jsonify([{"id": f.id, "filename": f.filename} for f in files]), 200

@files_bp.route('/files/download/<int:id>', methods=['GET'])
@jwt_required()
def download_file(id):
    file = File.query.get_or_404(id)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], file.filename, as_attachment=True)import os
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import File
from flask_jwt_extended import jwt_required, get_jwt_identity

files_bp = Blueprint('files', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'ppt', 'pptx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@files_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    current_user_id = int(get_jwt_identity())
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400
        
    if not allowed_file(file.filename):
        return jsonify({"error": "Tipo de arquivo não permitido"}), 400
        
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

@files_bp.route('/files', methods=['GET'])
@jwt_required()
def get_files():
    files = File.query.all()
    return jsonify([{"id": f.id, "filename": f.filename} for f in files]), 200

@files_bp.route('/files/download/<int:id>', methods=['GET'])
@jwt_required()
def download_file(id):
    file = File.query.get_or_404(id)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], file.filename, as_attachment=True)