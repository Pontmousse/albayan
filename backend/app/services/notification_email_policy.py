import enum

from app.models.enums import NotificationType


class NotificationDelivery(str, enum.Enum):
    IN_APP_ONLY = "in_app_only"
    IMPORTANT_EMAIL = "important_email"


_IMPORTANT_EMAIL_TYPES: set[NotificationType] = set()


def delivery_for_notification(type: NotificationType) -> NotificationDelivery:
    if type in _IMPORTANT_EMAIL_TYPES:
        return NotificationDelivery.IMPORTANT_EMAIL
    return NotificationDelivery.IN_APP_ONLY
