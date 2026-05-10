# backend/utils/river.py
# REAL river discharge data for all Tamil Nadu rivers
# Source: Open-Meteo Flood API which uses GloFAS (EU Copernicus)
# GloFAS covers every river in India — completely FREE, no API key

import requests

# Tamil Nadu major rivers with their coordinates and danger thresholds
# Danger threshold = discharge (m³/s) at which flooding begins
TN_RIVERS = {
    "adyar": {
        "lat": 13.0127, "lon": 80.1927,
        "danger_m3s": 400, "warning_m3s": 200,
        "cities": ["Chennai south", "Adyar", "Guindy"]
    },
    "cooum": {
        "lat": 13.0827, "lon": 80.2007,
        "danger_m3s": 300, "warning_m3s": 150,
        "cities": ["Chennai central", "Egmore", "Royapuram"]
    },
    "kosasthalaiyar": {
        "lat": 13.2500, "lon": 80.2800,
        "danger_m3s": 350, "warning_m3s": 175,
        "cities": ["North Chennai", "Ennore", "Manali"]
    },
    "cauvery_trichy": {
        "lat": 10.7905, "lon": 78.7047,
        "danger_m3s": 8000, "warning_m3s": 4000,
        "cities": ["Trichy", "Thanjavur", "Kumbakonam"]
    },
    "vaigai": {
        "lat": 9.9252, "lon": 78.1198,
        "danger_m3s": 3000, "warning_m3s": 1500,
        "cities": ["Madurai", "Dindigul"]
    },
    "tamiraparani": {
        "lat": 8.7139, "lon": 77.7567,
        "danger_m3s": 2500, "warning_m3s": 1200,
        "cities": ["Tirunelveli", "Tuticorin"]
    },
    "palar": {
        "lat": 12.9165, "lon": 79.1325,
        "danger_m3s": 1500, "warning_m3s": 750,
        "cities": ["Vellore", "Kanchipuram"]
    },
    "pennaiyar": {
        "lat": 11.7480, "lon": 79.7714,
        "danger_m3s": 1200, "warning_m3s": 600,
        "cities": ["Cuddalore", "Villupuram"]
    },
}


def get_river_discharge(lat: float, lon: float,
                         river_name: str = None) -> dict:
    """
    Gets live river discharge for the nearest river to lat/lon.
    Returns discharge in m³/s and danger status.
    
    If river_name is given, uses that river's thresholds.
    Otherwise uses default thresholds.
    """
    url = "https://flood-api.open-meteo.com/v1/flood"
    params = {
        "latitude":     lat,
        "longitude":    lon,
        "daily":        "river_discharge",
        "forecast_days": 7
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        d = r.json()
        discharge_list = d["daily"]["river_discharge"]
        # Replace None values with 0
        discharge_list = [v or 0.0 for v in discharge_list]

        current  = discharge_list[0]
        max_7day = max(discharge_list)

        # Get thresholds for this river
        info = TN_RIVERS.get(river_name, {})
        danger  = info.get("danger_m3s",  500)
        warning = info.get("warning_m3s", 200)

        status = (
            "DANGER"  if current >= danger  else
            "WARNING" if current >= warning else
            "NORMAL"
        )

        # Convert to 0-10 scale for flood formula
        level_0_10 = min(10.0, (current / danger) * 10)

        return {
            "discharge_m3s":  round(current, 1),
            "max_7day_m3s":   round(max_7day, 1),
            "danger_at_m3s":  danger,
            "status":         status,
            "level_0_10":     round(level_0_10, 2),
            "7day_forecast":  [round(v, 1) for v in discharge_list],
            "source":         "Open-Meteo GloFAS"
        }
    except Exception as e:
        print(f"River API error: {e}")
        return {"discharge_m3s": 0.0, "level_0_10": 2.0, "status": "NORMAL"}


def find_nearest_river(lat: float, lon: float) -> str:
    """Returns the name of the nearest river to this location."""
    nearest = None
    min_dist = float("inf")
    for name, data in TN_RIVERS.items():
        dist = ((lat - data["lat"])**2 + (lon - data["lon"])**2)**0.5
        if dist < min_dist:
            min_dist = dist
            nearest = name
    return nearest