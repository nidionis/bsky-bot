const path = require('path');
const os = require('os');

// Base configuration paths
const CONFIG_DIR = path.join(os.homedir(), '.config', 'bsky-bot');
const ACCOUNTS_DIR = path.join(CONFIG_DIR, 'accounts');
const ACCOUNTS_INDEX = path.join(ACCOUNTS_DIR, 'index.json');
const PROFILES_DIR = path.join(process.cwd(), 'profiles');

// Rate limiting (in milliseconds)
const MIN_DOWNLOAD_INTERVAL = 240000; // 4 minutes
const MAX_DOWNLOAD_INTERVAL = 360000; // 6 minutes

// API endpoints and constants
const BSKY_SERVICE = 'https://bsky.social';
const DEFAULT_PAGE_LIMIT = 100;
const POST_MAX_LENGTH = 300;
const POST_MIN_LENGTH = 1;

// Export constants
module.exports = {
  CONFIG_DIR,
  ACCOUNTS_DIR,
  ACCOUNTS_INDEX,
  PROFILES_DIR,
  MIN_DOWNLOAD_INTERVAL,
  MAX_DOWNLOAD_INTERVAL,
  BSKY_SERVICE,
  DEFAULT_PAGE_LIMIT,
  POST_MAX_LENGTH,
  POST_MIN_LENGTH
};
