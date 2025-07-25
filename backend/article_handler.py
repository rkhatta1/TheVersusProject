import os
import requests
import json
import google.generativeai as genai
from urllib.parse import urlparse
from datetime import datetime, timezone
from database import article_exists, add_article
from newspaper import Article

# --- Gemini Configuration ---
try:
    gemini_api_key = os.environ["GEMINI"]
    genai.configure(api_key=gemini_api_key)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
except KeyError:
    print("🔴 ERROR: GEMINI_API_KEY not found for article_handler.")
    gemini_model = None

SINGLE_ARTICLE_PROMPT_TEMPLATE = """
You are a world-class sports news analyst. Your task is to analyze the provided article content and create a concise, engaging summary.

Instructions:
1.  Read the article content below.
2.  Generate a single JSON object with two keys: "headline" and "summary".
3.  The "headline" should be a short, catchy title for the story.
4.  The "summary" should be a one-paragraph summary of the key information and enough context about the subjects of the story to understand its significance.

Here is the article content:
---
{article_text}
---
"""

def process_single_url(url, user_id):
    """Fetches, processes, and stores a single article from a URL."""
    if not gemini_model:
        return {"error": "Gemini API not configured."}

    # 1. Check if the article already exists for this user
    if article_exists(url, user_id):
        return {"message": "This article has already been processed."}

    # 2. Fetch and extract article content
    try:
        print(f"Fetching content from URL: {url}")
        article = Article(url)
        article.download()
        article.parse()
        article_text = article.text
        if not article_text:
            return {"error": "Could not extract content from the URL."}
    except Exception as e:
        print(f"🔴 ERROR during web fetch: {e}")
        return {"error": f"Failed to fetch or process URL: {e}"}

    # 3. Use Gemini to generate headline and summary
    try:
        prompt = SINGLE_ARTICLE_PROMPT_TEMPLATE.format(article_text=article_text)
        response = gemini_model.generate_content(prompt)
        clean_response = response.text.strip().replace("```json", "").replace("```", "")
        news_item = json.loads(clean_response)
        news_item['source_caption'] = article_text[:500] + '...' # Truncate for storage
    except Exception as e:
        print(f"🔴 ERROR during Gemini analysis: {e}")
        return {"error": "Failed to analyze article with Gemini.", "details": str(e)}

    # 4. Call Kaggle server for stylization
    inference_url = os.environ.get("KAGGLE_INFERENCE_URL")
    if inference_url:
        try:
            payload = {"summary": news_item['summary']}
            response = requests.post(f"{inference_url}/generate-caption", json=payload, timeout=60)
            if response.status_code == 200:
                news_item['versus_caption'] = response.json().get('stylized_caption', 'Error: Invalid response.')
            else:
                news_item['versus_caption'] = f"Error: Server returned status {response.status_code}"
        except requests.exceptions.RequestException as e:
            print(f"🔴 ERROR connecting to Kaggle server: {e}")
            news_item['versus_caption'] = "Error: Could not connect to inference server."
    else:
        news_item['versus_caption'] = "Kaggle URL not set. Stylization skipped."

    # 5. Add the new article to the database
    try:
        source_name = urlparse(url).netloc
        add_article(
            url=url,
            user_id=user_id,
            headline=news_item['headline'],
            source_name=source_name,
            summary=news_item['summary'],
            published_at=datetime.now(timezone.utc)
        )
        print(f"✅ Successfully processed and stored article from {url} for user {user_id}")
    except Exception as e:
        print(f"🔴 ERROR saving article to database: {e}")
        # Don't block the user, just log the error and return the content
        news_item["db_error"] = f"Could not save to database: {e}"

    return news_item
