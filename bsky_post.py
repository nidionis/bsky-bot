#!/usr/bin/env python3
import argparse
import sys
from atproto import Client
from bsky_connect import get_session, last_user


def create_post(text: str, session_string: str, langs=None):
    """Create a Bluesky post using the AT Protocol client."""
    client = Client()
    
    # Use the atproto client's built-in session authentication
    client.login(session_string=session_string)

    if langs:
        post = client.send_post(text, langs=langs)
    else:
        post = client.send_post(text)

    return post


def parse_args():
    parser = argparse.ArgumentParser(description="Create a Bluesky post")
    parser.add_argument("text", help="Text content for the post")
    parser.add_argument("-u", "--user", help="Bluesky username for authentication")
    parser.add_argument("-p", "--password", help="Bluesky password")
    parser.add_argument("-l", "--langs", nargs='+', help="Language codes (e.g., en en-US)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    return parser.parse_args()


def run():
    args = parse_args()

    try:
        # Determine the user first
        user = args.user or last_user()
        if not user:
            print("Error: No user provided and no last user found")
            return 1
            
        # Get session using bsky_connect functionality
        session_string = get_session(user, args.password)

        if args.verbose:
            print(f"Posting as: {user}")
            print(f"Post text: {args.text}")
            if args.langs:
                print(f"Languages: {args.langs}")

        # Create the post using the full session string
        post = create_post(args.text, session_string, args.langs)

        print(f"Post created successfully!")
        print(f"URI: {post.uri}")
        print(f"CID: {post.cid}")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(run())
