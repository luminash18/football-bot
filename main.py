import tweepy
import os
import feedparser
import yaml
from datetime import datetime
import random
from utils import clean_html, truncate_text

# Load configuration
def load_config():
    with open('sources.yml', 'r') as file:
        return yaml.safe_load(file)

# Get RSS feeds from config
def get_feeds():
    config = load_config()
    return config.get('rss_feeds', [])

# Fetch and parse RSS feeds
def fetch_news():
    feeds = get_feeds()
    all_entries = []

    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                # Only include recent entries (last 24 hours)
                published_time = datetime(*entry.published_parsed[:6])
                if (datetime.utcnow() - published_time).total_seconds() < 86400:
                    all_entries.append({
                        'title': entry.title,
                        'link': entry.link,
                        'published': published_time,
                        'summary': clean_html(getattr(entry, 'summary', ''))
                    })
        except Exception as e:
            print(f"Error parsing feed {feed_url}: {e}")

    return all_entries

# Select a news item to tweet
def select_news_item(news_items):
    if not news_items:
        return None

    # Filter out very short titles and select a random item
    valid_items = [item for item in news_items if len(item['title']) > 20]
    if valid_items:
        return random.choice(valid_items)
    return None

# Format tweet text
def format_tweet(news_item):
    title = truncate_text(news_item['title'], 200)
    hashtags = " #Football #Soccer #News #Sports"

    # Ensure tweet doesn't exceed 280 characters including link
    max_length = 280 - len(news_item['link']) - len(hashtags) - 5  # 5 for spaces and ellipsis

    if len(title) > max_length:
        title = title[:max_length-3] + "..."

    return f"{title}\n\n{news_item['link']}{hashtags}"

def main():
    # Twitter API credentials
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    access_token = os.getenv("ACCESS_TOKEN")
    access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

    if not all([api_key, api_secret, access_token, access_token_secret]):
        print("❌ Missing Twitter API credentials")
        return

    # Initialize Twitter client
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )

    # Fetch news
    print("📰 Fetching football news...")
    news_items = fetch_news()

    if not news_items:
        print("❌ No recent news found")
        return

    # Select and format news item
    selected_news = select_news_item(news_items)

    if not selected_news:
        print("❌ No suitable news item found")
        return

    tweet_text = format_tweet(selected_news)

    # Post tweet
    try:
        response = client.create_tweet(text=tweet_text)
        print("✅ Tweet posted successfully!")
        print(f"📋 Content: {tweet_text}")
        print(f"🔗 Response: {response}")
    except tweepy.TweepyException as e:
        print(f"❌ Error posting tweet: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
