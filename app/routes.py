from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, LoanApplication, Prediction
from app.validators import validate_application
from app.decision_engine import evaluate


def generate_reference_id():
    from datetime import date
    import random
    today = date.today().strftime('%Y%m%d')
    suffix = str(random.randint(1000, 9999))
    return f'LEPS-{today}-{suffix}'


main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone_number = request.form.get('phone_number', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []

        if not full_name:
            errors.append('Full name is required.')
        if not email:
            errors.append('Email address is required.')
        if not phone_number:
            errors.append('Phone number is required.')
        if not password:
            errors.append('Password is required.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        if not errors:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                errors.append('An account with this email address already exists.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html',
                                   full_name=full_name,
                                   email=email,
                                   phone_number=phone_number)

        user = User(
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            role='applicant'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Your account has been created. Please log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html')


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('main.admin_dashboard'))
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        errors = []
        if not email:
            errors.append('Email address is required.')
        if not password:
            errors.append('Password is required.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('login.html', email=email)

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Incorrect email address or password.', 'danger')
            return render_template('login.html', email=email)

        user.last_login = datetime.utcnow()
        db.session.commit()

        login_user(user, remember=bool(remember))

        if user.is_admin():
            return redirect(url_for('main.admin_dashboard'))

        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.index'))

    return render_template('login.html')


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))


