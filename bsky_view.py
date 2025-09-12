#!/usr/bin/env python3
"""
Bluesky Download Script - bsky_view.py

A comprehensive tool for downloading various Bluesky entities:
- Profiles and their information
- User feeds (posts by specific users)
- Custom feed generators
- Timelines
- Individual posts and threads
- User lists and their members

Uses bsky_connect.py for authentication and session management.
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import from bsky_connect.py
from bsky_connect import connect, get_config


def download_profile(client, actor: str, limit: int = None) -> Dict[str, Any]:
    """Download profile information for a specific actor."""
    print(f"Downloading profile for: {actor}")

    try:
        profile_data = client.get_profile(actor=actor)

        result = {
            'type': 'profile',
            'actor': actor,
            'data': {
                'did': profile_data.did,
                'handle': profile_data.handle,
                'display_name': profile_data.display_name,
                'description': profile_data.description,
                'avatar': profile_data.avatar,
                'banner': profile_data.banner,
                'followers_count': profile_data.followers_count,
                'follows_count': profile_data.follows_count,
                'posts_count': profile_data.posts_count,
                'created_at': profile_data.created_at,
                'labels': profile_data.labels,
                'viewer': profile_data.viewer
            },
            'downloaded_at': datetime.now().isoformat()
        }

        print(f"Profile downloaded: {profile_data.display_name} (@{profile_data.handle})")
        return result

    except Exception as e:
        print(f"Error downloading profile {actor}: {e}")
        return {}


def download_author_feed(client, actor: str, limit: int = 50, filter_type: str = "posts_with_replies") -> Dict[str, Any]:
    """Download posts from a specific author's feed."""
    print(f"Downloading author feed for: {actor} (limit: {limit})")

    try:
        posts = []
        cursor = None
        remaining_limit = limit if limit else float('inf')

        while remaining_limit > 0:
            batch_size = min(100, remaining_limit) if limit else 50

            feed_data = client.get_author_feed(
                actor=actor,
                filter=filter_type,
                limit=batch_size,
                cursor=cursor
            )

            batch_posts = feed_data.feed
            posts.extend(batch_posts)

            print(f"Downloaded {len(batch_posts)} posts (total: {len(posts)})")

            cursor = feed_data.cursor
            remaining_limit -= len(batch_posts)

            if not cursor or not batch_posts:
                break

        result = {
            'type': 'author_feed',
            'actor': actor,
            'filter': filter_type,
            'total_posts': len(posts),
            'data': posts,
            'downloaded_at': datetime.now().isoformat()
        }

        return result

    except Exception as e:
        print(f"Error downloading author feed for {actor}: {e}")
        return {}


def download_custom_feed(client, feed_uri: str, limit: int = 50) -> Dict[str, Any]:
    """Download posts from a custom feed generator."""
    print(f"Downloading custom feed: {feed_uri} (limit: {limit})")

    try:
        # Get feed generator metadata
        feed_info = client.app.bsky.feed.get_feed_generator({'feed': feed_uri})

        posts = []
        cursor = None
        remaining_limit = limit if limit else float('inf')

        while remaining_limit > 0:
            batch_size = min(100, remaining_limit) if limit else 50

            feed_data = client.app.bsky.feed.get_feed({
                'feed': feed_uri,
                'limit': batch_size,
                'cursor': cursor
            })

            batch_posts = feed_data.feed
            posts.extend(batch_posts)

            print(f"Downloaded {len(batch_posts)} posts (total: {len(posts)})")

            cursor = feed_data.cursor
            remaining_limit -= len(batch_posts)

            if not cursor or not batch_posts:
                break

        result = {
            'type': 'custom_feed',
            'feed_uri': feed_uri,
            'feed_info': {
                'display_name': feed_info.view.display_name,
                'description': feed_info.view.description,
                'creator': feed_info.view.creator.handle,
                'like_count': feed_info.view.like_count,
                'avatar': feed_info.view.avatar
            },
            'total_posts': len(posts),
            'data': posts,
            'downloaded_at': datetime.now().isoformat()
        }

        return result

    except Exception as e:
        print(f"Error downloading custom feed {feed_uri}: {e}")
        return {}


