const { BskyAgent } = require('@atproto/api');
const fs = require('fs-extra');
const path = require('path');
const inquirer = require('inquirer');
const chalk = require('chalk');
const { BSKY_SERVICE, ACCOUNTS_DIR, ACCOUNTS_INDEX } = require('./config');
const { safeReadJson, safeWriteJson, ensureDir } = require('./utils/fs');

class AuthManager {
  constructor() {
    this.agent = new BskyAgent({ service: BSKY_SERVICE });
    this.currentHandle = null;
  }

  /**
   * Initialize the auth manager by loading account state
   */
  async init() {
    await ensureDir(ACCOUNTS_DIR);

    const accountsIndex = await safeReadJson(ACCOUNTS_INDEX, { currentHandle: null, accounts: [] });
    this.currentHandle = accountsIndex.currentHandle;

    // If we have a current handle, try to resume that session
    if (this.currentHandle) {
      await this.resumeSession(this.currentHandle);
    }
  }

  /**
   * Interactive login flow
   */
  async login() {
    const handle = process.env.BSKY_HANDLE;
    const password = process.env.BSKY_APP_PASSWORD;

    // If environment variables are present, use them
    if (handle && password) {
      return this.loginWithCredentials(handle, password);
    }

    // Otherwise, prompt the user for credentials
    const answers = await inquirer.prompt([
      {
        type: 'input',
        name: 'handle',
        message: 'Enter your Bluesky handle (e.g., example.bsky.social):',
        validate: (input) => input && input.includes('.') ? true : 'Please enter a valid Bluesky handle'
      },
      {
        type: 'password',
        name: 'password',
        message: 'Enter your app password:',
        validate: (input) => input ? true : 'Password cannot be empty'
      }
    ]);

    return this.loginWithCredentials(answers.handle, answers.password);
  }

  /**
   * Login with provided credentials
   */
  async loginWithCredentials(handle, password) {
    try {
      const { success, data } = await this.agent.login({ identifier: handle, password });

      if (!success || !data) {
        throw new Error('Login failed');
      }

      // Store the session
      const sessionPath = path.join(ACCOUNTS_DIR, `${handle}.json`);
      await safeWriteJson(sessionPath, this.agent.session, { mode: 0o600 });

      // Update the accounts index
      const accountsIndex = await safeReadJson(ACCOUNTS_INDEX, { currentHandle: null, accounts: [] });

      // Add this account to the accounts list if not already present
      if (!accountsIndex.accounts.includes(handle)) {
        accountsIndex.accounts.push(handle);
      }

      // Set as current handle
      accountsIndex.currentHandle = handle;
      this.currentHandle = handle;

      await safeWriteJson(ACCOUNTS_INDEX, accountsIndex);

      return { success: true, handle, did: this.agent.session.did };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Resume a session for a specific handle
   */
  async resumeSession(handle) {
    try {
      const sessionPath = path.join(ACCOUNTS_DIR, `${handle}.json`);
      const session = await safeReadJson(sessionPath);

      if (!session) {
        return { success: false, error: `No stored session found for ${handle}` };
      }

      await this.agent.resumeSession(session);
      this.currentHandle = handle;

      return { success: true, handle, did: this.agent.session.did };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Switch to another account
   */
  async switchAccount(handle) {
    // Check if we have a session for this handle
    const sessionPath = path.join(ACCOUNTS_DIR, `${handle}.json`);
    const sessionExists = await fs.pathExists(sessionPath);

    if (!sessionExists) {
      return { success: false, error: `No session found for ${handle}` };
    }

    // Resume the session
    const result = await this.resumeSession(handle);

    if (result.success) {
      // Update the accounts index with the new current handle
      const accountsIndex = await safeReadJson(ACCOUNTS_INDEX, { currentHandle: null, accounts: [] });
      accountsIndex.currentHandle = handle;
      await safeWriteJson(ACCOUNTS_INDEX, accountsIndex);
    }

    return result;
  }

  /**
   * Logout from the current account
   */
  async logout() {
    if (!this.currentHandle) {
      return { success: false, error: 'No active session' };
    }

    try {
      const sessionPath = path.join(ACCOUNTS_DIR, `${this.currentHandle}.json`);
      await fs.remove(sessionPath);

      // Update the accounts index
      const accountsIndex = await safeReadJson(ACCOUNTS_INDEX, { currentHandle: null, accounts: [] });
      accountsIndex.accounts = accountsIndex.accounts.filter(a => a !== this.currentHandle);

      // If this was the current handle, unset it
      if (accountsIndex.currentHandle === this.currentHandle) {
        accountsIndex.currentHandle = accountsIndex.accounts.length > 0 ? accountsIndex.accounts[0] : null;
      }

      await safeWriteJson(ACCOUNTS_INDEX, accountsIndex);

      // Update local state
      const newHandle = accountsIndex.currentHandle;
      this.currentHandle = newHandle;

      // If we have a new current handle, resume that session
      if (newHandle) {
        await this.resumeSession(newHandle);
      } else {
        this.agent = new BskyAgent({ service: BSKY_SERVICE });
      }

      return { 
        success: true, 
        removedHandle: this.currentHandle,
        newCurrentHandle: newHandle 
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Get the current agent, ensuring we're authenticated
   */
  async getAgent() {
    if (!this.agent.session) {
      if (!this.currentHandle) {
        throw new Error('Not logged in. Please run `bsky-bot connect` first.');
      }

      const result = await this.resumeSession(this.currentHandle);
      if (!result.success) {
        throw new Error(`Failed to resume session: ${result.error}`);
      }
    }

    return this.agent;
  }

  /**
   * List all accounts
   */
  async listAccounts() {
    const accountsIndex = await safeReadJson(ACCOUNTS_INDEX, { currentHandle: null, accounts: [] });
    return {
      currentHandle: accountsIndex.currentHandle,
      accounts: accountsIndex.accounts
    };
  }
}

// Singleton instance
const authManager = new AuthManager();

module.exports = authManager;
