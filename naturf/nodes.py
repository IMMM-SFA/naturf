import geopandas as gpd
import math
import numpy as np
import pandas as pd
from pyproj.crs import CRS
from hamilton.function_modifiers import extract_columns

from .config import Settings


def _average_north_south_building_distances(building_id: pd.Series) -> dict:
    """Create a dictionary with an initialization value of 0 present for each building id.

    :param building_id:                         Building ID field.
    :type building_id:                          pd.Series

    :return:                                    Dictionary of with an initialization value of 0 present for each
                                                building id.

    """

    return {i: 0 for i in building_id.unique()}


def _building_height_dict(building_id: pd.Series, building_height: pd.Series) -> dict:
    """Calculate building height per building.

    :param building_id:                         Building ID field.
    :type building_id:                          pd.Series

    :param building_height:                     Building height field.
    :type building_height:                      pd.Series

    :return:                                    Dictionary of building id to building height

    """

    df = pd.DataFrame({Settings.id_field: building_id, Settings.height_field: building_height})

    return df.groupby(Settings.id_field)[Settings.height_field].max().to_dict()


def _footprint_building_areas(_building_height_dict: dict, _plan_area_dict: dict) -> dict:
    """Create a dictionary of the height and plan_area to a dictionary where the key is the
    target building ID.

    :param _building_height_dict:               Dictionary of building id to building height
    :type _building_height_dict:                dict

    :param _plan_area_dict:                     Dictionary of building id to the neighboring building areas.
    :type _plan_area_dict:                      dict

    :return:                                    Dictionary of building id to the height and plan area.

    """

    return {i: [_building_height_dict[i], _plan_area_dict[i]] for i in _plan_area_dict.keys()}


def _plan_area_dict(building_id: pd.Series, building_area_neighbor: pd.Series) -> dict:
    """Calculate the total area of all buildings within the plan area.

    :param building_id:                         Building ID field.
    :type building_id:                          pd.Series

    :param building_area_neighbor:              Building area neighbor field.
    :type building_area_neighbor:               pd.Series

    :return:                                    Dictionary of building id to the neighboring building areas

    """

    df = pd.DataFrame(
        {Settings.id_field: building_id, Settings.neighbor_area_field: building_area_neighbor}
    )

    return df.groupby(Settings.id_field)[Settings.neighbor_area_field].sum().to_dict()


def angle_in_degrees_to_neighbor(
    building_centroid_target: gpd.GeoSeries, building_centroid_neighbor: gpd.GeoSeries
) -> pd.Series:
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
    return pd.Series(
        np.where(angle_series < 0, angle_series + Settings.DEGREES_IN_CIRCLE, angle_series),
        index=building_centroid_target.index,
    )


