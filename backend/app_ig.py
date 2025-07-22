import os
import json
import requests
from flask import Flask, jsonify
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import google.generativeai as genai
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from database import init_db, post_exists, add_post

# --- Initialization ---
load_dotenv()
app = Flask(__name__)

# --- Database Initialization ---
try:
    init_db()
    print("✅ Database initialized.")
except Exception as e:
    print(f"🔴 ERROR: Could not initialize database: {e}")
    exit()

# --- Constants ---
CACHE_FILE = "cache.json"
CACHE_DURATION_MINUTES = 10
INSTA_SESSION_FILE = "session.json"

# --- Client Configurations ---
try:
    gemini_api_key = os.environ["GEMINI"]
    genai.configure(api_key=gemini_api_key)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Gemini API configured.")
except KeyError:
    print("🔴 ERROR: GEMINI_API_KEY not found in .env file.")
    exit()

# Configure Instagrapi Client
try:
    insta_username = os.environ["INSTA_USERNAME"]
    insta_password = os.environ["INSTA_PASSWORD"]
    cl = Client()

    if os.path.exists(INSTA_SESSION_FILE):
        cl.load_settings(INSTA_SESSION_FILE)
        print("✅ Instagram session loaded from file.")
        try:
            cl.get_timeline_feed()
            print("✅ Instagram session is valid.")
        except LoginRequired:
            print("🟠 Instagram session expired. Logging in again.")
            cl.login(insta_username, insta_password)
            cl.dump_settings(INSTA_SESSION_FILE)
    else:
        print("🟠 No Instagram session file found. Logging in for the first time.")
        cl.login(insta_username, insta_password)
        cl.dump_settings(INSTA_SESSION_FILE)

except KeyError as e:
    print(f"🔴 ERROR: Missing Instagram credential in .env file: {e}")
    exit()
except Exception as e:
    print(f"🔴 ERROR during Instagram login: {e}")
    exit()

# --- Journalist & Prompt Definitions ---
INSTA_USERNAMES = ["davidornstein", "fabriziorom", "brfootball", "theathleticfc", "433"]

BREAKING_NEWS_PROMPT_TEMPLATE = """
You are a world-class sports news analyst. Your task is to analyze the provided Instagram post captions and extract the top three most significant, confirmed breaking news stories.

Instructions:
1.  Read through all the post captions provided below.
2.  Identify up to five of the most important and distinct news stories. A story could be a major transfer, a significant match result, or a key injury update.
3.  For each story you identify, create a JSON object with three keys: "headline", "summary", and "source_caption".
4.  The "source_caption" key must contain the full, original caption text from which the story was derived.
5.  Return your findings as a single, valid JSON array containing these objects.
6.  If no significant news is found, return an empty JSON array: [].

Example JSON Output:
[
  {{
    "headline": "Player X Signs for Team Y",
    "summary": "Team Y has officially completed the signing of Player X from Team Z on a five-year contract.",
    "source_caption": "- @fabriziorom: It’s confirmed! Player X to Team Y, here we go! All documents are signed and the medical is complete. A five-year deal that will be announced by the clubs tomorrow. 🔵 #Transfer"
  }},
  {{
    "headline": "Team A Wins Domestic Cup Final",
    "summary": "A late goal from their star striker secured the cup for Team A in a dramatic 2-1 victory over their rivals.",
    "source_caption": "- @davidornstein: Full time: Team A 2-1 Team B. An incredible finish at Wembley sees Team A lift the cup for the third time in their history. What a match. #CupFinal"
  }}
]

Here are the latest Instagram post captions:
---
{insta_captions}
---
"""

# --- Core Logic ---
def fetch_latest_insta_posts():
    """Fetches the latest post captions from our list of journalists and logs them."""
    all_captions = []
    try:
        for username in INSTA_USERNAMES:
            print(f"Fetching posts for @{username}...")
            user_id = cl.user_id_from_username(username)
            medias = cl.user_medias(user_id, amount=20)
            for media in medias:
                post_id = str(media.pk) # Convert post ID to string
                if media.caption_text and not post_exists(post_id):
                    add_post(post_id, username, media.caption_text, media.taken_at)
                    all_captions.append(f"- @{username}: {media.caption_text}\n")
                elif media.caption_text:
                    print(f"Skipping post {post_id} from @{username} as it already exists in the database.")

        if not all_captions:
            return "No new posts with captions found."

        return "".join(all_captions)
    except Exception as e:
        print(f"🔴 ERROR during Instagram fetch: {e}")
        return f"Error: {e}"

# --- API Route with Caching ---
@app.route('/api/breaking-news', methods=['GET'])
def get_breaking_news():
    inference_url = os.environ.get("KAGGLE_INFERENCE_URL")
    if not inference_url:
        return jsonify({"error": "KAGGLE_INFERENCE_URL not set in .env file."}), 500

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cached_data = json.load(f)
        cached_time = datetime.fromisoformat(cached_data['timestamp'])
        if cached_time > datetime.now(timezone.utc) - timedelta(minutes=CACHE_DURATION_MINUTES):
            print("✅ Serving response from cache.")
            return jsonify(cached_data)

    print("Cache stale or not found. Fetching new data...")

    # 1. Fetch latest Instagram captions
    insta_captions = fetch_latest_insta_posts()
    if "Error:" in insta_captions or "No new posts" in insta_captions:
        return jsonify({"error": "Failed to fetch Instagram posts.", "details": insta_captions}), 500

    # 2. Use Gemini to rank and extract news from captions
    try:
        prompt = BREAKING_NEWS_PROMPT_TEMPLATE.format(insta_captions=insta_captions)
        response = gemini_model.generate_content(prompt)
        
        # Clean up the response from markdown code block
        clean_response = response.text.strip().replace("```json", "").replace("```", "")
        ranked_news = json.loads(clean_response)

    except Exception as e:
        print(f"🔴 ERROR during Gemini analysis: {e}")
        return jsonify({"error": "Failed to analyze news with Gemini.", "details": str(e)}), 500

    if not ranked_news:
        return jsonify({"message": "No significant news found to process."}), 200

    # 3. Loop through each news item and call your Kaggle server for stylization
    for item in ranked_news:
        try:
            # print(f"Calling Kaggle server to stylize: \"{item['headline']}\"")
            payload = {"summary": item['summary']}
            # The POST request to your Kaggle server's Llama model
            response = requests.post(f"{inference_url}/generate-caption", json=payload, timeout=60)
            
            if response.status_code == 200:
                item['versus_caption'] = response.json().get('stylized_caption', 'Error: Invalid response from server.')
            else:
                item['versus_caption'] = f"Error: Server returned status {response.status_code}"

        except requests.exceptions.RequestException as e:
            print(f"🔴 ERROR connecting to Kaggle server: {e}")
            item['versus_caption'] = "Error: Could not connect to inference server."
            
    # 4. Save the complete package (with stylized captions) to the cache
    cache_content = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "posts": ranked_news
    }
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_content, f, indent=4)
    
    print("✅ Full workflow complete. Response cached.")
    return jsonify(cache_content)

# --- Main execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)