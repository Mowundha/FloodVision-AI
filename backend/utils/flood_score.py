# backend/utils/flood_score.py

def get_simulated_river_level() -> float:
    """
    Simulates river level for prototype.
    In production: replace with Open-Meteo Flood API.
    
    Returns value between 0 and 10.
    0 = river is low/normal
    10 = river is at maximum dangerous level
    """
    # For demo: simulate moderate river level
    # You can change this to test different scenarios
    return 4.5


def get_simulated_tide_level() -> float:
    """
    Simulates ocean tide level for prototype.
    In production: replace with INCOIS data.
    
    Returns value between 0 and 10.
    0 = low tide
    10 = very high tide (blocks drainage)
    """
    # For demo: moderate tide level
    return 3.0


def calculate_flood_score(rain_mm: float,
                           elevation_m: float,
                           river_level: float = None,
                           tide_level: float = None) -> dict:
    """
    Your core flood formula:
    score = (0.6 * rain) + (0.25 * river) + (0.15 * tide) + (10 - elevation)
    
    rain_mm      → mm per hour from OpenWeather (real data)
    elevation_m  → metres above sea level (from street_data.py)
    river_level  → 0 to 10 scale (simulated for prototype)
    tide_level   → 0 to 10 scale (simulated for prototype)
    
    Score range:
    0–5   → LOW risk
    5–10  → MEDIUM risk
    10+   → HIGH risk
    """
    if river_level is None:
        river_level = get_simulated_river_level()
    if tide_level is None:
        tide_level = get_simulated_tide_level()

    # Normalize rain: cap at 50mm/hr for scoring
    # 50mm/hr is extremely heavy rain — anything above that is still 10
    rain_normalized = min(rain_mm, 50) / 5.0  # scale to 0–10

    # Elevation factor: lower elevation = higher flood risk
    # Street at 1m elevation gets factor 9. Street at 9m gets factor 1.
    elevation_factor = max(0, 10 - elevation_m)

    # Your formula
    score = (
        (0.6 * rain_normalized) +
        (0.25 * river_level) +
        (0.15 * tide_level) +
        elevation_factor
    )

    # Classify risk
    if score >= 10:
        risk = "HIGH"
        color = "RED"
        warning = (
            "⚠️ HIGH FLOOD RISK — Move your vehicle immediately! "
            "Water logging expected within 2 hours on this street."
        )
    elif score >= 5:
        risk = "MEDIUM"
        color = "YELLOW"
        warning = (
            "⚡ MEDIUM FLOOD RISK — Monitor the situation. "
            "Consider moving vehicle to higher ground as a precaution."
        )
    else:
        risk = "LOW"
        color = "GREEN"
        warning = (
            "✅ LOW FLOOD RISK — No immediate danger. "
            "Stay alert if rainfall increases."
        )

    return {
        "score": round(score, 2),
        "risk": risk,
        "color": color,
        "warning": warning,
        "breakdown": {
            "rain_contribution":      round(0.6 * rain_normalized, 2),
            "river_contribution":     round(0.25 * river_level, 2),
            "tide_contribution":      round(0.15 * tide_level, 2),
            "elevation_contribution": round(elevation_factor, 2)
        },
        "inputs": {
            "rain_mm_per_hr": rain_mm,
            "river_level":    river_level,
            "tide_level":     tide_level,
            "elevation_m":    elevation_m
        }
    }