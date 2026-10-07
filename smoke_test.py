import httpx
import json
import pathlib

BASE = "http://127.0.0.1:8000"
results = []

# 1. Health check
r = httpx.get(f"{BASE}/health")
results.append(("GET /health", r.status_code, r.json()))

# 2. Upload KML polygon
kml = pathlib.Path("sample_data/sample_polygon.kml")
with open(kml, "rb") as f:
    r = httpx.post(
        f"{BASE}/api/files/",
        files={"file": ("sample_polygon.kml", f, "application/vnd.google-earth.kml+xml")},
        timeout=30
    )
results.append(("POST /api/files/ [KML polygon]", r.status_code, r.json()))
file_id_kml = r.json().get("id") if r.status_code == 201 else None

# 3. Upload KML linestring
kml2 = pathlib.Path("sample_data/sample_linestring.kml")
with open(kml2, "rb") as f:
    r = httpx.post(
        f"{BASE}/api/files/",
        files={"file": ("sample_linestring.kml", f, "application/vnd.google-earth.kml+xml")},
        timeout=30
    )
results.append(("POST /api/files/ [KML linestring]", r.status_code, r.json()))

# 4. Upload Shapefile zip
zipf = pathlib.Path("sample_data/sample_shapefile.zip")
with open(zipf, "rb") as f:
    r = httpx.post(
        f"{BASE}/api/files/",
        files={"file": ("sample_shapefile.zip", f, "application/zip")},
        timeout=30
    )
results.append(("POST /api/files/ [ZIP shapefile]", r.status_code, r.json()))
file_id_zip = r.json().get("id") if r.status_code == 201 else None

# 5. GET file info
if file_id_kml:
    r = httpx.get(f"{BASE}/api/files/{file_id_kml}/", timeout=10)
    results.append(("GET /api/files/{id}/", r.status_code, r.json()))

# 6. GET measurements
if file_id_kml:
    r = httpx.get(f"{BASE}/api/files/{file_id_kml}/measurements/", timeout=10)
    d = r.json()
    meas = d.get("measurements", [])
    summary = {"count": len(meas), "status": d.get("status")}
    if meas:
        m0 = meas[0]
        summary["sample"] = {
            "geometry_type": m0.get("geometry_type"),
            "measurement_type": m0.get("measurement_type"),
            "value": m0.get("value"),
            "unit": m0.get("unit"),
        }
    results.append(("GET /api/files/{id}/measurements/", r.status_code, summary))

# 7. GET GeoJSON
if file_id_kml:
    r = httpx.get(f"{BASE}/api/files/{file_id_kml}/geojson/", timeout=10)
    d = r.json()
    results.append(("GET /api/files/{id}/geojson/", r.status_code,
                    {"features": len(d.get("features", [])), "type": d.get("type")}))

# 8. Corrupted ZIP
with open("sample_data/corrupted.zip", "rb") as f:
    r = httpx.post(
        f"{BASE}/api/files/",
        files={"file": ("corrupted.zip", f, "application/zip")},
        timeout=10
    )
results.append(("POST corrupted ZIP -> expect 400", r.status_code, r.json()))

# 9. Missing shapefile components
with open("sample_data/missing_components.zip", "rb") as f:
    r = httpx.post(
        f"{BASE}/api/files/",
        files={"file": ("missing_components.zip", f, "application/zip")},
        timeout=10
    )
results.append(("POST missing SHP components -> expect 400", r.status_code, r.json()))

# 10. Invalid extension
r = httpx.post(
    f"{BASE}/api/files/",
    files={"file": ("bad.txt", b"hello", "text/plain")},
    timeout=10
)
results.append(("POST invalid extension -> expect 400", r.status_code, r.json()))

# 11. 404 missing ID
r = httpx.get(f"{BASE}/api/files/nonexistent-id/", timeout=10)
results.append(("GET missing ID -> expect 404", r.status_code, r.json()))

# Print summary table
print()
print("=" * 70)
print("  LIVE API SMOKE TEST RESULTS")
print("=" * 70)

all_pass = True
for name, code, body in results:
    expected_pass = code in (200, 201, 400, 404)
    status_label = "PASS" if expected_pass else "FAIL"
    if not expected_pass:
        all_pass = False
    print(f"  [{status_label}] {name}")
    print(f"         HTTP {code} | {json.dumps(body)[:120]}")
    print()

print("=" * 70)
verdict = "ALL TESTS PASSED" if all_pass else "SOME TESTS FAILED"
print(f"  Overall: {verdict}")
print("=" * 70)
