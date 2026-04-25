from flask import Blueprint, request, jsonify
from app.extensions import db, bcrypt
from app.models import User
from flask_jwt_extended import create_access_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
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

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if user and bcrypt.check_password_hash(user.password_hash, data.get('password')):
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role, "name": user.name})
        return jsonify({"access_token": token, "role": user.role, "name": user.name, "id": user.id}), 200
    return jsonify({"error": "Credenciais inválidas"}), 401