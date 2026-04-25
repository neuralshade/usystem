import os
from flask import Flask
from config import Config
from app.extensions import db, jwt, bcrypt
from app.routes import register_blueprints

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Cria pasta de uploads caso não exista
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)

    register_blueprints(app)

    return app
