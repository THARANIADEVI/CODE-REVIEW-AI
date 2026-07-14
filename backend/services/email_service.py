"""Optional email notification sent after a review finishes. No-ops silently
when SMTP isn't configured (same fallback philosophy as the OpenAI/ESLint
integrations), so the app works with zero external setup and only sends mail
once an admin sets SMTP_HOST/USER/PASSWORD/FROM in the environment."""
import smtplib
from email.mime.text import MIMEText
from flask import current_app


def send_review_notification(user, project, review) -> bool:
    """Returns True if an email was sent, False if skipped (not configured)
    or if sending failed. Never raises — a notification failure must not
    break the analysis response."""
    host = current_app.config.get("SMTP_HOST")
    if not host:
        return False

    try:
        port = current_app.config.get("SMTP_PORT", 587)
        smtp_user = current_app.config.get("SMTP_USER", "")
        smtp_password = current_app.config.get("SMTP_PASSWORD", "")
        from_addr = current_app.config.get("SMTP_FROM") or smtp_user
        frontend_url = current_app.config.get("FRONTEND_URL", "")

        subject = f"Code review ready: {project.project_name} scored {review.review_score}/100"
        body = (
            f"Hi {user.name},\n\n"
            f"Your AI Code Review Assistant review for \"{project.project_name}\" is ready.\n\n"
            f"Score: {review.review_score}/100\n"
            f"Summary: {review.summary}\n\n"
            f"View the full report: {frontend_url}/reviews/{review.id}\n"
        )

        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = user.email

        with smtplib.SMTP(host, port, timeout=10) as server:
            server.starttls()
            if smtp_user:
                server.login(smtp_user, smtp_password)
            server.sendmail(from_addr, [user.email], msg.as_string())
        return True
    except Exception:  # pragma: no cover - network/SMTP failure, never fatal
        current_app.logger.warning("Review notification email failed to send", exc_info=True)
        return False
