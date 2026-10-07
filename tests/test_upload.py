from pathlib import Path

def test_kml_polygon_upload_success(client, sample_data_dir):
    kml_path = sample_data_dir / "sample_polygon.kml"
    assert kml_path.exists()

    with open(kml_path, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("sample_polygon.kml", f, "application/vnd.google-earth.kml+xml")}
        )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["filename"] == "sample_polygon.kml"
    assert data["file_type"] == "KML"
    assert data["status"] in ("COMPLETED", "PARTIAL_SUCCESS")
    assert data["feature_count"] == 1

    file_id = data["id"]
    # Test GET /api/files/{id}/
    info_resp = client.get(f"/api/files/{file_id}/")
    assert info_resp.status_code == 200
    info_data = info_resp.json()
    assert info_data["id"] == file_id
    assert info_data["feature_count"] == 1
    assert info_data["status"] == data["status"]

def test_zip_shapefile_upload_success(client, sample_data_dir):
    zip_path = sample_data_dir / "sample_shapefile.zip"
    assert zip_path.exists()

    with open(zip_path, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("sample_shapefile.zip", f, "application/zip")}
        )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["filename"] == "sample_shapefile.zip"
    assert data["file_type"] == "ZIP_SHAPEFILE"
    assert data["status"] == "COMPLETED"
    assert data["feature_count"] == 2
