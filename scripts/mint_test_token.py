"""Print a valid JWT access token for E2E tests.

Usage:
    venv/bin/python scripts/mint_test_token.py [email]

Defaults to the first user in the DB if no email is given. Used by the
frontend Playwright global-setup to obtain an authenticated session without
going through Google OAuth.
"""
import os
import sys

# Ensure the logbook root (parent of this scripts/ dir) is importable.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.main  # noqa: F401,E402 — registers all ORM models
from app.core.database import SessionLocal  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.features.users.models import User  # noqa: E402


def main() -> int:
    email = sys.argv[1] if len(sys.argv) > 1 else None
    db = SessionLocal()
    try:
        q = db.query(User)
        user = q.filter(User.email == email).first() if email else q.first()
        if not user:
            print("NO_USER", file=sys.stderr)
            return 1
        # Sentinel-wrapped so callers can extract the token despite any log noise.
        print(f"<<<TOKEN>>>{create_access_token(data={'sub': user.id})}<<<END>>>")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
