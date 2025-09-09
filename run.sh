#!/bin/bash

# This script is a wrapper for the bsky-bot CLI to ensure proper environment

# Set up any environment variables if needed
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Run bsky-bot with all arguments passed to this script
node bin/index.js "$@"
