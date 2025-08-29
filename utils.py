import re
from bs4 import BeautifulSoup

def clean_html(text):
    """Remove HTML tags from text"""
    if not text:
        return ""

    # Remove HTML tags using BeautifulSoup
    soup = BeautifulSoup(text, "html.parser")
    clean_text = soup.get_text()

    # Remove extra whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    return clean_text

def truncate_text(text, max_length):
    """Truncate text to maximum length without breaking words"""
    if len(text) <= max_length:
        return text

    # Truncate and add ellipsis
    truncated = text[:max_length-3]
    # Find the last space to avoid breaking words
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]

    return truncated + '...'

def is_valid_url(url):
    """Check if URL is valid"""
    import re
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return re.match(regex, url) is not None
