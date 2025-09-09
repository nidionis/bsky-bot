const { BskyAgent } = require('@atproto/api');
const fs = require('fs-extra');
const path = require('path');
require('dotenv').config();

class AuthManager {
  constructor() {
    this.envPath = path.join(process.cwd(), '.env');
    this.sessionPath = path.join(process.cwd(), 'session.json');
    this.agent = null;
  }

  async authenticate() {
    // Try to load existing session
    if (await this.loadSession()) {
      return this.agent;
    }

    // Interactive authentication
    const readline = require('readline').createInterface({
      input: process.stdin,
      output: process.stdout
    });

    const question = (prompt) => new Promise(resolve => readline.question(prompt, resolve));

    try {
      const handle = await question('Bluesky handle (e.g., user.bsky.social): ');
      const password = await question('App password: ');
      readline.close();

      this.agent = new BskyAgent({ service: 'https://bsky.social' });
      await this.agent.login({ identifier: handle, password });

      // Save credentials
      await this.saveSession(handle);

      return this.agent;
    } catch (error) {
      readline.close();
      throw new Error(`Authentication failed: ${error.message}`);
    }
  }

  async loadSession() {
    try {
      if (!fs.existsSync(this.sessionPath)) return false;

      const sessionData = JSON.parse(await fs.readFile(this.sessionPath, 'utf8'));
      this.agent = new BskyAgent({ service: 'https://bsky.social' });

      await this.agent.resumeSession(sessionData);
      return true;
    } catch (error) {
      return false;
    }
  }

  async saveSession(handle) {
    const sessionData = this.agent.session;
    await fs.writeFile(this.sessionPath, JSON.stringify(sessionData, null, 2));

    // Save handle to .env for reference
    let envContent = '';
    if (fs.existsSync(this.envPath)) {
      envContent = await fs.readFile(this.envPath, 'utf8');
    }

    if (!envContent.includes('BLUESKY_HANDLE=')) {
      envContent += `\nBLUESKY_HANDLE=${handle}\n`;
      await fs.writeFile(this.envPath, envContent);
    }
  }

  async getAuthenticatedAgent() {
    if (!this.agent && !(await this.loadSession())) {
      return null;
    }
    return this.agent;
  }

  async getStatus() {
    const authenticated = await this.loadSession();
    let handle = null;

    if (authenticated && this.agent.session) {
      handle = this.agent.session.handle;
    }

    return { authenticated, handle };
  }

  async switchAccount(handle, password = null) {
    // If password is not provided, prompt interactively
    if (!password) {
      const readline = require('readline').createInterface({
        input: process.stdin,
        output: process.stdout
      });

      password = await new Promise(resolve => {
        readline.question('App password: ', (answer) => {
          readline.close();
          resolve(answer);
        });
      });
    }

    try {
      // First logout if currently logged in
      await this.logout();

      // Login with new account
      this.agent = new BskyAgent({ service: 'https://bsky.social' });
      await this.agent.login({ identifier: handle, password });

      // Save new session
      await this.saveSession(handle);

      return this.agent;
    } catch (error) {
      throw new Error(`Failed to switch account: ${error.message}`);
    }
  }

  async logout() {
    if (fs.existsSync(this.sessionPath)) {
      await fs.remove(this.sessionPath);
    }

    if (fs.existsSync(this.envPath)) {
      let envContent = await fs.readFile(this.envPath, 'utf8');
      envContent = envContent.replace(/BLUESKY_HANDLE=.*\n?/g, '');
      await fs.writeFile(this.envPath, envContent);
    }

    this.agent = null;
  }
}

module.exports = { AuthManager };
