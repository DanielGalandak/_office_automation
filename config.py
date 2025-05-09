import os
from datetime import timedelta

# Základní konfigurace aplikace
SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-for-development')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Konfigurace pro upload souborů
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
TEMP_FOLDER = os.path.join(BASE_DIR, 'temp')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'xlsx', 'docx', 'csv', 'zip', 'rar'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB

# Konfigurace databáze
DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///office_automation.db')

# Konfigurace pro email
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.example.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'user@example.com')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'password')
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')

# Konfigurace pro Redis (pro ukládání úloh a cache)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Konfigurace pro session
PERMANENT_SESSION_LIFETIME = timedelta(days=7)