@main.route('/apply')
@login_required
def apply():
    if current_user.is_admin():
        return redirect(url_for('main.admin_dashboard'))
    return render_template('form.html')


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('You do not have permission to access that page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


def log_action(action_type, description):
    from app.models import AdminLog
    entry = AdminLog(
        admin_id=current_user.id,
        action_type=action_type,
        action_description=description,
        ip_address=request.remote_addr
    )
    db.session.add(entry)
    db.session.commit()


@main.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    from app.models import AdminLog
    total_applications = LoanApplication.query.count()
    eligible_count = Prediction.query.filter_by(predicted_class='Eligible').count()
    not_eligible_count = Prediction.query.filter_by(predicted_class='Not Eligible').count()
    under_review_count = Prediction.query.filter_by(predicted_class='Under Review').count()
    total_users = User.query.filter_by(role='applicant').count()

    recent_applications = (
        LoanApplication.query
        .order_by(LoanApplication.application_date.desc())
        .limit(10)
        .all()
    )

    return render_template(
        'admin/dashboard.html',
        total_applications=total_applications,
        eligible_count=eligible_count,
        not_eligible_count=not_eligible_count,
        under_review_count=under_review_count,
        total_users=total_users,
        recent_applications=recent_applications
    )


@main.route('/admin/applications')
@login_required
@admin_required
def admin_applications():
    search = request.args.get('search', '').strip()
    result_filter = request.args.get('result', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = LoanApplication.query

    if search:
        query = query.filter(
            db.or_(
                LoanApplication.full_name.ilike(f'%{search}%'),
                LoanApplication.reference_id.ilike(f'%{search}%')
            )
        )

    if result_filter:
        query = query.join(Prediction).filter(
            Prediction.predicted_class == result_filter
        )

    if status_filter:
        query = query.filter(LoanApplication.status == status_filter)

    applications = query.order_by(LoanApplication.application_date.desc()).all()

    return render_template(
        'admin/applications.html',
        applications=applications,
        search=search,
        result_filter=result_filter,
        status_filter=status_filter
    )


@main.route('/admin/application/<reference_id>')
@login_required
@admin_required
def admin_application_detail(reference_id):
    import json
    application = LoanApplication.query.filter_by(
        reference_id=reference_id
    ).first()

    if not application:
        flash('Application not found.', 'danger')
        return redirect(url_for('main.admin_applications'))

    key_factors = []
    if application.prediction and application.prediction.key_factors:
        try:
            key_factors = json.loads(application.prediction.key_factors)
        except (ValueError, TypeError):
            key_factors = []

    return render_template(
        'admin/detail.html',
        application=application,
        prediction=application.prediction,
        key_factors=key_factors
    )


@main.route('/admin/application/<reference_id>/update', methods=['POST'])
@login_required
@admin_required
def admin_update_application(reference_id):
    application = LoanApplication.query.filter_by(
        reference_id=reference_id
    ).first()

    if not application:
        flash('Application not found.', 'danger')
        return redirect(url_for('main.admin_applications'))

    new_status = request.form.get('status', '').strip()
    override_result = request.form.get('override_result', '').strip()

    valid_statuses = ['Pending', 'Processed', 'Reviewed']
    valid_results = ['Eligible', 'Not Eligible', 'Under Review']

    if new_status and new_status in valid_statuses:
        old_status = application.status
        application.status = new_status
        db.session.commit()
        log_action(
            'status_update',
            f'Updated status of {reference_id} from {old_status} to {new_status}'
        )
        flash(f'Status updated to {new_status}.', 'success')

    if override_result and override_result in valid_results and application.prediction:
        old_result = application.prediction.predicted_class
        application.prediction.predicted_class = override_result
        db.session.commit()
        log_action(
            'override',
            f'Overrode prediction of {reference_id} from {old_result} to {override_result}'
        )
        flash(f'Result overridden to {override_result}.', 'success')

    return redirect(url_for('main.admin_application_detail', reference_id=reference_id))


@main.route('/admin/applicants')
@login_required
@admin_required
def admin_applicants():
    search = request.args.get('search', '').strip()
    query = User.query.filter_by(role='applicant')

    if search:
        query = query.filter(
            db.or_(
                User.full_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )

    applicants = query.order_by(User.registration_date.desc()).all()
    return render_template('admin/applicants.html', applicants=applicants, search=search)


@main.route('/predict', methods=['POST'])
@login_required
def predict():
    if current_user.is_admin():
        return jsonify({'error': 'Administrators cannot submit loan applications.'}), 403

    raw = request.get_json()
    if not raw:
        return jsonify({'error': 'No data received.'}), 400

    validation = validate_application(raw)
    if not validation['valid']:
        return jsonify({'error': validation['errors'][0]}), 422

    data = validation['data']

    try:
        from app.ml.predict import predict_eligibility
        ml_result = predict_eligibility(data)
    except Exception:
        return jsonify({'error': 'The prediction model is not available. Please run the training script first.'}), 500

    result = evaluate(ml_result['score'], data)

    reference_id = generate_reference_id()

    application = LoanApplication(
        reference_id=reference_id,
        user_id=current_user.id,
        full_name=data['full_name'],
        date_of_birth=data['date_of_birth'],
        age=data['age'],
        gender=data['gender'],
        marital_status=data['marital_status'],
        education_level=data['education_level'],
        employment_type=data['employment_type'],
        monthly_income=data['monthly_income'],
        bvn_number=data['bvn_number'],
        nin_number=data['nin_number'],
        address=data['address'],
        city=data['city'],
        loan_amount_requested=data['loan_amount_requested'],
        loan_tenure_months=data['loan_tenure_months'],
        existing_loan_defaults=data['existing_loan_defaults'],
        existing_loan_amount=data['existing_loan_amount'],
        status='Pending'
    )
    db.session.add(application)
    db.session.flush()

    import json
    prediction = Prediction(
        application_id=application.id,
        predicted_class=result['predicted_class'],
        probability_score=result['probability_score'],
        estimated_loan_amount=result['estimated_loan_amount'],
        denial_reason=result['denial_reason'],
        key_factors=json.dumps(result['key_factors']),
        model_version='1.0'
    )
    db.session.add(prediction)
    db.session.commit()

    try:
        from app.email_service import send_result_email
        send_result_email(
            to_email=current_user.email,
            applicant_name=data['full_name'],
            application=application,
            prediction=prediction
        )
    except Exception:
        pass

    return jsonify({
        'application_id': reference_id,
        'predicted_class': result['predicted_class'],
        'eligibility_percentage': result['eligibility_percentage'],
        'estimated_loan_amount': result['estimated_loan_amount'],
        'denial_reason': result['denial_reason'],
        'key_factors': result['key_factors']
    }), 200


@main.route('/result/<reference_id>')
@login_required
def result(reference_id):
    if current_user.is_admin():
        return redirect(url_for('main.admin_dashboard'))

    application = LoanApplication.query.filter_by(
        reference_id=reference_id,
        user_id=current_user.id
    ).first()

    if not application:
        flash('Application not found.', 'danger')
        return redirect(url_for('main.index'))

    import json
    key_factors = []
    if application.prediction and application.prediction.key_factors:
        try:
            key_factors = json.loads(application.prediction.key_factors)
        except (ValueError, TypeError):
            key_factors = []

    return render_template(
        'result.html',
        application=application,
        prediction=application.prediction,
        key_factors=key_factors
    )


@main.route('/history')
@login_required
def history():
    if current_user.is_admin():
        return redirect(url_for('main.admin_dashboard'))

    applications = LoanApplication.query.filter_by(
        user_id=current_user.id
    ).order_by(LoanApplication.application_date.desc()).all()

    return render_template('history.html', applications=applications)
