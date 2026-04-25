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


@views_bp.route('/students/available')
def available_students():
    return render_template('available_students.html')


@views_bp.route('/students/<int:student_id>')
def student_association(student_id):
    return render_template('student_association.html', student_id=student_id)
