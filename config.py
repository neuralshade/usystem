import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-jwt-secret')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')