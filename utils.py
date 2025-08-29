import re
from bs4 import BeautifulSoup
import requests
import os
from urllib.parse import urljoin
import mimetypes

def clean_html(text):
    """Remove HTML tags from text"""
    if not text:
        return ""

    soup = BeautifulSoup(text, "html.parser")
    clean_text = soup.get_text()
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    return clean_text

def truncate_text(text, max_length):
    """Truncate text to maximum length without breaking words"""
    if len(text) <= max_length:
        return text

    truncated = text[:max_length-3]
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]

    return truncated + '...'

def find_image_in_content(entry):
    """Extract image URL from RSS entry content"""
    image_url = None

    # Check common image fields in RSS
    for field in ['media_thumbnail', 'media_content', 'links']:
        if hasattr(entry, field):
            try:
                if field == 'media_thumbnail' and entry.media_thumbnail:
                    image_url = entry.media_thumbnail[0]['url']
                    break
                elif field == 'links':
                    for link in entry.links:
                        if 'image' in link.get('type', ''):
                            image_url = link['href']
                            break
            except:
                pass

    # If no image found in RSS fields, parse HTML content
    if not image_url:
        content = getattr(entry, 'content', [{}])[0] if hasattr(entry, 'content') else {}
        content_value = content.get('value', '') or getattr(entry, 'summary', '')

        if content_value:
            soup = BeautifulSoup(content_value, 'html.parser')
            img_tag = soup.find('img')
            if img_tag and img_tag.get('src'):
                image_url = img_tag['src']
                # Make relative URLs absolute
                if image_url.startswith('/'):
                    base_url = getattr(entry, 'link', '') or getattr(entry, 'id', '')
                    if base_url:
                        image_url = urljoin(base_url, image_url)

    return image_url if is_valid_url(image_url) else None

def download_image(url, timeout=10):
    """Download image from URL and save temporarily"""
    if not url:
        return None

    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()

        # Check if content is an image
        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type:
            return None

        # Create temporary file
        ext = mimetypes.guess_extension(content_type) or '.jpg'
        temp_file = f"temp_image{ext}"

        with open(temp_file, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        return temp_file

    except Exception as e:
        print(f"Error downloading image {url}: {e}")
        return None

def is_valid_url(url):
    """Check if URL is valid"""
    if not url:
        return False

    try:
        result = re.match(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', url, re.IGNORECASE)
        return result is not None
    except:
        return False
