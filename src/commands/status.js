const chalk = require('chalk');
const authManager = require('../auth');
const rateLimiter = require('../limiter');

async function statusCommand(options) {
  try {
    // Initialize auth and rate limiter
    await authManager.init();
    await rateLimiter.init();

    // Get accounts information
    const accounts = await authManager.listAccounts();

    // Get rate limit information
    const rateLimitInfo = await rateLimiter.getRateLimitInfo();

    // Format the remaining time in minutes and seconds
    let timeRemainingStr = 'None';
    if (rateLimitInfo.timeRemaining > 0) {
      const minutes = Math.floor(rateLimitInfo.timeRemaining / 60000);
      const seconds = Math.floor((rateLimitInfo.timeRemaining % 60000) / 1000);
      timeRemainingStr = `${minutes}m ${seconds}s`;
    }

    // Prepare the status information
    const statusInfo = {
      currentAccount: accounts.currentHandle || null,
      accounts: accounts.accounts,
      rateLimit: {
        lastDownloadAt: rateLimitInfo.lastDownloadAt,
        nextAllowedAt: rateLimitInfo.nextAllowedAt,
        canDownloadNow: rateLimitInfo.canDownloadNow,
        timeRemaining: rateLimitInfo.timeRemaining
      }
    };

    // Output in JSON format if requested
    if (options.json) {
      console.log(JSON.stringify(statusInfo, null, 2));
      return;
    }

    // Display human-readable status
    console.log(chalk.blue('===== bsky-bot Status ====='));

    // Account information
    if (accounts.currentHandle) {
      console.log(chalk.green(`Current Account: ${chalk.bold(accounts.currentHandle)}`));
    } else {
      console.log(chalk.yellow('No active account. Run `bsky-bot connect` to log in.'));
    }

    // All accounts
    if (accounts.accounts.length > 0) {
      console.log(chalk.blue('\nAll Accounts:'));
      accounts.accounts.forEach(handle => {
        if (handle === accounts.currentHandle) {
          console.log(`  ${chalk.green('* ' + handle)} (current)`);
        } else {
          console.log(`  ${handle}`);
        }
      });
    }

    // Rate limit information
    console.log(chalk.blue('\nRate Limit Information:'));
    if (rateLimitInfo.lastDownloadAt) {
      console.log(`  Last Download: ${rateLimitInfo.lastDownloadAt}`);
      console.log(`  Next Allowed: ${rateLimitInfo.nextAllowedAt}`);
      console.log(`  Can Download Now: ${rateLimitInfo.canDownloadNow ? chalk.green('Yes') : chalk.yellow('No')}`);

      if (!rateLimitInfo.canDownloadNow) {
        console.log(`  Time Remaining: ${chalk.yellow(timeRemainingStr)}`);
      }
    } else {
      console.log(chalk.green('  No recent downloads. You can download profiles now.'));
    }
  } catch (error) {
    console.error(chalk.red(`Error: ${error.message}`));
    process.exit(1);
  }
}

module.exports = {
  statusCommand
};
