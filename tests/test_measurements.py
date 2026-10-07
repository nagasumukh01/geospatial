from shapely.geometry import Polygon, LineString, Point, GeometryCollection
from pyproj import CRS
from app.services.measurement_service import MeasurementService

def test_polygon_area_measurement(client, sample_data_dir):
    kml_path = sample_data_dir / "sample_polygon.kml"
    with open(kml_path, "rb") as f:
        upload_resp = client.post(
            "/api/files/",
            files={"file": ("sample_polygon.kml", f, "application/vnd.google-earth.kml+xml")}
        )

    file_id = upload_resp.json()["id"]

    meas_resp = client.get(f"/api/files/{file_id}/measurements/")
    assert meas_resp.status_code == 200
    data = meas_resp.json()
    assert data["file_id"] == file_id
    assert len(data["measurements"]) == 1

    m = data["measurements"][0]
    assert m["feature_id"] == 0
    assert m["geometry_type"] == "Polygon"
    assert m["measurement_type"] == "area"
    assert m["unit"] == "square_meters"
    assert m["value"] > 0.0

def test_linestring_length_measurement(client, sample_data_dir):
    kml_path = sample_data_dir / "sample_linestring.kml"
    with open(kml_path, "rb") as f:
        upload_resp = client.post(
            "/api/files/",
            files={"file": ("sample_linestring.kml", f, "application/vnd.google-earth.kml+xml")}
        )

    file_id = upload_resp.json()["id"]

    meas_resp = client.get(f"/api/files/{file_id}/measurements/")
    assert meas_resp.status_code == 200
    data = meas_resp.json()
    assert len(data["measurements"]) == 1

    m = data["measurements"][0]
    assert m["geometry_type"] == "LineString"
    assert m["measurement_type"] == "length"
    assert m["unit"] == "meters"
    assert m["value"] > 0.0

def test_point_geometry_measurement():
    pt = Point(-73.962, 40.784)
    m_type, val, unit, status, err = MeasurementService.measure_geometry(pt, CRS.from_epsg(4326))
    assert m_type == "none"
    assert val is None
    assert unit is None
    assert status == "SUCCESS"

def test_invalid_geometry_handling():
    # Bowtie polygon (self-intersecting)
    invalid_poly = Polygon([(0, 0), (0, 2), (2, 0), (2, 2), (0, 0)])
    m_type, val, unit, status, err = MeasurementService.measure_geometry(invalid_poly, CRS.from_epsg(4326))
    # Should automatically repair or handle cleanly
    assert status in ("SUCCESS", "FAILED")
