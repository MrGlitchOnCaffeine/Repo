import logging
import traceback

from flask import render_template, url_for
from flask_mail import Message
from app import mail

logger = logging.getLogger(__name__)


def send_receipt_email(to_email: str, applicant_name: str, application):
    """
    Sends a confirmation email after an application is submitted.
    Returns True on success, False on failure. Never raises.
    """
    subject = f'Application Received - {application.reference_id}'

    try:
        tracking_url = url_for(
            'main.application_details',
            reference_id=application.reference_id,
            _external=True
        )

        msg = Message(subject=subject, recipients=[to_email])
        msg.html = render_template(
            'emails/receipt_email.html',
            applicant_name=applicant_name,
            application=application,
            tracking_url=tracking_url
        )

        mail.send(msg)
        logger.info('Receipt email sent to %s for %s', to_email, application.reference_id)
        return True

    except Exception:
        logger.error(
            'Failed to send receipt email for %s to %s:\n%s',
            application.reference_id,
            to_email,
            traceback.format_exc()
        )
        return False


def send_decision_email(
    to_email: str,
    applicant_name: str,
    application,
    new_status: str,
    admin_comment: str = None
):
    """
    Sends a status decision email after an administrator updates an application.
    Returns True on success, False on failure. Never raises.
    """
    subject = f'Application Update - {application.reference_id}'

    try:
        tracking_url = url_for(
            'main.application_details',
            reference_id=application.reference_id,
            _external=True
        )

        msg = Message(subject=subject, recipients=[to_email])
        msg.html = render_template(
            'emails/decision_email.html',
            applicant_name=applicant_name,
            application=application,
            new_status=new_status,
            admin_comment=admin_comment,
            tracking_url=tracking_url
        )

        mail.send(msg)
        logger.info(
            'Decision email sent to %s for %s (status: %s)',
            to_email, application.reference_id, new_status
        )
        return True

    except Exception:
        logger.error(
            'Failed to send decision email for %s to %s:\n%s',
            application.reference_id,
            to_email,
            traceback.format_exc()
        )
        return False


def send_result_email(to_email: str, applicant_name: str, application, prediction):
    """
    Retained for backwards compatibility. Not used in the primary workflow.
    """
    subject = f'Your Loan Eligibility Result - {application.reference_id}'

    try:
        msg = Message(subject=subject, recipients=[to_email])
        msg.html = render_template(
            'emails/result_email.html',
            applicant_name=applicant_name,
            application=application,
            prediction=prediction
        )
        mail.send(msg)
        return True

    except Exception:
        logger.error(
            'Failed to send result email for %s:\n%s',
            application.reference_id,
            traceback.format_exc()
        )
        return False