def apply_max_building_height(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Cap building height at MAX_BUILDING_HEIGHT, specified in config.py.

    :param gdf:             GeoDataFrame of the input shapefile with renamed columns.
    :type gdf:              gpd.GeoDataFrame

    :return:                GeoDataFrame

    """

    gdf.loc[
        gdf[Settings.height_field] > Settings.MAX_BUILDING_HEIGHT, Settings.height_field
    ] = Settings.MAX_BUILDING_HEIGHT

    return gdf


def average_building_heights(
    building_id: pd.Series, building_height_neighbor: pd.Series
) -> pd.Series:
    """Average building heights for each target building when considering themselves
    and those that are within their buffered area.

    :param building_id:                         Building ID field.
    :type building_id:                          pd.Series

    :param building_height_neighbor:            Building height field for neighbors
    :type building_height_neighbor:             pd.Series

    :return:                                    Series of building heights for each target building in the buffered area

    """

    df = pd.DataFrame(
        {Settings.id_field: building_id, Settings.neighbor_height_field: building_height_neighbor}
    )

    return df.groupby(Settings.id_field)[Settings.neighbor_height_field].mean().fillna(0)


def average_direction_distance(
    building_id: pd.Series,
    orientation_to_neighbor: pd.Series,
    distance_to_neighbor_by_centroid: pd.Series,
) -> pd.Series:
    """Calculate the average directional distances for each target building to its neighbors

    :param building_id:                         Building ID field.
    :type building_id:                          pd.Series

    :param orientation_to_neighbor:             Either the east-west or north-south orientation of the target building
                                                to its neighbors.
    :type orientation_to_neighbor:              pd.Series

    :param distance_to_neighbor_by_centroid:    Distance to neighbor from the target building using centroids.
    :type distance_to_neighbor_by_centroid:     pd.Series

    :return:                                    Series of average directional distances for each target building to its
                                                neighbors.

    """

    df = pd.DataFrame(
        {
            Settings.id_field: building_id,
            "orientation": orientation_to_neighbor,
            "distance": distance_to_neighbor_by_centroid,
        }
    )

    df = df.groupby([Settings.id_field, "orientation"])["distance"].mean().reset_index()

    # exclude the target building to target building distance and direction (would be == 0)
    df = df.loc[df["distance"] > 0]

    return df


def average_distance_between_buildings(
    building_id: pd.Series, distance_to_neighbor_by_centroid: pd.Series
) -> pd.Series:
    """Calculate the average distance from the target building to all neighboring buildings.

    :param building_id:                         Building ID field.
    :type building_id:                          pd.Series

    :param distance_to_neighbor_by_centroid:        distance from the target building neighbor to each
                                                    neighbor building centroid.
    :type distance_to_neighbor_by_centroid:         pd.Series

    :return:                                        float

    """

    df = pd.DataFrame(
        {
            Settings.id_field: building_id,
            Settings.distance_to_neighbor_by_centroid: distance_to_neighbor_by_centroid,
        }
    )

    df[Settings.distance_to_neighbor_by_centroid] = df[
        Settings.distance_to_neighbor_by_centroid
    ].replace(0, np.nan)

    df = (
        df.groupby(Settings.id_field)[Settings.distance_to_neighbor_by_centroid]
        .mean()
        .reset_index()
        .replace(np.nan, Settings.DEFAULT_STREET_WIDTH)
        .rename(
            columns={
                Settings.distance_to_neighbor_by_centroid: Settings.average_distance_between_buildings
            }
        )
    )

    return df


def building_area(building_geometry: pd.Series) -> pd.Series:
    """Calculate the area of the building geometry.

    :param building_geometry:                       Building Geometry.
    :type building_geometry:                        pd.Series

    :return:                                        pd.Series

    """

    return building_geometry.area


def building_centroid(building_geometry: pd.Series) -> pd.Series:
    """Calculate the centroid of the building geometry.

    :param building_geometry:                       Geometry of the building.
    :type building_geometry:                        pd.Series

    :return:                                        pd.Series

    """

    return building_geometry.centroid


def building_centroid_neighbor(
    building_geometry_neighbor: pd.Series, target_crs: CRS
) -> gpd.GeoSeries:
    """Calculate the centroid geometry from the neighbor building geometry.

    :param building_geometry_neighbor:          Geometry field for the neighboring buildings from the spatially
                                                joined data.
    :type building_geometry_neighbor:           pd.Series

    :param target_crs:                          Coordinate reference system field of the parent geometry.
    :type target_crs:                           pd.Series

    :return:                                    The centroid geometry from the neighbor building geometry as a
                                                GeoSeries.

    """

    return gpd.GeoSeries(building_geometry_neighbor, crs=target_crs).centroid


def building_centroid_target(building_geometry_target: pd.Series, target_crs: CRS) -> gpd.GeoSeries:
    """Calculate the centroid geometry from the parent building geometry.

    :param building_geometry_target:            Geometry field for the target buildings from the spatially
                                                joined data.
    :type building_geometry_target:             pd.Series

    :param target_crs:                          Coordinate reference system field of the parent geometry.
    :type target_crs:                           pd.Series

    :return:                                    The centroid geometry from the target building geometry as a GeoSeries.

    """

    return gpd.GeoSeries(building_geometry_target, crs=target_crs).centroid


def buildings_intersecting_plan_area(
    building_id: pd.Series,
    building_height: pd.Series,
    building_geometry: pd.Series,
    building_area: pd.Series,
    total_plan_area_geometry: pd.Series,
    wall_length_north: pd.Series,
    wall_length_east: pd.Series,
    wall_length_south: pd.Series,
    wall_length_west: pd.Series,
    target_crs: CRS,
    join_type: str = "left",
    join_predicate: str = "intersects",
    join_lsuffix: str = "target",
    join_rsuffix: str = "neighbor",
) -> gpd.GeoDataFrame:
    """Conduct a spatial join to get the building areas that intersect the buffered target buildings.

    :param building_id:                         Building ID field.
    :type building_id:                          pd.Series

    :param building_height:                     Building height field.
    :type building_height:                      pd.Series

    :param building_geometry:                   Geometry field for the buildings.
    :type building_geometry:                    pd.Series

    :param building_area:                       Building area field.
    :type building_area:                        pd.Series

    :param total_plan_area_geometry:            Geometry of the buffered building.
    :type total_plan_area_geometry:             pd.Series

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

    :return:                                    GeoDataFrame of building areas that intersect the buffered target
                                                buildings and their attributes.

    """

    df = pd.DataFrame(
        {
            Settings.id_field: building_id,
            Settings.height_field: building_height,
            Settings.area_field: building_area,
            Settings.geometry_field: building_geometry,
            Settings.buffered_field: total_plan_area_geometry,
            Settings.wall_length_north: wall_length_north,
            Settings.wall_length_east: wall_length_east,
            Settings.wall_length_south: wall_length_south,
            Settings.wall_length_west: wall_length_west,
        }
    )

    # Create left and right GeoDataFrames.
    left_gdf = gpd.GeoDataFrame(df, geometry=Settings.buffered_field, crs=target_crs)
    right_gdf = gpd.GeoDataFrame(df, geometry=Settings.geometry_field, crs=target_crs)

    # Spatially join the building areas to the target buffered areas.
    xdf = gpd.sjoin(
        left_df=left_gdf,
        right_df=right_gdf,
        how=join_type,
        predicate=join_predicate,
        lsuffix=join_lsuffix,
        rsuffix=join_rsuffix,
    )

    # Add the neighbor building geometry.
    xdf = (
        xdf.set_index(f"{Settings.id_field}_{join_rsuffix}")
        .join(
            right_gdf.set_index(Settings.id_field)[Settings.geometry_field].rename(
                Settings.neighbor_geometry_field
            )
        )
        .sort_index()
    )

    return gpd.GeoDataFrame(xdf).set_geometry(Settings.geometry_field)


def building_plan_area(
    buildings_intersecting_plan_area: gpd.GeoDataFrame,
    join_predicate: str = "intersection",
    join_rsuffix: str = "neighbor",
) -> pd.Series:
    """Calculate the building plan area from the GeoDataFrame of buildings intersecting the plan area.

    :param buildings_intersecting_plan_area:    Geometry field for the neighboring buildings from the spatially
                                                joined data.
    :type buildings_intersecting_plan_area:     gpd.GeoDataFrame

    :param join_predicate:                      Selected topology of join.
                                                DEFAULT: `intersection`
    :type join_predicate:                       str

    :param join_rsuffix:                        Suffix of the right object in the join.
                                                DEFAULT: `neighbor`
    :type join_rsuffix:                         str

    :return:                                    The building plan area for each unique building in the
                                                `buildings_intersecting_plan_area` GeoDataFrame.

    """

    building_plan_area = []
    index = 0

    for target_building_id in np.sort(buildings_intersecting_plan_area.building_id_target.unique()):
        # Get DataFrame with any building that intersects the target_building_id plan area.
        target_building_gdf = buildings_intersecting_plan_area.loc[
            buildings_intersecting_plan_area[Settings.target_id_field] == target_building_id
        ].reset_index()

        # Create GeoDataFrames with building and neighbor info.
        target_gdf = (
            target_building_gdf[[Settings.target_id_field, Settings.target_buffered_field]]
            .set_geometry(Settings.target_buffered_field)
            .drop_duplicates()
        )
        neighbor_gdf = target_building_gdf[
            [f"index_{join_rsuffix}", Settings.neighbor_geometry_field]
        ].set_geometry(Settings.neighbor_geometry_field)

        # Create a new GeoDataFrame with the area of intersection.
        intersection_gdf = gpd.overlay(
            target_gdf, neighbor_gdf, how=join_predicate, keep_geom_type=False
        )

        # Sum up the area of intersection and add to the output list.
        building_plan_area.append(intersection_gdf[Settings.data_geometry_field_name].area.sum())

        index += 1

    return pd.Series(building_plan_area)


def distance_to_neighbor_by_centroid(
    building_centroid_target: gpd.GeoSeries, building_centroid_neighbor: gpd.GeoSeries
) -> pd.Series:
    """Calculate the distance from the target building neighbor to each neighbor building centroid.

    :param building_centroid_target:            Centroid geometry from the target building geometry.
    :type building_centroid_target:             gpd.GeoSeries

    :param building_centroid_neighbor:          Centroid geometry from the neighbor building geometry.
    :type building_centroid_neighbor:           gpd.GeoSeries

    :return:                                    Distance field in CRS units.

    """

    return building_centroid_target.distance(building_centroid_neighbor)


@extract_columns(*[Settings.id_field, Settings.height_field, Settings.geometry_field])
def filter_zero_height_df(standardize_column_names_df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Filter out any zero height buildings and reindex the data frame.  Extract the building_id,
    building_height, and geometry fields to nodes.

    :param standardize_column_names_df:             GeoDataFrame of the input shapefile with renamed columns.
    :type standardize_column_names_df:              gpd.GeoDataFrame

    :return:                                        GeoDataFrame

    """

    return standardize_column_names_df.loc[
        standardize_column_names_df[Settings.height_field] > 0
    ].reset_index(drop=True)


def frontal_area_density(
    frontal_length: pd.DataFrame, building_height: pd.Series, total_plan_area: pd.Series
) -> pd.DataFrame:
    """Calculate the frontal area density for each building in a GeoPandas GeoSeries. Frontal area density is the frontal area of a
    building at a specific height increment divided by the total plan area. naturf calculates frontal area density from the four cardinal
    directions (east, north, west, south) and at 5 meter increments from ground level to 75 meters unless otherwise specified.

    :param frontal_length:                Frontal length in each cardinal direction for each building.
    :type frontal_length:                 pd.DataFrame

    :param building_height:               Building height for each building.
    :type building_height:                pd.Series

    :param total_plan_area:               Total plan area for each building.
    :type total_plan_area:                pd.Series

    :return:                              Pandas DataFrame with frontal area density for each cardinal direction and
                                          each BUILDING_HEIGHT_INTERVAL for each building.
    """

    rows, cols = (
        len(building_height.index),
        int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL),
    )
    frontal_area_north, frontal_area_east, frontal_area_south, frontal_area_west = (
        [[0 for i in range(cols)] for j in range(rows)],
        [[0 for i in range(cols)] for j in range(rows)],
        [[0 for i in range(cols)] for j in range(rows)],
        [[0 for i in range(cols)] for j in range(rows)],
    )

    for building, building_frontal_length in frontal_length.iterrows():
        building_height_counter = Settings.BUILDING_HEIGHT_INTERVAL

        # Go from ground level to building height by the building height interval and calculate frontal area density.
        for building_height_index in range(
            0, math.ceil(building_height[building]), Settings.BUILDING_HEIGHT_INTERVAL
        ):
            if building_height_counter <= building_height[building]:
                frontal_area_north[building][
                    int(building_height_index / Settings.BUILDING_HEIGHT_INTERVAL)
                ] = (
                    building_frontal_length[Settings.frontal_length_north]
                    * Settings.BUILDING_HEIGHT_INTERVAL
                    / total_plan_area[building]
                )
                frontal_area_east[building][
                    int(building_height_index / Settings.BUILDING_HEIGHT_INTERVAL)
                ] = (
                    building_frontal_length[Settings.frontal_length_east]
                    * Settings.BUILDING_HEIGHT_INTERVAL
                    / total_plan_area[building]
                )
                frontal_area_south[building][
                    int(building_height_index / Settings.BUILDING_HEIGHT_INTERVAL)
                ] = (
                    building_frontal_length[Settings.frontal_length_south]
                    * Settings.BUILDING_HEIGHT_INTERVAL
                    / total_plan_area[building]
                )
                frontal_area_west[building][
                    int(building_height_index / Settings.BUILDING_HEIGHT_INTERVAL)
                ] = (
                    building_frontal_length[Settings.frontal_length_west]
                    * Settings.BUILDING_HEIGHT_INTERVAL
                    / total_plan_area[building]
                )
            else:
                frontal_area_north[building][
                    int(building_height_index / Settings.BUILDING_HEIGHT_INTERVAL)
                ] = (
                    building_frontal_length[Settings.frontal_length_north]
                    * (
                        Settings.BUILDING_HEIGHT_INTERVAL
                        - building_height_counter
                        + building_height[building]
                    )
                    / total_plan_area[building]
                )
                frontal_area_east[building][
                    int(building_height_index / Settings.BUILDING_HEIGHT_INTERVAL)
                ] = (
                    building_frontal_length[Settings.frontal_length_east]
                    * (
                        Settings.BUILDING_HEIGHT_INTERVAL
                        - building_height_counter
                        + building_height[building]
                    )
                    / total_plan_area[building]
                )
                frontal_area_south[building][
                    int(building_height_index / Settings.BUILDING_HEIGHT_INTERVAL)
                ] = (
                    building_frontal_length[Settings.frontal_length_south]
                    * (
                        Settings.BUILDING_HEIGHT_INTERVAL
                        - building_height_counter
                        + building_height[building]
                    )
                    / total_plan_area[building]
                )
                frontal_area_west[building][
                    int(building_height_index / Settings.BUILDING_HEIGHT_INTERVAL)
                ] = (
                    building_frontal_length[Settings.frontal_length_west]
                    * (
                        Settings.BUILDING_HEIGHT_INTERVAL
                        - building_height_counter
                        + building_height[building]
                    )
                    / total_plan_area[building]
                )
                break
            building_height_counter += Settings.BUILDING_HEIGHT_INTERVAL

    columns_north, columns_east, columns_south, columns_west = (
        [
            f"{Settings.frontal_area_north}_{i}"
            for i in range(int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL))
        ],
        [
            f"{Settings.frontal_area_east}_{i}"
            for i in range(int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL))
        ],
        [
            f"{Settings.frontal_area_south}_{i}"
            for i in range(int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL))
        ],
        [
            f"{Settings.frontal_area_west}_{i}"
            for i in range(int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL))
        ],
    )

    return pd.concat(
        [
            pd.DataFrame(frontal_area_north, columns=columns_north),
            pd.DataFrame(frontal_area_east, columns=columns_east),
            pd.DataFrame(frontal_area_south, columns=columns_south),
            pd.DataFrame(frontal_area_west, columns=columns_west),
        ],
        axis=1,
    )


