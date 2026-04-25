from app import create_app
from app.extensions import db, bcrypt
from app.models.models import User

app = create_app()

with app.app_context():
    # Cria as tabelas do banco
    db.create_all()

    # Criação de dados iniciais (Seed)
    if not User.query.first():
        hashed_pw = bcrypt.generate_password_hash('senha123').decode('utf-8')
        
        teacher = User(name='Professor Carlos', email='teacher@test.com', password_hash=hashed_pw, role='teacher')
        mentor = User(name='Mentor Joao', email='mentor@test.com', password_hash=hashed_pw, role='mentor')
        student = User(name='Aluno Pedro', email='student@test.com', password_hash=hashed_pw, role='student')
        
        db.session.add_all([teacher, mentor, student])
        db.session.commit()
        print("Banco inicializado e usuários criados com sucesso!")
    else:
        print("Banco já contém dados.")