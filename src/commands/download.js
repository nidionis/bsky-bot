const chalk = require('chalk');
const ora = require('ora');
const authManager = require('../auth');
const rateLimiter = require('../limiter');
const ProfileDownloader = require('../downloader');
const logger = require('../logger');

async function downloadCommand(handle, options) {
  // Set logger verbosity
  logger.setVerbose(options.verbose);

  try {
    // Initialize auth and rate limiter
    await authManager.init();
    await rateLimiter.init();

    // Check rate limiting
    if (!options.force) {
      const canDownload = await rateLimiter.canDownload();

      if (!canDownload) {
        const remainingTime = await rateLimiter.getTimeRemaining();
        const minutes = Math.ceil(remainingTime / 60000);

        console.log(chalk.yellow(`Rate limit in effect. Please wait ${minutes} minutes before downloading again.`));
        console.log(chalk.yellow(`Use --force to override this limit.`));

        process.exit(1);
      }
    }

    // Create downloader instance
    const downloader = new ProfileDownloader({
      verbose: options.verbose,
      compress: options.compress
    });

    // Mark download as started (for rate limiting)
    await rateLimiter.markDownloadStarted();

    // Start the download
    const result = await downloader.downloadProfile(handle);

    if (result.success) {
      console.log(chalk.green(`\nProfile for ${chalk.bold(handle)} was successfully downloaded.`));
      console.log(chalk.green(`Location: ${result.profileDir}`));

      if (options.compress) {
        console.log(chalk.green(`Compressed archive: ${result.profileDir}.zip`));
      }
    } else {
      console.log(chalk.red(`\nFailed to download profile: ${result.error}`));
      process.exit(1);
    }
  } catch (error) {
    console.error(chalk.red(`Error: ${error.message}`));
    process.exit(1);
  }
}

module.exports = {
  downloadCommand
};