def frontal_length(
    buildings_intersecting_plan_area: gpd.GeoDataFrame,
) -> pd.DataFrame:
    """Calculate the frontal length for each cardinal direction from the GeoDataFrame of buildings intersecting the plan area.
    `buildings_intersecting_plan_area()` needs to include `wall_length`.

    :param buildings_intersecting_plan_area:    Geometry field for the neighboring buildings from the spatially
                                                joined data.
    :type buildings_intersecting_plan_area:     gpd.GeoDataFrame

    :return:                                    The frontal area for each cardinal direction for each unique building in the
                                                `buildings_intersecting_plan_area` GeoDataFrame.

    """

    number_target_buildings = len(buildings_intersecting_plan_area.building_id_target.unique())
    frontal_length_north, frontal_length_east, frontal_length_south, frontal_length_west = (
        [0] * number_target_buildings,
        [0] * number_target_buildings,
        [0] * number_target_buildings,
        [0] * number_target_buildings,
    )
    index = 0

    for target_building_id in np.sort(buildings_intersecting_plan_area.building_id_target.unique()):
        # Get DataFrame with any building that intersects the target_building_id plan area.
        target_building_gdf = buildings_intersecting_plan_area.loc[
            buildings_intersecting_plan_area[Settings.target_id_field] == target_building_id
        ].reset_index()

        # Sum frontal length for each cardinal direction
        frontal_length_north[index] = target_building_gdf[
            f"{Settings.wall_length_north}_{Settings.neighbor}"
        ].sum()
        frontal_length_east[index] = target_building_gdf[
            f"{Settings.wall_length_east}_{Settings.neighbor}"
        ].sum()
        frontal_length_south[index] = target_building_gdf[
            f"{Settings.wall_length_south}_{Settings.neighbor}"
        ].sum()
        frontal_length_west[index] = target_building_gdf[
            f"{Settings.wall_length_west}_{Settings.neighbor}"
        ].sum()

        index += 1

    return pd.concat(
        [
            pd.Series(frontal_length_north, name=Settings.frontal_length_north),
            pd.Series(frontal_length_east, name=Settings.frontal_length_east),
            pd.Series(frontal_length_south, name=Settings.frontal_length_south),
            pd.Series(frontal_length_west, name=Settings.frontal_length_west),
        ],
        axis=1,
    )


