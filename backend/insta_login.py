import os
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired

# --- This script handles the initial interactive login ---
load_dotenv()

INSTA_USERNAME = os.environ["INSTA_USERNAME"]
INSTA_PASSWORD = os.environ["INSTA_PASSWORD"]
SESSION_FILE = "session.json"

cl = Client()

try:
    print(f"Attempting to log in as @{INSTA_USERNAME}...")
    cl.login(INSTA_USERNAME, INSTA_PASSWORD)

except TwoFactorRequired:
    print("🔴 Two-Factor Authentication is required.")
    # Instagram sends the code to your phone or email
    verification_code = input("Please enter the 6-digit code you received: ")

    print("Attempting login with 2FA code...")
    cl.login(INSTA_USERNAME, INSTA_PASSWORD, verification_code=verification_code)
    print("✅ 2FA Login Successful!")

except Exception as e:
    print(f"🔴 An unexpected error occurred: {e}")
    exit()

# Save the authenticated session to the file
cl.dump_settings(SESSION_FILE)
print(f"🎉 SUCCESS! Session saved to {SESSION_FILE}.")
print("You can now run the main app.py file.")