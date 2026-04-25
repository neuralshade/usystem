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

    # Importa os novos Blueprints modularizados
    from app.routes.api_v1.auth import auth_bp
    from app.routes.api_v1.users import users_bp
    from app.routes.api_v1.academic import academic_bp
    from app.routes.api_v1.study import study_bp
    from app.routes.api_v1.files import files_bp
    
    from app.routes.views import views_bp

    # Registra todos os Blueprints no prefixo /api
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(users_bp, url_prefix='/api')
    app.register_blueprint(academic_bp, url_prefix='/api')
    app.register_blueprint(study_bp, url_prefix='/api')
    app.register_blueprint(files_bp, url_prefix='/api')
    
    # Registra rotas de views padrão
    app.register_blueprint(views_bp)

    return app