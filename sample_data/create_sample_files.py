import os
import zipfile
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon, LineString, Point

SAMPLE_DIR = Path("./sample_data")
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

def create_sample_kml_polygon():
    kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Sample Polygon Document</name>
    <Placemark>
      <name>Central Park Reservoir Area</name>
      <description>Sample polygon feature in NYC</description>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              -73.9654,40.7829,0
              -73.9594,40.7829,0
              -73.9594,40.7869,0
              -73.9654,40.7869,0
              -73.9654,40.7829,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>"""
    file_path = SAMPLE_DIR / "sample_polygon.kml"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(kml_content)
    print(f"Created {file_path}")

def create_sample_kml_linestring():
    kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Sample LineString Document</name>
    <Placemark>
      <name>5th Avenue Walk</name>
      <description>Sample linestring feature</description>
      <LineString>
        <coordinates>
          -73.9654,40.7829,0
          -73.9634,40.7849,0
          -73.9614,40.7869,0
        </coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>"""
    file_path = SAMPLE_DIR / "sample_linestring.kml"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(kml_content)
    print(f"Created {file_path}")

def create_sample_shapefile_zip():
    # Shapefiles require uniform geometry types per file
    gdf_poly = gpd.GeoDataFrame(
        [
            {"name": "Polygon 1", "geometry": Polygon([(-73.965, 40.782), (-73.959, 40.782), (-73.959, 40.786), (-73.965, 40.786)])},
            {"name": "Polygon 2", "geometry": Polygon([(-73.975, 40.772), (-73.969, 40.772), (-73.969, 40.776), (-73.975, 40.776)])}
        ],
        crs="EPSG:4326"
    )

    temp_shp_dir = SAMPLE_DIR / "temp_shp"
    temp_shp_dir.mkdir(parents=True, exist_ok=True)
    shp_path = temp_shp_dir / "sample_polygons.shp"
    gdf_poly.to_file(shp_path)

    zip_path = SAMPLE_DIR / "sample_shapefile.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for p in temp_shp_dir.glob("sample_polygons.*"):
            zip_file.write(p, arcname=p.name)

    # Cleanup temp dir
    for p in temp_shp_dir.glob("*"):
        os.remove(p)
    os.rmdir(temp_shp_dir)
    print(f"Created {zip_path}")

def create_invalid_zip_missing_components():
    zip_path = SAMPLE_DIR / "missing_components.zip"
    with zipfile.ZipFile(zip_path, 'w') as zip_file:
        zip_file.writestr("test.shp", b"fake shp header data")
        # Missing .dbf and .shx
    print(f"Created {zip_path}")

def create_corrupted_zip():
    zip_path = SAMPLE_DIR / "corrupted.zip"
    with open(zip_path, 'wb') as f:
        f.write(b"NOT A REAL ZIP FILE HEADER 1234567890")
    print(f"Created {zip_path}")

def create_invalid_ext():
    file_path = SAMPLE_DIR / "invalid_file.txt"
    with open(file_path, "w") as f:
        f.write("This is a text file.")
    print(f"Created {file_path}")

if __name__ == "__main__":
    create_sample_kml_polygon()
    create_sample_kml_linestring()
    create_sample_shapefile_zip()
    create_invalid_zip_missing_components()
    create_corrupted_zip()
    create_invalid_ext()
