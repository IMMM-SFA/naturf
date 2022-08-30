import pandas as pd
import geopandas as gpd
from pyproj.crs import CRS
from hamilton.function_modifiers import extract_columns

from .config import Settings


def shapefile_df(input_shapefile: str) -> gpd.GeoDataFrame:
    """Import shapefile to GeoDataFrame and add columns to record.

    :params input_shapefile:                        Full path with file name and extension to the input shapefile.
    :type input_shapefile:                          str

    :return:                                        GeoDataFrame of shapefile target fields

    """

    # read in shapefile and only keep necessary fields
    gdf = gpd.read_file(input_shapefile)[[Settings.data_id_field_name,
                                          Settings.data_height_field_name,
                                          Settings.data_geometry_field_name]]

    # standardize field names from data to reference names in code
    gdf.rename(columns={Settings.data_id_field_name: Settings.id_field,
                        Settings.data_height_field_name: Settings.height_field,
                        Settings.data_geometry_field_name: Settings.geometry_field},
               inplace=True)

    return gdf


def target_crs(shapefile_df: gpd.GeoDataFrame) -> CRS:
    """Extract coordinate reference system from geometry."""

    return shapefile_df.crs


@extract_columns(*[Settings.id_field, Settings.height_field, Settings.geometry_field])
def filter_df(shapefile_df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Filter out any 0 height buildings and reindex the data frame.

    """

    return shapefile_df.loc[shapefile_df[Settings.height_field] > 0].reset_index(drop=True)


def area(geometry: pd.Series,
         target_crs: CRS) -> gpd.GeoSeries:
    """Calculate the area of the polygon geometry.

    :param geometry:                                Polygon geometry.
    :type geometry:                                 gpd.GeoSeries

    :return:                                        Calculated area in units of the geometry.

    """

    return gpd.GeoSeries(geometry, crs=target_crs).area


def centroid(geometry: gpd.GeoSeries) -> gpd.GeoSeries:
    """Calculate the centroid of the polygon geometry.

    :param geometry:                                Polygon geometry.
    :type geometry:                                 gpd.GeoSeries

    :return:                                        Centroid geometry of the polygon geometry.

    """

    return geometry.centroid


def buffered(centroid: gpd.GeoSeries,
             radius: int = 100,
             cap_style: int = 3) -> gpd.GeoSeries:
    """Calculate a buffered polygon geometry.

    :param centroid:                                Centroid geometry of the polygon.
    :type centroid:                                 gpd.GeoSeries

    :param radius:                                  The radius of the buffer.
                                                    100 (default)
    :type radius:                                   int

    :param cap_style:                               The shape of the buffer.
                                                    1 == Round
                                                    2 == Flat
                                                    3 == Square (default)

    :return:                                        Buffered geometry of the polygon geometry.

    """

    return centroid.buffer(distance=radius, cap_style=cap_style)


@extract_columns(*Settings.spatial_join_list)
def spatial_join_df(object_id: pd.Series,
                    height: pd.Series,
                    geometry: gpd.GeoSeries,
                    area: pd.Series,
                    centroid: gpd.GeoSeries,
                    buffered: gpd.GeoSeries) -> gpd.GeoDataFrame:
    """Conduct a spatial join to get the building centroids that intersect
    the buffered target buildings.

    """

    xdf = gpd.sjoin(
        left_df=gpd.GeoDataFrame({Settings.id_field: object_id,
                                  Settings.height_field: height,
                                  Settings.area_field: area,
                                  Settings.geometry_field: geometry,
                                  Settings.centroid_field: centroid,
                                  Settings.buffered_field: buffered},
                                 crs=geometry.crs,
                                 geometry=Settings.geometry_field),
        right_df=gpd.GeoDataFrame({Settings.id_field: object_id,
                                   Settings.height_field: height,
                                   Settings.area_field: area,
                                   Settings.centroid_field: centroid},
                                  crs=geometry.crs,
                                  geometry=Settings.centroid_field),
        how="left",
        predicate='intersects',
        lsuffix="target",
        rsuffix="neighbors")

    return xdf


def neighbor_centroid(spatial_join_df: pd.DataFrame) -> gpd.GeoSeries:

    # asdf
    neighbor_centroid_per_target_polygon = spatial_join_df.groupby(Settings.target_id_field)[Settings.centroid_field].first()

    # generate the building centroid of each neighbor building
    return gpd.GeoSeries(spatial_join_df[Settings.neighbor_id_field].map(neighbor_centroid_per_target_polygon),
                         crs=spatial_join_df.crs)
