#!/usr/bin/env python3
import argparse
import json
import sys
from bsky_connect import connect


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


def download_profile(client, handle: str, limit: int = 100):
    """Download all profile data for a given handle using authenticated client."""

    # Get profile information
    try:
        profile = client.app.bsky.actor.get_profile({'actor': handle})
    except Exception as e:
        raise Exception(f"Failed to get profile: {parse_error_message(e)}")

    # Initialize collections
    posts, likes, followers, follows = [], [], [], []

    # Download posts
    try:
        posts = fetch_collection(client, client.app.bsky.feed.get_author_feed, "feed", handle, limit)
    except Exception as e:
        print(f"Warning: Could not fetch posts for {handle}: {parse_error_message(e)}", file=sys.stderr)

    # Download likes
    try:
        likes = fetch_collection(client, client.app.bsky.feed.get_actor_likes, "feed", handle, limit)
    except Exception as e:
        print(f"Warning: Could not fetch likes for {handle}: {parse_error_message(e)}", file=sys.stderr)

    # Download followers
    try:
        followers = fetch_collection(client, client.app.bsky.graph.get_followers, "followers", handle, limit)
    except Exception as e:
        print(f"Warning: Could not fetch followers for {handle}: {parse_error_message(e)}", file=sys.stderr)

    # Download follows
    try:
        follows = fetch_collection(client, client.app.bsky.graph.get_follows, "follows", handle, limit)
    except Exception as e:
        print(f"Warning: Could not fetch follows for {handle}: {parse_error_message(e)}", file=sys.stderr)

    return {
        "profile": profile,
        "posts": posts,
        "likes": likes,
        "followers": followers,
        "follows": follows,
    }


def serialize_data(obj):
    """Convert atproto objects to serializable format."""
    return obj.model_dump() if hasattr(obj, "model_dump") else dict(obj)


def normalize_handle(handle):
    """Normalize and validate Bluesky handle format."""
    handle = handle.strip().lower()

    # Remove @ prefix if present
    if handle.startswith('@'):
        handle = handle[1:]

    # Add .bsky.social if no domain is present
    if '.' not in handle:
        handle = f"{handle}.bsky.social"

    return handle


def test_profile_access(client, handle, verbose=False):
    """Test different ways to access a profile for debugging."""
    if verbose:
        print(f"Testing profile access for: {handle}")

    results = {}

    # Test basic profile lookup
    try:
        profile = client.app.bsky.actor.get_profile({'actor': handle})
        results['profile'] = "✓ Accessible"
        if verbose:
            print(f"  Profile lookup: ✓ Success")
    except Exception as e:
        results['profile'] = f"✗ Error: {parse_error_message(e)}"
        if verbose:
            print(f"  Profile lookup: ✗ {parse_error_message(e)}")

    # Test if we can resolve the handle
    try:
        resolved = client.com.atproto.identity.resolve_handle({'handle': handle})
        results['resolve'] = f"✓ DID: {resolved.did}"
        if verbose:
            print(f"  Handle resolution: ✓ {resolved.did}")
    except Exception as e:
        results['resolve'] = f"✗ Error: {parse_error_message(e)}"
        if verbose:
            print(f"  Handle resolution: ✗ {parse_error_message(e)}")

    return results


def parse_error_message(error):
    """Parse error messages from API responses to make them more user-friendly."""
    error_str = str(error)

    # Extract error message from Response objects
    if "Profile not found" in error_str:
        return "Profile not found. The profile might be private, suspended, or the handle is incorrect."
    elif "InvalidRequest" in error_str:
        return "Invalid request. Please check the handle format (e.g., username.bsky.social)."
    elif "Unauthorized" in error_str:
        return "Unauthorized. Please check your authentication credentials."
    elif "RateLimited" in error_str:
        return "Rate limited. Please wait before making more requests."
    else:
        # For other errors, try to extract the core message
        if "message=" in error_str:
            try:
                start = error_str.find("message='") + 9
                end = error_str.find("'", start)
                if start > 8 and end > start:
                    return error_str[start:end]
            except:
                pass
        return f"API error: {error_str}"


