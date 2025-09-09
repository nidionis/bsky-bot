const { BskyAgent } = require('@atproto/api');
const fs = require('fs-extra');
const path = require('path');
const archiver = require('archiver');
const chalk = require('chalk');
const ora = require('ora');
const { DependencyInstaller } = require('./deps');
const { AuthManager } = require('./auth');
const { RateLimiter } = require('./limiter');
const { ProfileDownloader } = require('./downloader');
const { DataOrganizer } = require('./organizer');

class BlueskyBot {
  constructor(options = {}) {
    this.options = options;
    this.spinner = null;
    this.deps = new DependencyInstaller();
    this.auth = new AuthManager();
    this.limiter = new RateLimiter();
    this.downloader = null;
    this.organizer = new DataOrganizer();
  }

  async setup() {
    console.log(chalk.blue('🚀 Bluesky Profile Downloader Setup\n'));

    this.spinner = ora('Checking dependencies...').start();
    await this.deps.ensureDependencies();
    this.spinner.succeed('Dependencies ready');

    this.spinner = ora('Setting up authentication...').start();
    const agent = await this.auth.authenticate();

    if (agent) {
      this.spinner.succeed('Authentication successful');
      console.log(chalk.green('\n✅ Setup complete! You can now download profiles.'));
      console.log(chalk.gray('Example: bsky-dl download username'));
    } else {
      this.spinner.fail('Authentication failed');
      process.exit(1);
    }
  }

  async downloadProfile(username) {
    if (!username) {
      console.log(chalk.red('❌ Username is required'));
      process.exit(1);
    }

    console.log(chalk.blue(`📥 Downloading profile: ${chalk.bold(username)}\n`));

    try {
      // Check dependencies
      this.spinner = ora('Checking dependencies...').start();
      await this.deps.ensureDependencies();
      this.spinner.succeed();

      // Check authentication
      this.spinner = ora('Verifying authentication...').start();
      const agent = await this.auth.getAuthenticatedAgent();
      if (!agent) {
        this.spinner.fail('Not authenticated. Run: bsky-dl setup');
        process.exit(1);
      }
      this.spinner.succeed('Authenticated');

      // Check rate limiting
      if (!this.options.force) {
        this.spinner = ora('Checking rate limits...').start();
        const canDownload = await this.limiter.canDownload();
        if (!canDownload) {
          const waitTime = this.limiter.getWaitTime();
          this.spinner.fail(`Rate limited. Wait ${Math.ceil(waitTime / 60000)} minutes`);
          process.exit(1);
        }
        this.spinner.succeed('Rate limit OK');
      }

      // Initialize downloader
      this.downloader = new ProfileDownloader(agent, this.options);

      // Download profile data
      this.spinner = ora(`Fetching ${username}'s profile...`).start();
      const profileData = await this.downloader.downloadProfile(username);
      this.spinner.succeed(`Profile data retrieved (${profileData.posts.length} posts)`);

      // Organize data
      this.spinner = ora('Organizing files...').start();
      const profilePath = await this.organizer.organize(username, profileData);
      this.spinner.succeed('Files organized');

      // Compress if enabled
      if (this.options.compress !== false) {
        this.spinner = ora('Compressing profile...').start();
        await this.compressProfile(profilePath, username);
        this.spinner.succeed('Profile compressed');
      }

      // Update rate limiter
      await this.limiter.recordDownload();

      console.log(chalk.green(`\n✅ Profile downloaded successfully!`));
      console.log(chalk.gray(`Location: ${profilePath}`));

      if (this.options.compress !== false) {
        console.log(chalk.gray(`Archive: ${profilePath}/${username}.zip`));
      }

    } catch (error) {
      if (this.spinner) this.spinner.fail('Download failed');
      console.error(chalk.red(`❌ Error: ${error.message}`));
      if (this.options.verbose) {
        console.error(error.stack);
      }
      process.exit(1);
    }
  }

  async compressProfile(profilePath, username) {
    const output = fs.createWriteStream(path.join(profilePath, `${username}.zip`));
    const archive = archiver('zip', { zlib: { level: 9 } });

    return new Promise((resolve, reject) => {
      output.on('close', resolve);
      archive.on('error', reject);

      archive.pipe(output);
      archive.directory(path.join(profilePath, 'articles'), 'articles');
      archive.directory(path.join(profilePath, 'interactions'), 'interactions');
      archive.directory(path.join(profilePath, 'infos'), 'infos');
      archive.finalize();
    });
  }

