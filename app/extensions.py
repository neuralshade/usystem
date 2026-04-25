from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt

# Inicialização das extensões
db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()