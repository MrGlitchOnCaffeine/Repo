import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Brevo transactional email (HTTPS API, not SMTP).
    # BREVO_API_KEY: generated in Brevo dashboard under SMTP & API > API Keys.
    # BREVO_FROM_EMAIL: must be a verified sender in Brevo (Settings > Senders).
    # Both must be set as environment variables on Render.
    BREVO_API_KEY = os.environ.get('BREVO_API_KEY')
    BREVO_FROM_EMAIL = os.environ.get('BREVO_FROM_EMAIL')

    @staticmethod
    def get_database_uri():
        uri = os.environ.get('DATABASE_URL', 'sqlite:///loan_eligibility.db')
        if uri.startswith('postgres://'):
            uri = uri.replace('postgres://', 'postgresql://', 1)
        return uri

    SQLALCHEMY_DATABASE_URI = get_database_uri.__func__()

    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = False


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'sqlite:///loan_eligibility.db'
    )
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
