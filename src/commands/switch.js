const chalk = require('chalk');
const ora = require('ora');
const authManager = require('../auth');

async function switchCommand(handle) {
  const spinner = ora('Initializing auth manager...').start();

  try {
    await authManager.init();
    spinner.succeed('Auth manager initialized');

    // Check if we're trying to switch to the current account
    if (authManager.currentHandle === handle) {
      console.log(chalk.blue(`Already using ${chalk.bold(handle)}`));
      return;
    }

    spinner.text = `Switching to account ${handle}...`;
    spinner.start();

    const result = await authManager.switchAccount(handle);

    if (result.success) {
      spinner.succeed(`Switched to account ${chalk.bold(handle)}`);
    } else {
      spinner.fail(`Failed to switch account: ${result.error}`);
      console.log(chalk.yellow(`To connect to ${handle}, please run 'bsky-bot connect' after logging out.`));
      process.exit(1);
    }
  } catch (error) {
    spinner.fail(`Error: ${error.message}`);
    process.exit(1);
  }
}

module.exports = {
  switchCommand
};
