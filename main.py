import tweepy
import os
import feedparser
import yaml
from datetime import datetime, timedelta
import random
import logging
import requests
from bs4 import BeautifulSoup
from utils import clean_html, truncate_text, is_valid_url, download_image, find_image_in_content

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mapping of RSS feeds to Twitter handles
SOURCE_HANDLES = {
    "skysports.com": "@SkySports",
    "bbc.co.uk": "@BBCSport",
    "theguardian.com": "@GuardianSport",
    "premierleague.com": "@premierleague",
    "uefa.com": "@ChampionsLeague",
    "marca.com": "@marca",
    "as.com": "@diarioas",
    "espn.com": "@ESPNFC",
    "goal.com": "@goal",
    "fifa.com": "@FIFAcom",
    "transfermarkt.com": "@Transfermarkt",
    "90min.com": "@90min_Football",
    "mlssoccer.com": "@MLS"
}

def get_source_handle(url):
    """Get Twitter handle from URL"""
    for domain, handle in SOURCE_HANDLES.items():
        if domain in url:
            return handle
    return "@FootballNews"  # Default handle

def load_config():
    try:
        with open('sources.yml', 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {'rss_feeds': []}

def get_feeds():
    config = load_config()
    return config.get('rss_feeds', [])

def fetch_news(hours=4):
    feeds = get_feeds()
    all_entries = []
    time_threshold = datetime.utcnow() - timedelta(hours=hours)

    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                published_time = datetime(*entry.published_parsed[:6])
                if published_time >= time_threshold:
                    image_url = find_image_in_content(entry)
                    source_handle = get_source_handle(entry.get('link', feed_url))

                    all_entries.append({
                        'title': entry.title,
                        'link': entry.link,
                        'published': published_time,
                        'summary': clean_html(getattr(entry, 'summary', '')),
                        'image_url': image_url,
                        'source_handle': source_handle,
                        'source_url': feed_url
                    })
        except Exception as e:
            logger.error(f"Error parsing feed {feed_url}: {e}")

    return sorted(all_entries, key=lambda x: x['published'], reverse=True)

def select_top_news(news_items, count=3):
    if not news_items:
        return []

    valid_items = [item for item in news_items if len(item['title']) > 15]
    items_with_images = [item for item in valid_items if item.get('image_url')]
    items_without_images = [item for item in valid_items if not item.get('image_url')]

    selected = items_with_images[:count]
    if len(selected) < count:
        selected.extend(items_without_images[:count - len(selected)])

    return selected

def format_multi_news_tweet(news_items):
    hashtags = " #Football #Soccer #News #PremierLeague #UCL #Transfers"

    tweet_text = "⚽ TOP FOOTBALL NEWS ⚽\n\n"

    for i, item in enumerate(news_items, 1):
        # Combine title and source handle in brackets
        news_line = f"{i}️⃣ {truncate_text(item['title'], 75)} ({item['source_handle']})"
        tweet_text += f"{news_line}\n\n"

    tweet_text += f"Follow for more updates!{hashtags}"

    return tweet_text

def truncate_tweet_with_handles(tweet_text, news_items):
    max_length = 280
    if len(tweet_text) <= max_length:
        return tweet_text

    base_text = "⚽ TOP FOOTBALL NEWS ⚽\n\nFollow for more updates! #Football #Soccer #News #PremierLeague #UCL #Transfers"
    available_length = max_length - len(base_text)
    avg_item_length = available_length // len(news_items)

    tweet_text = "⚽ TOP FOOTBALL NEWS ⚽\n\n"

    for i, item in enumerate(news_items, 1):
        title_max_length = avg_item_length - len(item['source_handle']) - 5  # Space for numbering and brackets
        truncated_title = truncate_text(item['title'], title_max_length)

        tweet_text += f"{i}️⃣ {truncated_title} ({item['source_handle']})\n\n"

    tweet_text += "Follow for more updates! #Football #Soccer #News #PremierLeague #UCL #Transfers"

    if len(tweet_text) > max_length:
        tweet_text = tweet_text[:max_length-3] + "..."

    return tweet_text

def get_best_image(news_items):
    for item in news_items:
        if item.get('image_url'):
            return item['image_url']
    return None

def main():
    # Twitter API credentials
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    access_token = os.getenv("ACCESS_TOKEN")
    access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")
    bearer_token = os.getenv("BEARER_TOKEN")

    if not all([api_key, api_secret, access_token, access_token_secret]):
        logger.error("❌ Missing Twitter API credentials")
        return

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

    logger.info("📰 Fetching football news from last 4 hours...")
    news_items = fetch_news(hours=4)

    if not news_items:
        logger.error("❌ No recent news found")
        return

    top_news = select_top_news(news_items, count=3)

    if not top_news:
        logger.error("❌ No suitable news items found")
        return

    tweet_text = format_multi_news_tweet(top_news)

    if len(tweet_text) > 280:
        tweet_text = truncate_tweet_with_handles(tweet_text, top_news)

    media_id = None
    image_url = get_best_image(top_news)

    if image_url:
        try:
            image_path = download_image(image_url)
            if image_path:
                media = api.media_upload(image_path)
                media_id = media.media_id
                logger.info(f"✅ Image uploaded successfully: {image_url}")
                if os.path.exists(image_path):
                    os.remove(image_path)
        except Exception as e:
            logger.error(f"❌ Error uploading image: {e}")

    try:
        if media_id:
            response = client.create_tweet(text=tweet_text, media_ids=[media_id])
        else:
            response = client.create_tweet(text=tweet_text)

        logger.info("✅ Tweet posted successfully!")
        logger.info(f"📋 Content length: {len(tweet_text)} characters")
        logger.info(f"📝 Tweet content:\n{tweet_text}")

    except tweepy.TweepyException as e:
        logger.error(f"❌ Error posting tweet: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
