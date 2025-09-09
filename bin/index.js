#!/usr/bin/env node

require('dotenv').config();
const { Command } = require('commander');
const chalk = require('chalk');
const { connectCommand } = require('../src/commands/connect');
const { downloadCommand } = require('../src/commands/download');
const { postCommand } = require('../src/commands/post');
const { switchCommand } = require('../src/commands/switch');
const { logoutCommand } = require('../src/commands/logout');
const { statusCommand } = require('../src/commands/status');
const { checkEnvironment } = require('../src/deps');
const { version } = require('../package.json');

async function main() {
  try {
    // Validate environment
    await checkEnvironment();

    const program = new Command();

    program
      .name('bsky-bot')
      .description('Bluesky profile archiver and minimal poster')
      .version(version);

    // Setup (alias for connect)
    program
      .command('setup')
      .description('Alias for connect command')
      .action(() => {
        program.commands.find(cmd => cmd.name() === 'connect').action();
      });

    // Connect command
    program
      .command('connect')
      .description('Interactive login and session storage')
      .action(connectCommand);

    // Download command
    program
      .command('download <handle>')
      .description('Download a profile')
      .option('--force', 'Force download even if rate limited', false)
      .option('--no-compress', 'Skip compression of the profile', false)
      .option('-v, --verbose', 'Show detailed logs', false)
      .option('--batch <number>', 'Download specified number of articles in batch, then process individually', parseInt)
      .action(downloadCommand);

    // Post command
    program
      .command('post <text>')
      .description('Post a simple text to the current account')
      .action(postCommand);

    // Switch command
    program
      .command('switch <handle>')
      .description('Switch the current session to another stored account')
      .action(switchCommand);

    // Logout command
    program
      .command('logout')
      .description('Clear the current account\'s stored session')
      .action(logoutCommand);

    // Status command
    program
      .command('status')
      .description('Show current account and rate limit information')
      .option('--json', 'Output in JSON format', false)
      .action(statusCommand);

    await program.parseAsync(process.argv);
  } catch (error) {
    console.error(chalk.red(`Error: ${error.message}`));
    process.exit(1);
  }
}

main();
