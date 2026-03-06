"""
Email delivery service.

In development (SMTP_HOST is empty), emails are printed to the application
log instead of being sent.  In production, set SMTP_HOST (and optionally
SMTP_USER / SMTP_PASSWORD / SMTP_TLS) to enable real delivery.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from api.settings import settings

logger = logging.getLogger(__name__)


class EmailService:
    # ── public send helpers ────────────────────────────────────────────────────

    async def send_invite(
        self,
        to_email: str,
        invite_url: str,
        role: str,
    ) -> None:
        subject = "You've been invited to AI Infra Research Dashboard"
        text_body = (
            f"Hi,\n\n"
            f"You have been invited to join the AI Infra Research Dashboard "
            f"as a {role}.\n\n"
            f"Click the link below to set your password and activate your account "
            f"(link expires in {settings.invite_token_ttl_days} days):\n\n"
            f"  {invite_url}\n\n"
            f"If you did not expect this invitation, you can safely ignore this email.\n\n"
            f"— AI Infra Research Dashboard"
        )
        await self._send(to_email, subject, text_body)

    async def send_password_reset(
        self,
        to_email: str,
        reset_url: str,
    ) -> None:
        subject = "Reset your AI Infra Research Dashboard password"
        text_body = (
            f"Hi,\n\n"
            f"We received a request to reset the password for your account "
            f"({to_email}).\n\n"
            f"Click the link below to choose a new password "
            f"(link expires in {settings.reset_token_ttl_min} minutes):\n\n"
            f"  {reset_url}\n\n"
            f"If you did not request a password reset, you can safely ignore this "
            f"email — your password has not been changed.\n\n"
            f"— AI Infra Research Dashboard"
        )
        await self._send(to_email, subject, text_body)

    # ── internal ───────────────────────────────────────────────────────────────

    async def _send(self, to: str, subject: str, body: str) -> None:
        if not settings.smtp_host:
            # Console / log mode — useful for local development
            logger.info(
                "[EMAIL-CONSOLE] To: %s | Subject: %s\n%s",
                to,
                subject,
                body,
            )
            return

        # Offload blocking SMTP I/O to a thread so we don't block the event loop
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._send_sync, to, subject, body)

    def _send_sync(self, to: str, subject: str, body: str) -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from
        msg["To"] = to
        msg.attach(MIMEText(body, "plain"))

        if settings.smtp_tls:
            conn: smtplib.SMTP = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            conn.starttls()
        else:
            conn = smtplib.SMTP(settings.smtp_host, settings.smtp_port)

        try:
            if settings.smtp_user:
                conn.login(settings.smtp_user, settings.smtp_password)
            conn.sendmail(settings.smtp_from, [to], msg.as_string())
        finally:
            conn.quit()

        logger.info("Email sent to %s: %s", to, subject)


email_svc = EmailService()
