#!/bin/bash
# Usage: ./convert.sh input_dir output_dir

in="$1"
out="$2"

[ -z "$in" ] || [ -z "$out" ] && { echo "Usage: $0 input_dir output_dir"; exit 1; }

# python helper
py_script=$(cat <<'EOF'
import json,sys,os

def json_to_markdown(data):
    post = data["post"]
    author = post["author"]
    record = post["record"]
    embed = post.get("embed", {}).get("external", {})

    lines=[]
    if "title" in embed:
        lines.append(f"# {embed['title']}\n")
    lines.append(f"- **Author**: @{author['handle']}")
    lines.append(f"- **Date**: {record['createdAt']}")
    lines.append(f"- **Likes**: {post['likeCount']} | **Reposts**: {post['repostCount']} | **Replies**: {post['replyCount']}\n")

    text=record.get("text","").strip()
    if text:
        lines.append(text+"\n")
    if "uri" in embed:
        lines.append(f"[{embed.get('title','')}]({embed['uri']})")
        if "description" in embed:
            lines.append(f"> {embed['description']}")
        if "thumb" in embed:
            lines.append(f"![thumbnail]({embed['thumb']})\n")
    return "\n".join(lines)

data=json.load(sys.stdin)
print(json_to_markdown(data))
EOF
)

# walk files
find "$in" -type f -name '*.json' | while read -r f; do
    rel="${f#$in/}"
    out_file="$out/${rel%.json}.md"
    mkdir -p "$(dirname "$out_file")"
    python3 -c "$py_script" < "$f" > "$out_file"
done


##!/usr/bin/python3
#import json
#import sys
#
#def json_to_markdown(data):
#    post = data["post"]
#    author = post["author"]
#    record = post["record"]
#    embed = post.get("embed", {}).get("external", {})
#
#    lines = []
#    # Title
#    if "title" in embed:
#        lines.append(f"# {embed['title']}")
#        lines.append("")
#
#    # Meta
#    lines.append(f"- **Author**: @{author['handle']}")
#    lines.append(f"- **Date**: {record['createdAt']}")
#    lines.append(f"- **Likes**: {post['likeCount']} | **Reposts**: {post['repostCount']} | **Replies**: {post['replyCount']}")
#    lines.append("")
#
#    # Text
#    text = record.get("text", "").strip()
#    if text:
#        lines.append(text)
#        lines.append("")
#
#    # Embed
#    if "uri" in embed:
#        lines.append(f"[{embed['title']}]({embed['uri']})")
#        if "description" in embed:
#            lines.append(f"> {embed['description']}")
#        if "thumb" in embed:
#            lines.append(f"![thumbnail]({embed['thumb']})")
#        lines.append("")
#
#    return "\n".join(lines)
#
#if __name__ == "__main__":
#    data = json.load(sys.stdin)
#    print(json_to_markdown(data))
#