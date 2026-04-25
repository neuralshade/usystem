from flask import Blueprint, render_template

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    return render_template('login.html')

@views_bp.route('/register')
def register():
    return render_template('register.html')

@views_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')