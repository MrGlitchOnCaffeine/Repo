from flask import render_template
from flask_mail import Message
from app import mail


def send_result_email(to_email: str, applicant_name: str, application, prediction):
    """
    Sends the eligibility result email to the applicant.

    Parameters:
        to_email       - the applicant's registered email address
        applicant_name - the applicant's full name
        application    - the LoanApplication database record
        prediction     - the Prediction database record
    """
    subject = f'Your Loan Eligibility Result - {application.reference_id}'

    msg = Message(
        subject=subject,
        recipients=[to_email]
    )

    msg.html = render_template(
        'emails/result_email.html',
        applicant_name=applicant_name,
        application=application,
        prediction=prediction
    )

    try:
        mail.send(msg)
        return True
    except Exception:
        return False
