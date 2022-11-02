import numpy as np
import pandas as pd
import geopandas as gpd
from pyproj.crs import CRS
from hamilton.function_modifiers import extract_columns, tag

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

    :param building_polygon_geometry:               Polygon geometry of the building.
    :type building_polygon_geometry:                pd.Series

    :return:                                        pd.Series

    """

    return building_polygon_geometry.centroid


def building_buffered(building_polygon_geometry: pd.Series,
                      radius: int = 100,
                      cap_style: int = 3) -> pd.Series:
    """Calculate the buffer of the building polygon for the desired radius and cap style.

    :param building_polygon_geometry:               Polygon geometry of the building.
    :type building_polygon_geometry:                pd.Series

    :param radius:                                  The radius of the buffer.
                                                    100 (default)
    :type radius:                                   int

    :param cap_style:                               The shape of the buffer.
                                                    1 == Round
                                                    2 == Flat
                                                    3 == Square (default)

    :return:                                        pd.Series

    """

    return building_polygon_geometry.buffer(distance=radius, cap_style=cap_style)


@extract_columns(*Settings.spatial_join_list)
def get_neighboring_buildings_df(building_id: pd.Series,
                                 building_height: pd.Series,
                                 building_polygon_geometry: pd.Series,
                                 building_area: pd.Series,
                                 building_centroid: pd.Series,
                                 building_buffered: pd.Series,
                                 target_crs: CRS,
                                 join_type: str = "left",
                                 join_predicate: str = "intersects",
                                 join_lsuffix: str = "target",
                                 join_rsuffix: str = "neighbor") -> gpd.GeoDataFrame:
    """Conduct a spatial join to get the building centroids that intersect the buffered target buildings.

    :param building_id:                         Building ID field.
    :type building_id:                          pd.Series

    :param building_height:                     Building height field.
    :type building_height:                      pd.Series

    :param building_polygon_geometry:           Polygon geometry field for the buildings.
    :type building_polygon_geometry:            pd.Series

    :param building_area:                       Building area field.
    :type building_area:                        pd.Series

    :param building_centroid:                   Point centroid geometry of the building.
    :type building_centroid:                    pd.Series

    :param building_buffered:                   Polygon geometry of the buffered building polygon.
    :type building_buffered:                    pd.Series

    :param target_crs:                          Coordinate reference system field of the parent geometry.
    :type target_crs:                           pd.Series

    :param join_type:                           Type of join desired.
                                                DEFAULT: `left`
    :type join_type:                            str

    :param join_predicate:                      Selected topology of join.
                                                DEFAULT: `intersects`
    :type join_predicate:                       str

    :param join_lsuffix:                        Suffix of the left object in the join.
                                                DEFAULT: `target`
    :type join_lsuffix:                         str

    :param join_rsuffix:                        Suffix of the right object in the join.
                                                DEFAULT: `neighbor`
    :type join_rsuffix:                         str

    :return:                                    GeoDataFrame of building centroids that intersect the buffered target
                                                buildings and their attributes.

    """

    # assemble a pandas data frame
    df = pd.DataFrame({Settings.id_field: building_id,
                       Settings.height_field: building_height,
                       Settings.area_field: building_area,
                       Settings.geometry_field: building_polygon_geometry,
                       Settings.centroid_field: building_centroid,
                       Settings.buffered_field: building_buffered})

    # create left and right geodataframes
    left_gdf = gpd.GeoDataFrame(df, geometry=Settings.buffered_field, crs=target_crs)
    right_gdf = gpd.GeoDataFrame(df, geometry=Settings.centroid_field, crs=target_crs)

    # spatially join the building centroids to the target buffered areas
    xdf = gpd.sjoin(left_df=left_gdf,
                    right_df=right_gdf,
                    how=join_type,
                    predicate=join_predicate,
                    lsuffix=join_lsuffix,
                    rsuffix=join_rsuffix)

    return xdf


def building_centroid_target(building_polygon_geometry_target: pd.Series,
                             target_crs: CRS) -> gpd.GeoSeries:
    """Calculate the centroid geometry from the parent building geometry.

    :param building_polygon_geometry_target:    Polygon geometry field for the target buildings from the spatially
                                                joined data.
    :type building_polygon_geometry_target:     pd.Series

    :param target_crs:                          Coordinate reference system field of the parent geometry.
    :type target_crs:                           pd.Series

    :return:                                    The centroid geometry from the target building geometry as a GeoSeries.

    """

    return gpd.GeoSeries(building_polygon_geometry_target, crs=target_crs).centroid


def building_centroid_neighbor(building_polygon_geometry_neighbor: pd.Series,
                               target_crs: CRS) -> gpd.GeoSeries:
    """Calculate the centroid geometry from the neighbor building geometry.

    :param building_polygon_geometry_neighbor:  Polygon geometry field for the neighboring buildings from the spatially
                                                joined data.
    :type building_polygon_geometry_neighbor:   pd.Series

    :param target_crs:                          Coordinate reference system field of the parent geometry.
    :type target_crs:                           pd.Series

    :return:                                    The centroid geometry from the neighbor building geometry as a
                                                GeoSeries.

    """

    return gpd.GeoSeries(building_polygon_geometry_neighbor, crs=target_crs).centroid


def distance_to_neighbor_by_centroid(building_centroid_target: gpd.GeoSeries,
                                     building_centroid_neighbor: gpd.GeoSeries) -> pd.Series:
    """Calculate the distance from the target building neighbor to each neighbor building centroid.

    :param building_centroid_target:            Centroid geometry from the target building geometry.
    :type building_centroid_target:             gpd.GeoSeries

    :param building_centroid_neighbor:          Centroid geometry from the neighbor building geometry.
    :type building_centroid_neighbor:           gpd.GeoSeries

    :return:                                    Distance field in CRS units.

    """

    return building_centroid_target.distance(building_centroid_neighbor)


def angle_in_degrees_to_neighbor(building_centroid_target: gpd.GeoSeries,
                                 building_centroid_neighbor: gpd.GeoSeries) -> pd.Series:
    """Calculate the angle in degrees of the neighbor building orientation to the target.
    Adjust the angle to correspond to a circle where 0/360 degrees is directly east, and the
    degrees increase counter-clockwise.

    :param building_centroid_target:            Centroid geometry from the target building geometry.
    :type building_centroid_target:             gpd.GeoSeries

    :param building_centroid_neighbor:          Centroid geometry from the neighbor building geometry.
    :type building_centroid_neighbor:           gpd.GeoSeries

    :return:                                    Angle in degrees for each building interaction.

    """

    # unpack coordinates for readability
    target_x = building_centroid_target.x
    target_y = building_centroid_target.y
    neighbor_x = building_centroid_neighbor.x
    neighbor_y = building_centroid_neighbor.y

    # calculate the angle in degrees of the neighbor building orientation to the target
    angle_series = np.degrees(np.arctan2(neighbor_y - target_y, neighbor_x - target_x))

    # adjust the angle to correspond to a circle where 0/360 degrees is directly east, and the degrees increase
    # counter-clockwise
    return pd.Series(np.where(angle_series < 0,
                              angle_series + Settings.DEGREES_IN_CIRCLE,
                              angle_series),
                     index=building_centroid_target.index)


def orientation_to_neighbor(angle_in_degrees_to_neighbor: pd.Series) -> pd.Series:
    """Determine the east-west or north-south orientation of the target building to its neighbors.

    :param angle_in_degrees_to_neighbor:        Angle in degrees for each building interaction.
    :type angle_in_degrees_to_neighbor:         pd.Series

    :return:                                    Either the east-west or north-south orientation of the target building
                                                to its neighbors.

    """

    return pd.Series(
            np.where(
                (((Settings.SOUTHEAST_DEGREES <= angle_in_degrees_to_neighbor) &
                    (angle_in_degrees_to_neighbor <= Settings.DEGREES_IN_CIRCLE))
                | ((Settings.START_OF_CIRCLE_DEGREES <= angle_in_degrees_to_neighbor) &
                    (angle_in_degrees_to_neighbor < Settings.NORTHEAST_DEGREES)))
                | ((Settings.NORTHWEST_DEGREES <= angle_in_degrees_to_neighbor) &
                    (angle_in_degrees_to_neighbor < Settings.SOUTHWEST_DEGREES)),
                "east_west",
                "north_south"
            ),
            index=angle_in_degrees_to_neighbor.index
    )


def _plan_area_dict(building_id: pd.Series,
                    building_area_neighbor: pd.Series) -> dict:
    """Calculate the total area of all buildings within the plan area.

    :param building_id:                         Building ID field.
    :type building_id:                          pd.Series

    :param building_area_neighbor:              Building area neighbor field.
    :type building_area_neighbor:               pd.Series

    :return:                                    Dictionary of building id to the neighboring building areas

    """

    df = pd.DataFrame({Settings.id_field: building_id,
                       Settings.neighbor_area_field: building_area_neighbor})

    return df.groupby(Settings.id_field)[Settings.neighbor_area_field].sum().to_dict()


def _building_height_dict(building_id: pd.Series,
                          building_height: pd.Series) -> dict:
    """Calculate building height per building.

    :param building_id:                         Building ID field.
    :type building_id:                          pd.Series

    :param building_height:                     Building height field.
    :type building_height:                      pd.Series

    :return:                                    Dictionary of building id to building height

    """

    df = pd.DataFrame({Settings.id_field: building_id,
                       Settings.height_field: building_height})

    return df.groupby(Settings.id_field)[Settings.height_field].max().to_dict()


def _footprint_building_areas(_building_height_dict: dict,
                              _plan_area_dict: dict) -> dict:
    """Create a dictionary of the height and plan_area to a dictionary where the key is the
    target building ID.

    :param _building_height_dict:               Dictionary of building id to building height
    :type _building_height_dict:                dict

    :param _plan_area_dict:                     Dictionary of building id to the neighboring building areas.
    :type _plan_area_dict:                      dict

    :return:                                    Dictionary of building id to the height and plan area.

    """

    return {i: [_building_height_dict[i], _plan_area_dict[i]] for i in _plan_area_dict.keys()}


def average_building_heights(building_id: pd.Series,
                             building_height_neighbor: pd.Series) -> pd.Series:
    """Average building heights for each target building when considering themselves
    and those that are within their buffered area.

    :param building_id:                         Building ID field.
    :type building_id:                          pd.Series

    :param building_height_neighbor:            Building height field for neighbors
    :type building_height_neighbor:             pd.Series

    :return:                                    Series of building heights for each target building in the buffered area

    """

    df = pd.DataFrame({Settings.id_field: building_id,
                       Settings.neighbor_height_field: building_height_neighbor})

    return df.groupby(Settings.id_field)[Settings.neighbor_height_field].mean().fillna(0)


def standard_deviation_building_heights(building_id: pd.Series,
                                        building_height_neighbor: pd.Series) -> pd.Series:
    """Standard deviation of building heights for each target building when considering themselves
    and those that are within their buffered area.

    :param building_id:                         Building ID field.
    :type building_id:                          pd.Series

    :param building_height_neighbor:            Building height field for neighbors
    :type building_height_neighbor:             pd.Series

    :return:                                    Series of building heights for each target building in the buffered area

    """

    df = pd.DataFrame({Settings.id_field: building_id,
                       Settings.neighbor_height_field: building_height_neighbor})

    return df.groupby(Settings.id_field)[Settings.neighbor_height_field].std().fillna(0)