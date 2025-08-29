# ⚽ Football News Twitter Bot 🤖

A Python bot that automatically fetches the latest football news and transfer rumors from various RSS feeds and posts them to Twitter.

## 🌟 Features

- **📰 Automated News Posting**: Fetches and posts breaking football news from trusted sources
- **🔁 Transfer Rumors**: Special handling for transfer news from Transfermarkt
- **🖼️ Image Support**: Automatically attaches relevant images to tweets
- **⏰ Smart Scheduling**: Posts recent content (last 4 hours by default)
- **🎯 Source Attribution**: Properly credits original sources with Twitter handles
- **📊 Logging**: Comprehensive logging for monitoring and debugging

## 📋 Supported News Sources

| Source | Twitter Handle | Focus Area |
|--------|----------------|------------|
| Sky Sports | `@SkySports` | Premier League, General Football |
| BBC Sport | `@BBCSport` | UK Football, General Sports |
| The Guardian | `@GuardianSport` | Football News & Analysis |
| Premier League | `@premierleague` | Official EPL Content |
| UEFA | `@ChampionsLeague` | European Competitions |
| Marca | `@marca` | Spanish Football |
| AS | `@diarioas` | Spanish Football |
| ESPN FC | `@ESPNFC` | Global Football Coverage |
| Goal | `@goal` | Global Football News |
| FIFA | `@FIFAcom` | International Football |
| Transfermarkt | `@Transfermarkt` | Transfers & Rumors |
| 90min | `@90min_Football` | Football Content |
| MLS | `@MLS` | Major League Soccer |

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/football-news-bot.git
cd football-news-bot
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export API_KEY="your_twitter_api_key"
export API_SECRET="your_twitter_api_secret"
export ACCESS_TOKEN="your_twitter_access_token"
export ACCESS_TOKEN_SECRET="your_twitter_access_token_secret"
export BEARER_TOKEN="your_twitter_bearer_token"
```

## ⚙️ Configuration

Edit the `sources.yml` file to add or modify RSS feeds:

```yaml
rss_feeds:
  - "https://www.skysports.com/rss/12040"
  - "https://feeds.bbci.co.uk/sport/football/rss.xml"
  - "https://www.theguardian.com/football/rss"
  # Add more feeds as needed
```

## 🚀 Usage

Run the bot manually:
```bash
python main.py
```

For automated posting, set up a cron job or task scheduler to run the script every few hours.

## 📁 Project Structure

```
football-news-bot/
├── main.py              # Main bot script
├── utils.py             # Utility functions
├── sources.yml          # RSS feed configuration
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🔧 Dependencies

- `tweepy` - Twitter API client
- `feedparser` - RSS feed parsing
- `PyYAML` - YAML configuration parsing
- `beautifulsoup4` - HTML parsing
- `requests` - HTTP requests

## 🤝 Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## ⚠️ Limitations

- Twitter character limit (280 characters) may require text truncation
- Image availability depends on source RSS feeds
- Rate limiting by Twitter API and source websites

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- All football news sources for providing RSS feeds
- Twitter for API access
- Python community for excellent libraries

---

**⭐ If you find this project useful, please give it a star on GitHub!**
