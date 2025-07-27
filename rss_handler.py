import os
import requests
import xml.etree.ElementTree as ET
from dateutil.parser import parse as parse_date
from datetime import datetime, timedelta, timezone
from database import article_exists, add_article

def parse_rss(xml_content):
    """Parses the RSS XML content and returns a list of articles."""
    articles = []
    try:
        root = ET.fromstring(xml_content)
        for item in root.findall('.//item'):
            title = item.find('title').text
            link = item.find('link').text
            description = item.find('description').text
            pub_date_str = item.find('pubDate').text
            pub_date = parse_date(pub_date_str)

            articles.append({
                'url': link,
                'headline': title,
                'summary': description,
                'published_at': pub_date,
                'source_name': 'The Guardian RSS'
            })
    except ET.ParseError as e:
        print(f"🔴 ERROR: Failed to parse RSS XML: {e}")
    return articles

def fetch_and_store_articles(user_id, time_limit_hours=None):
    """Fetches RSS feed, parses it, and stores new articles in the database."""
    rss_url = os.environ.get("RSS_FEED")
    if not rss_url:
        print("🔴 ERROR: RSS_FEED URL not set in .env file.")
        return []

    min_timestamp = None
    if time_limit_hours:
        min_timestamp = datetime.now(timezone.utc) - timedelta(hours=int(time_limit_hours))

    try:
        print("Fetching articles from RSS feed...")
        response = requests.get(rss_url, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"🔴 ERROR: Could not fetch RSS feed: {e}")
        return []

    articles = parse_rss(response.content)
    new_article_captions = []

    for article in articles:
        # Ensure published_at is timezone-aware for comparison
        if article['published_at'].tzinfo is None:
            article['published_at'] = article['published_at'].replace(tzinfo=timezone.utc)

        if min_timestamp and article['published_at'] < min_timestamp:
            print(f"Skipping old RSS article: {article['headline']}. Timestamp: {article['published_at']}")
            continue

        if not article_exists(article['url'], user_id):
            print(f"Found new article: {article['headline']}")
            add_article(
                article['url'],
                user_id,
                article['headline'],
                article['source_name'],
                article['summary'],
                article['published_at']
            )
            # Add the headline and summary to the list for Gemini processing
            new_article_captions.append(f"- @{article['source_name']}: {article['headline']}\n{article['summary']}\n")
        else:
            print(f"Skipping article (already exists): {article['headline']}")

    return "".join(new_article_captions)