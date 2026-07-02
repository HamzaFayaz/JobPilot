"""Optional script to assign legacy single-user data to a new account."""

import argparse
import json
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.config import settings  # noqa: E402
from backend.app.services import auth_service, crypto  # noqa: E402
from backend.app.services.user_store import create_user, get_user_by_email  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate legacy single-user profile to an account")
    parser.add_argument("--email", required=True, help="Email for the new user account")
    parser.add_argument("--password", required=True, help="Password for the new user account")
    args = parser.parse_args()

    db_path = settings.db_path
    if not db_path.exists():
        print(f"No database at {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    tables = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "users" not in tables:
        print("Database is not on multi-user schema yet. Start the API once to migrate.")
        sys.exit(1)

    if get_user_by_email(args.email):
        print(f"User {args.email} already exists.")
        sys.exit(1)

    legacy_backup = settings.data_dir / "legacy_migration_backup.json"
    # Legacy data only exists if someone kept a backup; fresh migrate won't have id=1 profile
    user_id = create_user(args.email, auth_service.hash_password(args.password))
    print(f"Created user id={user_id} for {args.email}")

    if legacy_backup.exists():
        data = json.loads(legacy_backup.read_text(encoding="utf-8"))
        profile = data.get("profile")
        if profile:
            cv_text = profile.get("cv_text") or ""
            enc_cv = crypto.encrypt(cv_text) if cv_text else None
            conn.execute(
                """
                UPDATE profiles SET
                    cv_filename = ?, cv_path = ?, cv_text = ?,
                    skills = ?, skills_extraction_status = ?,
                    target_roles = ?, projects = ?
                WHERE user_id = ?
                """,
                (
                    profile.get("cv_filename"),
                    profile.get("cv_path"),
                    enc_cv,
                    profile.get("skills", "[]"),
                    profile.get("skills_extraction_status", "idle"),
                    profile.get("target_roles", "[]"),
                    profile.get("projects", "[]"),
                    user_id,
                ),
            )
            conn.commit()
            print("Restored profile from legacy_migration_backup.json")
    else:
        print("No legacy_migration_backup.json found — empty profile created.")

    print("Done.")


if __name__ == "__main__":
    main()
