const fs = require('fs-extra');
const path = require('path');
const { MIN_DOWNLOAD_INTERVAL, MAX_DOWNLOAD_INTERVAL, CONFIG_DIR } = require('./config');
const { safeReadJson, safeWriteJson, ensureDir } = require('./utils/fs');

class RateLimiter {
  constructor() {
    this.limitsFile = path.join(CONFIG_DIR, 'rate-limits.json');
    // Generate a random interval in the range [MIN_DOWNLOAD_INTERVAL, MAX_DOWNLOAD_INTERVAL]
    this.downloadInterval = Math.floor(
      Math.random() * (MAX_DOWNLOAD_INTERVAL - MIN_DOWNLOAD_INTERVAL + 1) + MIN_DOWNLOAD_INTERVAL
    );
  }

  /**
   * Initialize the rate limiter
   */
  async init() {
    await ensureDir(CONFIG_DIR);
    await this.loadLimits();
  }

  /**
   * Load rate limits from disk
   */
  async loadLimits() {
    this.limits = await safeReadJson(this.limitsFile, {
      lastDownloadAt: 0,
      downloadInterval: this.downloadInterval
    });

    // If there's no stored interval, use the random one we generated
    if (!this.limits.downloadInterval) {
      this.limits.downloadInterval = this.downloadInterval;
    } else {
      this.downloadInterval = this.limits.downloadInterval;
    }
  }

  /**
   * Save rate limits to disk
   */
  async saveLimits() {
    await safeWriteJson(this.limitsFile, this.limits);
  }

  /**
   * Check if a download is allowed based on rate limits
   */
  async canDownload() {
    await this.loadLimits();

    const now = Date.now();
    const lastDownload = this.limits.lastDownloadAt || 0;
    const elapsed = now - lastDownload;

    return elapsed >= this.downloadInterval;
  }

  /**
   * Get the remaining time until next allowed download
   */
  async getTimeRemaining() {
    await this.loadLimits();

    const now = Date.now();
    const lastDownload = this.limits.lastDownloadAt || 0;
    const elapsed = now - lastDownload;

    if (elapsed >= this.downloadInterval) {
      return 0;
    }

    return this.downloadInterval - elapsed;
  }

  /**
   * Mark a download as started
   */
  async markDownloadStarted() {
    await this.loadLimits();

    this.limits.lastDownloadAt = Date.now();
    // Generate a new random interval for next time
    this.limits.downloadInterval = Math.floor(
      Math.random() * (MAX_DOWNLOAD_INTERVAL - MIN_DOWNLOAD_INTERVAL + 1) + MIN_DOWNLOAD_INTERVAL
    );
    this.downloadInterval = this.limits.downloadInterval;

    await this.saveLimits();
  }

  /**
   * Get rate limit info
   */
  async getRateLimitInfo() {
    await this.loadLimits();

    const now = Date.now();
    const lastDownload = this.limits.lastDownloadAt || 0;
    const nextAllowedTime = lastDownload + this.downloadInterval;

    return {
      lastDownloadAt: lastDownload > 0 ? new Date(lastDownload).toISOString() : null,
      nextAllowedAt: lastDownload > 0 ? new Date(nextAllowedTime).toISOString() : null,
      canDownloadNow: now >= nextAllowedTime,
      timeRemaining: Math.max(0, nextAllowedTime - now)
    };
  }
}

// Singleton instance
const rateLimiter = new RateLimiter();

module.exports = rateLimiter;