  async showStatus() {
    console.log(chalk.blue('📊 Bluesky Bot Status\n'));

    const authStatus = await this.auth.getStatus();
    const rateStatus = this.limiter.getStatus();

    console.log(chalk.cyan('Authentication:'));
    if (authStatus.authenticated) {
      console.log(`  ✅ Logged in as: ${chalk.bold(authStatus.handle)}`);
    } else {
      console.log(`  ❌ Not authenticated`);
    }

    console.log(chalk.cyan('\nRate Limiting:'));
    if (rateStatus.canDownload) {
      console.log(`  ✅ Ready to download`);
    } else {
      const waitMinutes = Math.ceil(rateStatus.waitTime / 60000);
      console.log(`  ⏳ Wait ${waitMinutes} minutes before next download`);
    }

    if (rateStatus.lastDownload) {
      console.log(`  📅 Last download: ${new Date(rateStatus.lastDownload).toLocaleString()}`);
    }
  }

  async logout() {
    this.spinner = ora('Clearing authentication...').start();
    await this.auth.logout();
    this.spinner.succeed('Logged out successfully');
    console.log(chalk.green('✅ Authentication cleared. Use "bsky-dl setup" to login again.'));
  }

  async switchAccount(handle, password) {
    console.log(chalk.blue(`🔄 Switching to account: ${chalk.bold(handle)}`));

    try {
      // Check dependencies
      this.spinner = ora('Checking dependencies...').start();
      await this.deps.ensureDependencies();
      this.spinner.succeed('Dependencies ready');

      // Switch accounts
      this.spinner = ora('Authenticating with new account...').start();
      const agent = await this.auth.switchAccount(handle, password);

      if (agent) {
        this.spinner.succeed(`Switched to ${agent.session.handle}`);
        console.log(chalk.green('\n✅ Account switch successful!'));
      } else {
        this.spinner.fail('Failed to switch accounts');
        process.exit(1);
      }
    } catch (error) {
      if (this.spinner) this.spinner.fail('Account switch failed');
      console.error(chalk.red(`❌ Error: ${error.message}`));
      process.exit(1);
    }
  }

  async postText(text, replyTo) {
    console.log(chalk.blue(`📝 Posting to Bluesky`));

    try {
      // Check dependencies
      this.spinner = ora('Checking dependencies...').start();
      await this.deps.ensureDependencies();
      this.spinner.succeed('Dependencies ready');

      // Check authentication
      this.spinner = ora('Verifying authentication...').start();
      const agent = await this.auth.getAuthenticatedAgent();
      if (!agent) {
        this.spinner.fail('Not authenticated. Run: bsky-dl setup');
        process.exit(1);
      }
      this.spinner.succeed(`Authenticated as ${agent.session.handle}`);

      // Create post
      this.spinner = ora('Creating post...').start();

      const postParams = {
        text: text.slice(0, 300), // Bluesky has a character limit
        createdAt: new Date().toISOString()
      };

      // Add reply reference if provided
      if (replyTo) {
        try {
          // Handle both at:// and https:// formats
          const uri = replyTo.startsWith('at://') ? replyTo : 
                     replyTo.includes('/profile/') ? `at://${replyTo.split('/profile/')[1]}` : replyTo;

          const replyRef = await agent.getPost({ uri });

          if (replyRef?.data) {
            postParams.reply = {
              root: {
                uri: replyTo,
                cid: replyRef.data.cid
              },
              parent: {
                uri: replyTo,
                cid: replyRef.data.cid
              }
            };
          }
        } catch (error) {
          this.spinner.warn('Invalid reply URI, posting as a new post');
        }
      }

      const response = await agent.post(postParams);

      this.spinner.succeed('Post created successfully');
      console.log(chalk.green(`\n✅ Posted to Bluesky!`));
      console.log(chalk.gray(`Post URI: at://${response.uri}`));
    } catch (error) {
      if (this.spinner) this.spinner.fail('Post failed');
      console.error(chalk.red(`❌ Error: ${error.message}`));
      if (this.options.verbose) {
        console.error(error.stack);
      }
      process.exit(1);
    }
  }
}

module.exports = { BlueskyBot };
