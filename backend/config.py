# backend/config.py — updated to handle Render deployment
# The firebase JSON can be stored as a file OR as an environment variable string

import os
import json
import tempfile
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY", "")
if not OPENWEATHER_KEY:
    print("WARNING: OPENWEATHER_API_KEY not set")

# ── Firebase initialization ───────────────────────────────────
# Supports two modes:
#   1. Local development: reads firebase-service-account.json file
#   2. Render deployment: reads FIREBASE_CRED_JSON env variable (JSON string)

def _get_firebase_credentials():
    """
    Gets Firebase credentials whether running locally or on Render.

    Locally: uses the JSON file path in FIREBASE_CRED
    On Render: uses the JSON content in FIREBASE_CRED_JSON env variable
    """
    # Mode 1: JSON content stored as environment variable (Render)
    cred_json_str = os.getenv("FIREBASE_CRED_JSON", "")
    if cred_json_str:
        try:
            cred_dict = json.loads(cred_json_str)
            return credentials.Certificate(cred_dict)
        except json.JSONDecodeError as e:
            print(f"ERROR: FIREBASE_CRED_JSON is not valid JSON: {e}")

    # Mode 2: JSON file path (local development)
    cred_path = os.getenv("FIREBASE_CRED", "firebase-service-account.json")
    if os.path.exists(cred_path):
        return credentials.Certificate(cred_path)

    print("ERROR: No Firebase credentials found.")
    print("  Local: set FIREBASE_CRED=path/to/firebase-service-account.json")
    print("  Render: set FIREBASE_CRED_JSON=<entire JSON content>")
    return None


try:
    if not firebase_admin._apps:
        cred = _get_firebase_credentials()
        if cred:
            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully")
except Exception as e:
    print(f"Firebase initialization failed: {e}")

try:
    db = firestore.client()
    print("Firestore connected")
except Exception as e:
    db = None
    print(f"Firestore connection failed: {e}")