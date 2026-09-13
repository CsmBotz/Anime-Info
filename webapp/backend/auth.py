import hashlib
import hmac
import time
import urllib.parse
from typing import Dict, Any, Optional
from bot.config import BOT_TOKEN
from bot.utils.logging import get_logger

logger = get_logger(__name__)

def validate_telegram_init_data(init_data: str) -> Optional[Dict[str, Any]]:
    if not init_data or not BOT_TOKEN:
        return None
    
    try:
        parsed_data = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        if "hash" not in parsed_data:
            return None
        
        hash_check = parsed_data.pop("hash")
        
        # Check auth_date (reject stale > 24h)
        auth_date = int(parsed_data.get("auth_date", 0))
        if time.time() - auth_date > 86400:
            logger.warning("Rejected stale initData auth_date > 24h")
            return None

        # Build data check string
        data_check_arr = [f"{k}={v}" for k, v in sorted(parsed_data.items())]
        data_check_string = "\n".join(data_check_arr)

        # Calculate HMAC signature
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if calculated_hash.lower() == hash_check.lower():
            # Parse user JSON inside initData
            user_json = parsed_data.get("user")
            if user_json:
                import json
                return json.loads(user_json)
        return None
    except Exception as e:
        logger.error(f"Error validating Telegram initData: {e}")
        return None