@extract_columns(*Settings.spatial_join_list)
def get_neighboring_buildings_df(
    building_id: pd.Series,
    building_height: pd.Series,
    building_geometry: pd.Series,
    building_area: pd.Series,
    building_centroid: pd.Series,
    total_plan_area_geometry: pd.Series,
    target_crs: CRS,
    join_type: str = "left",
    join_predicate: str = "intersects",
    join_lsuffix: str = "target",
    join_rsuffix: str = "neighbor",
) -> gpd.GeoDataFrame:
    """Conduct a spatial join to get the building centroids that intersect the buffered target buildings.

    :param building_id:                         Building ID field.
    :type building_id:                          pd.Series

    :param building_height:                     Building height field.
    :type building_height:                      pd.Series

    :param building_geometry:                   Geometry field for the buildings.
    :type building_geometry:                    pd.Series

    :param building_area:                       Building area field.
    :type building_area:                        pd.Series

    :param building_centroid:                   Point centroid geometry of the building.
    :type building_centroid:                    pd.Series

    :param total_plan_area_geometry:            Geometry of the buffered building.
    :type total_plan_area_geometry:             pd.Series

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
    df = pd.DataFrame(
        {
            Settings.id_field: building_id,
            Settings.height_field: building_height,
            Settings.area_field: building_area,
            Settings.geometry_field: building_geometry,
            Settings.centroid_field: building_centroid,
            Settings.buffered_field: total_plan_area_geometry,
        }
    )

    # create left and right geodataframes
    left_gdf = gpd.GeoDataFrame(df, geometry=Settings.buffered_field, crs=target_crs)
    right_gdf = gpd.GeoDataFrame(df, geometry=Settings.centroid_field, crs=target_crs)

    # spatially join the building centroids to the target buffered areas
    xdf = gpd.sjoin(
        left_df=left_gdf,
        right_df=right_gdf,
        how=join_type,
        predicate=join_predicate,
        lsuffix=join_lsuffix,
        rsuffix=join_rsuffix,
    )

    return xdf


def grimmond_oke_displacement_height(building_height: pd.Series) -> pd.Series:
    """Calculate the Grimmond & Oke displacement height for each building

    :param building_height:                     Building height field.
    :type building_height:                      pd.Series

    :return:                                    pd.Series

    """

    return building_height * Settings.DISPLACEMENT_HEIGHT_FACTOR


def grimmond_oke_roughness_length(building_height: pd.Series) -> pd.Series:
    """Calculate the Grimmond & Oke roughness length for each building

    :param building_height:                     Building height field.
    :type building_height:                      pd.Series

    :return:                                    pd.Series

    """

    return building_height * Settings.ROUGHNESS_LENGTH_FACTOR


def height_to_width_ratio(
    average_building_heights: pd.Series, average_distance_between_buildings: pd.Series
) -> pd.Series:
    """Calculate the height to width ratio for each building.

    :param average_building_heights:           Series of building heights for each target building in the buffered area
    :type average_building_heights:            pd.Series

    :param average_distance_between_buildings: Series of average distance from each building to all neighboring buildings
    :type average_distance_between_buildings:  pd.Series

    :return:                                   pd.Series

    """

    return average_building_heights / average_distance_between_buildings


def input_shapefile_df(input_shapefile: str) -> gpd.GeoDataFrame:
    """Import shapefile to GeoDataFrame using only desired columns.

    :params input_shapefile:                        Full path with file name and extension to the input shapefile.
    :type input_shapefile:                          str

    :return:                                        GeoDataFrame

    """

    return gpd.read_file(input_shapefile)[
        [
            Settings.data_id_field_name,
            Settings.data_height_field_name,
            Settings.data_geometry_field_name,
        ]
    ]


def orientation_to_neighbor(angle_in_degrees_to_neighbor: pd.Series) -> pd.Series:
    """Determine the east-west or north-south orientation of the target building to its neighbors.

    :param angle_in_degrees_to_neighbor:        Angle in degrees for each building interaction.
    :type angle_in_degrees_to_neighbor:         pd.Series

    :return:                                    Either the east-west or north-south orientation of the target building
                                                to its neighbors.

    """

    return pd.Series(
        np.where(
            (
                (
                    (Settings.SOUTHEAST_DEGREES <= angle_in_degrees_to_neighbor)
                    & (angle_in_degrees_to_neighbor <= Settings.DEGREES_IN_CIRCLE)
                )
                | (
                    (Settings.START_OF_CIRCLE_DEGREES <= angle_in_degrees_to_neighbor)
                    & (angle_in_degrees_to_neighbor <= Settings.NORTHEAST_DEGREES)
                )
            )
            | (
                (Settings.NORTHWEST_DEGREES <= angle_in_degrees_to_neighbor)
                & (angle_in_degrees_to_neighbor <= Settings.SOUTHWEST_DEGREES)
            ),
            "east_west",
            "north_south",
        ),
        index=angle_in_degrees_to_neighbor.index,
    )


def plan_area_density(
    building_plan_area: pd.Series, building_height: pd.Series, total_plan_area: pd.Series
) -> pd.DataFrame:
    """Calculate the plan area density for each building in a GeoPandas GeoSeries. Plan area density is the building plan area
    at a specific height increment divided by the total plan area. naturf calculates plan area density from the four cardinal
    directions (north, east, south, west) and at 5-meter increments from ground level to 75 meters unless otherwise specified.

    :param building_plan_area:            Building plan area for each building.
    :type building_plan_area:             pd.Series

    :param building_height:               Building height for each building.
    :type building_height:                pd.Series

    :param total_plan_area:               Total plan area for each building.
    :type total_plan_area:                pd.Series

    :return:                              Pandas DataFrame with plan area density for each BUILDING_HEIGHT_INTERVAL for each building.
    """

    rows, cols = (
        len(building_height.index),
        int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL),
    )
    plan_area_density = [[0 for i in range(cols)] for j in range(rows)]

    for building in range(building_plan_area.size):
        building_height_counter = 0

        # Go from ground level to building height by the building height interval and calculate plan area density.
        while building_height_counter < building_height[building]:
            plan_area_density[building][
                int(building_height_counter / Settings.BUILDING_HEIGHT_INTERVAL)
            ] = (building_plan_area[building] / total_plan_area[building])
            building_height_counter += Settings.BUILDING_HEIGHT_INTERVAL

    columns_plan_area_density = [
        f"{Settings.plan_area_density}_{i}"
        for i in range(int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL))
    ]
    return pd.DataFrame(plan_area_density, columns=columns_plan_area_density)


def rooftop_area_density(plan_area_density: pd.DataFrame) -> pd.DataFrame:
    """Calculate the rooftop area density for each building in a Pandas DataFrame. Rooftop area density is the roof area
    of all buildings within the total plan area  at a specified height increment divided by the total plan area. naturf
    projects building footprints vertically to the building height, meaning that rooftop area density is equal to the plan area
    density.

    :param building_plan_area:            Plan area density at each specified height increment.
    :type building_plan_area:             pd.DataFrame

    :return:                              Pandas DataFrame with rooftop area density for each BUILDING_HEIGHT_INTERVAL for each building.
    """

    columns_rooftop_area_density = [
        f"{Settings.rooftop_area_density}_{i}"
        for i in range(int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL))
    ]

    return pd.DataFrame(plan_area_density.values.tolist(), columns=columns_rooftop_area_density)


def sky_view_factor(
    building_height: pd.Series, average_distance_between_buildings: pd.Series
) -> pd.Series:
    """Calculate the 2D sky view factor for each building.

    :param building_height:                     Building height field.
    :type building_height:                      pd.Series

    :param average_distance_between_buildings:  Average distance between the target building and all neighboring buildings.
    :type average_distance_between_buildings:   float

    :return:                                    pd.Series

    """

    return np.cos(np.arctan(building_height / (0.5 * average_distance_between_buildings)))


def standard_deviation_building_heights(
    building_id: pd.Series, building_height_neighbor: pd.Series
) -> pd.Series:
    """Standard deviation of building heights for each target building when considering themselves
    and those that are within their buffered area.

    :param building_id:                         Building ID field.
    :type building_id:                          pd.Series

    :param building_height_neighbor:            Building height field for neighbors
    :type building_height_neighbor:             pd.Series

    :return:                                    Series of building heights for each target building in the buffered area

    """

    df = pd.DataFrame(
        {Settings.id_field: building_id, Settings.neighbor_height_field: building_height_neighbor}
    )

    return df.groupby(Settings.id_field)[Settings.neighbor_height_field].std().fillna(0)


def standardize_column_names_df(input_shapefile_df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Standardize field names so use throughout code will be consistent throughout.

    :params input_shapefile_df:                     GeoDataFrame of from the input shapefile.
    :type input_shapefile_df:                       gpd.GeoDataFrame

    :return:                                        GeoDataFrame

    """

    # standardize field names from data to reference names in code
    input_shapefile_df.rename(
        columns={
            Settings.data_id_field_name: Settings.id_field,
            Settings.data_height_field_name: Settings.height_field,
            Settings.data_geometry_field_name: Settings.geometry_field,
        },
        inplace=True,
    )

    return input_shapefile_df.set_geometry(Settings.geometry_field)


