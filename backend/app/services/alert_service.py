"""Alert service stub.

In a production environment this service would integrate with messaging
platforms (e.g. Slack, email) to notify stakeholders of incidents. For
demonstration purposes the implementation simply logs that an alert would
have been sent.
"""

from app.core.logging import get_logger


logger = get_logger(__name__)


def send_alert(incident_id: int, message: str) -> None:
    """Emit a log entry for the alert instead of sending a real notification."""

    logger.info("alert", incident_id=incident_id, message=message)