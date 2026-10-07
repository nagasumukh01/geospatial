# Geospatial File Measurement API 🌍📏

A production-ready RESTful backend API built with **Python**, **FastAPI**, **GeoPandas**, **Shapely**, **PyProj**, and **SQLAlchemy**. This service accepts geospatial files (`.kml` and `.zip` containing Shapefiles), extracts features, performs automated Coordinate Reference System (CRS) transformations to metric projected systems, computes accurate geometry measurements (area and length), and exposes structured metadata through REST endpoints.

---

## 1. Project Overview

Calculating geometry measurements directly on geographic coordinates (such as WGS84 / EPSG:4326 in latitude and longitude degrees) produces incorrect results because degrees do not represent uniform distance grid units across the Earth's curved surface.

This project solves this real-world problem by providing an automated, scalable backend service that:
1. Validates and safely extracts uploaded `.kml` or `.zip` Shapefile archives.
2. Inspects source dataset features and detects the active CRS.
3. Automatically computes the geographical centroid for unprojected datasets and transforms geometries to an appropriate **Universal Transverse Mercator (UTM)** projected CRS (measured in meters).
4. Accurately calculates **Polygon area** (in $m^2$) and **LineString length** (in $m$).
5. Gracefully handles invalid or unsupported geometries without interrupting the processing of valid features.
6. Exposes metadata and measurement results via RESTful endpoints.

---

## 2. Features

- **Multi-Format Geospatial Ingestion**: Supports `.kml` XML files and `.zip` archives containing Shapefile components (`.shp`, `.shx`, `.dbf`, `.prj`).
- **Automated CRS Transformation Engine**: Dynamically determines the target UTM zone based on dataset centroid coordinates and transforms geometries using PyProj.
- **Robust Geometry Measurement**:
  - **Polygon / MultiPolygon**: Calculates accurate surface area in square meters ($m^2$).
  - **LineString / MultiLineString**: Calculates accurate linear length in meters ($m$).
  - **Point / MultiPoint**: Categorized gracefully without unnecessary computation.
  - **Geometry Collection**: Recursively processes and aggregates composite geometries.
- **Fault-Tolerant Bulk Processing**: Invalid geometries are repaired with `make_valid()` or recorded as partial failures without terminating the entire file job (`PARTIAL_SUCCESS` status).
- **Security First**: Prevents Zip Slip / path-traversal attacks, validates file headers, limits upload size (50MB default), and sanitizes filenames.
- **Database & Architecture**: Clean separation of concerns with SQLAlchemy ORM (SQLite for local dev, PostGIS/PostgreSQL compatible).
- **Automated Open API Documentation**: Native Swagger UI (`/docs`) and ReDoc (`/redoc`) integrations.

---

## 3. Mandatory Technology Stack

| Technology | Purpose |
| :--- | :--- |
| **Python 3.11+** | Primary programming language |
| **FastAPI** | High-performance asynchronous web framework |
| **Uvicorn** | ASGI web server |
| **Pydantic v2** | Data validation & settings management |
| **GeoPandas / Fiona** | Geospatial dataset reading & manipulation |
| **Shapely** | Planar geometry operations & validation |
| **PyProj** | Cartographic projection & coordinate transformation |
| **SQLAlchemy** | Database ORM & session management |
| **SQLite / PostgreSQL** | Relational data store |
| **pytest & httpx** | Automated test suite and API testing |

---

## 4. Architecture & Data Flow

