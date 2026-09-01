from app.core.database import SessionLocal
from app.services.admin_user_service import reconcile_admin_roles


def main() -> None:
    db = SessionLocal()
    try:
        changed = reconcile_admin_roles(db)
    finally:
        db.close()
    print(f"reconciled_admin_roles={changed}")


if __name__ == "__main__":
    main()
