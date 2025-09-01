import tweepy
import os
import logging
import requests
import feedparser
from datetime import datetime, timedelta
from utils import truncate_text, download_image, get_hashtags_from_headline

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# RSS feeds for football news (add more as needed)
RSS_FEEDS = [
    "https://www.goal.com/feeds/en/news",
    "https://www.skysports.com/rss/12040",
    "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "https://www.theguardian.com/football/rss",
]

POSTED_URLS_FILE = "posted_urls.txt"

def get_twitter_api():
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    access_token = os.getenv("ACCESS_TOKEN")
    access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")
    bearer_token = os.getenv("BEARER_TOKEN")

    # Debug logging to see what's being loaded
    logger.info(f"API_KEY found: {bool(api_key)}")
    logger.info(f"API_SECRET found: {bool(api_secret)}")
    logger.info(f"ACCESS_TOKEN found: {bool(access_token)}")
    logger.info(f"ACCESS_TOKEN_SECRET found: {bool(access_token_secret)}")

    if not all([api_key, api_secret, access_token, access_token_secret]):
        logger.error("❌ Missing Twitter API credentials")
        logger.error("Please set API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET environment variables")
        return None, None

    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
        bearer_token=bearer_token
    )
    auth = tweepy.OAuth1UserHandler(
        api_key, api_secret, access_token, access_token_secret
    )
    api = tweepy.API(auth)
    return client, api

def load_posted_urls():
    if not os.path.exists(POSTED_URLS_FILE):
        return set()
    with open(POSTED_URLS_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_posted_url(url):
    with open(POSTED_URLS_FILE, "a") as f:
        f.write(url + "\n")

def fetch_news_from_rss():
    """Fetch news from all RSS feeds"""
    all_news = []

    for feed_url in RSS_FEEDS:
        try:
            logger.info(f"📡 Fetching news from RSS feed: {feed_url}")
            feed = feedparser.parse(feed_url)

            for entry in feed.entries:
                # Only consider recent articles (last 4 hours)
                published_time = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                if datetime.now() - published_time > timedelta(hours=4):
                    continue

                # Extract image if available
                image_url = None
                if hasattr(entry, 'links'):
                    for link in entry.links:
                        if link.get('type', '').startswith('image/'):
                            image_url = link.href
                            break

                # If no image found in links, try media content
                if not image_url and hasattr(entry, 'media_content'):
                    for media in entry.media_content:
                        if media.get('type', '').startswith('image/'):
                            image_url = media['url']
                            break

                # If still no image, try media thumbnail
                if not image_url and hasattr(entry, 'media_thumbnail'):
                    image_url = entry.media_thumbnail[0]['url']

                news_item = {
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.get('summary', ''),
                    "published": published_time,
                    "image_url": image_url,
                    "source": feed_url  # Track which feed this came from
                }
                all_news.append(news_item)

        except Exception as e:
            logger.error(f"❌ Error processing RSS feed {feed_url}: {e}")

    # Sort by publication date (newest first)
    all_news.sort(key=lambda x: x['published'], reverse=True)
    logger.info(f"🔍 Found {len(all_news)} recent news articles from RSS feeds")
    return all_news

def get_twitter_handle_from_source(source_url):
    """Map RSS feed URL to Twitter handle"""
    handle_map = {
        "https://www.goal.com/feeds/en/news": "@goal",
        "https://www.skysports.com/rss/12040": "@SkySports",
        "https://feeds.bbci.co.uk/sport/football/rss.xml": "@BBCSport",
        "https://www.theguardian.com/football/rss": "@GuardianSport",
    }
    return handle_map.get(source_url, "")

def format_tweet(news_item):
    """Format a tweet from news item"""
    hashtags = get_hashtags_from_headline(news_item['title'])
    source_handle = get_twitter_handle_from_source(news_item['source'])

    tweet_text = f"⚽ {news_item['title']}\n\n"
    if news_item['summary']:
        # Clean the summary and truncate if needed
        clean_summary = news_item['summary'].split('.')[0]  # Take first sentence
        if len(clean_summary) > 120:
            clean_summary = clean_summary[:117] + '...'
        tweet_text += f"{clean_summary}\n\n"

    tweet_text += f"🔗 Read more: {news_item['link']}\n"

    if source_handle:
        tweet_text += f"Via {source_handle}\n"

    tweet_text += ' '.join(hashtags[:3])  # Use up to 3 hashtags

    # Truncate if needed
    if len(tweet_text) > 280:
        tweet_text = truncate_text(tweet_text, 275) + "..."

    return tweet_text

def post_news_on_x():
    client, api = get_twitter_api()
    if not client or not api:
        logger.error("❌ Twitter API not configured.")
        return

    posted_urls = load_posted_urls()
    news_items = fetch_news_from_rss()
    posted = False

    for news in news_items:
        if news["link"] in posted_urls:
            continue

        tweet_text = format_tweet(news)
        logger.info(f"📝 Prepared tweet: {tweet_text}")

        media_id = None
        if news["image_url"]:
            try:
                image_path = download_image(news["image_url"])
                if image_path:
                    media = api.media_upload(image_path)
                    media_id = media.media_id
                    logger.info("✅ Image uploaded successfully.")
                    os.remove(image_path)
            except Exception as e:
                logger.error(f"❌ Error uploading image: {e}")

        try:
            if media_id:
                response = client.create_tweet(text=tweet_text, media_ids=[media_id])
            else:
                response = client.create_tweet(text=tweet_text)

            logger.info("✅ Tweet posted successfully!")
            save_posted_url(news["link"])
            posted = True
            logger.info(f"📝 News posted: {news['title']}")
            break  # Post only one per run

        except tweepy.TweepyException as e:
            logger.error(f"❌ Error posting tweet: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")

    if not posted:
        logger.info("ℹ️ No new news to post right now.")

def main():
    post_news_on_x()

if __name__ == "__main__":
    main()
