#!/usr/bin/env python3
import argparse
import asyncio
import json
from atproto import Client
from bsky_connect import load_token

async def download_profile(handle: str, limit: int = 100, username=None, password=None):
    """Download complete Bluesky profile data including posts, likes, followers, and follows."""
    # Load session token
    session_string = load_token(username, password)

    # Parse session string: handle|did|accessJwt|refreshJwt|pdsEndpoint
    parts = session_string.split("|")
    if len(parts) != 5:
        raise ValueError("Invalid stored session string format")

    handle_from_token, did, access_jwt, refresh_jwt, pds_endpoint = parts

    # Create client and set session
    client = Client(base_url=pds_endpoint)
    client._client.session.headers.update({"Authorization": f"Bearer {access_jwt}"})

    # Get profile information
    profile = client.app.bsky.actor.get_profile(params={'actor': handle})

    # Get author feed (posts)
    posts, cursor = [], None
    while True:
        resp = client.app.bsky.feed.get_author_feed(params={
            'actor': handle, 
            'limit': limit, 
            'cursor': cursor
        })
        posts.extend(resp.feed)
        cursor = resp.cursor
        if not cursor:
            break

    # Get likes
    likes, cursor = [], None
    while True:
        resp = client.app.bsky.feed.get_actor_likes(params={
            'actor': handle,
            'limit': limit,
            'cursor': cursor
        })
        likes.extend(resp.feed)
        cursor = resp.cursor
        if not cursor:
            break

    # Get followers
    followers, cursor = [], None
    while True:
        resp = client.app.bsky.graph.get_followers(params={
            'actor': handle,
            'limit': limit,
            'cursor': cursor
        })
        followers.extend(resp.followers)
        cursor = resp.cursor
        if not cursor:
            break

    # Get follows
    follows, cursor = [], None
    while True:
        resp = client.app.bsky.graph.get_follows(params={
            'actor': handle,
            'limit': limit,
            'cursor': cursor
        })
        follows.extend(resp.follows)
        cursor = resp.cursor
        if not cursor:
            break

    return {
        "profile": profile,
        "posts": posts,
        "likes": likes,
        "followers": followers,
        "follows": follows,
    }

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Download Bluesky profile data")
    parser.add_argument("handle", help="Bluesky handle (e.g. alice.bsky.social)")
    parser.add_argument("-L", "--limit", type=int, default=100, 
                       help="Number of items per request (default: 100)")
    parser.add_argument("-u", "--user", help="Bluesky username for authentication")
    parser.add_argument("-p", "--password", help="Bluesky password (if needed)")
    parser.add_argument("-o", "--output", help="Output JSON file path")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Verbose output")
    return parser.parse_args()

async def run():
    """Main entrypoint function."""
    args = parse_args()

    try:
        if args.verbose:
            print(f"Downloading profile data for: {args.handle}")

        data = await download_profile(
            args.handle, 
            args.limit, 
            args.user, 
            args.password
        )

        # Print summary
        profile_info = data["profile"]
        print(f"Profile: {profile_info.handle}")
        if hasattr(profile_info, 'display_name') and profile_info.display_name:
            print(f"Display Name: {profile_info.display_name}")
        print(f"Posts: {len(data['posts'])}")
        print(f"Likes: {len(data['likes'])}")
        print(f"Followers: {len(data['followers'])}")
        print(f"Follows: {len(data['follows'])}")

        # Save to file if requested
        if args.output:
            # Convert atproto models to dictionaries for JSON serialization
            serializable_data = {
                "profile": profile_info.model_dump() if hasattr(profile_info, 'model_dump') else dict(profile_info),
                "posts": [post.model_dump() if hasattr(post, 'model_dump') else dict(post) for post in data["posts"]],
                "likes": [like.model_dump() if hasattr(like, 'model_dump') else dict(like) for like in data["likes"]],
                "followers": [follower.model_dump() if hasattr(follower, 'model_dump') else dict(follower) for follower in data["followers"]],
                "follows": [follow.model_dump() if hasattr(follow, 'model_dump') else dict(follow) for follow in data["follows"]]
            }

            with open(args.output, 'w') as f:
                json.dump(serializable_data, f, indent=2, default=str)
            print(f"Data saved to: {args.output}")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(run())
    exit(exit_code)