def download_timeline(client, limit: int = 50) -> Dict[str, Any]:
    """Download user's timeline."""
    print(f"Downloading timeline (limit: {limit})")

    try:
        posts = []
        cursor = None
        remaining_limit = limit if limit else float('inf')

        while remaining_limit > 0:
            batch_size = min(100, remaining_limit) if limit else 50

            timeline_data = client.get_timeline(
                limit=batch_size,
                cursor=cursor
            )

            batch_posts = timeline_data.feed
            posts.extend(batch_posts)

            print(f"Downloaded {len(batch_posts)} posts (total: {len(posts)})")

            cursor = timeline_data.cursor
            remaining_limit -= len(batch_posts)

            if not cursor or not batch_posts:
                break

        result = {
            'type': 'timeline',
            'total_posts': len(posts),
            'data': posts,
            'downloaded_at': datetime.now().isoformat()
        }

        return result

    except Exception as e:
        print(f"Error downloading timeline: {e}")
        return {}


def download_post(client, post_uri: str) -> Dict[str, Any]:
    """Download a single post."""
    print(f"Downloading post: {post_uri}")

    try:
        # Extract post from thread response
        thread_data = client.get_post_thread(uri=post_uri, depth=0, parent_height=0)

        result = {
            'type': 'post',
            'post_uri': post_uri,
            'data': thread_data.thread,
            'downloaded_at': datetime.now().isoformat()
        }

        return result

    except Exception as e:
        print(f"Error downloading post {post_uri}: {e}")
        return {}


def download_thread(client, post_uri: str, depth: int = 6, parent_height: int = 80) -> Dict[str, Any]:
    """Download a complete thread."""
    print(f"Downloading thread: {post_uri} (depth: {depth}, parent_height: {parent_height})")

    try:
        thread_data = client.get_post_thread(
            uri=post_uri,
            depth=depth,
            parent_height=parent_height
        )

        result = {
            'type': 'thread',
            'post_uri': post_uri,
            'depth': depth,
            'parent_height': parent_height,
            'data': thread_data.thread,
            'downloaded_at': datetime.now().isoformat()
        }

        return result

    except Exception as e:
        print(f"Error downloading thread {post_uri}: {e}")
        return {}


def download_user_list(client, list_uri: str, limit: int = None) -> Dict[str, Any]:
    """Download a user list and its members."""
    print(f"Downloading list: {list_uri}")

    try:
        members = []
        cursor = None
        remaining_limit = limit if limit else float('inf')

        # Get list info and initial members
        while remaining_limit > 0:
            batch_size = min(100, remaining_limit) if limit else 30

            list_data = client.app.bsky.graph.get_list({
                'list': list_uri,
                'limit': batch_size,
                'cursor': cursor
            })

            batch_members = list_data.items
            members.extend(batch_members)

            print(f"Downloaded {len(batch_members)} members (total: {len(members)})")

            cursor = list_data.cursor
            remaining_limit -= len(batch_members)

            if not cursor or not batch_members:
                break

        result = {
            'type': 'user_list',
            'list_uri': list_uri,
            'list_info': {
                'name': list_data.list.name,
                'description': list_data.list.description,
                'purpose': list_data.list.purpose,
                'creator': list_data.list.creator.handle,
                'member_count': list_data.list.list_item_count,
                'created_at': list_data.list.created_at
            },
            'total_members': len(members),
            'data': members,
            'downloaded_at': datetime.now().isoformat()
        }

        return result

    except Exception as e:
        print(f"Error downloading list {list_uri}: {e}")
        return {}


