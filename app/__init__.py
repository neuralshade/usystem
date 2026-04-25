import os
from functools import lru_cache
from pathlib import Path

from flask import Flask
from markupsafe import Markup, escape
from config import Config
from app.extensions import db, jwt, bcrypt
from app.routes import register_blueprints

ICON_DIR = Path(__file__).resolve().parent / "static" / "icons"


@lru_cache(maxsize=128)
def _load_icon(name: str) -> str:
    icon_path = ICON_DIR / f"{name}.svg"
    if not icon_path.exists():
        raise FileNotFoundError(f"Icon '{name}' was not found in {ICON_DIR}.")
    return icon_path.read_text(encoding="utf-8").strip()


def render_icon(name: str, class_name: str = "", aria_label: str = "") -> Markup:
    svg = _load_icon(name)
    full_class = "ui-icon"
    if class_name:
        full_class = f"{full_class} {class_name}"

    attrs = [
        f'class="{escape(full_class)}"',
        'focusable="false"',
    ]

    if aria_label:
        attrs.extend([
            'role="img"',
            f'aria-label="{escape(aria_label)}"',
        ])
    else:
        attrs.append('aria-hidden="true"')

    return Markup(svg.replace("<svg", f"<svg {' '.join(attrs)}", 1))

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Cria pasta de uploads caso não exista
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    app.jinja_env.globals["render_icon"] = render_icon

    register_blueprints(app)

    return app
