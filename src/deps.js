const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class DependencyInstaller {
  constructor() {
    this.requiredDeps = [
      '@atproto/api',
      'commander',
      'fs-extra',
      'archiver',
      'dotenv',
      'chalk',
      'ora'
    ];
  }

  async ensureDependencies() {
    const packageJsonPath = path.join(process.cwd(), 'package.json');

    if (!fs.existsSync(packageJsonPath)) {
      throw new Error('package.json not found. Run npm init first.');
    }

    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    const installedDeps = {
      ...packageJson.dependencies || {},
      ...packageJson.devDependencies || {}
    };

    const missingDeps = this.requiredDeps.filter(dep => !installedDeps[dep]);

    if (missingDeps.length > 0) {
      console.log(`Installing missing dependencies: ${missingDeps.join(', ')}`);
      execSync(`npm install ${missingDeps.join(' ')}`, { stdio: 'inherit' });
    }
  }
}

module.exports = { DependencyInstaller };
