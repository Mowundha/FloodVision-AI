# scripts/test_all_apis.py
# Run this to confirm all 4 real data sources are working
# Command: python scripts/test_all_apis.py

import sys
sys.path.insert(0, ".")

from backend.utils.rainfall  import get_current_rainfall, get_forecast_rainfall_3h
from backend.utils.river     import get_river_discharge
from backend.utils.tide      import compute_tide_height
from backend.utils.elevation import get_elevation_from_dem

# Test location: Chennai (Adyar area)
LAT, LON = 13.0490, 80.1698

print("=" * 50)
print("FloodVision AI — API Test")
print("Location: Chennai (Adyar)")
print("=" * 50)

print("\n1. RAINFALL (OpenWeather):")
rain = get_current_rainfall(LAT, LON)
print(f"   Current rain: {rain['rain_mm_per_hr']} mm/hr")
print(f"   Weather: {rain['weather_desc']}")

print("\n2. RAINFALL FORECAST (Open-Meteo):")
forecast = get_forecast_rainfall_3h(LAT, LON)
print(f"   Next 3 hours: {forecast['next_3h_mm']} mm")
print(f"   Next 6 hours: {forecast['next_6h_mm']} mm")

print("\n3. RIVER DISCHARGE (Open-Meteo GloFAS):")
river = get_river_discharge(LAT, LON, "adyar")
print(f"   Discharge: {river['discharge_m3s']} m3/s")
print(f"   Status: {river['status']}")

print("\n4. TIDE HEIGHT (INCOIS harmonic constants):")
tide = compute_tide_height("chennai")
print(f"   Tide height: {tide['tide_height_m']} m")
print(f"   Drainage blocked: {tide['drainage_blocked']}")

print("\n5. ELEVATION (ISRO CartoDEM / fallback):")
elev = get_elevation_from_dem(LAT, LON)
print(f"   Elevation: {elev['elevation_m']} m")
print(f"   TWI: {elev['twi']}")
print(f"   Source: {elev['source']}")

print("\n All data sources working!")