def download_user_lists(client, actor: str, limit: int = None) -> Dict[str, Any]:
    """Download lists created by a user."""
    print(f"Downloading lists created by: {actor}")

    try:
        lists = []
        cursor = None
        remaining_limit = limit if limit else float('inf')

        while remaining_limit > 0:
            batch_size = min(100, remaining_limit) if limit else 30

            lists_data = client.app.bsky.graph.get_lists({
                'actor': actor,
                'limit': batch_size,
                'cursor': cursor
            })

            batch_lists = lists_data.lists
            lists.extend(batch_lists)

            print(f"Downloaded {len(batch_lists)} lists (total: {len(lists)})")

            cursor = lists_data.cursor
            remaining_limit -= len(batch_lists)

            if not cursor or not batch_lists:
                break

        result = {
            'type': 'user_lists',
            'actor': actor,
            'total_lists': len(lists),
            'data': lists,
            'downloaded_at': datetime.now().isoformat()
        }

        return result

    except Exception as e:
        print(f"Error downloading lists for {actor}: {e}")
        return {}


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Download various Bluesky entities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s profile alice.bsky.social
  %(prog)s feed alice.bsky.social --limit 100 --filter posts_no_replies
  %(prog)s timeline --limit 50
  %(prog)s post at://did:plc:abc123/app.bsky.feed.post/xyz789
  %(prog)s thread at://did:plc:abc123/app.bsky.feed.post/xyz789 --depth 10
  %(prog)s list at://did:plc:abc123/app.bsky.graph.list/listkey
  %(prog)s custom-feed at://did:plc:abc123/app.bsky.feed.generator/feedkey
  %(prog)s user-lists alice.bsky.social
        """
    )

    # Authentication options
    auth_group = parser.add_argument_group('Authentication')
    auth_group.add_argument('-u', '--user', help='Bluesky user ID')
    auth_group.add_argument('-p', '--password', help='Bluesky password')

    # Output options
    output_group = parser.add_argument_group('Output')
    output_group.add_argument('-v', '--verbose', action='store_true',
                             help='Verbose output')

    # General options
    parser.add_argument('-l', '--limit', type=int,
                       help='Maximum number of items to download')

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Profile command
    profile_parser = subparsers.add_parser('profile', help='Download user profile')
    profile_parser.add_argument('actor', help='User handle or DID')

    # Author feed command
    feed_parser = subparsers.add_parser('feed', help='Download author feed')
    feed_parser.add_argument('actor', help='User handle or DID')
    feed_parser.add_argument('--filter', choices=[
        'posts_with_replies', 'posts_no_replies', 'posts_with_media', 'posts_and_author_threads'
    ], default='posts_with_replies', help='Filter type for posts')

    # Timeline command
    timeline_parser = subparsers.add_parser('timeline', help='Download your timeline')

    # Post command
    post_parser = subparsers.add_parser('post', help='Download single post')
    post_parser.add_argument('uri', help='Post URI')

    # Thread command
    thread_parser = subparsers.add_parser('thread', help='Download thread')
    thread_parser.add_argument('uri', help='Post URI')
    thread_parser.add_argument('--depth', type=int, default=6,
                              help='Thread depth (default: 6)')
    thread_parser.add_argument('--parent-height', type=int, default=80,
                              help='Parent height (default: 80)')

    # List command
    list_parser = subparsers.add_parser('list', help='Download user list')
    list_parser.add_argument('uri', help='List URI')

    # Custom feed command
    custom_feed_parser = subparsers.add_parser('custom-feed', help='Download custom feed')
    custom_feed_parser.add_argument('uri', help='Feed generator URI')

    # User lists command
    user_lists_parser = subparsers.add_parser('user-lists', help='Download lists created by user')
    user_lists_parser.add_argument('actor', help='User handle or DID')

    return parser


def main():
    """Main function."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        # Connect to Bluesky
        connection = connect(args.user, args.password)
        client = connection['client']

        if args.verbose:
            print(f"Connected as: {connection['user_id']}")

        # Execute command
        result = {}

        if args.command == 'profile':
            result = download_profile(client, args.actor)

        elif args.command == 'feed':
            result = download_author_feed(client, args.actor, args.limit, args.filter)

        elif args.command == 'timeline':
            result = download_timeline(client, args.limit)

        elif args.command == 'post':
            result = download_post(client, args.uri)

        elif args.command == 'thread':
            result = download_thread(client, args.uri, args.depth, args.parent_height)

        elif args.command == 'list':
            result = download_user_list(client, args.uri, args.limit)

        elif args.command == 'custom-feed':
            result = download_custom_feed(client, args.uri, args.limit)

        elif args.command == 'user-lists':
            result = download_user_lists(client, args.actor, args.limit)

        if result:
            # Print JSON data to stdout
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        else:
            print("Download failed - no data retrieved", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
