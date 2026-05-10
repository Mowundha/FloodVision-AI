import os
import numpy as np

# Point to your FOLDER instead of a single file
DEM_DIR = "backend/data/tiles"

def get_elevation_from_dem(lat: float, lon: float) -> dict:
    try:
        import rasterio
        from rasterio.transform import rowcol

        # 1. Get a list of all .tif files in your tiles folder
        if not os.path.exists(DEM_DIR):
            return _fallback_elevation(lat, lon)
            
        tif_files = [os.path.join(DEM_DIR, f) for f in os.listdir(DEM_DIR) if f.endswith('.tif')]

        # 2. Check each tile to see if the current lat/lon is inside its boundaries
        for tif_path in tif_files:
            with rasterio.open(tif_path) as src:
                bounds = src.bounds
                if (bounds.left <= lon <= bounds.right) and (bounds.bottom <= lat <= bounds.top):
                    # Found the right tile! Now read the data
                    row, col = rowcol(src.transform, lon, lat)
                    
                    # Read 3x3 window for slope
                    win = rasterio.windows.Window(col-1, row-1, 3, 3)
                    data = src.read(1, window=win).astype(float)
                    
                    raw_elevation = float(data[1, 1])
                    elevation = raw_elevation+85.0

                    # Calculate Slope (Horn's method)
                    cell_m = abs(src.transform[0]) * 111000 
                    dzdx = (data[1,2] - data[1,0]) / (2 * cell_m)
                    dzdy = (data[0,1] - data[2,1]) / (2 * cell_m)
                    slope_rad = np.arctan(np.sqrt(dzdx**2 + dzdy**2))
                    slope_deg = float(np.degrees(slope_rad))

                    # Topographic Wetness Index
                    contrib_area = max(elevation * 10, 1)
                    twi = float(np.log(contrib_area / max(np.tan(slope_rad), 0.001)))

                    return {
                        "elevation_m": round(elevation, 2),
                        "slope_deg":   round(slope_deg, 3),
                        "twi":         round(twi, 3),
                        "source":      f"ISRO CartoDEM ({os.path.basename(tif_path)})"
                    }

        # If no tile matches the coordinates
        return _fallback_elevation(lat, lon)

    except Exception as e:
        print(f"DEM read error: {e}")
        return _fallback_elevation(lat, lon)