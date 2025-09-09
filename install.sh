#!/bin/bash

set -e

# Colors
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

echo -e "${BLUE}=== bsky-bot Installer ===${NC}"
echo -e "${BLUE}This script will install bsky-bot and set up your account.${NC}"
echo

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed!${NC}"
    echo -e "${YELLOW}Please install Node.js version 18 or higher before continuing.${NC}"
    echo -e "${YELLOW}Visit https://nodejs.org/ to download and install Node.js.${NC}"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d 'v' -f 2 | cut -d '.' -f 1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo -e "${RED}Error: Node.js version 18 or higher is required.${NC}"
    echo -e "${YELLOW}Current version: $(node -v)${NC}"
    echo -e "${YELLOW}Please upgrade your Node.js installation.${NC}"
    exit 1
fi

echo -e "${GREEN}Node.js version $(node -v) detected. Continuing...${NC}"

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
if [ -f "package.json" ]; then
    npm install
    echo -e "${GREEN}Dependencies installed successfully!${NC}"
else
    echo -e "${RED}Error: package.json not found!${NC}"
    echo -e "${YELLOW}Make sure you are running this script from the bsky-bot directory.${NC}"
    exit 1
fi

# Create .env file if not exists
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo -e "${BLUE}Creating .env file from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}.env file created.${NC}"
fi

# Ask if the user wants to set up an account now
echo
echo -e "${BLUE}Would you like to set up your Bluesky account now? (y/n)${NC}"
read -r SETUP_NOW

if [ "$SETUP_NOW" = "y" ] || [ "$SETUP_NOW" = "Y" ]; then
    echo -e "${BLUE}Running account setup...${NC}"
    node bin/index.js connect
else
    echo -e "${YELLOW}Skipping account setup.${NC}"
    echo -e "${YELLOW}You can set up your account later by running: ./run.sh connect${NC}"
fi

# Make run.sh executable
if [ -f "run.sh" ]; then
    chmod +x run.sh
    echo -e "${GREEN}Made run.sh executable.${NC}"
fi

echo
echo -e "${GREEN}bsky-bot installation complete!${NC}"
echo -e "${GREEN}You can now use the bot with the run.sh script:${NC}"
echo -e "${BLUE}  ./run.sh [command] [options]${NC}"
echo
echo -e "${BLUE}Examples:${NC}"
echo -e "${BLUE}  ./run.sh download username.bsky.social${NC}"
echo -e "${BLUE}  ./run.sh post \"Hello, Bluesky!\"${NC}"
echo -e "${BLUE}  ./run.sh status${NC}"