def target_crs(input_shapefile_df: gpd.GeoDataFrame) -> CRS:
    """Extract coordinate reference system from geometry.

    :params input_shapefile_df:                     GeoDataFrame of from the input shapefile.
    :type input_shapefile_df:                       gpd.GeoDataFrame

    :return:                                        pyproj Coordinate Reference System (CRS) object

    """

    return input_shapefile_df.crs


def total_plan_area(total_plan_area_geometry: gpd.GeoSeries) -> pd.Series:
    """Calculate the total plan area for each building in a GeoPandas GeoSeries.

    :param geometry:                    Geometry for a series of buildings.
    :type geometry:                     gpd.GeoSeries

    :return:                            Pandas Series with total plan area for each building.

    """

    return total_plan_area_geometry.area


def total_plan_area_geometry(
    building_geometry: pd.Series, radius: int = Settings.RADIUS, cap_style: int = 3
) -> gpd.GeoSeries:
    """Calculate the geometry of the total plan area which is the buffer of the building for the desired radius and cap style.

    :param building_geometry:                       Geometry of the building.
    :type building_geometry:                        pd.Series

    :param radius:                                  The radius of the buffer.
                                                    100 (default, set in config.py)
    :type radius:                                   int

    :param cap_style:                               The shape of the buffer.
                                                    1 == Round
                                                    2 == Flat
                                                    3 == Square (default)

    :return:                                        pd.Series

    """

    return building_geometry.buffer(distance=radius, cap_style=cap_style)


