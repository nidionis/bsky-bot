#!/usr/bin/env python3
"""
Bluesky connection management using atproto.
Handles JWT token storage, authentication, and session management.
"""

import argparse
import os
import json
import sys
from pathlib import Path
from getpass import getpass
from atproto import Client


# Default configuration
DEFAULT_BSKY_TOKENS_PATH = "/tmp/skY"
DEFAULT_BSKY_DOM = "bsky.social"
DEFAULT_BSKY_ID = "myBot"
DEFAULT_BSKY_PASSWD = ""


def get_config():
    """Get configuration from environment variables or defaults."""
    return {
        'tokens_path': os.getenv('BSKY_TOKENS_PATH', DEFAULT_BSKY_TOKENS_PATH),
        'domain': os.getenv('BSKY_DOM', DEFAULT_BSKY_DOM),
        'user_id': os.getenv('BSKY_ID', DEFAULT_BSKY_ID),
        'password': os.getenv('BSKY_PASSWD', DEFAULT_BSKY_PASSWD)
    }


def get_token_file_path(tokens_path, user_id):
    """Get the full path to the token file for a specific user."""
    tokens_dir = Path(tokens_path)
    tokens_dir.mkdir(parents=True, exist_ok=True)
    return tokens_dir / f"{user_id}.token"


def save_token(user_id, session_string, tokens_path):
    """Save JWT token to file."""
    token_file = get_token_file_path(tokens_path, user_id)

    token_data = {
        'user_id': user_id,
        'session_string': session_string
    }

    try:
        with open(token_file, 'w') as f:
            json.dump(token_data, f)
        return True
    except Exception as e:
        print(f"Error saving token: {e}")
        return False


def load_token(user_id, tokens_path):
    """Load JWT token from file."""
    token_file = get_token_file_path(tokens_path, user_id)

    if not token_file.exists():
        return None

    try:
        with open(token_file, 'r') as f:
            token_data = json.load(f)
        return token_data.get('session_string')
    except Exception as e:
        print(f"Error loading token: {e}")
        return None


def test_token(session_string):
    """Test if a token is still valid."""
    try:
        client = Client()
        client.login(session_string=session_string)
        # Try a simple operation to verify the session works
        client.get_profile(client.me.handle)
        return True
    except Exception:
        return False


def authenticate(user_id, password, domain):
    """Authenticate with Bluesky and return session string."""
    try:
        client = Client()
        client.login(user_id, password)
        return client.export_session_string()
    except Exception as e:
        print(f"Authentication failed: {e}")
        return None


def get_session(user_id=None, password=None):
    """Get a valid session string for the specified user."""
    config = get_config()

    # Use provided user_id or fall back to config
    if not user_id:
        user_id = config['user_id']

    # Use provided password or fall back to config
    if not password:
        password = config['password']

    # Try to load existing token
    session_string = load_token(user_id, config['tokens_path'])

    # Test if existing token is valid
    if session_string and test_token(session_string):
        return session_string

    # Token doesn't exist or is invalid, need to authenticate
    if not password:
        password = getpass(f"Enter password for {user_id}: ")

    # Authenticate and get new session
    session_string = authenticate(user_id, password, config['domain'])
    if not session_string:
        raise Exception("Failed to authenticate")

    # Save the new token
    if not save_token(user_id, session_string, config['tokens_path']):
        print("Warning: Failed to save token")

    return session_string


def last_user():
    """Get the last user that was authenticated."""
    config = get_config()
    tokens_dir = Path(config['tokens_path'])

    if not tokens_dir.exists():
        return None

    # Find the most recently modified token file
    token_files = list(tokens_dir.glob("*.token"))
    if not token_files:
        return None

    latest_file = max(token_files, key=lambda f: f.stat().st_mtime)

    try:
        with open(latest_file, 'r') as f:
            token_data = json.load(f)
        return token_data.get('user_id')
    except Exception:
        return None


def connect(user_id=None, password=None):
    """Connect and return authenticated client and profile info."""
    session_string = get_session(user_id, password)

    client = Client()
    client.login(session_string=session_string)

    profile = client.get_profile(client.me.handle)

    return {
        'client': client,
        'session_string': session_string,
        'profile': profile,
        'user_id': client.me.handle
    }


def parse_args():
    """Parse command line arguments."""
    config = get_config()

    parser = argparse.ArgumentParser(description="Bluesky connection manager")
    parser.add_argument("-u", "--user", default=config['user_id'], 
                       help=f"Bluesky user ID (default: {config['user_id']})")
    parser.add_argument("-p", "--password", default=config['password'],
                       help="Bluesky password")
    parser.add_argument("-d", "--domain", default=config['domain'],
                       help=f"Bluesky domain (default: {config['domain']})")
    parser.add_argument("-t", "--tokens-path", default=config['tokens_path'],
                       help=f"Path to store tokens (default: {config['tokens_path']})")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Verbose output")

    return parser.parse_args()


def main():
    """Main function for testing and initial setup."""
    args = parse_args()

    # Update config with command line arguments
    config = {
        'tokens_path': args.tokens_path,
        'domain': args.domain,
        'user_id': args.user,
        'password': args.password
    }

    try:
        if args.verbose:
            print(f"Connecting as: {config['user_id']}")
            print(f"Domain: {config['domain']}")
            print(f"Tokens path: {config['tokens_path']}")

        # Test connection
        connection_info = connect(config['user_id'], config['password'])

        print(f"Successfully connected as: {connection_info['user_id']}")
        print(f"Display name: {connection_info['profile'].display_name}")
        print(f"Token saved to: {get_token_file_path(config['tokens_path'], config['user_id'])}")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
