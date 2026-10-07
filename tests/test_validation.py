def test_invalid_file_extension(client, sample_data_dir):
    txt_path = sample_data_dir / "invalid_file.txt"
    assert txt_path.exists()

    with open(txt_path, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("invalid_file.txt", f, "text/plain")}
        )

    assert response.status_code == 400
    data = response.json()
    assert "Unsupported file type" in data["detail"]

def test_empty_file_upload(client, tmp_path):
    empty_file = tmp_path / "empty.kml"
    empty_file.write_bytes(b"")

    with open(empty_file, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("empty.kml", f, "application/vnd.google-earth.kml+xml")}
        )

    assert response.status_code == 400
    data = response.json()
    assert "Uploaded file is empty" in data["detail"]
