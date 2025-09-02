import os
import requests
import mimetypes
import logging
from bs4 import BeautifulSoup
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def truncate_text(text, max_length):
    """Truncate text to maximum length without breaking words"""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length-3]
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + '...'

def download_image(url, timeout=10):
    """Download image from URL and save temporarily"""
    if not url:
        return None
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type:
            return None
        ext = mimetypes.guess_extension(content_type) or '.jpg'
        temp_file = f"temp_image{ext}"
        with open(temp_file, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return temp_file
    except Exception as e:
        print(f"Error downloading image {url}: {e}")
        return None

def get_hashtags_from_headline(headline):
    """
    Return up to 3 hashtags from the headline: words longer than 4 characters, lowercased, no duplicates
    """
    words = re.findall(r"\b[a-zA-Z]{5,}\b", headline)
    tags = []
    for word in words:
        word = word.lower()
        if word not in tags:
            tags.append(word)
        if len(tags) == 3:
            break
    return ["#" + tag for tag in tags]

def clean_html(text):
    """Remove HTML tags from text"""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    clean_text = soup.get_text()
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def get_twitter_handle_from_source(source_url):
    """Map RSS feed URL to Twitter handle"""
    handle_map = {
        "https://www.goal.com/feeds/en/news": "@goal",
        "https://feeds.bbci.co.uk/sport/football/rss.xml": "@BBCSport",
        "https://www.theguardian.com/football/rss": "@GuardianSport",
    }
    return handle_map.get(source_url, "")
