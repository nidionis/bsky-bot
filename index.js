#!/usr/bin/env node

const { program } = require('commander');
const { BlueskyBot } = require('./src/bot');
const chalk = require('chalk');
const pkg = require('./package.json');

program
  .name('bsky-dl')
  .description('Download and compress Bluesky profiles with organized folder structure')
  .version(pkg.version)
  .helpOption('-h, --help', 'Display help for command')
  .configureHelp({
    sortSubcommands: true,
    subcommandTerm: (cmd) => cmd.name()
  });

program
  .command('setup')
  .description('Initial setup - authenticate with Bluesky account')
  .action(async () => {
    const bot = new BlueskyBot();
    await bot.setup();
  });

program
  .command('download')
  .description('Download a Bluesky profile')
  .argument('<username>', 'Bluesky username (without @)')
  .option('-f, --force', 'Skip rate limiting (use with caution)')
  .option('-n, --no-compress', 'Skip compression of downloaded data')
  .option('-v, --verbose', 'Verbose output')
  .action(async (username, options) => {
    const bot = new BlueskyBot(options);
    await bot.downloadProfile(username);
  });

program
  .command('status')
  .description('Show authentication status and last download info')
  .action(async () => {
    const bot = new BlueskyBot();
    await bot.showStatus();
  });

program
  .command('logout')
  .description('Clear stored authentication')
  .action(async () => {
    const bot = new BlueskyBot();
    await bot.logout();
  });

program
  .command('switch')
  .description('Switch to a different Bluesky account')
  .argument('<handle>', 'Bluesky handle to switch to')
  .option('-p, --password <password>', 'App password for the account')
  .action(async (handle, options) => {
    const bot = new BlueskyBot();
    await bot.switchAccount(handle, options.password);
  });

program
  .command('post')
  .description('Post a simple text post to Bluesky')
  .argument('<text>', 'Text content to post')
  .option('-r, --reply-to <uri>', 'URI of post to reply to')
  .action(async (text, options) => {
    const bot = new BlueskyBot();
    await bot.postText(text, options.replyTo);
  });

// Enhanced help
program.addHelpText('after', `
${chalk.cyan('Examples:')}
  ${chalk.gray('$')} bsky-dl setup                    # First time setup
  ${chalk.gray('$')} bsky-dl download username        # Download profile
  ${chalk.gray('$')} bsky-dl download username -v     # Verbose download
  ${chalk.gray('$')} bsky-dl switch handle            # Switch accounts
  ${chalk.gray('$')} bsky-dl post "Hello world"       # Post to Bluesky
  ${chalk.gray('$')} bsky-dl status                   # Check auth status
  ${chalk.gray('$')} bsky-dl logout                   # Clear stored auth

${chalk.cyan('Rate Limiting:')}
  • Default: 1 profile per 4-6 minutes (randomized)
  • Use --force to bypass (not recommended)
  • Bot remembers last download time across restarts

${chalk.cyan('Output Structure:')}
  profiles/
  ├── {username}/
  │   ├── articles/           # Posts and threads
  │   ├── interactions/       # Likes, reposts, follows
  │   ├── infos/             # Profile metadata
  │   └── {username}.zip     # Compressed archive

${chalk.cyan('Authentication:')}
  • Stored persistently in .env and session.json
  • No need to re-authenticate between runs
  • Use 'bsky-dl logout' to clear credentials
`);

if (process.argv.length === 2) {
  program.help();
}

program.parse();
