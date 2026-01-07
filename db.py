import os, json, sys
from dotenv import load_dotenv
from supabase import create_client
from pathlib import Path
from PyQt6.QtCore import QStandardPaths

base_path = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
load_dotenv(os.path.join(base_path, ".env"))

# fetches path towards session.json
def get_session_path():
    base = Path(QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation
    ))
    base.mkdir(parents=True, exist_ok=True)
    return base / "session.json"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SESSION_FILE = get_session_path()
APP_NAME = "a-track"

_cached_client = None
_cached_session = None

# initial login for user
def login(email: str, password: str):
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        
        if response.user:
            session = response.session
            if session:
                data = {
                    "access_token": session.access_token,
                    "refresh_token": session.refresh_token,
                    "uid": response.user.id
                }
                with SESSION_FILE.open("w") as f:
                    json.dump(data, f)
                print("logged in successfully")
                return True
    except Exception as e:
        print(f"login error: {e}")
    
    print("invalid credentials")
    return False

# refreshes current session
def refresh_session():
    global _cached_session, _cached_client
    if not SESSION_FILE.exists():
        return None

    try:
        with SESSION_FILE.open("r") as f:
            data = json.load(f)

        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

        refresh_token = data.get("refresh_token")
        if not refresh_token:
            return None

        # refresh session
        response = supabase.auth.refresh_session(refresh_token)

        session = response.session
        if not session:
            return None

        updated_data = {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "uid": session.user.id
        }

        # save updated tokens
        with SESSION_FILE.open("w") as f:
            json.dump(updated_data, f)

        # set new session in client
        supabase.auth.set_session(session.access_token, session.refresh_token)

        _cached_session = updated_data
        _cached_client = supabase
        return updated_data

    except Exception as e:
        print(f"session refresh failed: {e}")
        return None

# gets supabase client for target uid
def get_user_client():
    global _cached_client, _cached_session
    if _cached_client:
        return _cached_client

    # try to refresh session first
    refreshed = refresh_session()
    if not refreshed:
        print("No valid session, please login")
        return None

    return _cached_client

# fetches user id
def get_uid():
    if not SESSION_FILE.exists():
        return None
    try:
        with SESSION_FILE.open("r") as f:
            return json.load(f).get("uid")
    except Exception:
        return None

# checks whether there is an existing session
def has_valid_session():
    if not SESSION_FILE.exists():
        return False

    try:
        with SESSION_FILE.open("r") as f:
            data = json.load(f)

        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        supabase.auth.set_session(
            data.get("access_token"),
            data.get("refresh_token")
        )

        user = supabase.auth.get_user()
        return bool(user.user)
    except Exception:
        return False