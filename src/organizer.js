const path = require('path');
const fs = require('fs-extra');
const archiver = require('archiver');
const { getProfileDir } = require('./utils/fs');

/**
 * Compress a profile directory into a zip file
 */
async function compressProfile(handle, profileDir) {
  return new Promise((resolve, reject) => {
    const outputPath = `${profileDir}.zip`;
    const output = fs.createWriteStream(outputPath);
    const archive = archiver('zip', {
      zlib: { level: 9 } // Best compression
    });

    // Listen for events
    output.on('close', () => {
      resolve({
        success: true,
        path: outputPath,
        size: archive.pointer()
      });
    });

    archive.on('error', (err) => {
      reject(err);
    });

    // Pipe archive data to the output file
    archive.pipe(output);

    // Add the profile directory to the archive
    archive.directory(profileDir, handle);

    // Finalize the archive
    archive.finalize();
  });
}

module.exports = {
  compressProfile
};
