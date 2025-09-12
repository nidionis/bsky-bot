#!/usr/bin/env python3
"""
Bluesky Download Script - bsky_dl.py

A tool that downloads various Bluesky entities and stores them as folder tree structures.
Reuses download functions from bsky_view.py but saves the JSON structure to disk
as a nested folder hierarchy with meaningful filenames and no raw JSON files.

Features:
- Intelligent folder naming based on content (handles, DIDs, URIs)
- Appropriate file extensions (.str, .int, .bool, .url, .at_uri, etc.)
- JSON chunking at configurable depth levels
- No redundant raw JSON files

Uses bsky_view.py for downloading and bsky_connect.py for authentication.
"""

import argparse
import json
import os
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import re

# Import all download functions from bsky_view.py
from bsky_view import (
    download_profile, download_author_feed, download_custom_feed,
    download_timeline, download_post, download_thread, 
    download_user_list, download_user_lists, connect
)


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be safe for use as a filename or directory name."""
    # Convert to string if not already
    name = str(name)
    # Replace problematic characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Replace multiple spaces/underscores with single underscore
    sanitized = re.sub(r'[_\s]+', '_', sanitized)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    # Limit length to prevent filesystem issues
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    # Ensure it's not empty
    if not sanitized:
        sanitized = "unnamed"
    return sanitized


def should_filter_key(key: str) -> bool:
    """Check if a key should be filtered out based on specified criteria."""
    # Exact matches for fields to remove
    filtered_keys = {
        'py_type', 'type', 'start', 'end', 'index', 'size', 'ref', 
        'mime_type', 'bookmarked', 'pinned', 'disabled',
        # Additional noise fields
        'byte_start', 'byte_end', 'activity_subscription', 'blocking',
        'blocking_by_list', 'muted_by_list', 'known_followers',
        'embedding_disabled', 'thread_muted', 'reply_disabled',
        'labels', 'viewer', 'verification', 'associated', 'status',
        'chat', 'feedgens', 'labeler', 'lists', 'starter_packs',
        'entities', 'threadgate', 'feed_context', 'req_id'
    }
    return key in filtered_keys


def filter_empty_and_noise(data: Any) -> Any:
    """Recursively filter out empty values and noise fields."""
    if isinstance(data, dict):
        filtered = {}
        for key, value in data.items():
            # Skip filtered keys
            if should_filter_key(key):
                continue

            # Recursively filter the value
            filtered_value = filter_empty_and_noise(value)

            # Skip empty/null values
            if filtered_value is None:
                continue
            if isinstance(filtered_value, (list, dict)) and len(filtered_value) == 0:
                continue
            if isinstance(filtered_value, str) and filtered_value.strip() == '':
                continue

            # Apply media quality modification for image URLs
            if key in ['fullsize', 'thumb', 'avatar'] and isinstance(filtered_value, str):
                filtered_value = modify_media_quality(filtered_value)

            filtered[key] = filtered_value

        return filtered if filtered else None

    elif isinstance(data, list):
        filtered = []
        for item in data:
            filtered_item = filter_empty_and_noise(item)
            if filtered_item is not None:
                filtered.append(filtered_item)
        return filtered if filtered else None

    else:
        return data


def modify_media_quality(url: str) -> str:
    """Modify media URLs to use low quality versions."""
    if not url or not isinstance(url, str):
        return url

    if 'cdn.bsky.app' in url:
        # Replace fullsize with thumbnail for images
        if 'feed_fullsize' in url:
            url = url.replace('feed_fullsize', 'feed_thumbnail')

        # For other images, try to add quality parameters
        if '@jpeg' in url or '@png' in url:
            # Keep the URL but prefer smaller versions
            pass

    return url


def categorize_item_content(data: Any) -> str:
    """Determine the category for organizing item content into subfolders."""
    if isinstance(data, dict):
        # Post content
        if 'text' in data and 'author' in data:
            return 'posts'
        elif 'post' in data and isinstance(data['post'], dict):
            return 'posts'

        # Profile/author content
        elif 'handle' in data or 'did' in data or 'display_name' in data:
            return 'profiles'

        # Media content
        elif 'fullsize' in str(data) or 'thumb' in str(data) or 'images' in data:
            return 'media'

        # External embeds
        elif 'external' in data or 'embed' in data:
            return 'embeds'

        # Thread/reply content
        elif 'reply' in data or 'parent' in data or 'root' in data:
            return 'threads'

        # Repost reasons
        elif 'reason' in data or 'by' in data:
            return 'interactions'

    return 'content'


def get_meaningful_list_name(item: Any, index: int) -> str:
    """Generate a meaningful name for a list item based on its content."""
    if isinstance(item, dict):
        # Determine category first
        category = categorize_item_content(item)

        # For posts, try to extract meaningful content
        if category == 'posts':
            if 'post' in item and isinstance(item['post'], dict):
                post_data = item['post']
                if 'record' in post_data and 'text' in post_data['record']:
                    text_snippet = str(post_data['record']['text'])[:30].replace('\n', ' ').strip()
                    if text_snippet:
                        safe_text = sanitize_filename(text_snippet)
                        return f"{index:04d}_{category}_{safe_text}"
                if 'author' in post_data and 'handle' in post_data['author']:
                    handle = sanitize_filename(str(post_data['author']['handle']))
                    return f"{index:04d}_{category}_{handle}"

        # For profiles, use handle or display name
        elif category == 'profiles':
            for key in ['handle', 'display_name']:
                if key in item and item[key]:
                    value = sanitize_filename(str(item[key]))
                    return f"{index:04d}_{category}_{value}"

        # Try to find other identifying fields
        for key in ['handle', 'did', 'uri', 'title', 'name', 'display_name']:
            if key in item and item[key]:
                value = str(item[key])
                # For URIs, extract the last part
                if key == 'uri' and '/' in value:
                    value = value.split('/')[-1][:20]
                elif key == 'did' and ':' in value:
                    value = value.split(':')[-1][:15]
                safe_value = sanitize_filename(value)
                return f"{index:04d}_{category}_{safe_value}"

    return f"{index:04d}_item"


def get_filename_for_value(key: str, value: Any) -> str:
    """Generate an appropriate filename based on the key and value type."""
    base_name = sanitize_filename(key) if key else "data"

    if value is None:
        return f"{base_name}.null"
    elif isinstance(value, bool):
        return f"{base_name}.bool"
    elif isinstance(value, int):
        return f"{base_name}.int"
    elif isinstance(value, float):
        return f"{base_name}.float"
    elif isinstance(value, str):
        # Check if it looks like specific data types
        if value.startswith('http://') or value.startswith('https://'):
            return f"{base_name}.url"
        elif value.startswith('at://'):
            return f"{base_name}.at_uri"
        elif '@' in value and '.' in value:
            return f"{base_name}.handle"
        elif value.startswith('did:'):
            return f"{base_name}.did"
        elif len(value) > 100:
            return f"{base_name}.text"
        else:
            return f"{base_name}.str"
    else:
        return f"{base_name}.txt"


def save_json_as_tree(data: Any, base_path: Path, current_depth: int = 0, max_depth: int = 4, parent_key: str = None) -> None:
    """
    Recursively save JSON data as a folder tree structure with filtering and organization.

    Args:
        data: The data to save (dict, list, or primitive)
        base_path: The base directory path
        current_depth: Current recursion depth
        max_depth: Maximum depth before creating files instead of folders
        parent_key: The key from the parent level (for better naming)
    """
    # Apply filtering first
    filtered_data = filter_empty_and_noise(data)
    if filtered_data is None:
        return

    # Ensure base path exists
    base_path.mkdir(parents=True, exist_ok=True)

    if isinstance(filtered_data, dict):
        if current_depth >= max_depth:
            # At max depth, create individual files for each key-value pair
            for key, value in filtered_data.items():
                if isinstance(value, (dict, list)) and len(str(value)) > 500:
                    # Large nested structures get their own JSON file
                    filename = f"{sanitize_filename(key)}.json"
                    with open(base_path / filename, 'w', encoding='utf-8') as f:
                        json.dump(value, f, indent=2, ensure_ascii=False, default=str)
                else:
                    # Small values get individual files
                    filename = get_filename_for_value(key, value)
                    content = json.dumps(value, ensure_ascii=False, default=str) if isinstance(value, (dict, list)) else str(value)
                    with open(base_path / filename, 'w', encoding='utf-8') as f:
                        f.write(content)
        else:
            # Organize content into category subfolders when appropriate
            if parent_key == 'data' and isinstance(filtered_data, dict) and len(filtered_data) > 3:
                # For data sections, create category-based organization
                categorized_content = {}
                uncategorized_content = {}

                for key, value in filtered_data.items():
                    if isinstance(value, dict):
                        category = categorize_item_content(value)
                        if category != 'content':
                            if category not in categorized_content:
                                categorized_content[category] = {}
                            categorized_content[category][key] = value
                        else:
                            uncategorized_content[key] = value
                    else:
                        uncategorized_content[key] = value

                # Save categorized content in subfolders
                for category, content in categorized_content.items():
                    category_path = base_path / category
                    save_json_as_tree(content, category_path, current_depth + 1, max_depth, category)

                # Save uncategorized content directly
                for key, value in uncategorized_content.items():
                    safe_key = sanitize_filename(key)
                    new_path = base_path / safe_key
                    save_json_as_tree(value, new_path, current_depth + 1, max_depth, key)
            else:
                # Regular folder creation for each key
                for key, value in filtered_data.items():
                    safe_key = sanitize_filename(key)
                    new_path = base_path / safe_key
                    save_json_as_tree(value, new_path, current_depth + 1, max_depth, key)

    elif isinstance(filtered_data, list):
        if current_depth >= max_depth:
            # At max depth, create a chunked JSON file
            filename = f"{sanitize_filename(parent_key or 'list')}_chunk.json"
            with open(base_path / filename, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, indent=2, ensure_ascii=False, default=str)
        else:
            # Create meaningfully named folders for each list item with subfolder organization
            for i, item in enumerate(filtered_data):
                safe_name = get_meaningful_list_name(item, i)
                new_path = base_path / safe_name

                # For items, create subfolders to organize their content
                if isinstance(item, dict) and len(item) > 2:
                    # Create content subfolders within each item
                    save_json_as_tree(item, new_path, current_depth + 1, max_depth, f"item_{i}")
                else:
                    save_json_as_tree(item, new_path, current_depth + 1, max_depth, f"item_{i}")

    else:
        # Primitive value - create a file with appropriate extension
        filename = get_filename_for_value(parent_key or "value", filtered_data)

        # Handle different types appropriately
        if filtered_data is None:
            content = "null"
        elif isinstance(filtered_data, bool):
            content = "true" if filtered_data else "false"
        elif isinstance(filtered_data, (int, float)):
            content = str(filtered_data)
        else:
            content = str(filtered_data)

        with open(base_path / filename, 'w', encoding='utf-8') as f:
            f.write(content)


def create_output_directory(base_dir: str, entity_type: str, identifier: str) -> Path:
    """Create a timestamped output directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_identifier = sanitize_filename(identifier) if identifier else "unknown"
    dir_name = f"{entity_type}_{safe_identifier}_{timestamp}"
    output_path = Path(base_dir) / dir_name
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Download Bluesky entities and save as folder tree structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s profile alice.bsky.social -o ./downloads
  %(prog)s feed alice.bsky.social --limit 100 --filter posts_no_replies -d 3
  %(prog)s timeline --limit 50 -o ./my_timeline
  %(prog)s post at://did:plc:abc123/app.bsky.feed.post/xyz789
  %(prog)s thread at://did:plc:abc123/app.bsky.feed.post/xyz789 --depth 10
        """
    )

    # Authentication options
    auth_group = parser.add_argument_group('Authentication')
    auth_group.add_argument('-u', '--user', help='Bluesky user ID')
    auth_group.add_argument('-p', '--password', help='Bluesky password')

    # Output options
    output_group = parser.add_argument_group('Output')
    output_group.add_argument('-o', '--output', default='./downloads',
                             help='Output directory (default: ./downloads)')
    output_group.add_argument('-d', '--max-depth', type=int, default=4,
                             help='Maximum folder depth before creating JSON files (default: 4)')
    output_group.add_argument('--high-quality', action='store_true',
                             help='Keep high-quality media URLs (default: use low quality)')
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
        # Connect to Bluesky (reusing bsky_view's connect function)
        from bsky_connect import connect
        connection = connect(args.user, args.password)
        client = connection['client']

        if args.verbose:
            print(f"Connected as: {connection['user_id']}")

        # Execute command and get data
        result = {}
        identifier = ""

        if args.command == 'profile':
            result = download_profile(client, args.actor)
            identifier = args.actor

        elif args.command == 'feed':
            result = download_author_feed(client, args.actor, args.limit, args.filter)
            identifier = args.actor

        elif args.command == 'timeline':
            result = download_timeline(client, args.limit)
            identifier = connection['user_id']

        elif args.command == 'post':
            result = download_post(client, args.uri)
            identifier = args.uri.split('/')[-1] if '/' in args.uri else args.uri

        elif args.command == 'thread':
            result = download_thread(client, args.uri, args.depth, args.parent_height)
            identifier = args.uri.split('/')[-1] if '/' in args.uri else args.uri

        elif args.command == 'list':
            result = download_user_list(client, args.uri, args.limit)
            identifier = args.uri.split('/')[-1] if '/' in args.uri else args.uri

        elif args.command == 'custom-feed':
            result = download_custom_feed(client, args.uri, args.limit)
            identifier = args.uri.split('/')[-1] if '/' in args.uri else args.uri

        elif args.command == 'user-lists':
            result = download_user_lists(client, args.actor, args.limit)
            identifier = args.actor

        if result:
            # Create output directory
            output_path = create_output_directory(args.output, args.command, identifier)

            if args.verbose:
                print(f"Saving data to: {output_path}")
                print(f"Using maximum folder depth: {args.max_depth}")
                print(f"Media quality: {'high' if args.high_quality else 'low'}")
                print("Filtering out: py_type, type, start, end, index, size, ref, mime_type, bookmarked, pinned, disabled")

            # Save data as organized and filtered folder tree
            save_json_as_tree(result, output_path, max_depth=args.max_depth)

            print(f"Download completed! Filtered and organized data saved to: {output_path}")

            # Print summary
            if args.verbose:
                print(f"Entity type: {result.get('type', 'unknown')}")
                if 'total_posts' in result:
                    print(f"Total posts: {result['total_posts']}")
                if 'total_members' in result:
                    print(f"Total members: {result['total_members']}")
                if 'total_lists' in result:
                    print(f"Total lists: {result['total_lists']}")

                # Count files and directories created
                total_files = sum(1 for _ in output_path.rglob('*') if _.is_file())
                total_dirs = sum(1 for _ in output_path.rglob('*') if _.is_dir())
                print(f"Created {total_files} files in {total_dirs} directories")

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