```text
Client (cURL / Frontend / HTTP)
       │
       ▼
   FastAPI Route Layer (/api/files/)
       │
       ▼
 ┌─────────────────────────────────────────┐
 │ File Validation & Security              │
 │ - Extension & MIME type check           │
 │ - Zip Slip / Path Traversal Guard       │
 └────────────────────┬────────────────────┘
                      │
                      ▼
 ┌─────────────────────────────────────────┐
 │ GeoSpatial Service                      │
 │ - Shapefile component extraction        │
 │ - GeoPandas / Fiona KML & SHP parsing   │
 └────────────────────┬────────────────────┘
                      │
                      ▼
 ┌─────────────────────────────────────────┐
 │ CRS & Projection Engine                 │
 │ - Detect source CRS (e.g. EPSG:4326)    │
 │ - Calculate Centroid (Lon, Lat)         │
 │ - Select UTM Zone EPSG (326XX / 327XX)  │
 └────────────────────┬────────────────────┘
                      │
                      ▼
 ┌─────────────────────────────────────────┐
 │ Measurement Engine                      │
 │ - Repair geometry (make_valid)          │
 │ - Transform coordinates to metric CRS   │
 │ - Polygon Area (m²) | Line Length (m)   │
 └────────────────────┬────────────────────┘
                      │
                      ▼
 ┌─────────────────────────────────────────┐
 │ Relational Database (SQLAlchemy)        │
 │ - FileRecord (Status, Metadata, CRS)    │
 │ - FeatureMeasurement (Values, Units)    │
 └────────────────────┬────────────────────┘
                      │
                      ▼
            Structured JSON Response
```

---

## 5. CRS Selection Strategy

### Why Geographic Coordinates Cannot Be Used Directly
Geographic Coordinate Reference Systems (like **WGS 84 / EPSG:4326**) measure location in angular degrees (latitude and longitude). 
Because the Earth is an oblate spheroid, 1 degree of longitude shrinks from ~111 km at the Equator down to 0 km at the Poles. 
Calculating area (`degrees²`) or length (`degrees`) directly on geographic coordinates yields meaningless numbers that vary wildly depending on latitude.

### Automated Projected CRS Selection Workflow
1. **Source CRS Detection**: The API inspects the metadata of the uploaded file.
2. **Projected CRS Verification**:
   - If the dataset is **already in a projected CRS** (e.g., State Plane, UTM, EPSG:3857), the original projected coordinates are used directly for linear measurements.
3. **Geographic CRS Transformation**:
   - If the dataset is **geographic** (e.g., EPSG:4326):
     - The centroid $(\text{longitude}, \text{latitude})$ of the feature/dataset is calculated.
     - The optimal **Universal Transverse Mercator (UTM)** zone is determined using:
       $$\text{UTM Zone} = \lfloor (\text{longitude} + 180) / 6 \rfloor + 1$$
     - If $\text{latitude} \ge 0$ (Northern Hemisphere): Target EPSG = $32600 + \text{UTM Zone}$
     - If $\text{latitude} < 0$ (Southern Hemisphere): Target EPSG = $32700 + \text{UTM Zone}$
4. **Coordinate Transformation**: `PyProj` transforms the geometry coordinates from WGS84 degrees to UTM meters.
5. **Metric Calculation**: Area is calculated in square meters ($m^2$) and length in meters ($m$).

---

## 6. API Endpoints & Usage Examples

### A. Upload & Process File
- **Endpoint**: `POST /api/files/`
- **Content-Type**: `multipart/form-data`
- **Supported Extensions**: `.kml`, `.zip`

**Example cURL Request (KML File)**:
```bash
curl -X 'POST' \
  'http://localhost:8000/api/files/' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@sample_data/sample_polygon.kml'
```

**Example Response**:
```json
{
  "id": "e4a9f3b1-7c2d-4b8a-9e1f-3d5c7b9a2e4f",
  "filename": "sample_polygon.kml",
  "file_type": "KML",
  "feature_count": 1,
  "crs": "EPSG:4326",
  "status": "COMPLETED",
  "upload_timestamp": "2026-10-07T12:30:00.000Z",
  "processing_start_time": "2026-10-07T12:30:00.100Z",
  "processing_completion_time": "2026-10-07T12:30:00.250Z",
  "processing_duration": 0.15,
  "error_message": null
}
```

---

### B. Get File Metadata & Processing Status
- **Endpoint**: `GET /api/files/{id}/`

**Example cURL Request**:
```bash
curl -X 'GET' 'http://localhost:8000/api/files/e4a9f3b1-7c2d-4b8a-9e1f-3d5c7b9a2e4f/'
```

