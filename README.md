​🌊 Floodvision: Geospatial AI for Flood Risk Analytics
​       Floodvision is a high-performance backend infrastructure designed for real-time flood monitoring and predictive risk assessment in the Tamil Nadu region. The system utilizes a multi-parametric approach, aggregating data from satellite archives and live meteorological sensors to provide actionable insights into urban and rural flooding.

----------------------------------------------------------------------------------------------------------------------------------

​🛠️ Technical Stack
  * Category Technology : Language Python 3.x
  * Geospatial Processing : Google Earth Engine (GEE)
  * APIs : Open-Meteo (Hydrology, Weather, Marine), Open-Elevation
  * Data Analysis : NumPy, Pandas, Rasterio
  * Machine Learning Scikit-learn (Random Forest, XGBoost - Upcoming)
  * Version Control : Git / GitHub
 -------------------------------------------------------------------------------------------------------------------------------- 

Key Features:

​📡 Multi-Source Data Mesh
​Unlike standard weather apps, Floodvision synchronizes four critical environmental parameters via a centralized API hub:
 * ​Hydrology: Live monitoring of river discharge rates (m^3/s).
​ * Meteorology: High-precision precipitation tracking.
​ * Oceanography: Coastal tide and wave height analysis to predict drainage backflow.
​ * Topography: Digital Elevation Model (DEM) integration for terrain-based risk analysis.  

​🛰️ Satellite Archive Integration
​     The project leverages the Google Earth Engine API to perform deep-temporal analysis of the Tamil Nadu landscape, using MODIS and Sentinel datasets to identify historical flood patterns.


​🧮 Topographical Intelligence
​Calculates the Topographic Wetness Index (TWI), a physics-based metric that allows the system to identify geographical bottlenecks where water is most likely to accumulate during heavy discharge.

----------------------------------------------------------------------------------------------------------------------------------

​📂 Project Architecture

floodvision/
├── backend/
│   ├── data/             # Geospatial datasets and .tif files
│   ├── scripts/          # Core Python modules & API logic
│   │   └── test_all_apis.py # Master diagnostic & data aggregator
│   └── analysis/         # Raster processing & TWI calculation logic
├── docs/                 # System architecture and technical specs
└── README.md             # Project documentation

----------------------------------------------------------------------------------------------------------------------------------

🚦 Usage & Deployment

1.​Environment Setup:

  pip install requests earthengine-api rasterio numpy pandas

2.Live Diagnostic Check
​    The backend includes a master diagnostic script. Running this command pings all integrated global APIs (Rain, River, Ocean, and Elevation) to ensure the data mesh is active and returning valid JSON payloads:

      python backend/scripts/test_all_apis.py

3.  Satellite Data Authentication
​     To access the historical satellite archive and processing power of the Google Earth Engine:   

    earthengine authenticate

----------------------------------------------------------------------------------------------------------------------------------

📈 Roadmap & Future Scope
​ * [x] Phase 1: Implementation of Multi-Parametric Data Pipeline.
​ * [x] Phase 2: Cloud-based Satellite Integration via GEE.
​ * [ ] Phase 3: Integration of XGBoost for real-time predictive risk scoring.
​ * [ ] Phase 4: Development of a voice-integrated visual analytics dashboard.

----------------------------------------------------------------------------------------------------------------------------------

​👤 Author
​Praveena A Data Engineering & Backend Developer Specializing in Geospatial Data & Predictive Analytics