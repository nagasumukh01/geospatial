def test_corrupted_zip_upload(client, sample_data_dir):
    zip_path = sample_data_dir / "corrupted.zip"
    with open(zip_path, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("corrupted.zip", f, "application/zip")}
        )

    assert response.status_code == 400
    data = response.json()
    assert "Corrupted or invalid ZIP file" in data["detail"]

def test_missing_shapefile_components_zip(client, sample_data_dir):
    zip_path = sample_data_dir / "missing_components.zip"
    with open(zip_path, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("missing_components.zip", f, "application/zip")}
        )

    assert response.status_code == 400
    data = response.json()
    assert "Missing required Shapefile components" in data["detail"]

def test_get_nonexistent_file_id_info(client):
    response = client.get("/api/files/nonexistent-uuid-12345/")
    assert response.status_code == 404
    data = response.json()
    assert "File record with ID" in data["detail"]

def test_get_nonexistent_file_id_measurements(client):
    response = client.get("/api/files/nonexistent-uuid-12345/measurements/")
    assert response.status_code == 404
    data = response.json()
    assert "File record with ID" in data["detail"]
