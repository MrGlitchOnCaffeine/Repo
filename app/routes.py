from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, LoanApplication, Prediction
from app.validators import validate_application
from app.decision_engine import evaluate
from app.pdf_generator import generate_application_pdf
import json


def generate_reference_id():
    from datetime import date
    import random
    today = date.today().strftime('%Y%m%d')
    suffix = str(random.randint(1000, 9999))
    return f'LEPS-{today}-{suffix}'


main = Blueprint('main', __name__)


@main.route('/')
def index():
    if current_user.is_authenticated and current_user.is_admin():
        return redirect(url_for('main.admin_dashboard'))

    if current_user.is_authenticated:
        applications = (
            LoanApplication.query
            .filter_by(user_id=current_user.id)
            .order_by(LoanApplication.application_date.desc())
            .all()
        )

        latest_application = applications[0] if applications else None

        home_data = {
            'user_name': current_user.full_name or current_user.email,
            'latest_application': latest_application,
            'has_applications': bool(applications),
        }

        return render_template('home.html', home_data=home_data)

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

    page = request.args.get('page', 1, type=int)
    per_page = 25

    pagination = query.order_by(LoanApplication.application_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    applications = pagination.items

    return render_template(
        'admin/applications.html',
        applications=applications,
        pagination=pagination,
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
    from app.models import AdminLog
    from app.email_service import send_decision_email

    application = LoanApplication.query.filter_by(
        reference_id=reference_id
    ).first()

    if not application:
        flash('Application not found.', 'danger')
        return redirect(url_for('main.admin_applications'))

    new_status = request.form.get('status', '').strip()
    admin_comment = request.form.get('admin_comment', '').strip() or None
    notify_applicant = request.form.get('notify_applicant') == 'on'
    override_result = request.form.get('override_result', '').strip()

    valid_statuses = [
        'Pending Review',
        'Under Review',
        'Eligible',
        'Not Eligible',
        'Requires Additional Information',
    ]
    valid_results = ['Eligible', 'Not Eligible', 'Under Review']

    if new_status and new_status in valid_statuses:
        import logging
        import threading
        import traceback
        admin_logger = logging.getLogger(__name__)

        old_status = application.status
        application.status = new_status
        application.admin_comment = admin_comment
        db.session.commit()

        # Email is fired on a background daemon thread and NOT waited on.
        #
        # Render's free tier blocks outbound SMTP ports entirely at the
        # network level (confirmed via Render's own changelog) — no
        # code-level fix can make that connection succeed, only bound how
        # long we wait for it to fail. Waiting on it synchronously — even
        # with a timeout — meant every single status save paid that wait.
        # Firing it and moving on keeps Save Status instant regardless.
        # Once the platform-level SMTP limitation is resolved (paid plan or
        # an HTTP-based email provider), delivery starts working with no
        # further change needed here.
        #
        # email_sent below reflects whether a send was attempted, not
        # confirmed delivery — true delivery confirmation would require
        # waiting on the thread, which is exactly what we're avoiding.
        email_attempted = False
        if notify_applicant:
            from app.models import User
            applicant = application.user if hasattr(application, 'user') else None
            if not applicant:
                applicant = User.query.get(application.user_id)

            if applicant:
                email_attempted = True
                from flask import current_app
                _app            = current_app._get_current_object()
                _to_email       = applicant.email
                _applicant_name = applicant.full_name
                _ref_id         = application.reference_id
                _new_status     = new_status
                _admin_comment  = admin_comment
                _tracking_url   = url_for(
                    'main.application_details',
                    reference_id=application.reference_id,
                    _external=True
                )

                def _send_decision_in_background():
                    with _app.app_context():
                        try:
                            from app.email_service import send_decision_email
                            send_decision_email(
                                to_email=_to_email,
                                applicant_name=_applicant_name,
                                application_ref=_ref_id,
                                new_status=_new_status,
                                admin_comment=_admin_comment,
                                tracking_url=_tracking_url
                            )
                        except Exception:
                            logging.getLogger(__name__).error(
                                'Background decision email failed for %s:\n%s',
                                _ref_id, traceback.format_exc()
                            )

                threading.Thread(target=_send_decision_in_background, daemon=True).start()
            else:
                admin_logger.warning(
                    'Could not find applicant for %s — notification not sent', reference_id
                )

        entry = AdminLog(
            admin_id=current_user.id,
            action_type='status_update',
            action_description=(
                f'Updated status of {reference_id} from {old_status} to {new_status}'
            ),
            email_sent=email_attempted,
            ip_address=request.remote_addr
        )
        db.session.add(entry)
        db.session.commit()

        flash(f'Status updated to {new_status}.', 'success')
        if notify_applicant and not email_attempted:
            flash('Status saved, but no applicant account was found to notify.', 'warning')

    if override_result and override_result in valid_results and application.prediction:
        old_result = application.prediction.predicted_class
        application.prediction.predicted_class = override_result
        db.session.commit()

        entry = AdminLog(
            admin_id=current_user.id,
            action_type='override',
            action_description=(
                f'Overrode prediction of {reference_id} from {old_result} to {override_result}'
            ),
            email_sent=False,
            ip_address=request.remote_addr
        )
        db.session.add(entry)
        db.session.commit()

        flash(f'Result overridden to {override_result}.', 'success')

    return redirect(url_for('main.admin_application_detail', reference_id=reference_id))


@main.route('/admin/applicants')
@login_required
@admin_required
def admin_applicants():
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = User.query.filter_by(role='applicant')

    if search:
        query = query.filter(
            db.or_(
                User.full_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )

    pagination = query.order_by(User.registration_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    applicants = pagination.items

    return render_template(
        'admin/applicants.html',
        applicants=applicants,
        pagination=pagination,
        search=search
    )


@main.route('/admin/applicants/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_applicant(user_id):
    from app.models import AdminLog
    applicant = User.query.get_or_404(user_id)

    if applicant.is_admin():
        flash('Administrator accounts cannot be edited here.', 'danger')
        return redirect(url_for('main.admin_applicants'))

    if request.method == 'POST':
        old_name = applicant.full_name
        old_phone = applicant.phone_number

        new_name = request.form.get('full_name', '').strip()
        new_phone = request.form.get('phone_number', '').strip()

        if not new_name:
            flash('Full name is required.', 'danger')
            return render_template('admin/edit_applicant.html', applicant=applicant)

        applicant.full_name = new_name
        applicant.phone_number = new_phone
        db.session.commit()

        changes = []
        if old_name != new_name:
            changes.append(f'name: {old_name} -> {new_name}')
        if old_phone != new_phone:
            changes.append(f'phone: {old_phone} -> {new_phone}')

        description = f'Edited applicant #{user_id}'
        if changes:
            description += ' (' + ', '.join(changes) + ')'

        entry = AdminLog(
            admin_id=current_user.id,
            action_type='edit_applicant',
            action_description=description,
            email_sent=False,
            ip_address=request.remote_addr
        )
        db.session.add(entry)
        db.session.commit()

        flash(f'Applicant record updated.', 'success')
        return redirect(url_for('main.admin_applicants'))

    return render_template('admin/edit_applicant.html', applicant=applicant)


@main.route('/admin/applicants/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_applicant(user_id):
    from app.models import AdminLog
    applicant = User.query.get_or_404(user_id)

    if applicant.is_admin():
        flash('Administrator accounts cannot be deleted here.', 'danger')
        return redirect(url_for('main.admin_applicants'))

    name_snapshot = applicant.full_name
    LoanApplication.query.filter_by(user_id=user_id).delete()
    db.session.delete(applicant)
    db.session.commit()

    entry = AdminLog(
        admin_id=current_user.id,
        action_type='delete_applicant',
        action_description=f'Deleted applicant #{user_id} ({name_snapshot}) and all associated records',
        email_sent=False,
        ip_address=request.remote_addr
    )
    db.session.add(entry)
    db.session.commit()

    flash(f'Applicant "{name_snapshot}" and all associated applications have been removed.', 'success')
    return redirect(url_for('main.admin_applicants'))


@main.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    from app.models import AdminLog
    from sqlalchemy import func

    total_applications = LoanApplication.query.count()
    total_users = User.query.filter_by(role='applicant').count()

    eligible_count = Prediction.query.filter_by(predicted_class='Eligible').count()
    not_eligible_count = Prediction.query.filter_by(predicted_class='Not Eligible').count()
    under_review_count = Prediction.query.filter_by(predicted_class='Under Review').count()

    approval_rate = round((eligible_count / total_applications * 100), 1) if total_applications > 0 else 0
    denial_rate = round((not_eligible_count / total_applications * 100), 1) if total_applications > 0 else 0
    review_rate = round((under_review_count / total_applications * 100), 1) if total_applications > 0 else 0

    avg_loan = db.session.query(func.avg(LoanApplication.loan_amount_requested)).scalar()
    avg_loan = round(avg_loan, 2) if avg_loan else 0

    max_loan = db.session.query(func.max(LoanApplication.loan_amount_requested)).scalar() or 0
    min_loan = db.session.query(func.min(LoanApplication.loan_amount_requested)).scalar() or 0

    avg_score = db.session.query(func.avg(Prediction.probability_score)).scalar()
    avg_score = round(avg_score * 100, 1) if avg_score else 0

    avg_income = db.session.query(func.avg(LoanApplication.monthly_income)).scalar()
    avg_income = round(avg_income, 2) if avg_income else 0

    employment_breakdown = (
        db.session.query(LoanApplication.employment_type, func.count(LoanApplication.id))
        .group_by(LoanApplication.employment_type)
        .all()
    )

    education_breakdown = (
        db.session.query(LoanApplication.education_level, func.count(LoanApplication.id))
        .group_by(LoanApplication.education_level)
        .all()
    )

    status_breakdown = (
        db.session.query(LoanApplication.status, func.count(LoanApplication.id))
        .group_by(LoanApplication.status)
        .all()
    )

    recent_logs = (
        AdminLog.query
        .order_by(AdminLog.timestamp.desc())
        .limit(10)
        .all()
    )

    try:
        import joblib, os
        model_path = os.path.join(os.path.dirname(__file__), 'ml', 'model.pkl')
        model = joblib.load(model_path)
        model_name = type(model).__name__
    except Exception:
        model_name = 'Unknown'

    return render_template(
        'admin/reports.html',
        total_applications=total_applications,
        total_users=total_users,
        eligible_count=eligible_count,
        not_eligible_count=not_eligible_count,
        under_review_count=under_review_count,
        approval_rate=approval_rate,
        denial_rate=denial_rate,
        review_rate=review_rate,
        avg_loan=avg_loan,
        max_loan=max_loan,
        min_loan=min_loan,
        avg_score=avg_score,
        avg_income=avg_income,
        employment_breakdown=employment_breakdown,
        education_breakdown=education_breakdown,
        status_breakdown=status_breakdown,
        recent_logs=recent_logs,
        model_name=model_name,
    )


@main.route('/admin/diagnostics/smtp-test')
@login_required
@admin_required
def admin_smtp_diagnostic():
    """
    Tests the SMTP connection in three separate stages so we can see exactly
    where it fails: raw TCP connect, STARTTLS handshake, then authenticated
    login. Each stage is timed and reported independently. This settles
    definitively whether the connection is being network-blocked (raw
    connect times out or is refused) versus a config/credentials issue
    (connect succeeds, auth fails).

    Visit this route directly in the browser while logged in as an admin.
    Nothing is sent — no email leaves this diagnostic.
    """
    import socket
    import smtplib
    import time

    server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
    port = current_app.config.get('MAIL_PORT', 587)
    username = current_app.config.get('MAIL_USERNAME')
    password = current_app.config.get('MAIL_PASSWORD')
    sender = current_app.config.get('MAIL_DEFAULT_SENDER')

    stages = []

    # Stage 0: config sanity check — no network involved
    stages.append({
        'stage': '0. Configuration',
        'result': 'INFO',
        'detail': (
            f'MAIL_SERVER={server!r}, MAIL_PORT={port!r}, '
            f'MAIL_USERNAME={"SET" if username else "MISSING"}, '
            f'MAIL_PASSWORD={"SET" if password else "MISSING"}, '
            f'MAIL_DEFAULT_SENDER={sender!r}'
        )
    })

    # Stage 1: DNS resolution — report every address returned, both families
    try:
        addr_infos = socket.getaddrinfo(server, port, proto=socket.IPPROTO_TCP)
        seen = set()
        addr_list = []
        for family, _, _, _, sockaddr in addr_infos:
            ip = sockaddr[0]
            fam_name = 'IPv6' if family == socket.AF_INET6 else 'IPv4'
            key = (fam_name, ip)
            if key not in seen:
                seen.add(key)
                addr_list.append((fam_name, ip, family))

        stages.append({
            'stage': '1. DNS resolution',
            'result': 'INFO',
            'detail': 'Resolved to: ' + ', '.join(f'{fam} {ip}' for fam, ip, _ in addr_list)
        })
    except Exception as e:
        stages.append({
            'stage': '1. DNS resolution',
            'result': 'FAILED',
            'detail': f'{type(e).__name__}: {e}'
        })
        return _render_smtp_diagnostic(stages)

    # Stage 2: try each resolved address individually, IPv4 and IPv6 separately.
    # This tells us definitively whether this is a routing/IPv6 issue (one
    # family fails, the other succeeds) versus a genuine full block (every
    # address, every family, fails the same way).
    sock = None
    working_family = None
    for fam_name, ip, family in addr_list:
        t0 = time.time()
        try:
            s = socket.socket(family, socket.SOCK_STREAM)
            s.settimeout(8)
            s.connect((ip, port))
            elapsed = round(time.time() - t0, 2)
            stages.append({
                'stage': f'2. Connect via {fam_name} ({ip})',
                'result': 'SUCCESS',
                'detail': f'Connected in {elapsed}s'
            })
            sock = s
            working_family = fam_name
            break
        except socket.timeout:
            elapsed = round(time.time() - t0, 2)
            stages.append({
                'stage': f'2. Connect via {fam_name} ({ip})',
                'result': 'TIMEOUT',
                'detail': f'No response after {elapsed}s — packets likely being silently dropped.'
            })
        except OSError as e:
            elapsed = round(time.time() - t0, 2)
            stages.append({
                'stage': f'2. Connect via {fam_name} ({ip})',
                'result': 'FAILED',
                'detail': f'{type(e).__name__}: {e} (after {elapsed}s)'
            })

    if sock is None:
        stages.append({
            'stage': '2. Summary',
            'result': 'ALL FAILED',
            'detail': (
                'Every resolved address failed, across all address families. '
                'This is consistent with the port itself being blocked at '
                'the network level for every route out.'
            )
        })
        return _render_smtp_diagnostic(stages)
    else:
        stages.append({
            'stage': '2. Summary',
            'result': 'INFO',
            'detail': (
                f'Connection succeeded via {working_family}. If another '
                f'family failed above, this was a routing issue for that '
                f'family specifically, not a full port block.'
            )
        })

    # Stage 2: STARTTLS handshake — only reached if TCP connect succeeded
    try:
        smtp = smtplib.SMTP(timeout=10)
        smtp.sock = sock
        smtp.file = sock.makefile('rb')
        smtp.helo()
        smtp.starttls()
        stages.append({
            'stage': '3. STARTTLS handshake',
            'result': 'SUCCESS',
            'detail': 'TLS negotiation completed successfully.'
        })
    except Exception as e:
        stages.append({
            'stage': '3. STARTTLS handshake',
            'result': 'FAILED',
            'detail': f'{type(e).__name__}: {e}'
        })
        return _render_smtp_diagnostic(stages)

    # Stage 3: authenticated login — only reached if TLS succeeded
    try:
        if not username or not password:
            stages.append({
                'stage': '4. Authentication',
                'result': 'SKIPPED',
                'detail': 'MAIL_USERNAME or MAIL_PASSWORD not set — cannot test login.'
            })
        else:
            smtp.login(username, password)
            stages.append({
                'stage': '4. Authentication',
                'result': 'SUCCESS',
                'detail': f'Logged in as {username}. SMTP is fully functional end-to-end.'
            })
    except smtplib.SMTPAuthenticationError as e:
        stages.append({
            'stage': '4. Authentication',
            'result': 'FAILED',
            'detail': (
                f'{e}. If using Gmail, this usually means an App Password '
                f'is required (not your normal Gmail password), or 2FA is '
                f'not enabled on the account.'
            )
        })
    except Exception as e:
        stages.append({
            'stage': '4. Authentication',
            'result': 'FAILED',
            'detail': f'{type(e).__name__}: {e}'
        })
    finally:
        try:
            smtp.quit()
        except Exception:
            pass

    return _render_smtp_diagnostic(stages)


def _render_smtp_diagnostic(stages):
    """Renders the SMTP diagnostic stages as plain, readable HTML."""
    rows = ''
    color_map = {
        'SUCCESS': '#2D6B40',
        'TIMEOUT': '#8C2A1E',
        'REFUSED': '#8C2A1E',
        'FAILED': '#8C2A1E',
        'SKIPPED': '#7A5200',
        'INFO': '#374151',
    }
    for s in stages:
        color = color_map.get(s['result'], '#374151')
        rows += f"""
        <div style="border:1px solid #EAE4D4; border-radius:8px; padding:1rem 1.25rem; margin-bottom:0.85rem; font-family: monospace;">
            <div style="font-weight:700; font-size:0.9rem; margin-bottom:0.3rem;">{s['stage']}</div>
            <div style="color:{color}; font-weight:700; font-size:0.85rem; margin-bottom:0.4rem;">{s['result']}</div>
            <div style="font-size:0.82rem; color:#374151; line-height:1.5;">{s['detail']}</div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SMTP Diagnostic</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 640px; margin: 2rem auto; padding: 0 1rem; background:#F8F5EE;">
        <h2 style="font-size:1.25rem;">SMTP Diagnostic Result</h2>
        <p style="font-size:0.85rem; color:#6B6E7A; margin-bottom:1.5rem;">
            No email was sent. This only tests the connection.
        </p>
        {rows}
        <p style="font-size:0.8rem; color:#9CA3AF; margin-top:1.5rem;">
            Refresh this page to run the test again.
        </p>
    </body>
    </html>
    """
    return html


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

    import json
    import logging
    import threading
    import traceback

    predict_logger = logging.getLogger(__name__)

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
        status='Pending Review'
    )
    db.session.add(application)
    db.session.flush()

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

    predict_logger.info(
        'Application %s committed to database for user %s',
        reference_id, current_user.id
    )

    # Email is fired on a background daemon thread and NOT waited on.
    # Render's free tier blocks outbound SMTP ports entirely at the network
    # level (confirmed via Render's own changelog) — no code-level fix can
    # make that connection succeed, only bound how long we wait for it to
    # fail. Since the connection can never succeed on this plan, waiting on
    # it synchronously (even with a timeout) means every submission pays
    # that wait. Firing it and moving on keeps the response instant either
    # way — once the platform-level SMTP limitation is resolved (paid plan
    # or an HTTP-based email provider), delivery will start working with no
    # further changes needed here.
    from flask import current_app
    _app = current_app._get_current_object()
    _to_email = current_user.email
    _applicant_name = data['full_name']
    _reference_id = reference_id

    def _send_receipt_in_background():
        with _app.app_context():
            try:
                from app.email_service import send_receipt_email
                app_row = LoanApplication.query.filter_by(reference_id=_reference_id).first()
                if app_row:
                    send_receipt_email(
                        to_email=_to_email,
                        applicant_name=_applicant_name,
                        application=app_row
                    )
            except Exception:
                logging.getLogger(__name__).error(
                    'Background receipt email failed for %s:\n%s',
                    _reference_id, traceback.format_exc()
                )

    threading.Thread(target=_send_receipt_in_background, daemon=True).start()

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
    
@main.route('/application-submitted/<reference_id>')
@login_required
def application_submitted(reference_id):
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
        'application_submitted.html',
        application=application,
        prediction=application.prediction,
        key_factors=key_factors
    )

@main.route('/application-details/<reference_id>')
@login_required
def application_details(reference_id):
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
        'application_details.html',
        application=application,
        prediction=application.prediction,
        key_factors=key_factors
    )
    
@main.route('/application-details/<reference_id>/pdf')
@login_required
def download_application_pdf(reference_id):
    if current_user.is_admin():
        return redirect(url_for('main.admin_dashboard'))

    application = LoanApplication.query.filter_by(
        reference_id=reference_id,
        user_id=current_user.id
    ).first()

    if not application:
        flash('Application not found.', 'danger')
        return redirect(url_for('main.index'))

    prediction = application.prediction
    key_factors = []

    if prediction and prediction.key_factors:
        try:
            key_factors = json.loads(prediction.key_factors)
        except (TypeError, ValueError):
            key_factors = []

    pdf_buffer = generate_application_pdf(
        application=application,
        prediction=prediction,
        key_factors=key_factors
    )

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"LEPS_{application.reference_id}.pdf",
        mimetype="application/pdf"
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
