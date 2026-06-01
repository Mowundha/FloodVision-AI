# backend/utils/security.py
#
# WHAT THIS DOES:
#   1. Rate limiting  — limits how many times one person can call your API
#   2. Security headers — standard HTTP headers that protect users
#   3. Input sanitizer — removes dangerous characters from text inputs
#
# WHY RATE LIMITING MATTERS (beginner explanation):
#   Without it, one person (or a bot) can call your API 1000 times per second.
#   This crashes your server and costs you money.
#   With rate limiting: "You can only call /predict 30 times per minute."
#   If they exceed it, they get a 429 error: "Too Many Requests"
#
# WHY SECURITY HEADERS MATTER:
#   These are standard HTTP headers that tell browsers how to behave safely.
#   Example: X-Content-Type-Options tells browser not to guess file types.
#   They don't affect your Flutter app at all — only make it safer.

import re
from slowapi import Limiter
from slowapi.util import get_remote_address

# ── Rate Limiter setup ────────────────────────────────────────
# get_remote_address = identify users by their IP address
# Each IP gets its own counter
limiter = Limiter(key_func=get_remote_address)

# ── Rate limit rules ──────────────────────────────────────────
# These strings are used as decorators on your endpoints
# "30/minute" = max 30 calls per minute per IP address
RATE_PREDICT  = "30/minute"    # flood prediction — moderate limit
RATE_STREETS  = "10/minute"    # streets map — less frequent
RATE_REPORT   = "10/minute"    # submit report — prevent spam
RATE_NOTIFY   = "20/minute"    # notifications
RATE_DEFAULT  = "60/minute"    # general endpoints


def get_security_headers() -> dict:
    """
    Returns standard HTTP security headers.
    Add these to every response.

    What each header does:
    X-Content-Type-Options  → browser won't guess file types (prevents sniffing)
    X-Frame-Options         → page can't be embedded in iframes (prevents clickjacking)
    X-XSS-Protection        → browser blocks obvious XSS attacks
    Referrer-Policy         → controls what URL info is shared with other sites
    Cache-Control           → API responses not cached (fresh data always)
    """
    return {
        "X-Content-Type-Options":  "nosniff",
        "X-Frame-Options":         "DENY",
        "X-XSS-Protection":        "1; mode=block",
        "Referrer-Policy":         "strict-origin-when-cross-origin",
        "Cache-Control":           "no-store, no-cache, must-revalidate",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
    }


def sanitize_text(text: str, max_length: int = 500) -> str:
    """
    Cleans user-submitted text before saving to database.

    What it removes:
    - HTML tags like <script> (prevents XSS attacks)
    - Null bytes (crashes some databases)
    - Strips leading/trailing whitespace

    Example:
      Input:  "  Water is deep <script>alert('hack')</script>  "
      Output: "Water is deep alert('hack')"

    Parameters:
      text       = the text to clean
      max_length = maximum allowed length (truncates if longer)
    """
    if not text:
        return ""

    # Remove HTML tags
    cleaned = re.sub(r"<[^>]+>", "", text)

    # Remove null bytes
    cleaned = cleaned.replace("\x00", "")

    # Remove other control characters except newlines
    cleaned = re.sub(r"[\x01-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", cleaned)

    # Strip whitespace and truncate
    cleaned = cleaned.strip()[:max_length]

    return cleaned


def sanitize_street_name(name: str) -> str:
    """
    Cleans street/city names.
    Allows only letters, numbers, spaces, commas, dots, hyphens.
    Rejects anything else.
    """
    if not name:
        return ""
    # Allow Tamil characters (Unicode range), English, numbers, basic punctuation
    cleaned = re.sub(r"[^\w\s,.\-\u0B80-\u0BFF]", "", name)
    return cleaned.strip()[:200]