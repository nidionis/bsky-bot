#!/usr/bin/env python3
import argparse
import json
import os
from atproto import Client
from bsky_connect import get_session


def fetch_collection(client, method, key: str, handle: str, limit: int):
    """Generic paginator for Bluesky collections."""
    items, cursor = [], None
    while True:
        resp = method({'actor': handle, 'limit': limit, 'cursor': cursor})
        part = getattr(resp, key)
        items.extend(part)
        cursor = getattr(resp, "cursor", None)
        if not cursor:
            break
    return items


def download_profile(handle: str, access_jwt: str, limit: int = 100):
    client = Client()
    client.request.add_additional_header("Authorization", f"Bearer {access_jwt}")

    profile = client.app.bsky.actor.get_profile({'actor': handle})

    posts = fetch_collection(client, client.app.bsky.feed.get_author_feed, "feed", handle, limit)
    likes = fetch_collection(client, client.app.bsky.feed.get_actor_likes, "feed", handle, limit)
    followers = fetch_collection(client, client.app.bsky.graph.get_followers, "followers", handle, limit)
    follows = fetch_collection(client, client.app.bsky.graph.get_follows, "follows", handle, limit)

    return {
        "profile": profile,
        "posts": posts,
        "likes": likes,
        "followers": followers,
        "follows": follows,
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Download Bluesky profile data")
    parser.add_argument("handle", help="Bluesky handle (e.g. alice.bsky.social)")
    parser.add_argument("-L", "--limit", type=int, default=100, help="Items per request")
    parser.add_argument("-u", "--user", help="Bluesky username for authentication")
    parser.add_argument("-p", "--password", help="Bluesky password")
    parser.add_argument("-o", "--output", help="Output JSON file path")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    return parser.parse_args()


def run():
    args = parse_args()
    try:
        session_string = get_session(args.user, args.password)
        _, _, access_jwt, _, _ = session_string.split("|")

        if args.verbose:
            print(f"Downloading profile data for: {args.handle}")
        data = download_profile(args.handle, access_jwt, args.limit)

        profile_info = data["profile"]
        print(f"Profile: {profile_info.handle}")
        if getattr(profile_info, "display_name", None):
            print(f"Display Name: {profile_info.display_name}")
        print(f"Posts: {len(data['posts'])}")
        print(f"Likes: {len(data['likes'])}")
        print(f"Followers: {len(data['followers'])}")
        print(f"Follows: {len(data['follows'])}")

        if args.output:
            def dump(obj):
                return obj.model_dump() if hasattr(obj, "model_dump") else dict(obj)

            serializable_data = {
                "profile": dump(profile_info),
                "posts": [dump(p) for p in data["posts"]],
                "likes": [dump(l) for l in data["likes"]],
                "followers": [dump(f) for f in data["followers"]],
                "follows": [dump(f) for f in data["follows"]],
            }
            with open(args.output, "w") as f:
                json.dump(serializable_data, f, indent=2, default=str)
            print(f"Data saved to: {args.output}")

    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(run())
