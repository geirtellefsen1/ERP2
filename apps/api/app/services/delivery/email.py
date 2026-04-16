import logging

logger = logging.getLogger(__name__)


def send_password_reset_email(to_email: str, reset_url: str) -> None:
    """Send password reset email. Stub -- logs instead of sending."""
    logger.info("Password reset email to %s: %s", to_email, reset_url)
