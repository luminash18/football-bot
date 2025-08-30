import tweepy
import os
import logging
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils import truncate_text, download_image

GOAL_NEWS_URL = "https://www.goal.com/en/news"
POSTED_URLS_FILE = "posted_goal_urls.txt"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_twitter_api():
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    access_token = os.getenv("ACCESS_TOKEN")
    access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")
    bearer_token = os.getenv("BEARER_TOKEN")
    if not all([api_key, api_secret, access_token, access_token_secret, bearer_token]):
        logger.error("❌ Missing Twitter API credentials")
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

def get_hashtags_from_headline(headline):
    # Simple tags: 3 longest, meaningful words, cleaned and lowercased, no duplicates
    words = re.findall(r"\b[a-zA-Z]{5,}\b", headline)
    tags = []
    for word in words:
        word = word.lower()
        if word not in tags:
            tags.append(word)
        if len(tags) == 3:
            break
    return ["#" + tag for tag in tags]

def fetch_goal_news():
    logger.info(f"🌍 Scraping latest football news from Goal.com ...")
    try:
        resp = requests.get(GOAL_NEWS_URL, timeout=15)
    except Exception as e:
        logger.error(f"❌ Error loading Goal.com: {e}")
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    articles = soup.find_all("a", class_="type-article")  # Adapt this if Goal.com changes layout!
    news_items = []
    seen_links = set()
    for article in articles:
        # Get absolute article URL
        article_url = article.get("href")
        if article_url and article_url.startswith("/"):
            article_url = "https://www.goal.com" + article_url
        if not article_url or article_url in seen_links:
            continue
        seen_links.add(article_url)
        # Headline
        headline_div = article.find("div", class_="title")
        headline = headline_div.get_text(strip=True) if headline_div else None
        if not headline:
            continue
        # Visit article, fetch image (prefer og:image)
        try:
            detail_resp = requests.get(article_url, timeout=10)
            detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
            image_url = None
            ogimg = detail_soup.find("meta", property="og:image")
            if ogimg and ogimg.get("content"):
                image_url = ogimg["content"]
            else:
                imgtag = detail_soup.find("img")
                if imgtag and imgtag.get("src"):
                    image_url = imgtag["src"]
        except Exception:
            image_url = None
        news_items.append({
            "headline": headline,
            "link": article_url,
            "image_url": image_url
        })
    logger.info(f"🔍 Extracted {len(news_items)} news articles from Goal.com")
    return news_items

def format_tweet(news_item):
    # Only headline and 3 hashtags
    hashtags = get_hashtags_from_headline(news_item["headline"])
    tweet_text = news_item["headline"] + "\n" + " ".join(hashtags)
    if len(tweet_text) > 280:
        tweet_text = truncate_text(tweet_text, 275) + "..."
    return tweet_text

def post_news_on_x():
    client, api = get_twitter_api()
    if not client or not api:
        logger.error("❌ Twitter API not configured.")
        return
    posted_urls = load_posted_urls()
    news_items = fetch_goal_news()
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
            logger.info(f"📝 Full story posted: {news['headline']}")
            posted = True
            break  # Post only one per run/schedule
        except tweepy.TweepyException as e:
            logger.error(f"❌ Error posting tweet: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
    if not posted:
        logger.info("❌ No new news to post!")

def main():
    post_news_on_x()

if __name__ == "__main__":
    main()
