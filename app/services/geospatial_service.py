import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape, Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon
from pyproj import CRS
from fastapi import HTTPException
import fiona
from app.core.logging import logger

# Enable KML/LIBKML drivers in fiona if available
try:
    fiona.drvsupport.supported_drivers['KML'] = 'rw'
    fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'
except Exception as e:
    logger.warning(f"Could not register KML driver in fiona: {e}")

class GeoSpatialService:
    @classmethod
    def read_geospatial_dataset(cls, file_path: Path, file_type: str) -> gpd.GeoDataFrame:
        """
        Reads a geospatial file (.kml or .shp from zip) into a GeoPandas GeoDataFrame.
        Uses GeoPandas first, and falls back to a custom XML parser for KML if driver is missing.
        """
        if not file_path.exists():
            raise HTTPException(status_code=400, detail="Geospatial data file not found.")

        try:
            if file_type == "KML":
                return cls._read_kml(file_path)
            elif file_type == "ZIP_SHAPEFILE":
                return cls._read_shapefile(file_path)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error reading geospatial dataset '{file_path}': {e}")
            raise HTTPException(status_code=400, detail=f"Invalid geospatial dataset or corrupted file: {str(e)}")

    @classmethod
    def _read_shapefile(cls, shp_path: Path) -> gpd.GeoDataFrame:
        try:
            gdf = gpd.read_file(shp_path)
            if gdf.empty:
                raise HTTPException(status_code=400, detail="Shapefile contains no features or records.")
            return gdf
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse Shapefile: {str(e)}")

    @classmethod
    def _read_kml(cls, kml_path: Path) -> gpd.GeoDataFrame:
        # Try GeoPandas first
        try:
            gdf = gpd.read_file(kml_path, driver="KML")
            if not gdf.empty:
                if gdf.crs is None:
                    gdf.set_crs("EPSG:4326", inplace=True)
                return gdf
        except Exception as e:
            logger.info(f"GeoPandas KML driver failed ({e}), attempting fallback XML KML parser.")

        # Fallback XML parser for KML
        return cls._parse_kml_xml(kml_path)

    @classmethod
    def _parse_kml_xml(cls, kml_path: Path) -> gpd.GeoDataFrame:
        """
        Fallback parser for KML files using ElementTree XML parsing.
        """
        try:
            tree = ET.parse(kml_path)
            root = tree.getroot()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid or malformed KML file: {str(e)}")

        # KML namespaces
        namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}
        # Search for Placemark elements with or without namespace
        placemarks = root.findall('.//kml:Placemark', namespaces)
        if not placemarks:
            # Try without namespace prefix
            placemarks = root.findall('.//Placemark')

        features = []
        geometries = []

        for idx, pm in enumerate(placemarks):
            name_elem = pm.find('kml:name', namespaces) or pm.find('name')
            name = name_elem.text if name_elem is not None else f"Feature_{idx}"

            desc_elem = pm.find('kml:description', namespaces) or pm.find('description')
            desc = desc_elem.text if desc_elem is not None else ""

            # Geometry parsing
            geom = cls._extract_kml_geometry(pm, namespaces)

            if geom is not None:
                geometries.append(geom)
                features.append({"name": name, "description": desc, "feature_id": idx})

        if not geometries:
            raise HTTPException(status_code=400, detail="No valid placemarks or geometries found in KML file.")

        gdf = gpd.GeoDataFrame(features, geometry=geometries, crs="EPSG:4326")
        return gdf

    @classmethod
    def _extract_kml_geometry(cls, elem: ET.Element, ns: Dict[str, str]):
        """
        Extracts Shapely geometry from a KML Placemark element.
        """
        # Point
        pt = elem.find('.//kml:Point/kml:coordinates', ns) or elem.find('.//Point/coordinates')
        if pt is not None and pt.text:
            coords = cls._parse_kml_coords(pt.text)
            if coords:
                return Point(coords[0])

        # LineString
        ls = elem.find('.//kml:LineString/kml:coordinates', ns) or elem.find('.//LineString/coordinates')
        if ls is not None and ls.text:
            coords = cls._parse_kml_coords(ls.text)
            if len(coords) >= 2:
                return LineString(coords)

        # Polygon
        poly = elem.find('.//kml:Polygon', ns) or elem.find('.//Polygon')
        if poly is not None:
            outer = poly.find('.//kml:outerBoundaryIs//kml:coordinates', ns) or poly.find('.//outerBoundaryIs//coordinates')
            if outer is not None and outer.text:
                outer_coords = cls._parse_kml_coords(outer.text)
                if len(outer_coords) >= 3:
                    inner_holes = []
                    inners = poly.findall('.//kml:innerBoundaryIs//kml:coordinates', ns) or poly.findall('.//innerBoundaryIs//coordinates')
                    for inner in inners:
                        if inner.text:
                            hole_coords = cls._parse_kml_coords(inner.text)
                            if len(hole_coords) >= 3:
                                inner_holes.append(hole_coords)
                    return Polygon(shell=outer_coords, holes=inner_holes)

        return None

    @staticmethod
    def _parse_kml_coords(coords_str: str) -> List[Tuple[float, ...]]:
        """
        Parses KML coordinate text string into tuple of (lon, lat) or (lon, lat, alt).
        """
        result = []
        raw_tuples = coords_str.strip().split()
        for raw in raw_tuples:
            parts = raw.split(',')
            if len(parts) >= 2:
                try:
                    lon = float(parts[0])
                    lat = float(parts[1])
                    result.append((lon, lat))
                except ValueError:
                    continue
        return result