**Example Response**:
```json
{
  "id": "e4a9f3b1-7c2d-4b8a-9e1f-3d5c7b9a2e4f",
  "filename": "sample_polygon.kml",
  "file_type": "KML",
  "feature_count": 1,
  "crs": "EPSG:4326",
  "status": "COMPLETED",
  "upload_timestamp": "2026-10-07T12:30:00.000Z",
  "processing_start_time": "2026-10-07T12:30:00.100Z",
  "processing_completion_time": "2026-10-07T12:30:00.250Z",
  "processing_duration": 0.15,
  "error_message": null
}
```

---

### C. Get Calculated Feature Measurements
- **Endpoint**: `GET /api/files/{id}/measurements/`

**Example cURL Request**:
```bash
curl -X 'GET' 'http://localhost:8000/api/files/e4a9f3b1-7c2d-4b8a-9e1f-3d5c7b9a2e4f/measurements/'
```

**Example Response**:
```json
{
  "file_id": "e4a9f3b1-7c2d-4b8a-9e1f-3d5c7b9a2e4f",
  "status": "COMPLETED",
  "measurements": [
    {
      "feature_id": 0,
      "geometry_type": "Polygon",
      "measurement_type": "area",
      "value": 223541.67,
      "unit": "square_meters",
      "status": "SUCCESS",
      "error": null,
      "properties": {
        "name": "Central Park Reservoir Area",
        "description": "Sample polygon feature in NYC"
      }
    }
  ]
}
```

---

## 7. Installation & Setup

### Prerequisites
- Python 3.11 or higher
- Git

### 1. Clone Repository
```bash
git clone https://github.com/nagasumukh01/geospatial.git
cd geospatial
```

### 2. Create and Activate Virtual Environment
**Windows (PowerShell)**:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 8. Running the Application

Start the local development server with Uvicorn:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access the interactive API documentation in your web browser:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 9. Automated Testing

The project includes unit, integration, validation, and boundary tests using `pytest` and FastAPI's `TestClient`.

Run the full test suite:

```bash
pytest -v
```

**Test Coverage Summary**:
- `test_upload.py`: KML & Shapefile `.zip` file ingestion and feature extraction.
- `test_measurements.py`: Polygon area, LineString length, Point handling, and invalid geometry recovery.
- `test_crs.py`: UTM EPSG calculation, geographic-to-projected transformations.
- `test_validation.py`: Extension validation, empty file rejection, file size limits.
- `test_error_handling.py`: Corrupted ZIP files, missing Shapefile components, 404 responses.

---

## 10. Docker Support

To run the application inside a container:

### Build Docker Image
```bash
docker build -t geospatial-measurement-api .
```

### Run Docker Container
```bash
docker run -d -p 8000:8000 --name geospatial-api geospatial-measurement-api
```

Test health check:
```bash
curl http://localhost:8000/health
```

---

## 11. Design Decisions

1. **Modular Service Layer**: Separated HTTP handling (`routes`), file orchestration (`FileService`), geospatial reading (`GeoSpatialService`), projection logic (`CRSService`), and geometry measurement (`MeasurementService`).
2. **KML Fallback Parsing**: Integrated a native XML fallback parser alongside GeoPandas to ensure KML files process successfully even on systems lacking full GDAL/LIBKML bindings.
3. **Fault Tolerance per Feature**: Processing failures on individual corrupt features log an error while allowing valid features in the same file to complete (`PARTIAL_SUCCESS`).
4. **Security Hardening**: Prevented path traversal (Zip Slip) attacks by checking target extraction paths against canonical root paths.
5. **DB Abstraction**: Used SQLAlchemy 2.0 declarative models to enable instant compatibility with SQLite for local development and PostgreSQL/PostGIS for production.

---

## 12. Future Improvements

- **Asynchronous Task Queue**: Integrate Celery or ARQ with Redis for processing multi-gigabyte shapefiles asynchronously.
- **Cloud Object Storage**: Store uploaded raw files in AWS S3 or Google Cloud Storage instead of local filesystem storage.
- **PostGIS Spatial Queries**: Enable spatial index searching (e.g. bounding box queries, spatial intersections).
- **Authentication & Rate Limiting**: Add OAuth2 / JWT authentication and API key rate limiting.
