from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='applicant')
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.email}>'


class LoanApplication(db.Model):
    __tablename__ = 'loan_applications'

    id = db.Column(db.Integer, primary_key=True)
    reference_id = db.Column(db.String(30), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Personal details
    full_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    marital_status = db.Column(db.String(20), nullable=False)
    education_level = db.Column(db.String(20), nullable=False)

    # Employment and income
    employment_type = db.Column(db.String(20), nullable=False)
    monthly_income = db.Column(db.Float, nullable=False)

    # Identity
    bvn_number = db.Column(db.String(11), nullable=False)
    nin_number = db.Column(db.String(11), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)

    # Loan request
    loan_amount_requested = db.Column(db.Float, nullable=False)
    loan_tenure_months = db.Column(db.Integer, nullable=False)
    existing_loan_defaults = db.Column(db.Integer, nullable=False, default=0)
    existing_loan_amount = db.Column(db.Float, nullable=False, default=0.0)

    # Status
    status = db.Column(db.String(20), nullable=False, default='Pending')
    application_date = db.Column(db.DateTime, default=datetime.utcnow)

    prediction = db.relationship('Prediction', backref='application', uselist=False)

    def __repr__(self):
        return f'<LoanApplication {self.reference_id}>'


class Prediction(db.Model):
    __tablename__ = 'predictions'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(
        db.Integer, db.ForeignKey('loan_applications.id'), nullable=False
    )

    predicted_class = db.Column(db.String(20), nullable=False)
    probability_score = db.Column(db.Float, nullable=False)
    estimated_loan_amount = db.Column(db.Float, nullable=True)
    denial_reason = db.Column(db.String(200), nullable=True)
    key_factors = db.Column(db.Text, nullable=True)
    model_version = db.Column(db.String(20), nullable=False, default='1.0')
    prediction_date = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def eligibility_percentage(self):
        return round(self.probability_score * 100, 1)

    def __repr__(self):
        return f'<Prediction {self.predicted_class} {self.probability_score}>'


class AdminLog(db.Model):
    __tablename__ = 'admin_logs'

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)
    action_description = db.Column(db.String(300), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f'<AdminLog {self.action_type} by admin {self.admin_id}>'
