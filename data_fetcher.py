# data_fetcher.py
import os
import json
import feedparser
import requests
from datetime import datetime
from typing import Callable
from dotenv import load_dotenv

load_dotenv()

# ------------------------
# RSS Parser
# ------------------------
def parse_rss_articles(feed, source_name, limit=10):
    items = []
    for entry in feed.entries[:limit]:
        items.append({
            "title": entry.get("title"),
            "link": entry.get("link"),
            "published": entry.get("published"),
            "content": entry.get("summary", ""),
            "extra": {}
        })
    return {
        "source": source_name,
        "timestamp": datetime.utcnow().isoformat(),
        "data_type": "news",
        "data": items,
        "error": None
    }

def parse_bbc(feed):
    return parse_rss_articles(feed, "bbc_news")

def parse_cnn(feed):
    return parse_rss_articles(feed, "cnn_news")

def parse_reuters(feed):
    return parse_rss_articles(feed, "reuters_news")

def parse_noaa(feed):
    return parse_rss_articles(feed, "noaa_env")

# ------------------------
# Social Media Parsers
# ------------------------
def fetch_x_tweets(query="collapse OR recession OR climate", max_results=50):
    url = f"https://api.twitter.com/2/tweets/search/recent?query={query}&max_results={max_results}"
    headers = {"Authorization": f"Bearer {os.getenv('X_BEARER_TOKEN')}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def parse_x_tweets(tweets, source_name="x_social"):
    items = []
    for tweet in tweets.get("data", []):
        items.append({
            "title": tweet.get("id"),
            "link": None,
            "published": datetime.utcnow().isoformat(),
            "content": tweet.get("text"),
            "extra": {}
        })
    return {
        "source": source_name,
        "timestamp": datetime.utcnow().isoformat(),
        "data_type": "social",
        "data": items,
        "error": tweets.get("error")
    }

def parse_reddit(url, source_name="reddit_social"):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        items = []
        for post in data.get("data", []):
            items.append({
                "title": post.get("title"),
                "link": None,
                "published": datetime.utcfromtimestamp(post.get("created_utc")).isoformat(),
                "content": post.get("selftext", ""),
                "extra": {"subreddit": post.get("subreddit")}
            })
        return {
            "source": source_name,
            "timestamp": datetime.utcnow().isoformat(),
            "data_type": "social",
            "data": items,
            "error": None
        }
    except Exception as e:
        return {
            "source": source_name,
            "timestamp": datetime.utcnow().isoformat(),
            "data_type": "social",
            "data": [],
            "error": str(e)
        }

# ------------------------
# Environmental / Wildcard Parsers
# ------------------------
def fetch_generic_api(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def parse_generic_api(api_data, source_name, data_type="generic"):
    return {
        "source": source_name,
        "timestamp": datetime.utcnow().isoformat(),
        "data_type": data_type,
        "data": api_data if api_data else [],
        "error": api_data.get("error") if isinstance(api_data, dict) else None
    }

def parse_usgs(url):
    return parse_generic_api(fetch_generic_api(url), "environment_usgs", "environment")

def parse_env_noaa(url):
    return parse_generic_api(fetch_generic_api(url), "environment_noaa", "environment")

def parse_google_trends(url):
    return parse_generic_api(fetch_generic_api(url), "wildcard_google_trends", "wildcard")

def parse_climate(url):
    return parse_generic_api(fetch_generic_api(url), "wildcard_climate", "wildcard")

# ------------------------
# Fetch a single source
# ------------------------
def fetch_source(source: dict):
    name = source.get("name")
    url = source.get("url")
    parser_name = source.get("parser")
    source_type = source.get("type", "api")

    try:
        if parser_name.startswith("parse_") and source_type == "rss":
            feed = feedparser.parse(url)
            parser_func: Callable = globals()[parser_name]
            return parser_func(feed)
        elif parser_name == "fetch_x_tweets":
            tweets = fetch_x_tweets()
            return parse_x_tweets(tweets, name)
        elif parser_name.startswith("parse_") or parser_name.startswith("fetch_"):
            parser_func: Callable = globals().get(parser_name)
            if parser_func:
                return parser_func(url)
            else:
                return parse_generic_api({"error": f"Parser {parser_name} not found"}, name)
        else:
            return parse_generic_api(fetch_generic_api(url), name)
    except Exception as e:
        return {
            "source": name,
            "timestamp": datetime.utcnow().isoformat(),
            "data_type": source_type,
            "data": [],
            "error": str(e)
        }

# ------------------------
# Fetch all sources from config
# ------------------------
def fetch_all_sources(config_file="data_sources.json"):
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            sources = json.load(f)
    except Exception as e:
        print(f"Failed to load {config_file}: {e}")
        return []

    all_data = []
    for src in sources:
        data = fetch_source(src)
        all_data.append(data)
    return all_data

# ------------------------
# Main execution
# ------------------------
if __name__ == "__main__":
    all_data = fetch_all_sources()
    print(json.dumps(all_data, indent=2, ensure_ascii=False))
