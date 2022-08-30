import pandas as pd
import geopandas as gpd
from pyproj.crs import CRS
from hamilton.function_modifiers import extract_columns

from .config import Settings


def input_shapefile_df(input_shapefile: str) -> gpd.GeoDataFrame:
    """Import shapefile to GeoDataFrame and add columns to record.

    :params input_shapefile:                        Full path with file name and extension to the input shapefile.
    :type input_shapefile:                          str

    :return:                                        GeoDataFrame of shapefile target fields

    """

    # read in shapefile and only keep necessary fields
    return gpd.read_file(input_shapefile)[[Settings.data_id_field_name,
                                           Settings.data_height_field_name,
                                           Settings.data_geometry_field_name]]


def target_crs(input_shapefile_df: gpd.GeoDataFrame) -> CRS:
    """Extract coordinate reference system from geometry.

    """

    return input_shapefile_df.crs


def standardize_column_names_df(input_shapefile_df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Standardize field names from data to reference names in code.

    """

    # standardize field names from data to reference names in code
    input_shapefile_df.rename(columns={Settings.data_id_field_name: Settings.id_field,
                                       Settings.data_height_field_name: Settings.height_field,
                                       Settings.data_geometry_field_name: Settings.geometry_field},
                              inplace=True)

    return input_shapefile_df


@extract_columns(*[Settings.id_field, Settings.height_field, Settings.geometry_field])
def filter_zero_height_df(standardize_column_names_df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Filter out any 0 height buildings and reindex the data frame.

    """

    return standardize_column_names_df.loc[standardize_column_names_df[Settings.height_field] > 0].reset_index(drop=True)


def building_area(building_polygon_geometry: pd.Series) -> gpd.GeoSeries:
    """Calculate the area of the polygon geometry.

    :param geometry:                                Polygon geometry.
    :type geometry:                                 pd.Series

    :return:                                        Calculated area in units of the geometry.

    """

    return building_polygon_geometry.area


def building_centroid(building_polygon_geometry: pd.Series) -> pd.Series:
    """Calculate the centroid of the polygon geometry.

    :param geometry:                                Polygon geometry.
    :type geometry:                                 pd.Series

    :return:                                        Centroid geometry of the polygon geometry.

    """

    return building_polygon_geometry.centroid


def building_centroid_buffered(building_centroid: pd.Series,
                               radius: int = 100,
                               cap_style: int = 3) -> pd.Series:
    """Calculate a buffered polygon geometry.

    :param building_centroid:                       Centroid geometry of the polygon.
    :type building_centroid:                        pd.Series

    :param radius:                                  The radius of the buffer.
                                                    100 (default)
    :type radius:                                   int

    :param cap_style:                               The shape of the buffer.
                                                    1 == Round
                                                    2 == Flat
                                                    3 == Square (default)

    :return:                                        Buffered geometry of the polygon geometry.

    """

    return building_centroid.buffer(distance=radius, cap_style=cap_style)


@extract_columns(*Settings.spatial_join_list)
def target_buffered_buildings_to_neighbor_centroids_df(building_id: pd.Series,
                    building_height: pd.Series,
                    building_polygon_geometry: pd.Series,
                    building_area: pd.Series,
                    building_centroid: pd.Series,
                    building_centroid_buffered: pd.Series,
                    target_crs: CRS) -> gpd.GeoDataFrame:
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
        how="left",
        predicate='intersects',
        lsuffix="target",
        rsuffix="neighbors")

    return xdf


def neighbor_centroid(target_buffered_buildings_to_neighbor_centroids_df: pd.DataFrame) -> gpd.GeoSeries:
    """asdf

    """

    # get the centroid for each
    x = target_buffered_buildings_to_neighbor_centroids_df.groupby(Settings.target_id_field)[Settings.centroid_field].first()

    # generate the building centroid of each neighbor building
    return target_buffered_buildings_to_neighbor_centroids_df[Settings.neighbor_id_field].map(x)


# calculate the distance from the target building neighbor to each neighbor building centroid
gdf["distance"] = gdf.geometry.centroid.distance(gdf["neighbor_centroid"])

# calculate the angle in degrees of the neighbor building orientation to the target
gdf["angle_in_degrees"] = np.degrees(np.arctan2(gdf["neighbor_centroid"].y - gdf["centroid"].y, gdf["neighbor_centroid"].x - gdf["centroid"].x))

# adjust the angle to correspond to a circle where 0/360 degrees is directly east, and the degrees increase counter-clockwise
gdf["angle_in_degrees"] = np.where(gdf["angle_in_degrees"] < 0,
                                   gdf["angle_in_degrees"] + DEGREES_IN_CIRCLE,
                                   gdf["angle_in_degrees"])


def target_centroid_to_neighbor_centroid_distance():

    pass