from app import create_app
from app.extensions import db, bcrypt
from app.models.user import User

DEFAULT_PASSWORD = 'senha123'
TEST_USERS = (
    {'name': 'Professor Carlos', 'email': 'teacher@test.com', 'role': 'teacher'},
    {'name': 'Mentor Joao', 'email': 'mentor@test.com', 'role': 'mentor'},
    {'name': 'Aluno Pedro', 'email': 'student@test.com', 'role': 'student'},
)


def seed_users():
    if User.query.first():
        print("Banco já contém dados.")
        return

    hashed_password = bcrypt.generate_password_hash(DEFAULT_PASSWORD).decode('utf-8')
    users = [User(password_hash=hashed_password, **payload) for payload in TEST_USERS]
    db.session.add_all(users)
    db.session.commit()
    print("Banco inicializado e usuários teste criados com sucesso!")


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_users()


if __name__ == '__main__':
    main()
