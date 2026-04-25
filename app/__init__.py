import os
from flask import Flask
from config import Config
from app.extensions import db, jwt, bcrypt

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Cria pasta de uploads caso não exista
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)

    from app.routes.api import api_bp
    from app.routes.views import views_bp

    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(views_bp)

    return app