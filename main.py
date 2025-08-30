import tweepy
import os
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from utils import truncate_text, download_image

def get_daily_football_stat():
    """
    Scrape a football stat of the day from Transfermarkt (or other public stats site)
    Returns: (stat_text, stat_image_url or None)
    """
    url = "https://www.transfermarkt.com/statistik"
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        # Example: Grab headline stat from Transfermarkt, adapt as needed
        stat_card = soup.find("div", class_="statistik-startseite-box")
        if stat_card:
            headline = stat_card.find("strong")
            stat_text = headline.get_text(strip=True) if headline else None
            # Try to find a related image
            img_tag = stat_card.find("img")
            stat_img = img_tag["src"] if img_tag else None
            # Compose a friendly stat message
            fact = f"Football Stat of the Day: {stat_text}" if stat_text else ''
            return (fact, stat_img)
        # fallback: default message
        return ("Here's your football stat of the day!", None)
    except Exception as e:
        logger.error(f"Error fetching daily football stat: {e}")
        return ("Here's your football stat of the day!", None)


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

GOAL_NEWS_URL = "https://www.goal.com/en/news"
POSTED_URLS_FILE = "posted_goal_urls.txt"

def get_twitter_api():
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    access_token = os.getenv("ACCESS_TOKEN")
    access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")
    bearer_token = os.getenv("BEARER_TOKEN")
    if not all([api_key, api_secret, access_token, access_token_secret]):
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

def fetch_goal_news():
    logger.info(f"🌍 Scraping latest football news from {GOAL_NEWS_URL} ...")
    resp = requests.get(GOAL_NEWS_URL, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")

    articles = soup.find_all("a", class_="type-article")  # Layout as of Aug 2025
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

        # Headline/text
        headline = article.find("div", class_="title").get_text(strip=True) if article.find("div", class_="title") else None
        if not headline:
            continue
        # Visit article page for clean image and summary
        detail_resp = requests.get(article_url, timeout=15)
        detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
        # Grab the summary (meta description)
        summary = ""
        desc_meta = detail_soup.find("meta", {"name": "description"})
        if desc_meta and desc_meta.get("content"):
            summary = desc_meta["content"]
        # Get main image (prefer og:image for HQ)
        image_url = None
        ogimg = detail_soup.find("meta", property="og:image")
        if ogimg and ogimg.get("content"):
            image_url = ogimg["content"]
        else:
            imgtag = detail_soup.find("img")
            if imgtag and imgtag.get("src"):  # Fallback to first img
                image_url = imgtag["src"]
        news_items.append({
            "headline": headline,
            "link": article_url,
            "summary": summary,
            "image_url": image_url
        })
    logger.info(f"🔍 Extracted {len(news_items)} news articles from Goal.com")
    return news_items

def format_tweet(news_item):
    hashtags = " #Football #Soccer #News #Goal"
    tweet_text = f"⚽ {news_item['headline']}\n\n"
    if news_item['summary']:
        tweet_text += f"{news_item['summary']}\n\n"
    tweet_text += f"🔗 Read more: {news_item['link']}\n"
    tweet_text += f"{hashtags}"
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
            posted = True
            logger.info(f"📝 Full story posted: {news['headline']}")
            break  # Post only one per run
        except tweepy.TweepyException as e:
            logger.error(f"❌ Error posting tweet: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")


    if not posted:
      logger.info("❌ No new news to post! Posting a football stat instead...")
      stat_text, stat_img_url = get_daily_football_stat()
      media_id = None
      if stat_img_url:
          image_path = download_image(stat_img_url)
          if image_path:
              try:
                  media = api.media_upload(image_path)
                  media_id = media.media_id
                  os.remove(image_path)
              except Exception as e:
                  logger.error(f"❌ Error uploading stat image: {e}")
      try:
          if media_id:
              response = client.create_tweet(text=stat_text, media_ids=[media_id])
          else:
              response = client.create_tweet(text=stat_text)
          logger.info("✅ Football stat posted successfully!")
      except tweepy.TweepyException as e:
          logger.error(f"❌ Error posting stat tweet: {e}")
      except Exception as e:
          logger.error(f"❌ Unexpected error: {e}")

def main():
    post_news_on_x()

if __name__ == "__main__":
    main()
