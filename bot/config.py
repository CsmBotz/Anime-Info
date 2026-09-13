import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

USERS_MONGO_URI = os.getenv("USERS_MONGO_URI")
BOT_MONGO_URI = os.getenv("BOT_MONGO_URI")
CACHE_MONGO_URI = os.getenv("CACHE_MONGO_URI")

WEBAPP_URL = os.getenv("WEBAPP_URL", "")

def validate_config():
    missing = []
    if not API_ID:
        missing.append("API_ID")
    if not API_HASH:
        missing.append("API_HASH")
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not USERS_MONGO_URI:
        missing.append("USERS_MONGO_URI")
    if not BOT_MONGO_URI:
        missing.append("BOT_MONGO_URI")
    if not CACHE_MONGO_URI:
        missing.append("CACHE_MONGO_URI")
    
    if missing:
        print(f"[FATAL] Missing required env vars: {', '.join(missing)}")
        print("Please check your .env file or environment configuration.")
        return False
    return True

