const chalk = require('chalk');

/**
 * Check if the environment is properly set up
 */
async function checkEnvironment() {
  // Check Node.js version
  const nodeVersion = process.versions.node;
  const majorVersion = parseInt(nodeVersion.split('.')[0], 10);

  if (majorVersion < 18) {
    throw new Error(`Node.js version 18 or higher is required. You are using version ${nodeVersion}`);
  }

  // Additional environment checks could go here

  return { success: true };
}

module.exports = {
  checkEnvironment
};
