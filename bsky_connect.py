#!/usr/bin/env python3
import os, sys, argparse, requests

API_BASE = "https://bsky.social/xrpc"
PDS_ENDPOINT = "https://bsky.social"
TOKEN_DIR = os.environ.get("BSKY_TOKENS", "/tmp/skY")
LAST_FILE = os.path.join(TOKEN_DIR, ".last")

def token_path(user):
    os.makedirs(TOKEN_DIR, exist_ok=True)
    return os.path.join(TOKEN_DIR, user)

def last_user():
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE) as f: return f.read().strip()
    return None

def save_last(user):
    with open(LAST_FILE, "w") as f: f.write(user)

def read_token(user):
    path = token_path(user)
    if os.path.exists(path):
        with open(path) as f:
            content = f.read().strip()
            if content and len(content.split("|")) == 5:
                return content
    return None

def create_token(user, password):
    if not password:
        sys.exit("password required")
    try:
        r = requests.post(f"{API_BASE}/com.atproto.server.createSession",
                          json={"identifier": user, "password": password})
        r.raise_for_status()
        d = r.json()
        session = "|".join([d["handle"], d["did"], d["accessJwt"], d["refreshJwt"], PDS_ENDPOINT])
    except requests.exceptions.RequestException as e:
        print(f"Network/HTTP error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            try:
                error_data = e.response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Response text: {e.response.text}")
        sys.exit("connection failed")
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit("connection failed")
    with open(token_path(user), "w") as f: f.write(session)
    save_last(user)
    return session

def get_session(user=None, password=None):
    user = user or last_user() or sys.exit("no user provided and no last user found")
    return read_token(user) or create_token(user, password)

def connect(user=None, password=None):
    session_string = get_session(user, password)
    _, _, access, _, _ = session_string.split("|")
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {access}"})
    return s

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-u","--user")
    p.add_argument("-p","--password")
    a = p.parse_args()
    get_session(a.user, a.password)
    print(f"Token ready for user {a.user or last_user()}")

if __name__ == "__main__":
    main()

