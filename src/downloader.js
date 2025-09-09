class ProfileDownloader {
  constructor(agent, options = {}) {
    this.agent = agent;
    this.options = options;
  }

  async downloadProfile(username) {
    const handle = username.includes('.') ? username : `${username}.bsky.social`;

    // Get profile info
    const profile = await this.agent.getProfile({ actor: handle });

    // Get posts
    const posts = await this.getAllPosts(handle);

    // Get follows/followers
    const follows = await this.getFollows(handle);
    const followers = await this.getFollowers(handle);

    // Get likes
    const likes = await this.getLikes(handle);

    return {
      profile: profile.data,
      posts,
      follows,
      followers,
      likes,
      downloadedAt: new Date().toISOString()
    };
  }

  async getAllPosts(handle, cursor = null, allPosts = []) {
    try {
      const response = await this.agent.getAuthorFeed({
        actor: handle,
        cursor,
        limit: 100
      });

      allPosts.push(...response.data.feed.map(item => item.post));

      if (response.data.cursor && response.data.feed.length === 100) {
        // Add small delay to avoid rate limits
        await new Promise(resolve => setTimeout(resolve, 1000));
        return this.getAllPosts(handle, response.data.cursor, allPosts);
      }

      return allPosts;
    } catch (error) {
      if (this.options.verbose) {
        console.warn(`Warning: Could not fetch all posts: ${error.message}`);
      }
      return allPosts;
    }
  }

  async getFollows(handle) {
    try {
      const response = await this.agent.getFollows({
        actor: handle,
        limit: 100
      });
      return response.data.follows;
    } catch (error) {
      if (this.options.verbose) {
        console.warn(`Warning: Could not fetch follows: ${error.message}`);
      }
      return [];
    }
  }

  async getFollowers(handle) {
    try {
      const response = await this.agent.getFollowers({
        actor: handle,
        limit: 100
      });
      return response.data.followers;
    } catch (error) {
      if (this.options.verbose) {
        console.warn(`Warning: Could not fetch followers: ${error.message}`);
      }
      return [];
    }
  }

  async getLikes(handle) {
    try {
      // Note: Likes endpoint might not be available for all profiles
      return [];
    } catch (error) {
      return [];
    }
  }
}

module.exports = { ProfileDownloader };
