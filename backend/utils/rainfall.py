# backend/utils/rainfall.py
# REAL live rainfall data for any location in India
# Uses two APIs:
#   1. OpenWeather — current rain right now (needs API key)
#   2. Open-Meteo — 3-hour forecast (FREE, no key, uses IMD data)

import requests
from backend.config import OPENWEATHER_KEY


def get_current_rainfall(lat: float, lon: float) -> dict:
    """
    Returns current rainfall in mm/hr at any Indian location.
    Works for Chennai, Madurai, Cuddalore, Mumbai, etc.
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_KEY,
        "units": "metric"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        d = r.json()

        # Rain key only present when it is actually raining
        rain_mm = d.get("rain", {}).get("1h", 0.0)
        weather  = d.get("weather", [{}])[0].get("description", "clear")
        humidity = d.get("main", {}).get("humidity", 0)
        wind_ms  = d.get("wind", {}).get("speed", 0.0)

        return {
            "rain_mm_per_hr": rain_mm,
            "weather_desc":   weather,
            "humidity_pct":   humidity,
            "wind_ms":        wind_ms,
            "source":         "OpenWeather"
        }
    except Exception as e:
        print(f"OpenWeather error: {e}")
        return {"rain_mm_per_hr": 0.0, "weather_desc": "error", "source": "error"}


def get_forecast_rainfall_3h(lat: float, lon: float) -> dict:
    """
    Gets rainfall forecast for the NEXT 3 and 6 hours.
    This is your early warning — predict before it floods.
    Uses Open-Meteo — completely FREE, no API key needed.
    Covers all of India including Tamil Nadu coast.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":     lat,
        "longitude":    lon,
        "hourly":       "precipitation,rain",
        "forecast_days": 1,
        "timezone":     "Asia/Kolkata"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        d = r.json()
        hourly = d["hourly"]["precipitation"]

        return {
            "next_1h_mm":  round(hourly[0], 2),
            "next_3h_mm":  round(sum(hourly[:3]), 2),
            "next_6h_mm":  round(sum(hourly[:6]), 2),
            "next_24h_mm": round(sum(hourly[:24]), 2),
            "hourly_24h":  [round(h, 2) for h in hourly[:24]],
            "source":      "Open-Meteo (IMD data)"
        }
    except Exception as e:
        print(f"Open-Meteo forecast error: {e}")
        return {"next_1h_mm": 0.0, "next_3h_mm": 0.0, "next_6h_mm": 0.0}