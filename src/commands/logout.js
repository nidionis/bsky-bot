const chalk = require('chalk');
const ora = require('ora');
const authManager = require('../auth');

async function logoutCommand() {
  const spinner = ora('Initializing auth manager...').start();

  try {
    await authManager.init();
    spinner.succeed('Auth manager initialized');

    if (!authManager.currentHandle) {
      console.log(chalk.yellow('No active session to log out from.'));
      return;
    }

    const currentHandle = authManager.currentHandle;

    spinner.text = `Logging out from ${currentHandle}...`;
    spinner.start();

    const result = await authManager.logout();

    if (result.success) {
      spinner.succeed(`Logged out from ${chalk.bold(result.removedHandle)}`);

      if (result.newCurrentHandle) {
        console.log(chalk.blue(`Switched to account ${chalk.bold(result.newCurrentHandle)}`));
      } else {
        console.log(chalk.blue('No accounts remaining. Use `bsky-bot connect` to add a new account.'));
      }
    } else {
      spinner.fail(`Failed to log out: ${result.error}`);
      process.exit(1);
    }
  } catch (error) {
    spinner.fail(`Error: ${error.message}`);
    process.exit(1);
  }
}

module.exports = {
  logoutCommand
};