def print_profile_summary(data):
    """Print a summary of downloaded profile data."""
    profile_info = data["profile"]
    print(f"Profile: {profile_info.handle}")
    if getattr(profile_info, "display_name", None):
        print(f"Display Name: {profile_info.display_name}")
    print(f"Posts: {len(data['posts'])}")
    print(f"Likes: {len(data['likes'])}")
    print(f"Followers: {len(data['followers'])}")
    print(f"Follows: {len(data['follows'])}")


def save_data_to_file(data, output_path):
    """Save profile data to JSON file."""
    serializable_data = {
        "profile": serialize_data(data["profile"]),
        "posts": [serialize_data(p) for p in data["posts"]],
        "likes": [serialize_data(l) for l in data["likes"]],
        "followers": [serialize_data(f) for f in data["followers"]],
        "follows": [serialize_data(f) for f in data["follows"]],
    }

    with open(output_path, "w") as f:
        json.dump(serializable_data, f, indent=2, default=str)
    print(f"Data saved to: {output_path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Download Bluesky profile data")
    parser.add_argument("handles", nargs='+', help="Bluesky handle(s) (e.g. alice.bsky.social bob.bsky.social)")
    parser.add_argument("-L", "--limit", type=int, default=100, help="Items per request")
    parser.add_argument("-u", "--user", help="Bluesky username for authentication")
    parser.add_argument("-p", "--password", help="Bluesky password")
    parser.add_argument("-o", "--output", help="Output JSON file path (for single handle) or directory (for multiple)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--debug", action="store_true", help="Debug mode with detailed diagnostics")
    parser.add_argument("--test-access", action="store_true", help="Test profile access without downloading data")
    return parser.parse_args()


def main():
    """Main function to handle profile downloading."""
    args = parse_args()

    try:
        # Connect to Bluesky using bsky_connect
        if args.verbose:
            print(f"Connecting to Bluesky as: {args.user or 'default user'}")

        connection_info = connect(args.user, args.password)
        client = connection_info['client']

        if args.verbose:
            print(f"Successfully connected as: {connection_info['user_id']}")

        success_count = 0
        total_handles = len(args.handles)

        # Process each handle individually
        for i, handle in enumerate(args.handles):
            # Normalize the handle
            normalized_handle = normalize_handle(handle)

            if args.verbose or total_handles > 1:
                print(f"\n--- Processing {i+1}/{total_handles}: {handle} ---")
                if normalized_handle != handle:
                    print(f"Normalized to: {normalized_handle}")

            # Test access mode - just check if we can access the profile
            if args.test_access:
                results = test_profile_access(client, normalized_handle, args.debug or args.verbose)
                print(f"Access test results for {normalized_handle}:")
                for test, result in results.items():
                    print(f"  {test}: {result}")
                continue

            try:
                # Download profile data
                if args.debug:
                    print(f"Debug: Starting download for {normalized_handle}")

                data = download_profile(client, normalized_handle, args.limit)

                if args.debug:
                    print(f"Debug: Download completed successfully for {normalized_handle}")

                # Print summary
                print_profile_summary(data)

                # Save to file if requested
                if args.output:
                    if total_handles == 1:
                        # Single file for single handle
                        save_data_to_file(data, args.output)
                    else:
                        # Multiple files or directory for multiple handles
                        import os
                        if os.path.isdir(args.output):
                            output_file = os.path.join(args.output, f"{normalized_handle}.json")
                        else:
                            # Create filename with handle
                            base, ext = os.path.splitext(args.output)
                            output_file = f"{base}_{normalized_handle}{ext}"
                        save_data_to_file(data, output_file)

                success_count += 1

            except Exception as e:
                error_msg = parse_error_message(e)
                print(f"Error processing {normalized_handle}: {error_msg}", file=sys.stderr)

                # In debug mode, run diagnostic tests
                if args.debug:
                    print(f"\nDebug: Download failed, running diagnostics for {normalized_handle}")
                    test_results = test_profile_access(client, normalized_handle, True)
                    print("This is unexpected since the profile appears accessible.")

                continue

        if total_handles > 1:
            print(f"\nSummary: Successfully processed {success_count}/{total_handles} profiles")

        return 0 if success_count > 0 else 1

    except Exception as e:
        print(f"Connection error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
