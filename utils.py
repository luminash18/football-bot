# Add this function to your utils.py
def get_twitter_handle_from_source(source_url):
    """Map RSS feed URL to Twitter handle"""
    handle_map = {
        "https://www.goal.com/feeds/en/news": "@goal",
        "https://www.skysports.com/rss/12040": "@SkySports",
        "https://feeds.bbci.co.uk/sport/football/rss.xml": "@BBCSport",
        "https://www.theguardian.com/football/rss": "@GuardianSport",
        # Add more mappings as needed based on your RSS_FEEDS
    }
    return handle_map.get(source_url, "")
