# bsky-bot

A Node.js CLI tool for archiving Bluesky profiles and posting content.

## Features

- **Profile Archiving**: Download and archive complete Bluesky profiles including posts, following, followers, and likes
- **Rate Limiting**: Built-in rate limiting to prevent API abuse
- **Compression**: Automatically compress downloaded profiles
- **Multi-Account Support**: Manage multiple Bluesky accounts
- **Simple Posting**: Post text content to Bluesky

## Installation

### Requirements

- Node.js 18 or higher
- npm (comes with Node.js)

### Quick Install

1. Clone or download this repository
2. Run the installation script:

```bash
./install.sh
```

The install script will:
- Install required dependencies
- Create a .env file (sorry for passwd in clear)
- Offer to set up your Bluesky account
- Make the run.sh script executable

## Quick Start

Use the `run.sh` script to execute bsky-bot commands:

```bash
# Log in to Bluesky
./run.sh connect

# Download a profile
./run.sh download user.bsky.social

# Post a message
./run.sh post "Hello from bsky-bot!"
```

## Command Reference

### `connect` (or `setup`)

Interactively log in and store your session.

```bash
./run.sh connect
```

You can also set these environment variables instead of interactive login:
- `BSKY_HANDLE`: Your Bluesky handle (e.g., example.bsky.social)
- `BSKY_APP_PASSWORD`: Your Bluesky app password

### `download <handle>`

Download and archive a Bluesky profile.

```bash
./run.sh download user.bsky.social
```

Options:
- `--force`: Override rate limiting
- `--no-compress`: Skip creating a zip archive
- `-v, --verbose`: Show detailed logs

### `post <text>`

Post a simple text message to Bluesky.

```bash
./run.sh post "Hello, Bluesky!"
```

### `switch <handle>`

Switch to another stored account.

```bash
./run.sh switch other-user.bsky.social
```

### `logout`

Log out from the current account.

```bash
./run.sh logout
```

### `status`

Show current account and rate limit information.

```bash
./run.sh status
```

Options:
- `--json`: Output in JSON format

## Output Structure

Downloaded profiles are stored in the `profiles/` directory with the following structure:

```
profiles/
  username.bsky.social/
    infos/
      profile.json       # Profile metadata
      manifest.json      # Download metadata, counts, timestamps
    articles/
      posts-0001.json   # Posts by the user (paginated)
      posts-0002.json
      ...
    interactions/
      following.json    # Accounts the user follows
      followers.json    # Accounts following the user
      likes-0001.json   # Posts liked by the user (if available)
      ...
```

Compressed archives are saved as `profiles/username.bsky.social.zip`.

## Security Notes

- Sessions are stored in `~/.config/bsky-bot/accounts/` with restricted permissions
- Never share your app password or session files
- The application uses file system storage only - no external databases or services

## Troubleshooting

- If you encounter API errors, try again later as Bluesky API may have rate limits
- For permission errors, check that your shell has proper filesystem access
- If the CLI won't start, ensure you have Node.js 18+ installed: `node --version`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
