import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send_email(subject: str, to: list[str], template_name: str, context: dict, from_email: str | None = None) -> bool:
    """Send a multipart email.

    Args:
        subject: Email subject line.
        to: List of recipient email addresses.
        template_name: Path to the HTML template (relative to the templates directory).
        context: Context dictionary passed to the template renderer.
        from_email: Sender address – defaults to ``settings.DEFAULT_FROM_EMAIL``.

    Returns:
        ``True`` on success, ``False`` on any exception (logged).
    """
    try:
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            to=to,
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        logger.info("Email sent: %s to %s", subject, to)
        return True
    except Exception as exc:  # pragma: no cover – defensive
        logger.error("Failed to send email %s to %s: %s", subject, to, exc, exc_info=True)
        return False
