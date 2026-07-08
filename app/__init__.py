from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from config import config
import os

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

login_manager.login_view = 'main.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

from app.models import User


def create_admin():
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_email or not admin_password:
        return

    admin = User.query.filter_by(email=admin_email).first()

    if not admin:
        admin = User(
            full_name=os.getenv("ADMIN_NAME", "Admin User"),
            email=admin_email,
            phone_number=os.getenv("ADMIN_PHONE", ""),
            role="admin"
        )
        admin.set_password(admin_password)
        db.session.add(admin)
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
    mail.init_app(app)
    csrf.init_app(app)

    from app.routes import predict
    csrf.exempt(predict)

    from app.routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()
        create_admin()

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
