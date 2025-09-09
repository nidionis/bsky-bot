
#!/bin/bash
# Usage: ./json-to-md.py input_dir output_dir

in="$1"
out="$2"

[ -z "$in" ] || [ -z "$out" ] && { echo "Usage: $0 input_dir output_dir"; exit 1; }

# Create media directory
media_dir="$out/media"
mkdir -p "$media_dir"

# python helper
py_script=$(cat <<'EOF'
import json, sys, os, urllib.request, urllib.parse, hashlib
from pathlib import Path

def download_media(url, media_dir, filename_prefix=""):
    """Download media file and return local path"""
    try:
        if not url or not url.startswith('http'):
            return None

        # Create a hash-based filename to avoid conflicts
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

        # Get file extension from URL
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        ext = os.path.splitext(path)[1] if path else ''
        if not ext:
            ext = '.jpg'  # Default extension for images

        filename = f"{filename_prefix}{url_hash}{ext}"
        filepath = os.path.join(media_dir, filename)

        # Skip if already downloaded
        if os.path.exists(filepath):
            return f"media/{filename}"

        # Download the file
        urllib.request.urlretrieve(url, filepath)
        return f"media/{filename}"

    except Exception as e:
        print(f"Failed to download {url}: {e}", file=sys.stderr)
        return None

def json_to_markdown(data, media_dir=""):
    # Handle different JSON structures
    post = None

    # Case 1: Direct post object with "post" key
    if isinstance(data, dict) and "post" in data:
        post = data["post"]
    # Case 2: Direct post object (post data at root)
    elif isinstance(data, dict) and "author" in data and "record" in data:
        post = data
    # Case 3: Array of posts - take the first one
    elif isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], dict) and "post" in data[0]:
            post = data[0]["post"]
        elif isinstance(data[0], dict) and "author" in data[0]:
            post = data[0]

    # If we couldn't extract a post, return a minimal markdown
    if not post:
        return "# Unknown Post Format\n\nCould not parse post data from JSON structure."

    # Extract data safely
    author = post.get("author", {})
    record = post.get("record", {})
    embed = post.get("embed", {})

    lines = []

    # Handle missing author/record data gracefully
    handle = author.get("handle", "unknown")
    created_at = record.get("createdAt", "unknown")
    like_count = post.get("likeCount", 0)
    repost_count = post.get("repostCount", 0)
    reply_count = post.get("replyCount", 0)

    # Title from embed or use author handle
    external_embed = embed.get("external", {})
    if "title" in external_embed:
        lines.append(f"# {external_embed['title']}\n")
    else:
        lines.append(f"# Post by @{handle}\n")

    lines.append(f"- **Author**: @{handle}")
    lines.append(f"- **Date**: {created_at}")
    lines.append(f"- **Likes**: {like_count} | **Reposts**: {repost_count} | **Replies**: {reply_count}\n")

    # Post text
    text = record.get("text", "").strip()
    if text:
        lines.append(text + "\n")

    # Handle different types of embeds
    if embed:
        # External link embed
        if "external" in embed:
            ext = embed["external"]
            if "uri" in ext:
                title = ext.get('title', 'Link')
                lines.append(f"[{title}]({ext['uri']})")
                if "description" in ext:
                    lines.append(f"> {ext['description']}")
                # Download thumbnail
                if "thumb" in ext and media_dir:
                    local_thumb = download_media(ext["thumb"], media_dir, "thumb_")
                    if local_thumb:
                        lines.append(f"![thumbnail]({local_thumb})")
                    else:
                        lines.append(f"![thumbnail]({ext['thumb']})")

        # Image embed
        if "images" in embed:
            for i, img in enumerate(embed["images"]):
                if "fullsize" in img and media_dir:
                    local_img = download_media(img["fullsize"], media_dir, f"img_{i}_")
                    if local_img:
                        alt_text = img.get("alt", f"Image {i+1}")
                        lines.append(f"![{alt_text}]({local_img})")
                    else:
                        lines.append(f"![Image {i+1}]({img['fullsize']})")
                elif "fullsize" in img:
                    lines.append(f"![Image {i+1}]({img['fullsize']})")

        # Video embed
        if "video" in embed:
            video = embed["video"]
            if "playlist" in video:
                lines.append(f"[Video]({video['playlist']})")
            if "thumbnail" in video and media_dir:
                local_thumb = download_media(video["thumbnail"], media_dir, "video_thumb_")
                if local_thumb:
                    lines.append(f"![video thumbnail]({local_thumb})")

    # Handle avatar download
    if "avatar" in author and media_dir:
        local_avatar = download_media(author["avatar"], media_dir, "avatar_")
        if local_avatar:
            lines.insert(-3, f"![avatar]({local_avatar})")  # Insert before metadata

    return "\n".join(lines)

# Get media directory from command line arguments
media_dir = sys.argv[1] if len(sys.argv) > 1 else ""

try:
    data = json.load(sys.stdin)
    print(json_to_markdown(data, media_dir))
except json.JSONDecodeError as e:
    print(f"# JSON Parse Error\n\nCould not parse JSON file: {e}")
except Exception as e:
    print(f"# Processing Error\n\nError processing file: {e}")
EOF
)

# Counter for progress
total_files=$(find "$in" -type f -name '*.json' | wc -l)
current=0

echo "Found $total_files JSON files to process..."

# Process files with progress indication
find "$in" -type f -name '*.json' | while read -r f; do
    current=$((current + 1))
    rel="${f#$in/}"
    out_file="$out/${rel%.json}.md"

    # Show progress every 10 files
    if [ $((current % 10)) -eq 0 ] || [ $current -eq 1 ]; then
        echo "Processing file $current/$total_files: $rel"
    fi

    mkdir -p "$(dirname "$out_file")"

    # Pass media directory to Python script
    python3 -c "$py_script" "$media_dir" < "$f" > "$out_file"

    # Optional: Add a small delay to prevent overwhelming the system
    # sleep 0.1
done

echo "Conversion complete! Processed $total_files files."
echo "Media files saved to: $media_dir"