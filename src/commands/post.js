const chalk = require('chalk');
const ora = require('ora');
const authManager = require('../auth');
const { POST_MAX_LENGTH, POST_MIN_LENGTH } = require('../config');

async function postCommand(text) {
  const spinner = ora('Initializing auth manager...').start();

  try {
    await authManager.init();
    spinner.succeed('Auth manager initialized');

    // Validate the text length
    const trimmedText = text.trim();

    if (trimmedText.length < POST_MIN_LENGTH) {
      console.log(chalk.red(`Error: Post text is too short. Minimum length is ${POST_MIN_LENGTH} character.`));
      process.exit(1);
    }

    if (trimmedText.length > POST_MAX_LENGTH) {
      console.log(chalk.red(`Error: Post text is too long. Maximum length is ${POST_MAX_LENGTH} characters.`));
      console.log(chalk.red(`Your post is ${trimmedText.length} characters.`));
      process.exit(1);
    }

    // Get the agent and ensure we're logged in
    spinner.text = 'Preparing to post...';
    spinner.start();

    const agent = await authManager.getAgent();

    if (!agent.session) {
      spinner.fail('Not logged in');
      console.log(chalk.yellow('Please run `bsky-bot connect` to log in first.'));
      process.exit(1);
    }

    spinner.text = 'Posting to Bluesky...';

    // Create the post
    const postResult = await agent.post({
      text: trimmedText
    });

    // The @atproto/api client returns the result directly on success
    // If we get here without an error being thrown, the post was successful
    spinner.succeed('Post published successfully');

    // Extract the post URI
    const postUri = postResult.uri;
    console.log(chalk.green(`Post URI: ${chalk.bold(postUri)}`));

  } catch (error) {
    spinner.fail('Failed to publish post');
    
    // Better error handling
    if (error.message) {
      console.log(chalk.red(`Error: ${error.message}`));
    } else if (error.error) {
      console.log(chalk.red(`Error: ${error.error}`));
    } else {
      console.log(chalk.red('Error: Unknown error'));
      console.log(chalk.red('Full error:'), error);
    }
    
    process.exit(1);
  }
}

module.exports = {
  postCommand
};