def wall_angle_direction_length(geometry: gpd.GeoSeries) -> pd.DataFrame:
    """Calculate the wall angle, direction, and length for each building in a GeoPandas GeoSeries.

    :param geometry:                    Geometry for a series of buildings.
    :type geometry:                     gpd.GeoSeries

    :return:                            Pandas DataFrame with wall angle, direction, and length for each building.

    """

    wall_angle, wall_direction, wall_length = (
        [[] for x in range(geometry.size)],
        [[] for x in range(geometry.size)],
        [[] for x in range(geometry.size)],
    )

    for building in range(geometry.size):
        points_in_polygon = geometry.values[building].exterior.xy

        for index, item in enumerate(zip(points_in_polygon[0], points_in_polygon[1])):
            x, y = item

            # Store the first set of coordinates.
            if index == 0:
                x1, y1 = x, y

            else:
                x2, y2 = x, y

                wall_angle[building].append(np.degrees(np.arctan2(y2 - y1, x2 - x1)))

                # For each direction, the start degree (from counterclockwise) is included (<=) and the end degree is not included (<).
                if (
                    Settings.NORTHEAST_DEGREES
                    <= wall_angle[building][index - 1]
                    < Settings.NORTHWEST_DEGREES
                ):
                    wall_direction[building].append(Settings.west)
                elif (
                    Settings.SOUTHEAST_DEGREES_ARCTAN
                    <= wall_angle[building][index - 1]
                    < Settings.NORTHEAST_DEGREES
                ):
                    wall_direction[building].append(Settings.north)
                elif (
                    Settings.SOUTHWEST_DEGREES_ARCTAN
                    <= wall_angle[building][index - 1]
                    < Settings.SOUTHEAST_DEGREES_ARCTAN
                ):
                    wall_direction[building].append(Settings.east)
                else:
                    wall_direction[building].append(Settings.south)

                wall_length[building].append(np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2))

                # Reset start coordinates.
                x1, y1 = x, y

    return pd.concat(
        [
            pd.Series(wall_angle, name=Settings.wall_angle),
            pd.Series(wall_direction, name=Settings.wall_direction),
            pd.Series(wall_length, name=Settings.wall_length),
        ],
        axis=1,
    )


