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
                    # Try to extract image from content
                    image_url = find_image_in_content(entry)

                    all_entries.append({
                        'title': entry.title,
                        'link': entry.link,
                        'published': published_time,
                        'summary': clean_html(getattr(entry, 'summary', '')),
                        'image_url': image_url,
                        'source': feed_url
                    })
        except Exception as e:
            logger.error(f"Error parsing feed {feed_url}: {e}")

    return sorted(all_entries, key=lambda x: x['published'], reverse=True)

def select_top_news(news_items, count=3):
    if not news_items:
        return []

    # Filter out short titles and select top recent news
    valid_items = [item for item in news_items if len(item['title']) > 15]

    # Prioritize items with images
    items_with_images = [item for item in valid_items if item.get('image_url')]
    items_without_images = [item for item in valid_items if not item.get('image_url')]

    selected = items_with_images[:count]
    if len(selected) < count:
        selected.extend(items_without_images[:count - len(selected)])

    return selected

def format_multi_news_tweet(news_items):
    hashtags = " #Football #Soccer #News #Sports #PremierLeague #UCL"

    tweet_text = "⚽ TOP FOOTBALL NEWS ⚽\n\n"

    for i, item in enumerate(news_items, 1):
        news_line = f"{i}️⃣ {truncate_text(item['title'], 80)}"
        tweet_text += f"{news_line}\n"

    tweet_text += f"\n📖 Read more:{hashtags}"

    # Ensure tweet doesn't exceed character limit
    if len(tweet_text) > 280:
        tweet_text = tweet_text[:275] + "..."

    return tweet_text

def get_best_image(news_items):
    """Select the best image from news items (prioritize larger images)"""
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

    # Initialize Twitter client
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
        bearer_token=bearer_token
    )

    # Initialize OAuth1 for media upload
    auth = tweepy.OAuth1UserHandler(
        api_key, api_secret, access_token, access_token_secret
    )
    api = tweepy.API(auth)

    # Fetch news from last 4 hours
    logger.info("📰 Fetching football news from last 4 hours...")
    news_items = fetch_news(hours=4)

    if not news_items:
        logger.error("❌ No recent news found")
        return

    # Select top 3 news items
    top_news = select_top_news(news_items, count=3)

    if not top_news:
        logger.error("❌ No suitable news items found")
        return

    # Format tweet
    tweet_text = format_multi_news_tweet(top_news)

    # Try to get and upload image
    media_id = None
    image_url = get_best_image(top_news)

    if image_url:
        try:
            image_path = download_image(image_url)
            if image_path:
                media = api.media_upload(image_path)
                media_id = media.media_id
                logger.info(f"✅ Image uploaded successfully: {image_url}")
                # Clean up temporary file
                if os.path.exists(image_path):
                    os.remove(image_path)
        except Exception as e:
            logger.error(f"❌ Error uploading image: {e}")

    # Post tweet
    try:
        if media_id:
            response = client.create_tweet(text=tweet_text, media_ids=[media_id])
        else:
            response = client.create_tweet(text=tweet_text)

        logger.info("✅ Tweet posted successfully!")
        logger.info(f"📋 Content: {tweet_text}")

        # Add reply with individual links
        reply_text = "🔗 Read full stories:\n"
        for i, item in enumerate(top_news, 1):
            reply_text += f"{i}. {item['link']}\n"

        # Post as reply
        client.create_tweet(text=reply_text, in_reply_to_tweet_id=response.data['id'])
        logger.info("✅ Reply with links posted!")

    except tweepy.TweepyException as e:
        logger.error(f"❌ Error posting tweet: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
