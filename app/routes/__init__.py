from app.routes.academic import academic_bp
from app.routes.auth import auth_bp
from app.routes.chat import chat_bp
from app.routes.files import files_bp
from app.routes.study import study_bp
from app.routes.users import users_bp
from app.routes.views import views_bp


def register_blueprints(app):
    for blueprint in (auth_bp, users_bp, academic_bp, study_bp, chat_bp, files_bp):
        app.register_blueprint(blueprint, url_prefix="/api")
    app.register_blueprint(views_bp)
