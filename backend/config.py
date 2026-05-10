# backend/config.py
# Loads all API keys from your .env file
# Every other file imports from here — never hardcode keys anywhere else

import os
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY", "")
FIREBASE_CRED   = os.getenv("FIREBASE_CRED", "backend/firebase-service-account.json")