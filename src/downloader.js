const fs = require('fs-extra');
const path = require('path');
const ora = require('ora');
const chalk = require('chalk');
const authManager = require('./auth');
const { DEFAULT_PAGE_LIMIT } = require('./config');
const { ensureDir, safeReadJson, safeWriteJson, getProfileDir } = require('./utils/fs');
const { compressProfile } = require('./organizer');
const logger = require('./logger');

class ProfileDownloader {
  constructor(options = {}) {
    this.verbose = options.verbose || false;
    this.compress = options.compress !== false;
  }

  /**
   * Download a profile and all its data
   */
  async downloadProfile(handle) {
    const agent = await authManager.getAgent();
    const spinner = ora(`Resolving profile for ${handle}...`).start();

    try {
      // Resolve the handle to get the DID
      let did;
      try {
        const resolved = await agent.resolveHandle({ handle });
        did = resolved.data.did;
        spinner.succeed(`Resolved ${handle} to ${did}`);
      } catch (error) {
        spinner.fail(`Failed to resolve handle ${handle}`);
        throw new Error(`Could not resolve handle: ${error.message}`);
      }

      // Set up the profile directory structure
      const profileDir = getProfileDir(handle);
      const infosDir = path.join(profileDir, 'infos');
      const articlesDir = path.join(profileDir, 'articles');
      const interactionsDir = path.join(profileDir, 'interactions');

      await Promise.all([
        ensureDir(profileDir),
        ensureDir(infosDir),
        ensureDir(articlesDir),
        ensureDir(interactionsDir)
      ]);

      // Read or create manifest
      const manifestPath = path.join(infosDir, 'manifest.json');
      const manifest = await safeReadJson(manifestPath, {
        handle,
        did,
        downloadedAt: [],
        postsCount: 0,
        followersCount: 0,
        followsCount: 0,
        likesCount: 0,
        cursors: {
          posts: null,
          followers: null,
          follows: null,
          likes: null
        }
      });

      // Add this download to the manifest
      manifest.downloadedAt.push(new Date().toISOString());

      // Fetch profile information
      spinner.text = `Fetching profile info for ${handle}...`;
      try {
        const profileInfo = await agent.getProfile({ actor: did });
        await safeWriteJson(path.join(infosDir, 'profile.json'), profileInfo.data);

        // Update manifest with counts
        manifest.postsCount = profileInfo.data.postsCount || 0;
        manifest.followersCount = profileInfo.data.followersCount || 0;
        manifest.followsCount = profileInfo.data.followsCount || 0;

        spinner.succeed(`Downloaded profile info for ${handle}`);
      } catch (error) {
        spinner.warn(`Could not fetch complete profile info: ${error.message}`);
      }

      // Download posts (author feed)
      await this.downloadPosts(did, articlesDir, manifest, spinner);

      // Download followers
      await this.downloadFollowers(did, interactionsDir, manifest, spinner);

      // Download follows
      await this.downloadFollows(did, interactionsDir, manifest, spinner);

      // Download likes (if available)
      await this.downloadLikes(did, interactionsDir, manifest, spinner);

      // Save the final manifest
      await safeWriteJson(manifestPath, manifest);

      // Compress the profile if requested
      if (this.compress) {
        spinner.text = `Compressing profile data for ${handle}...`;
        await compressProfile(handle, profileDir);
        spinner.succeed(`Compressed profile data for ${handle}`);
      }

      return { success: true, profileDir };
    } catch (error) {
      spinner.fail(`Failed to download profile: ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  /**
   * Download all posts from a user
   */
  async downloadPosts(did, articlesDir, manifest, spinner) {
    const agent = await authManager.getAgent();
    spinner.text = 'Downloading posts...';

    let cursor = manifest.cursors.posts;
    let postsCount = 0;
    let fileCounter = 1;
    let currentBatch = [];
    const BATCH_SIZE = 100; // How many posts to store per file

    try {
      let hasMore = true;
      while (hasMore) {
        const result = await agent.getAuthorFeed({
          actor: did,
          limit: DEFAULT_PAGE_LIMIT,
          cursor
        });

        if (!result.data || !result.data.feed || result.data.feed.length === 0) {
          hasMore = false;
          break;
        }

        // Process the posts
        currentBatch = [...currentBatch, ...result.data.feed];
        postsCount += result.data.feed.length;

        // Update cursor for the next request
        cursor = result.data.cursor;
        manifest.cursors.posts = cursor;

        if (this.verbose) {
          logger.verbose(`Downloaded ${result.data.feed.length} posts, cursor: ${cursor}`);
        }

        // If we've collected enough posts, or there are no more posts, write to file
        if (currentBatch.length >= BATCH_SIZE || !cursor) {
          const filename = `posts-${String(fileCounter).padStart(4, '0')}.json`;
          await safeWriteJson(path.join(articlesDir, filename), currentBatch);

          if (this.verbose) {
            logger.verbose(`Wrote ${currentBatch.length} posts to ${filename}`);
          }

          currentBatch = [];
          fileCounter++;
        }

        // If no more cursor, we're done
        if (!cursor) {
          hasMore = false;
        }

        spinner.text = `Downloaded ${postsCount} posts...`;
      }

      // Write any remaining posts
      if (currentBatch.length > 0) {
        const filename = `posts-${String(fileCounter).padStart(4, '0')}.json`;
        await safeWriteJson(path.join(articlesDir, filename), currentBatch);
      }

      spinner.succeed(`Downloaded ${postsCount} posts`);
    } catch (error) {
      spinner.warn(`Error downloading posts: ${error.message}`);
    }
  }

  /**
   * Download all followers of a user
   */
  async downloadFollowers(did, interactionsDir, manifest, spinner) {
    const agent = await authManager.getAgent();
    spinner.text = 'Downloading followers...';

    let cursor = manifest.cursors.followers;
    let followers = [];

    // Try to load existing followers
    const followersPath = path.join(interactionsDir, 'followers.json');
    const existingFollowers = await safeReadJson(followersPath, []);
    if (existingFollowers.length > 0) {
      followers = existingFollowers;
    }

    try {
      let hasMore = true;
      while (hasMore) {
        const result = await agent.getFollowers({
          actor: did,
          limit: DEFAULT_PAGE_LIMIT,
          cursor
        });

        if (!result.data || !result.data.followers || result.data.followers.length === 0) {
          hasMore = false;
          break;
        }

        // Process the followers
        followers = [...followers, ...result.data.followers];

        // Update cursor for the next request
        cursor = result.data.cursor;
        manifest.cursors.followers = cursor;

        if (this.verbose) {
          logger.verbose(`Downloaded ${result.data.followers.length} followers, cursor: ${cursor}`);
        }

        // If no more cursor, we're done
        if (!cursor) {
          hasMore = false;
        }

        spinner.text = `Downloaded ${followers.length} followers...`;
      }

      // Write followers to file
      await safeWriteJson(followersPath, followers);
      manifest.followersCount = followers.length;

      spinner.succeed(`Downloaded ${followers.length} followers`);
    } catch (error) {
      spinner.warn(`Error downloading followers: ${error.message}`);
    }
  }

  /**
   * Download all accounts the user follows
   */
  async downloadFollows(did, interactionsDir, manifest, spinner) {
    const agent = await authManager.getAgent();
    spinner.text = 'Downloading follows...';

    let cursor = manifest.cursors.follows;
    let follows = [];

    // Try to load existing follows
    const followsPath = path.join(interactionsDir, 'following.json');
    const existingFollows = await safeReadJson(followsPath, []);
    if (existingFollows.length > 0) {
      follows = existingFollows;
    }

    try {
      let hasMore = true;
      while (hasMore) {
        const result = await agent.getFollows({
          actor: did,
          limit: DEFAULT_PAGE_LIMIT,
          cursor
        });

        if (!result.data || !result.data.follows || result.data.follows.length === 0) {
          hasMore = false;
          break;
        }

        // Process the follows
        follows = [...follows, ...result.data.follows];

        // Update cursor for the next request
        cursor = result.data.cursor;
        manifest.cursors.follows = cursor;

        if (this.verbose) {
          logger.verbose(`Downloaded ${result.data.follows.length} follows, cursor: ${cursor}`);
        }

        // If no more cursor, we're done
        if (!cursor) {
          hasMore = false;
        }

        spinner.text = `Downloaded ${follows.length} follows...`;
      }

      // Write follows to file
      await safeWriteJson(followsPath, follows);
      manifest.followsCount = follows.length;

      spinner.succeed(`Downloaded ${follows.length} follows`);
    } catch (error) {
      spinner.warn(`Error downloading follows: ${error.message}`);
    }
  }

  /**
   * Download all likes by a user
   */
  async downloadLikes(did, interactionsDir, manifest, spinner) {
    const agent = await authManager.getAgent();
    spinner.text = 'Downloading likes...';

    let cursor = manifest.cursors.likes;
    let likesCount = 0;
    let fileCounter = 1;
    let currentBatch = [];
    const BATCH_SIZE = 100;

    try {
      // First check if the API supports getLikes
      if (!agent.getLikes) {
        spinner.info('This version of @atproto/api does not support getLikes endpoint');
        return;
      }

      let hasMore = true;
      while (hasMore) {
        const result = await agent.getLikes({
          actor: did,
          limit: DEFAULT_PAGE_LIMIT,
          cursor
        });

        if (!result.data || !result.data.likes || result.data.likes.length === 0) {
          hasMore = false;
          break;
        }

        // Process the likes
        currentBatch = [...currentBatch, ...result.data.likes];
        likesCount += result.data.likes.length;

        // Update cursor for the next request
        cursor = result.data.cursor;
        manifest.cursors.likes = cursor;

        if (this.verbose) {
          logger.verbose(`Downloaded ${result.data.likes.length} likes, cursor: ${cursor}`);
        }

        // If we've collected enough likes, or there are no more likes, write to file
        if (currentBatch.length >= BATCH_SIZE || !cursor) {
          const filename = `likes-${String(fileCounter).padStart(4, '0')}.json`;
          await safeWriteJson(path.join(interactionsDir, filename), currentBatch);

          if (this.verbose) {
            logger.verbose(`Wrote ${currentBatch.length} likes to ${filename}`);
          }

          currentBatch = [];
          fileCounter++;
        }

        // If no more cursor, we're done
        if (!cursor) {
          hasMore = false;
        }

        spinner.text = `Downloaded ${likesCount} likes...`;
      }

      // Write any remaining likes
      if (currentBatch.length > 0) {
        const filename = `likes-${String(fileCounter).padStart(4, '0')}.json`;
        await safeWriteJson(path.join(interactionsDir, filename), currentBatch);
      }

      manifest.likesCount = likesCount;
      spinner.succeed(`Downloaded ${likesCount} likes`);
    } catch (error) {
      // If the error is related to the API endpoint not being available, inform the user
      if (error.message.includes('not supported') || error.message.includes('not found')) {
        spinner.info('Likes endpoint not available in this version of @atproto/api');
      } else {
        spinner.warn(`Error downloading likes: ${error.message}`);
      }
    }
  }
}

module.exports = ProfileDownloader;
