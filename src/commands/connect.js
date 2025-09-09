const chalk = require('chalk');
const ora = require('ora');
const authManager = require('../auth');

async function connectCommand() {
  const spinner = ora('Initializing auth manager...').start();

  try {
    await authManager.init();
    spinner.succeed('Auth manager initialized');

    // Check if we're already logged in
    if (authManager.currentHandle) {
      console.log(chalk.blue(`Already logged in as ${chalk.bold(authManager.currentHandle)}`));
      console.log(chalk.blue('To connect a different account, please run `bsky-bot logout` first.'));
      return;
    }

    spinner.text = 'Logging in...';
    spinner.start();

    const result = await authManager.login();

    if (result.success) {
      spinner.succeed(`Successfully logged in as ${chalk.bold(result.handle)}`);
      console.log(chalk.green('You can now use other commands to interact with Bluesky.'));
    } else {
      spinner.fail(`Login failed: ${result.error}`);
      console.log(chalk.yellow('Please check your credentials and try again.'));
      process.exit(1);
    }
  } catch (error) {
    spinner.fail(`Error: ${error.message}`);
    process.exit(1);
  }
}

module.exports = {
  connectCommand
};