def wall_length(wall_angle_direction_length: pd.DataFrame) -> pd.DataFrame:
    """Calculate the wall angle, direction, and length for each building in a GeoPandas GeoSeries.

    :param wall_angle_direction_length:                Wall angle, direction, and length for a series of buildings.
    :type wall_angle_direction_length:                 pd.DataFrame

    :return:                                           Pandas DataFrame with wall area for each cardinal direction for each building.

    """

    wall_length_north, wall_length_east, wall_length_south, wall_length_west = (
        [0] * len(wall_angle_direction_length.index),
        [0] * len(wall_angle_direction_length.index),
        [0] * len(wall_angle_direction_length.index),
        [0] * len(wall_angle_direction_length.index),
    )

    for index, row in wall_angle_direction_length.iterrows():
        for j in range(len(row[Settings.wall_direction])):
            if row[Settings.wall_direction][j] == Settings.north:
                wall_length_north[index] += row[Settings.wall_length][j]
            elif row[Settings.wall_direction][j] == Settings.east:
                wall_length_east[index] += row[Settings.wall_length][j]
            elif row[Settings.wall_direction][j] == Settings.south:
                wall_length_south[index] += row[Settings.wall_length][j]
            else:
                wall_length_west[index] += row[Settings.wall_length][j]

    return pd.concat(
        [
            pd.Series(wall_length_north, name=Settings.wall_length_north),
            pd.Series(wall_length_east, name=Settings.wall_length_east),
            pd.Series(wall_length_south, name=Settings.wall_length_south),
            pd.Series(wall_length_west, name=Settings.wall_length_west),
        ],
        axis=1,
    )
