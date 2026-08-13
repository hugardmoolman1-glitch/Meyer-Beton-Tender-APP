"""
Sends a reviewed RFQ draft over SMTP. This is only ever called from the
explicit POST /rfq/{id}/send endpoint - never automatically - so a human has
always reviewed the subject/body first.

Configure via environment variables before enabling real sending:
    SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL
    SMTP_USE_TLS=true|false (default true)

If these aren't set, send_email raises SMTPNotConfiguredError with a message
explaining what to set - the app is fully usable without them, it just can't
actually push emails out until they're provided.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


class SMTPNotConfiguredError(RuntimeError):
    pass


def send_email(to_email: str, subject: str, body: str) -> None:
    host = os.environ.get("SMTP_HOST")
    port = os.environ.get("SMTP_PORT")
    username = os.environ.get("SMTP_USERNAME")
    password = os.environ.get("SMTP_PASSWORD")
    from_email = os.environ.get("SMTP_FROM_EMAIL", username)
    use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() != "false"

    if not host or not port or not from_email:
        raise SMTPNotConfiguredError(
            "Email sending isn't configured yet. Set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, "
            "SMTP_PASSWORD and SMTP_FROM_EMAIL as environment variables on the backend, then try again. "
            "Until then, drafts can still be reviewed and copied out manually."
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = to_email
    message.set_content(body)

    with smtplib.SMTP(host, int(port), timeout=20) as server:
        if use_tls:
            server.starttls()
        if username and password:
            server.login(username, password)
        server.send_message(message)
