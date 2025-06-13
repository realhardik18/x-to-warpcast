import os
import requests
import time
import json
from dotenv import load_dotenv

def log(msg):
    print(f"[LOG] {msg}")

load_dotenv()

# Check envs
REQUIRED_ENVS = ['TWEET_ID', 'RAPID_API_KEY', 'FARCASTER_MNEMONIC']
missing_envs = [e for e in REQUIRED_ENVS if not os.getenv(e)]
if missing_envs:
    log(f"Missing required environment variables: {', '.join(missing_envs)}")
else:
    log("All required environment variables are set.")

def get_screen_ids():
    tweet_ids = os.getenv('TWEET_ID', '')
    return [tid.strip() for tid in tweet_ids.split(',') if tid.strip()]

def extract_tweets_from_entry(entry):
    tweets = []
    # TimelineTimelineItem (single tweet)
    if entry.get("content", {}).get("entryType") == "TimelineTimelineItem":
        item_content = entry["content"].get("itemContent", {})
        tweet_results = item_content.get("tweet_results", {})
        result = tweet_results.get("result")
        if result:
            tweets.append(result)
    # TimelineTimelineModule (conversation or module)
    elif entry.get("content", {}).get("entryType") == "TimelineTimelineModule":
        items = entry["content"].get("items", [])
        for item in items:
            item_content = item.get("item", {}).get("itemContent", {})
            tweet_results = item_content.get("tweet_results", {})
            result = tweet_results.get("result")
            if result:
                tweets.append(result)
    return tweets

def fetch_last_5_tweets(user_id):
    url = f"https://twitter241.p.rapidapi.com/user-tweets?user={user_id}&count=5"
    headers = {
        "x-rapidapi-host": "twitter241.p.rapidapi.com",
        "x-rapidapi-key": os.getenv('RAPID_API_KEY')
    }
    response = requests.get(url, headers=headers)
    tweets = []
    if response.status_code == 200:
        try:
            instructions = response.json()['result']['timeline']['instructions']
            for instruction in instructions:
                if instruction.get("type") == "TimelineAddEntries":
                    for entry in instruction.get("entries", []):
                        for tweet in extract_tweets_from_entry(entry):
                            legacy = tweet.get("legacy", {})
                            tweet_text = legacy.get("full_text", "")
                            if tweet_text[:2] == "RT":
                                continue
                            screen_name = tweet.get("core", {}).get("user_results", {}).get("result", {}).get("legacy", {}).get("screen_name", "")
                            tweet_id = legacy.get("id_str", tweet.get("rest_id", ""))
                            tweet_url = f"https://twitter.com/{screen_name}/status/{tweet_id}"
                            tweets.append({
                                "tweet_id": tweet_id,
                                "tweet_text": tweet_text,
                                "tweet_url": tweet_url
                            })
                elif instruction.get("type") == "TimelinePinEntry":
                    entry = instruction.get("entry", {})
                    for tweet in extract_tweets_from_entry(entry):
                        legacy = tweet.get("legacy", {})
                        tweet_text = legacy.get("full_text", "")
                        if tweet_text[:2] == "RT":
                            continue
                        screen_name = tweet.get("core", {}).get("user_results", {}).get("result", {}).get("legacy", {}).get("screen_name", "")
                        tweet_id = legacy.get("id_str", tweet.get("rest_id", ""))
                        tweet_url = f"https://twitter.com/{screen_name}/status/{tweet_id}"
                        tweets.append({
                            "tweet_id": tweet_id,
                            "tweet_text": tweet_text,
                            "tweet_url": tweet_url
                        })
        except Exception as e:
            print(f"Error parsing tweets for user {user_id}: {e}")
    else:
        print(f"Failed to fetch tweets for user {user_id}: {response.status_code}")
    # Only keep the last 5 tweets
    return tweets[:5]

TWEET_CACHE_FILE = 'tweet_cache.json'

def load_tweet_cache():
    if os.path.exists(TWEET_CACHE_FILE):
        log(f"Loading tweet cache from {TWEET_CACHE_FILE}")
        with open(TWEET_CACHE_FILE, 'r') as f:
            return json.load(f)
    else:
        log(f"Cache file {TWEET_CACHE_FILE} does not exist. It will be created.")
    return {}

def save_tweet_cache(cache):
    with open(TWEET_CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)
    log(f"Saved tweet cache to {TWEET_CACHE_FILE}")

# Farcaster integration
def cast_to_farcaster(text):
    from farcaster import Warpcast
    mnemonic = os.getenv("FARCASTER_MNEMONIC")
    if not mnemonic:
        log("FARCASTER_MNEMONIC not set. Skipping cast.")
        return
    try:
        client = Warpcast(mnemonic=mnemonic)
        health = client.get_healthcheck()
        log(f"Farcaster healthcheck: {health}")
        broadcast = client.post_cast(text=text)
        hash = broadcast.cast.hash
        log(f"Successfully casted to Farcaster. Hash: {hash}")
    except Exception as e:
        log(f"Error casting to Farcaster: {e}")

def main_loop():
    while True:
        ids = get_screen_ids()
        tweet_cache = load_tweet_cache()
        for user_id in ids:
            tweets = fetch_last_5_tweets(user_id)
            cached_tweet_ids = set(t['tweet_id'] for t in tweet_cache.get(user_id, []))
            new_tweets = [t for t in tweets if t['tweet_id'] not in cached_tweet_ids]
            if new_tweets:
                for t in new_tweets:
                    log(f"New tweet for {user_id}:")
                    log(f"Text: {t['tweet_text']}")
                    log(f"URL: {t['tweet_url']}")
                    cast_to_farcaster(f"{t['tweet_text']}")
            tweet_cache[user_id] = tweets
        save_tweet_cache(tweet_cache)
        log(f"Sleeping for {os.getenv('COOLDOWN_TIME')} seconds...\n")
        time.sleep(os.getenv('COOLDOWN_TIME'))

if __name__ == "__main__":
    main_loop()