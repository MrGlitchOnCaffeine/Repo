from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import config
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

login_manager.login_view = 'main.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

from app.models import User


def create_user_if_missing(name, email, password, phone, role):
    if not email or not password:
        return

    user = User.query.filter_by(email=email).first()

    if not user:
        user = User(
            full_name=name,
            email=email,
            phone_number=phone,
            role=role
        )

        user.set_password(password)

        db.session.add(user)
        db.session.commit()


def create_app(config_name='default'):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        template_folder=os.path.join(root, 'templates'),
        static_folder=os.path.join(root, 'static')
    )
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    # Exempt the predict endpoint after blueprint registration so the
    # exempt binds to the fully qualified view function the blueprint exposes.
    csrf.exempt(app.view_functions['main.predict'])

    with app.app_context():
        db.create_all()
    
        create_user_if_missing(
            name=os.getenv("ADMIN_NAME", "Admin User"),
            email=os.getenv("ADMIN_EMAIL"),
            password=os.getenv("ADMIN_PASSWORD"),
            phone=os.getenv("ADMIN_PHONE", ""),
            role="admin"
        )

        create_user_if_missing(
            name=os.getenv("TEST_USER_NAME", "Test Applicant"),
            email=os.getenv("TEST_USER_EMAIL"),
            password=os.getenv("TEST_USER_PASSWORD"),
            phone=os.getenv("TEST_USER_PHONE", ""),
            role="user"
        )

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
