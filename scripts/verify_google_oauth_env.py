"""Verify GOOGLE_* vars in .env (format + Google token endpoint probe)."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


def main() -> None:
    if not ENV_PATH.exists():
        print("FAIL: .env not found")
        return

    env = load_env(ENV_PATH)
    client_id = env.get("GOOGLE_CLIENT_ID", "")
    client_secret = env.get("GOOGLE_CLIENT_SECRET", "")
    redirect_uri = env.get("GOOGLE_REDIRECT_URI", "")

    checks: list[tuple[str, bool]] = [
        ("GOOGLE_CLIENT_ID set", bool(client_id)),
        (
            "Client ID format",
            bool(re.match(r"^\d+-[a-z0-9]+\.apps\.googleusercontent\.com$", client_id)),
        ),
        ("GOOGLE_CLIENT_SECRET set", bool(client_secret)),
        (
            "Secret format (GOCSPX-)",
            client_secret.startswith("GOCSPX-") and len(client_secret) > 20,
        ),
        (
            "GOOGLE_REDIRECT_URI",
            redirect_uri == "http://localhost:8000/auth/google/callback",
        ),
        (
            "No stray quotes/spaces",
            all(
                v
                and not v.startswith('"')
                and not v.endswith('"')
                and " " not in v
                for v in (client_id, client_secret, redirect_uri)
            ),
        ),
    ]

    print("FORMAT CHECKS")
    all_ok = True
    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")
        all_ok = all_ok and ok

    if not all_ok:
        return

    data = urllib.parse.urlencode(
        {
            "code": "invalid_probe_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
    ).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=data, method="POST"
    )

    print("GOOGLE API PROBE")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = json.loads(exc.read().decode())
    except OSError as exc:
        print(f"  FAIL: network error — {exc}")
        return

    err = body.get("error", "")
    if err == "invalid_grant":
        print(
            "  PASS: Google accepted client ID + secret "
            "(invalid_grant = credentials OK; test code rejected as expected)"
        )
    elif err == "invalid_client":
        print("  FAIL: invalid_client — Client ID or Secret does not match Google Console")
    elif err == "redirect_uri_mismatch":
        print(
            "  FAIL: redirect_uri_mismatch — register "
            "http://localhost:8000/auth/google/callback in Google Console"
        )
    else:
        desc = body.get("error_description", "")[:160]
        print(f"  INFO: error={err!r} desc={desc}")


if __name__ == "__main__":
    main()
