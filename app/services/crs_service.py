from typing import Tuple, Optional
import pyproj
from pyproj import CRS, Transformer
from shapely.geometry import base
from shapely.ops import transform as shapely_transform
from app.core.logging import logger

class CRSService:
    @staticmethod
    def get_utm_epsg_for_location(longitude: float, latitude: float) -> int:
        """
        Determines the appropriate UTM EPSG code for a given (longitude, latitude) point.
        Northern hemisphere: 32601 - 32660
        Southern hemisphere: 32701 - 32760
        """
        # Constrain lon between -180 and 180
        lon = (longitude + 180) % 360 - 180
        lat = max(-80.0, min(84.0, latitude))  # Standard UTM coverage

        zone = int((lon + 180) / 6) + 1
        zone = max(1, min(60, zone))

        if lat >= 0:
            return 32600 + zone
        else:
            return 32700 + zone

    @classmethod
    def transform_geometry_to_projected(
        cls,
        geom: base.BaseGeometry,
        source_crs: Optional[CRS]
    ) -> Tuple[base.BaseGeometry, str]:
        """
        Transforms a geometry from a geographic CRS to an optimal projected CRS (meters).
        If the source CRS is already projected, returns the original geometry and CRS name.
        """
        if source_crs is None:
            # Fallback to EPSG:4326 if unassigned
            source_crs = CRS.from_epsg(4326)

        # If already projected, return as-is
        if source_crs.is_projected:
            crs_str = source_crs.to_string()
            return geom, crs_str

        # If geographic (e.g., EPSG:4326), compute centroid to pick appropriate UTM zone
        try:
            centroid = geom.centroid
            lon, lat = centroid.x, centroid.y

            utm_epsg = cls.get_utm_epsg_for_location(lon, lat)
            target_crs = CRS.from_epsg(utm_epsg)

            # Create transformer from source to target projected CRS
            # always_xy=True ensures (longitude, latitude) -> (easting, northing) order
            transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)

            projected_geom = shapely_transform(transformer.transform, geom)
            return projected_geom, f"EPSG:{utm_epsg}"

        except Exception as e:
            logger.warning(f"Failed to transform geometry with source CRS {source_crs}: {e}")
            # Return original if transformation fails
            return geom, source_crs.to_string() if source_crs else "UNKNOWN"
