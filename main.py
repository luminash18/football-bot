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

# Transfermarkt RSS feed for rumors
TRANSFERMARKT_RSS = "https://www.transfermarkt.com/rss/news"

def fetch_transfer_rumors():
    """Fetch actual transfer rumors from Transfermarkt RSS feed"""
    try:
        logger.info("📋 Fetching transfer rumors from Transfermarkt...")
        feed = feedparser.parse(TRANSFERMARKT_RSS)
        rumors = []

        for entry in feed.entries[:10]:  # Check last 10 entries
            # Look for transfer-related keywords
            title = entry.title.lower()
            transfer_keywords = ['transfer', 'rumor', 'rumour', 'target', 'interest', 'bid', 'deal', 'signing', 'move', 'linked']

            if any(keyword in title for keyword in transfer_keywords):
                published_time = datetime(*entry.published_parsed[:6])
                # Get rumors from last 7 days (wider window for transfers)
                if (datetime.utcnow() - published_time).days <= 7:
                    rumors.append({
                        'title': entry.title,
                        'link': entry.link,
                        'published': published_time,
                        'summary': clean_html(getattr(entry, 'summary', '')),
                        'source_handle': "@Transfermarkt"
                    })

        return rumors

    except Exception as e:
        logger.error(f"❌ Error fetching transfer rumors: {e}")
        return []

def get_source_handle(url):
    """Get Twitter handle from URL"""
    for domain, handle in SOURCE_HANDLES.items():
        if domain in url:
            return handle
    return "@FootballNews"

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

def select_best_news(news_items):
    """Select the single best news item (prioritize those with images)"""
    if not news_items:
        return None

    # Prioritize items with images
    items_with_images = [item for item in news_items if item.get('image_url')]
    if items_with_images:
        return random.choice(items_with_images)

    # If no images, return any valid news item
    valid_items = [item for item in news_items if len(item['title']) > 15]
    if valid_items:
        return random.choice(valid_items)

    return None

def format_single_news_tweet(news_item):
    """Format a single complete news story"""
    hashtags = " #Football #Soccer #News #PremierLeague #UCL"

    tweet_text = f"⚽ BREAKING: {news_item['title']}\n\n"
    tweet_text += f"📰 Source: {news_item['source_handle']}\n"
    tweet_text += f"🔗 Read more: {news_item['link']}\n\n"
    tweet_text += f"Follow for more updates!{hashtags}"

    return tweet_text

def format_transfer_tweet(transfer_rumor):
    """Format a single transfer rumor into a tweet"""
    hashtags = " #TransferNews #Rumors #Football #Soccer #Transfers"

    tweet_text = f"🔁 TRANSFER RUMOR: {transfer_rumor['title']}\n\n"
    tweet_text += f"📰 Source: @Transfermarkt\n"
    tweet_text += f"🔗 Read more: {transfer_rumor['link']}\n\n"
    tweet_text += f"Stay tuned for updates!{hashtags}"

    return tweet_text

def post_transfer_rumor(client, api):
    """Post a single transfer rumor from Transfermarkt"""
    transfer_rumors = fetch_transfer_rumors()

    if not transfer_rumors:
        logger.warning("❌ No transfer rumors found either")
        return None

    # Select the most recent transfer rumor
    transfer_rumor = transfer_rumors[0]
    tweet_text = format_transfer_tweet(transfer_rumor)

    logger.info(f"📋 Transfer rumor tweet: {tweet_text}")

    try:
        response = client.create_tweet(text=tweet_text)
        logger.info("✅ Transfer rumor posted successfully!")
        return response
    except tweepy.TweepyException as e:
        logger.error(f"❌ Error posting transfer rumor: {e}")
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
        logger.warning("❌ No recent news found - checking for transfer rumors...")
        post_transfer_rumor(client, api)
        return

    best_news = select_best_news(news_items)

    if not best_news:
        logger.warning("❌ No suitable news items found - checking for transfer rumors...")
        post_transfer_rumor(client, api)
        return

    tweet_text = format_single_news_tweet(best_news)

    # Ensure tweet doesn't exceed character limit (though it should be fine with full story)
    if len(tweet_text) > 280:
        # Only truncate if absolutely necessary, but keep the link intact
        tweet_text = truncate_text(tweet_text, 275) + "..."

    media_id = None
    image_url = best_news.get('image_url')

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
        logger.info(f"📝 Full story: {best_news['title']}")

    except tweepy.TweepyException as e:
        logger.error(f"❌ Error posting tweet: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
