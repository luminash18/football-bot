import tweepy
import os

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

client = tweepy.Client(
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)

try:
    response = client.create_tweet(text="⚽ Football bot test tweet from GitHub Actions!")
    print("✅ Tweet posted:", response)
except Exception as e:
    print("❌ Error posting tweet:", e)
