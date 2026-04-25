from app.extensions import db

class StudyPlan(db.Model):
    """Cronograma estratégico (12, 9 ou 6 meses)"""
    __tablename__ = 'study_plans'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    duration_months = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')
    notes = db.Column(db.Text)

class StudyTask(db.Model):
    """Metas semanais do cronograma"""
    __tablename__ = 'study_tasks'
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('study_plans.id'), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    subject = db.Column(db.String(80))
    due_date = db.Column(db.String(50))

class ExamResult(db.Model):
    """Acompanhamento de desempenho em Simulados"""
    __tablename__ = 'exam_results'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exam_title = db.Column(db.String(150), nullable=False)
    score = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(50), nullable=False)
    exam_type = db.Column(db.String(30), nullable=False, default='mock_exam')
    correct_answers = db.Column(db.Integer)
    total_questions = db.Column(db.Integer)
    notes = db.Column(db.Text)


class SharedLink(db.Model):
    """Links compartilhados pelo mentor/professor com o aluno"""
    __tablename__ = 'shared_links'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    url = db.Column(db.String(500), nullable=False)
