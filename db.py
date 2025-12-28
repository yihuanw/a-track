import os, json, sys
from dotenv import load_dotenv
from supabase import create_client

base_path = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
load_dotenv(os.path.join(base_path, ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SESSION_FILE = "session.json"

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
                with open(SESSION_FILE, "w") as f:
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
    if not os.path.exists(SESSION_FILE):
        return None
    
    try:
        with open(SESSION_FILE, "r") as f:
            data = json.load(f)
        
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        # set the session
        supabase.auth.set_session(data.get("access_token"), data.get("refresh_token"))
        
        # try to get user to check if token is valid
        user_response = supabase.auth.get_user()
        
        if user_response.user:
            # update session file with current tokens
            current_session = supabase.auth.get_session()
            if current_session:
                updated_data = {
                    "access_token": current_session.access_token,
                    "refresh_token": current_session.refresh_token,
                    "uid": user_response.user.id
                }
                with open(SESSION_FILE, "w") as f:
                    json.dump(updated_data, f)
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
    refresh_session()
    
    if not os.path.exists(SESSION_FILE):
        print("no session file found")
        return None
    
    try:
        with open(SESSION_FILE, "r") as f:
            data = json.load(f)
        
        access_token = data.get("access_token")
        
        if not access_token:
            print("no access token in session")
            return None
        
        # create client with auth header
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        # set the session
        supabase.auth.set_session(access_token, data.get("refresh_token"))
        
        _cached_client = supabase
        _cached_session = data
        
        return supabase
    except Exception as e:
        print(f"error creating authenticated client: {e}")
        return None

# fetches user id
def get_uid():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r") as f:
            return json.load(f).get("uid")
    except Exception:
        return None

# checks whether there is an existing session
def has_valid_session():
    if not os.path.exists(SESSION_FILE):
        return False

    try:
        with open(SESSION_FILE, "r") as f:
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