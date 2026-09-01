from app.core.database import SessionLocal
from app.services.email_automation_service import (
    send_due_review_reminders,
    send_unread_notification_digests,
)


def main() -> None:
    db = SessionLocal()
    try:
        reminders = send_due_review_reminders(db)
        digests = send_unread_notification_digests(db)
    finally:
        db.close()
    print(f"sent_review_reminders={reminders} sent_notification_digests={digests}")


if __name__ == "__main__":
    main()
