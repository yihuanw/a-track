import os
import json
import sys
from dotenv import load_dotenv
from supabase import create_client
from pathlib import Path
from PyQt6.QtCore import QStandardPaths


# ---------- Constants ----------
base_path = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
load_dotenv(os.path.join(base_path, ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

APP_NAME = "a-track"
SESSION_FILE = None

_cached_client = None
_cached_session = None
_supabase_client = None

# Timestamp of last successful refresh to avoid hammering the auth endpoint
# on every single DB call (e.g. every checkbox toggle).
_last_refresh_time = 0
_REFRESH_INTERVAL_SECS = 300  # Re-refresh at most every 5 minutes


# ---------- Session path ----------
def get_session_path():
    global SESSION_FILE
    if SESSION_FILE:
        return SESSION_FILE

    base = Path(QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation
    ))
    base.mkdir(parents=True, exist_ok=True)

    SESSION_FILE = base / "session.json"
    return SESSION_FILE


# ---------- Supabase client ----------
def get_supabase_client():
    global _supabase_client
    if _supabase_client:
        return _supabase_client
    _supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _supabase_client


SESSION_FILE = get_session_path()


# ---------- Login ----------
def login(email: str, password: str):
    global _cached_client, _cached_session, _last_refresh_time
    supabase = get_supabase_client()

    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.user and response.session:
            session = response.session

            data = {
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "uid": response.user.id
            }

            with SESSION_FILE.open("w") as f:
                json.dump(data, f)

            # Warm up the cache so the first post-login DB call is instant
            supabase.auth.set_session(session.access_token, session.refresh_token)
            _cached_session = data
            _cached_client = supabase

            import time
            _last_refresh_time = time.monotonic()

            return True

    except Exception as e:
        print(f"login error: {e}")

    return False


# ---------- Refresh session ----------
def refresh_session():
    """
    Refreshes the Supabase session from the stored refresh token.
    Rate-limited: skips the network call and returns the cached session
    if we refreshed within the last _REFRESH_INTERVAL_SECS seconds.
    """
    global _cached_client, _cached_session, _last_refresh_time

    import time
    now = time.monotonic()

    # Return cached client immediately if we refreshed recently
    if _cached_client and _cached_session and (now - _last_refresh_time) < _REFRESH_INTERVAL_SECS:
        return _cached_session

    if not SESSION_FILE.exists():
        return None

    try:
        with SESSION_FILE.open("r") as f:
            data = json.load(f)

        supabase = get_supabase_client()

        refresh_token = data.get("refresh_token")
        if not refresh_token:
            return None

        response = supabase.auth.refresh_session(refresh_token)
        session = response.session

        if not session:
            return None

        updated_data = {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "uid": session.user.id if session.user else data.get("uid")
        }

        with SESSION_FILE.open("w") as f:
            json.dump(updated_data, f)

        supabase.auth.set_session(
            session.access_token,
            session.refresh_token
        )

        _cached_session = updated_data
        _cached_client = supabase
        _last_refresh_time = now

        return updated_data

    except Exception as e:
        print(f"session refresh failed: {e}")
        return None


# ---------- User client ----------
def get_user_client():
    global _cached_client, _cached_session

    refreshed = refresh_session()
    if not refreshed:
        _cached_client = None
        return None

    return _cached_client


# ---------- UID ----------
def get_uid():
    # Prefer in-memory cache to avoid a file read on every call
    if _cached_session:
        return _cached_session.get("uid")

    if not SESSION_FILE.exists():
        return None

    try:
        with SESSION_FILE.open("r") as f:
            return json.load(f).get("uid")
    except Exception:
        return None


# ---------- Session check ----------
def has_valid_session():
    # Fast path: trust the in-memory cache if it's populated
    if _cached_session:
        return bool(
            _cached_session.get("access_token") and
            _cached_session.get("refresh_token") and
            _cached_session.get("uid")
        )

    if not SESSION_FILE.exists():
        return False

    try:
        with SESSION_FILE.open("r") as f:
            data = json.load(f)

        return bool(
            data.get("access_token") and
            data.get("refresh_token") and
            data.get("uid")
        )

    except Exception:
        return False


# ---------- Logout ----------
def logout():
    global _cached_client, _cached_session, _last_refresh_time

    if SESSION_FILE.exists():
        SESSION_FILE.unlink()

    _cached_client = None
    _cached_session = None
    _last_refresh_time = 0