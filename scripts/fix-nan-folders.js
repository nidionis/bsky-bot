#!/usr/bin/env node

const fs = require('fs-extra');
const path = require('path');
const { getProfileDir } = require('../src/utils/fs');

/**
 * Fix the NaN folders issue by moving the content to a proper fallback structure
 */
async function fixNaNFolders() {
  console.log('Starting to fix NaN folders issue...');

  // Get all profiles
  const profilesDir = path.join(process.cwd(), 'profiles');
  if (!await fs.pathExists(profilesDir)) {
    console.log('No profiles directory found. Nothing to fix.');
    return;
  }

  const profiles = await fs.readdir(profilesDir);

  for (const handle of profiles) {
    const profileDir = path.join(profilesDir, handle);
    const articlesDir = path.join(profileDir, 'articles');

    // Skip if no articles directory
    if (!await fs.pathExists(articlesDir)) {
      continue;
    }

    console.log(`Checking profile: ${handle}`);

    // Check for NaN directories
    const nanDirPath = path.join(articlesDir, 'NaN');
    if (await fs.pathExists(nanDirPath)) {
      console.log(`Found NaN directory in ${handle}'s profile`);

      // Create a fallback structure
      const fallbackDir = path.join(articlesDir, 'undated');
      await fs.ensureDir(fallbackDir);

      // Function to recursively find JSON files
      async function findJsonFiles(dir) {
        const items = await fs.readdir(dir, { withFileTypes: true });
        let files = [];

        for (const item of items) {
          const fullPath = path.join(dir, item.name);

          if (item.isDirectory()) {
            files = files.concat(await findJsonFiles(fullPath));
          } else if (item.isFile() && item.name.endsWith('.json')) {
            files.push(fullPath);
          }
        }

        return files;
      }

      // Find all JSON files in the NaN directory structure
      const jsonFiles = await findJsonFiles(nanDirPath);
      console.log(`Found ${jsonFiles.length} JSON files in NaN folders`);

      // Move each file to the fallback directory
      for (const file of jsonFiles) {
        const fileName = path.basename(file);
        const destPath = path.join(fallbackDir, fileName);

        // If file with same name exists, add a suffix
        let finalDestPath = destPath;
        let counter = 1;

        while (await fs.pathExists(finalDestPath)) {
          const fileNameParts = path.parse(fileName);
          finalDestPath = path.join(fallbackDir, `${fileNameParts.name}_${counter}${fileNameParts.ext}`);
          counter++;
        }

        await fs.copy(file, finalDestPath);
        console.log(`Moved ${fileName} to fallback directory`);
      }

      // Remove the NaN directory after moving all files
      await fs.remove(nanDirPath);
      console.log(`Removed NaN directory structure for ${handle}`);
    }
  }

  console.log('Finished fixing NaN folders issue.');
}

// Run the function
fixNaNFolders().catch(error => {
  console.error('Error fixing NaN folders:', error);
  process.exit(1);
});
