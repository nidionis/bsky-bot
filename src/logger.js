const chalk = require('chalk');

class Logger {
  constructor() {
    this.isVerbose = false;
  }

  /**
   * Set verbose mode
   */
  setVerbose(verbose) {
    this.isVerbose = verbose;
  }

  /**
   * Log a message only in verbose mode
   */
  verbose(message) {
    if (this.isVerbose) {
      console.log(chalk.gray(`[DEBUG] ${message}`));
    }
  }

  /**
   * Log an info message
   */
  info(message) {
    console.log(chalk.blue(`ℹ ${message}`));
  }

  /**
   * Log a success message
   */
  success(message) {
    console.log(chalk.green(`✓ ${message}`));
  }

  /**
   * Log a warning message
   */
  warn(message) {
    console.log(chalk.yellow(`⚠ ${message}`));
  }

  /**
   * Log an error message
   */
  error(message) {
    console.log(chalk.red(`✖ ${message}`));
  }
}

// Singleton instance
const logger = new Logger();

module.exports = logger;
