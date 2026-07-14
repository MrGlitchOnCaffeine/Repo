import contextlib
import logging
import socket
import traceback

from flask import render_template, url_for
from flask_mail import Message
from app import mail

logger = logging.getLogger(__name__)

# Flask-Mail 0.10.0 calls smtplib.SMTP(server, port) with no timeout
# argument, so a connection that hangs (common on cloud egress to Gmail's
# SMTP port) blocks forever with no exception ever raised. smtplib falls
# back to the interpreter's global default socket timeout when none is
# passed explicitly, so we set that default for the duration of the send
# call only, then restore it — guaranteeing every SMTP call in this module
# raises socket.timeout instead of hanging indefinitely, without affecting
# unrelated sockets elsewhere in the app.
_MAIL_SOCKET_TIMEOUT_SECONDS = 15


@contextlib.contextmanager
def _mail_socket_timeout():
    previous = socket.getdefaulttimeout()
    socket.setdefaulttimeout(_MAIL_SOCKET_TIMEOUT_SECONDS)
    try:
        yield
    finally:
        socket.setdefaulttimeout(previous)


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

        with _mail_socket_timeout():
            mail.send(msg)

        logger.info('Receipt email sent to %s for %s', to_email, application.reference_id)
        return True

    except socket.timeout:
        logger.error(
            'Receipt email to %s for %s timed out after %ss (SMTP connection hung)',
            to_email, application.reference_id, _MAIL_SOCKET_TIMEOUT_SECONDS
        )
        return False

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
    new_status: str,
    admin_comment: str = None,
    application=None,
    application_ref: str = None,
    tracking_url: str = None,
):
    """
    Sends a status decision email after an administrator updates an application.

    This is called synchronously on the main request thread, deliberately —
    the same pattern already proven to work for send_receipt_email. No
    background threading is used here. See gunicorn.conf.py for why
    threading combined with preload_app caused the previous hangs.

    Returns True on success, False on failure. Never raises.
    """
    ref_id = application_ref or (application.reference_id if application else 'unknown')
    subject = f'Application Update - {ref_id}'

    try:
        if tracking_url is None:
            tracking_url = url_for(
                'main.application_details',
                reference_id=ref_id,
                _external=True
            )

        # Minimal proxy so the template works with just a reference string.
        class _AppProxy:
            def __init__(self, ref):
                self.reference_id = ref
                self.application_date = None

        template_app = application if application is not None else _AppProxy(ref_id)

        msg = Message(subject=subject, recipients=[to_email])
        msg.html = render_template(
            'emails/decision_email.html',
            applicant_name=applicant_name,
            application=template_app,
            new_status=new_status,
            admin_comment=admin_comment,
            tracking_url=tracking_url
        )

        with _mail_socket_timeout():
            mail.send(msg)

        logger.info(
            'Decision email sent to %s for %s (status: %s)',
            to_email, ref_id, new_status
        )
        return True

    except socket.timeout:
        logger.error(
            'Decision email to %s for %s timed out after %ss (SMTP connection hung)',
            to_email, ref_id, _MAIL_SOCKET_TIMEOUT_SECONDS
        )
        return False

    except Exception:
        logger.error(
            'Failed to send decision email for %s to %s:\n%s',
            ref_id,
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

        with _mail_socket_timeout():
            mail.send(msg)

        return True

    except socket.timeout:
        logger.error(
            'Result email for %s timed out after %ss (SMTP connection hung)',
            application.reference_id, _MAIL_SOCKET_TIMEOUT_SECONDS
        )
        return False

    except Exception:
        logger.error(
            'Failed to send result email for %s:\n%s',
            application.reference_id,
            traceback.format_exc()
        )
        return False
