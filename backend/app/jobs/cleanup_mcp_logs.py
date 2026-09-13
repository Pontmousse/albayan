from app.core.database import SessionLocal
from app.services.mcp_analytics_service import delete_expired_logs


def main() -> None:
    db = SessionLocal()
    try:
        deleted = delete_expired_logs(db)
    finally:
        db.close()
    print(f"deleted_mcp_call_logs={deleted}")


if __name__ == "__main__":
    main()
