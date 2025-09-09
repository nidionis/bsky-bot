const fs = require('fs-extra');
const path = require('path');

/**
 * Ensure a directory exists
 */
async function ensureDir(dirPath) {
  try {
    await fs.ensureDir(dirPath);
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Safely read a JSON file
 */
async function safeReadJson(filePath, defaultValue = null) {
  try {
    if (await fs.pathExists(filePath)) {
      return await fs.readJson(filePath);
    }
    return defaultValue;
  } catch (error) {
    return defaultValue;
  }
}

/**
 * Safely write a JSON file with permissions
 */
async function safeWriteJson(filePath, data, options = {}) {
  try {
    await fs.writeJson(filePath, data, { spaces: 2, ...options });
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Get the directory for a specific profile
 */
function getProfileDir(handle) {
  // Sanitize handle for file system use
  const sanitizedHandle = handle.replace(/[^a-zA-Z0-9.\-_]/g, '_');
  return path.join(process.cwd(), 'profiles', sanitizedHandle);
}

module.exports = {
  ensureDir,
  safeReadJson,
  safeWriteJson,
  getProfileDir
};
