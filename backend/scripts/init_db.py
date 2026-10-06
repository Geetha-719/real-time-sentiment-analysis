"""Create the application role and database if they do not exist.

Run:  python -m backend.scripts.init_db   (or)  python backend/scripts/init_db.py
Connects using POSTGRES_ADMIN_URL and is safe to re-run.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import create_engine, text  # noqa: E402

from app.config import settings  # noqa: E402


def main() -> int:
    admin = create_engine(settings.postgres_admin_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        role_exists = conn.execute(
            text("SELECT 1 FROM pg_roles WHERE rolname = :r"), {"r": settings.postgres_user}
        ).scalar()
        if not role_exists:
            # CREATE ROLE does not accept bind parameters, so quote safely.
            safe_pw = settings.postgres_password.replace("'", "''")
            safe_user = settings.postgres_user.replace('"', '""')
            conn.execute(text(f'CREATE ROLE "{safe_user}" LOGIN PASSWORD \'{safe_pw}\''))
            print(f"Created role {settings.postgres_user}")
        else:
            print(f"Role {settings.postgres_user} already exists")

        db_exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :d"), {"d": settings.postgres_db}
        ).scalar()
        if not db_exists:
            conn.execute(text(f'CREATE DATABASE "{settings.postgres_db}" OWNER "{settings.postgres_user}"'))
            print(f"Created database {settings.postgres_db}")
        else:
            print(f"Database {settings.postgres_db} already exists")

    # Ensure schema ownership / privileges
    from sqlalchemy.engine import make_url

    app_url = make_url(settings.postgres_admin_url).set(database=settings.postgres_db)
    app_engine = create_engine(app_url, isolation_level="AUTOCOMMIT")
    with app_engine.connect() as conn:
        conn.execute(text(f'GRANT ALL ON SCHEMA public TO "{settings.postgres_user}"'))
        conn.execute(text(f'ALTER SCHEMA public OWNER TO "{settings.postgres_user}"'))
    print("Privileges granted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
