from pyproj import CRS
from shapely.geometry import Polygon, LineString
from app.services.crs_service import CRSService

def test_utm_epsg_determination():
    # NYC (lon=-73.96, lat=40.78) -> UTM Zone 18N (EPSG:32618)
    epsg_nyc = CRSService.get_utm_epsg_for_location(-73.96, 40.78)
    assert epsg_nyc == 32618

    # Sydney Australia (lon=151.20, lat=-33.86) -> UTM Zone 56S (EPSG:32756)
    epsg_sydney = CRSService.get_utm_epsg_for_location(151.20, -33.86)
    assert epsg_sydney == 32756

def test_geographic_to_projected_transformation():
    # Square polygon near NYC in geographic coords (EPSG:4326)
    poly = Polygon([(-73.965, 40.782), (-73.959, 40.782), (-73.959, 40.786), (-73.965, 40.786)])
    source_crs = CRS.from_epsg(4326)

    proj_geom, target_crs_str = CRSService.transform_geometry_to_projected(poly, source_crs)

    assert target_crs_str == "EPSG:32618"
    # In UTM zone 18N, coordinates are in meters (e.g. x ~ 587,000 m, y ~ 4,515,000 m)
    assert proj_geom.area > 100000.0  # Area in square meters (approx 220,000 m^2)

def test_projected_crs_passthrough():
    # Already projected in UTM zone 18N (EPSG:32618)
    poly = Polygon([(500000, 4000000), (501000, 4000000), (501000, 4001000), (500000, 4001000)])
    source_crs = CRS.from_epsg(32618)

    proj_geom, target_crs_str = CRSService.transform_geometry_to_projected(poly, source_crs)
    assert proj_geom == poly
    assert "32618" in target_crs_str
