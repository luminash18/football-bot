# Football → X Daily Bot

A Python bot that automatically posts football news to X (Twitter) using RSS feeds.

## Features

- Fetches news from multiple RSS feeds (BBC Sport, ESPN Soccer)
- Posts 4 times daily (8AM, 12PM, 4PM, 8PM UTC)
- Automatically formats tweets with hashtags
- Filters for recent news (last 24 hours)

## Setup

1. **Twitter Developer Account**: Apply for a developer account at https://developer.twitter.com/

2. **Create App**: Create a new app and generate API keys:
   - API Key
   - API Secret
   - Access Token
   - Access Token Secret

3. **GitHub Secrets**: Add these as secrets in your GitHub repository:
   - `API_KEY`
   - `API_SECRET`
   - `ACCESS_TOKEN`
   - `ACCESS_TOKEN_SECRET`

4. **Customize**: Edit `sources.yml` to add or modify RSS feeds

## Usage

The bot runs automatically on schedule, but you can also trigger it manually from the GitHub Actions tab.

## RSS Feeds

Currently configured:
- BBC Sport Football RSS
- ESPN Soccer News RSS

Add more feeds in `sources.yml` as needed.
