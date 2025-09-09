#!/bin/bash

# This script is a wrapper for the bsky-bot CLI to ensure proper environment

# Set up any environment variables if needed
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check for batch download option
if [[ "$1" == "download" && "$3" == "--batch" ]]; then
    handle="$2"
    batch_size="$4"
    instance="$5"

    # Run the command with the batch parameter
    node bin/index.js download "$handle" --batch "$batch_size" "$instance"
else
    # Run bsky-bot with all arguments passed to this script as normal
    node bin/index.js "$@"
fi
