from typing import Dict, Any, Optional, Tuple
from shapely.geometry import base
from shapely.validation import make_valid
from app.services.crs_service import CRSService
from pyproj import CRS
from app.core.logging import logger

class MeasurementService:
    @staticmethod
    def measure_geometry(
        geom: base.BaseGeometry,
        source_crs: Optional[CRS]
    ) -> Tuple[str, Optional[float], Optional[str], str, Optional[str]]:
        """
        Measures area for Polygons or length for LineStrings.
        Handles CRS transformation to projected CRS before measurement.

        Returns: (measurement_type, value, unit, status, error_message)
        """
        if geom is None or geom.is_empty:
            return ("none", None, None, "FAILED", "Empty or null geometry")

        # Repair invalid geometries if possible
        if not geom.is_valid:
            try:
                geom = make_valid(geom)
            except Exception as e:
                return ("none", None, None, "FAILED", f"Invalid geometry could not be repaired: {str(e)}")

        geom_type = geom.geom_type

        # 1. Point / MultiPoint
        if geom_type in ("Point", "MultiPoint"):
            return ("none", None, None, "SUCCESS", None)

        # 2. Polygon / MultiPolygon
        elif geom_type in ("Polygon", "MultiPolygon"):
            try:
                projected_geom, _ = CRSService.transform_geometry_to_projected(geom, source_crs)
                area_val = float(projected_geom.area)
                return ("area", round(area_val, 2), "square_meters", "SUCCESS", None)
            except Exception as e:
                logger.error(f"Error measuring polygon area: {e}")
                return ("area", None, None, "FAILED", f"Area calculation failed: {str(e)}")

        # 3. LineString / MultiLineString
        elif geom_type in ("LineString", "MultiLineString"):
            try:
                projected_geom, _ = CRSService.transform_geometry_to_projected(geom, source_crs)
                length_val = float(projected_geom.length)
                return ("length", round(length_val, 2), "meters", "SUCCESS", None)
            except Exception as e:
                logger.error(f"Error measuring linestring length: {e}")
                return ("length", None, None, "FAILED", f"Length calculation failed: {str(e)}")

        # 4. GeometryCollection or Unsupported
        elif geom_type == "GeometryCollection":
            # Sum up areas of polygons and lengths of linestrings if present
            try:
                total_area = 0.0
                total_length = 0.0
                has_polygon = False
                has_linestring = False

                for member in geom.geoms:
                    m_type, val, _, status, _ = MeasurementService.measure_geometry(member, source_crs)
                    if status == "SUCCESS" and val is not None:
                        if m_type == "area":
                            total_area += val
                            has_polygon = True
                        elif m_type == "length":
                            total_length += val
                            has_linestring = True

                if has_polygon and not has_linestring:
                    return ("area", round(total_area, 2), "square_meters", "SUCCESS", None)
                elif has_linestring and not has_polygon:
                    return ("length", round(total_length, 2), "meters", "SUCCESS", None)
                elif has_polygon and has_linestring:
                    # If both exist, primary measurement is area
                    return ("area", round(total_area, 2), "square_meters", "SUCCESS", None)
                else:
                    return ("none", None, None, "SUCCESS", None)
            except Exception as e:
                return ("none", None, None, "FAILED", f"GeometryCollection processing failed: {str(e)}")

        else:
            return ("none", None, None, "UNSUPPORTED", f"Unsupported geometry type: {geom_type}")
