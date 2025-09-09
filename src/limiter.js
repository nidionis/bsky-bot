const fs = require('fs-extra');
const path = require('path');

class RateLimiter {
  constructor() {
    this.limiterPath = path.join(process.cwd(), 'rate_limiter.json');
    this.minInterval = 4 * 60 * 1000; // 4 minutes
    this.maxInterval = 6 * 60 * 1000; // 6 minutes
  }

  async canDownload() {
    const data = await this.loadData();
    if (!data.lastDownload) return true;

    const randomInterval = this.minInterval + Math.random() * (this.maxInterval - this.minInterval);
    const timeSinceLastDownload = Date.now() - data.lastDownload;

    return timeSinceLastDownload >= randomInterval;
  }

  getWaitTime() {
    const data = this.loadDataSync();
    if (!data.lastDownload) return 0;

    const randomInterval = this.minInterval + Math.random() * (this.maxInterval - this.minInterval);
    const timeSinceLastDownload = Date.now() - data.lastDownload;

    return Math.max(0, randomInterval - timeSinceLastDownload);
  }

  async recordDownload() {
    const data = await this.loadData();
    data.lastDownload = Date.now();
    data.downloadCount = (data.downloadCount || 0) + 1;
    await fs.writeFile(this.limiterPath, JSON.stringify(data, null, 2));
  }

  async loadData() {
    try {
      if (!fs.existsSync(this.limiterPath)) {
        return { lastDownload: null, downloadCount: 0 };
      }
      return JSON.parse(await fs.readFile(this.limiterPath, 'utf8'));
    } catch {
      return { lastDownload: null, downloadCount: 0 };
    }
  }

  loadDataSync() {
    try {
      if (!fs.existsSync(this.limiterPath)) {
        return { lastDownload: null, downloadCount: 0 };
      }
      return JSON.parse(fs.readFileSync(this.limiterPath, 'utf8'));
    } catch {
      return { lastDownload: null, downloadCount: 0 };
    }
  }

  getStatus() {
    const data = this.loadDataSync();
    return {
      canDownload: this.canDownload(),
      waitTime: this.getWaitTime(),
      lastDownload: data.lastDownload,
      downloadCount: data.downloadCount || 0
    };
  }
}

module.exports = { RateLimiter };
