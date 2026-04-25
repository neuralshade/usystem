from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token

from app.extensions import db, bcrypt
from app.models import User


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    required_fields = ('name', 'email', 'password', 'role')
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({"error": f"Campos obrigatórios: {', '.join(missing_fields)}"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email já cadastrado"}), 400

    hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(
        name=data['name'],
        email=data['email'],
        password_hash=hashed_pw,
        role=data['role']
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Usuário registrado com sucesso"}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({"error": "Email e senha são obrigatórios"}), 400

    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password_hash, password):
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role, "name": user.name})
        return jsonify({"access_token": token, "role": user.role, "name": user.name, "id": user.id}), 200
    return jsonify({"error": "Credenciais inválidas"}), 401
