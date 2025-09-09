# Bluesky Profile Downloader

A comprehensive CLI tool to download and archive Bluesky profiles with rate limiting and compression.

## Features

- 🔐 Persistent authentication (login once, use everywhere)
- 📁 Organized folder structure (articles, interactions, infos)
- 🗜️ Automatic compression to ZIP archives  
- ⏱️ Smart rate limiting (4-6 minutes between downloads)
- 🎲 Randomized delays to avoid detection
- 📊 Status tracking and verbose logging
- 🛡️ Error handling and recovery
- 🔄 Switch between multiple accounts
- 📝 Post text content directly from the command line

## Quick Start

```bash
# Install and setup
npm install
bsky-dl setup

# Download a profile
bsky-dl download username

# Check status
bsky-dl status
```

## Commands

| Command | Description |
|---------|-------------|
| `setup` | Initial authentication with Bluesky |
| `download <username>` | Download and compress a profile |
| `switch <handle>` | Switch to a different Bluesky account |
| `post <text>` | Post a simple text post to Bluesky |
| `status` | Show auth status and rate limit info |
| `logout` | Clear stored authentication |

## Options

| Flag | Description |
|------|-------------|
| `-f, --force` | Skip rate limiting (use with caution) |
| `-n, --no-compress` | Skip compression |
| `-v, --verbose` | Detailed output |
| `-h, --help` | Show help |

## Output Structure

```
profiles/
└── username/
    ├── articles/           # Individual posts as JSON files
    ├── interactions/       # Follows, followers, likes
    ├── infos/             # Profile metadata and download info
    └── username.zip       # Compressed archive
```

## Rate Limiting

- Default: 4-6 minutes between downloads (randomized)
- Persistent across restarts
- Use `--force` to bypass (not recommended)

## Authentication

- Stored securely in `session.json` and `.env`
- No need to re-authenticate between runs
- Use app passwords (not your main password)

## Examples

```bash
# First time setup
bsky-dl setup

# Download a profile with verbose output
bsky-dl download johndoe -v

# Download without compression
bsky-dl download janedoe --no-compress

# Force download (bypass rate limit)
bsky-dl download fastuser --force

# Switch between accounts
bsky-dl switch newuser.bsky.social
bsky-dl switch newuser.bsky.social --password "app-password"

# Post a simple text message
bsky-dl post "Hello, Bluesky world!"

# Post a reply to another post
bsky-dl post "This is my reply" --reply-to "at://did:plc:abcdef/app.bsky.feed.post/12345"

# Check when you can download next
bsky-dl status
```
