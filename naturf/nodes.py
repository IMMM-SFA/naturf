import pandas as pd
import geopandas as gpd
from pyproj.crs import CRS
from hamilton.function_modifiers import extract_columns

from .config import Settings


def input_shapefile_df(input_shapefile: str) -> gpd.GeoDataFrame:
    """Import shapefile to GeoDataFrame using only desired columns.

    :params input_shapefile:                        Full path with file name and extension to the input shapefile.
    :type input_shapefile:                          str

    :return:                                        GeoDataFrame

    """

    return gpd.read_file(input_shapefile)[[Settings.data_id_field_name,
                                           Settings.data_height_field_name,
                                           Settings.data_geometry_field_name]]


def target_crs(input_shapefile_df: gpd.GeoDataFrame) -> CRS:
    """Extract coordinate reference system from geometry.

    :params input_shapefile_df:                     GeoDataFrame of from the input shapefile.
    :type input_shapefile_df:                       gpd.GeoDataFrame

    :return:                                        pyproj Coordinate Reference System (CRS) object

    """

    return input_shapefile_df.crs


def standardize_column_names_df(input_shapefile_df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Standardize field names so use throughout code will be consistent throughout.

    :params input_shapefile_df:                     GeoDataFrame of from the input shapefile.
    :type input_shapefile_df:                       gpd.GeoDataFrame

    :return:                                        GeoDataFrame

    """

    # standardize field names from data to reference names in code
    input_shapefile_df.rename(columns={Settings.data_id_field_name: Settings.id_field,
                                       Settings.data_height_field_name: Settings.height_field,
                                       Settings.data_geometry_field_name: Settings.geometry_field},
                              inplace=True)

    return input_shapefile_df


@extract_columns(*[Settings.id_field, Settings.height_field, Settings.geometry_field])
def filter_zero_height_df(standardize_column_names_df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Filter out any zero height buildings and reindex the data frame.  Extract the building_id,
    building_height, and polygon geometry fields to nodes.

    :param standardize_column_names_df:             GeoDataFrame of the input shapefile with renamed columns.
    :type standardize_column_names_df:              gpd.GeoDataFrame

    :return:                                        GeoDataFrame

    """

    return standardize_column_names_df.loc[standardize_column_names_df[Settings.height_field] > 0].reset_index(drop=True)


def building_area(building_polygon_geometry: pd.Series) -> pd.Series:
    """Calculate the area of the polygon geometry.

    :param building_polygon_geometry:               Polygon geometry.
    :type building_polygon_geometry:                pd.Series

    :return:                                        pd.Series

    """

    return building_polygon_geometry.area


def building_centroid(building_polygon_geometry: pd.Series) -> pd.Series:
    """Calculate the centroid of the polygon geometry.

    :param building_polygon_geometry:               Polygon geometry.
    :type building_polygon_geometry:                pd.Series

    :return:                                        pd.Series

    """

    return building_polygon_geometry.centroid


def building_centroid_buffered(building_centroid: pd.Series,
                               radius: int = 100,
                               cap_style: int = 3) -> pd.Series:
    """Calculate the buffer of the building centroid for the desired radius and cap style.

    :param building_centroid:                       Centroid geometry of the polygon.
    :type building_centroid:                        pd.Series

    :param radius:                                  The radius of the buffer.
                                                    100 (default)
    :type radius:                                   int

    :param cap_style:                               The shape of the buffer.
                                                    1 == Round
                                                    2 == Flat
                                                    3 == Square (default)

    :return:                                        pd.Series

    """

    return building_centroid.buffer(distance=radius, cap_style=cap_style)


@extract_columns(*Settings.spatial_join_list)
def get_neighboring_buildings_df(building_id: pd.Series,
                                 building_height: pd.Series,
                                 building_polygon_geometry: pd.Series,
                                 building_area: pd.Series,
                                 building_centroid: pd.Series,
                                 building_centroid_buffered: pd.Series,
                                 target_crs: CRS,
                                 join_type: str = "left",
                                 join_predicate: str = "intersects",
                                 join_lsuffix: str = "target",
                                 join_rsuffix: str = "neighbor") -> gpd.GeoDataFrame:
    """Conduct a spatial join to get the building centroids that intersect
    the buffered target buildings.

    """

    xdf = gpd.sjoin(
        left_df=gpd.GeoDataFrame({Settings.id_field: building_id,
                                  Settings.height_field: building_height,
                                  Settings.area_field: building_area,
                                  Settings.geometry_field: building_polygon_geometry,
                                  Settings.centroid_field: building_centroid,
                                  Settings.buffered_field: building_centroid_buffered},
                                 crs=target_crs,
                                 geometry=Settings.geometry_field),
        right_df=gpd.GeoDataFrame({Settings.id_field: building_id,
                                   Settings.height_field: building_height,
                                   Settings.area_field: building_area,
                                   Settings.centroid_field: building_centroid},
                                  crs=target_crs,
                                  geometry=Settings.centroid_field),
        how=join_type,
        predicate=join_predicate,
        lsuffix=join_lsuffix,
        rsuffix=join_rsuffix)

    return xdf


# def neighbor_centroid(get_neighboring_buildings_df: pd.DataFrame) -> gpd.GeoSeries:
#     """Generate a centroid geometry for each neighbor building in each row.
#
#
#
#     """
#
#     # get the centroid for each
#     x = get_neighboring_buildings.groupby(Settings.target_id_field)[Settings.centroid_field].first()
#
#     # generate the building centroid of each neighbor building
#     return get_neighboring_buildings[Settings.neighbor_id_field].map(x)
#
#
# def target_centroid_to_neighbor_centroid_distance():
#
#     pass