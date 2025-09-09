const fs = require('fs-extra');
const path = require('path');

class DataOrganizer {
  async organize(username, profileData) {
    const profilePath = path.join(process.cwd(), 'profiles', username);

    // Create folder structure
    await fs.ensureDir(path.join(profilePath, 'articles'));
    await fs.ensureDir(path.join(profilePath, 'interactions'));
    await fs.ensureDir(path.join(profilePath, 'infos'));

    // Save profile info
    await fs.writeFile(
      path.join(profilePath, 'infos', 'profile.json'),
      JSON.stringify(profileData.profile, null, 2)
    );

    await fs.writeFile(
      path.join(profilePath, 'infos', 'download_info.json'),
      JSON.stringify({
        username,
        downloadedAt: profileData.downloadedAt,
        totalPosts: profileData.posts.length,
        totalFollows: profileData.follows.length,
        totalFollowers: profileData.followers.length
      }, null, 2)
    );

    // Save posts as individual files
    for (const [index, post] of profileData.posts.entries()) {
      const filename = `${String(index).padStart(4, '0')}_${post.cid}.json`;
      await fs.writeFile(
        path.join(profilePath, 'articles', filename),
        JSON.stringify(post, null, 2)
      );
    }

    // Save interactions
    await fs.writeFile(
      path.join(profilePath, 'interactions', 'follows.json'),
      JSON.stringify(profileData.follows, null, 2)
    );

    await fs.writeFile(
      path.join(profilePath, 'interactions', 'followers.json'),
      JSON.stringify(profileData.followers, null, 2)
    );

    await fs.writeFile(
      path.join(profilePath, 'interactions', 'likes.json'),
      JSON.stringify(profileData.likes, null, 2)
    );

    return profilePath;
  }
}

module.exports = { DataOrganizer };
