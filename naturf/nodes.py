import geopandas as gpd
import math
import numpy as np
import pandas as pd
from pyproj.crs import CRS
from hamilton.function_modifiers import extract_columns

from .config import Settings


def area_weighted_mean_of_building_heights(
    buildings_intersecting_plan_area: gpd.GeoDataFrame,
) -> pd.Series:
    """Calculate the area weighted mean of building heights for each target building in a GeoPandas GeoDataFrame.
    The entire area of buildings considered to be neighbors are included in the calculation.

    :param buildings_intersecting_plan_area:    Geometry field for the neighboring buildings from the spatially
                                                joined data.
    :type buildings_intersecting_plan_area:     gpd.GeoDataFrame

    :return:                                    The area weighted mean of building heights for all buildings within the target
                                                building's plan area.
    """

    buildings_intersecting_plan_area[Settings.NEIGHBOR_VOLUME_FIELD] = (
        buildings_intersecting_plan_area[Settings.NEIGHBOR_HEIGHT_FIELD]
        * buildings_intersecting_plan_area[Settings.NEIGHBOR_AREA_FIELD]
    )

    volume_sum = buildings_intersecting_plan_area.groupby(Settings.TARGET_ID_FIELD)[
        Settings.NEIGHBOR_VOLUME_FIELD
    ].sum()
    area_sum = buildings_intersecting_plan_area.groupby(Settings.TARGET_ID_FIELD)[
        Settings.NEIGHBOR_AREA_FIELD
    ].sum()

    df = volume_sum / area_sum

    return pd.Series(df.values)


def average_distance_between_buildings(distance_between_buildings: pd.Series) -> pd.Series:
    """Calculate the average distance from the target building to all neighboring buildings.

    :param distance_between_buildings:          distance from the target building to each
                                                neighbor building.
    :type distance_between_buildings:           pd.Series

    :return:                                    float

    """

    df = distance_between_buildings.replace(0, np.nan)
    df = (
        df.groupby(Settings.NEIGHBOR_ID_FIELD)
        .mean()
        .reset_index()
        .replace(np.nan, Settings.DEFAULT_STREET_WIDTH)
        .rename(
            columns={
                Settings.DISTANCE_BETWEEN_BUILDINGS: Settings.AVERAGE_DISTANCE_BETWEEN_BUILDINGS
            }
        )
    )
    return df[Settings.AVERAGE_DISTANCE_BETWEEN_BUILDINGS]


def building_area(building_geometry: pd.Series) -> pd.Series:
    """Calculate the area of the building geometry.

    :param building_geometry:                       Building Geometry.
    :type building_geometry:                        pd.Series

    :return:                                        pd.Series

    """

    return building_geometry.area


def buildings_intersecting_plan_area(
    building_id: pd.Series,
    building_height: pd.Series,
    building_geometry: pd.Series,
    building_area: pd.Series,
    total_plan_area_geometry: pd.Series,
    wall_length: pd.DataFrame,
    target_crs: CRS,
    join_type: str = "left",
    join_predicate: str = "intersects",
    join_lsuffix: str = Settings.TARGET,
    join_rsuffix: str = Settings.NEIGHBOR,
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
            Settings.ID_FIELD: building_id,
            Settings.HEIGHT_FIELD: building_height,
            Settings.AREA_FIELD: building_area,
            Settings.GEOMETRY_FIELD: building_geometry,
            Settings.BUFFERED_FIELD: total_plan_area_geometry,
            Settings.WALL_LENGTH_NORTH: wall_length[Settings.WALL_LENGTH_NORTH],
            Settings.WALL_LENGTH_EAST: wall_length[Settings.WALL_LENGTH_EAST],
            Settings.WALL_LENGTH_SOUTH: wall_length[Settings.WALL_LENGTH_SOUTH],
            Settings.WALL_LENGTH_WEST: wall_length[Settings.WALL_LENGTH_WEST],
        }
    )

    # Create left and right GeoDataFrames.
    left_gdf = gpd.GeoDataFrame(df, geometry=Settings.BUFFERED_FIELD, crs=target_crs)
    right_gdf = gpd.GeoDataFrame(df, geometry=Settings.GEOMETRY_FIELD, crs=target_crs)

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
        xdf.set_index(f"{Settings.ID_FIELD}_{join_rsuffix}")
        .join(
            right_gdf.set_index(Settings.ID_FIELD)[Settings.GEOMETRY_FIELD].rename(
                Settings.NEIGHBOR_GEOMETRY_FIELD
            )
        )
        .sort_index()
    )

    return gpd.GeoDataFrame(xdf).set_geometry(Settings.GEOMETRY_FIELD)


def building_plan_area(
    buildings_intersecting_plan_area: gpd.GeoDataFrame,
    join_predicate: str = "intersection",
    join_rsuffix: str = Settings.NEIGHBOR,
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
            buildings_intersecting_plan_area[Settings.TARGET_ID_FIELD] == target_building_id
        ].reset_index()

        # Create GeoDataFrames with building and neighbor info.
        target_gdf = (
            target_building_gdf[[Settings.TARGET_ID_FIELD, Settings.TARGET_BUFFERED_FIELD]]
            .set_geometry(Settings.TARGET_BUFFERED_FIELD)
            .drop_duplicates()
        )
        neighbor_gdf = target_building_gdf[
            [f"index_{join_rsuffix}", Settings.NEIGHBOR_GEOMETRY_FIELD]
        ].set_geometry(Settings.NEIGHBOR_GEOMETRY_FIELD)

        # Create a new GeoDataFrame with the area of intersection.
        intersection_gdf = gpd.overlay(
            target_gdf, neighbor_gdf, how=join_predicate, keep_geom_type=False
        )

        # Sum up the area of intersection and add to the output list.
        building_plan_area.append(intersection_gdf[Settings.DATA_GEOMETRY_FIELD_NAME].area.sum())

        index += 1

    return pd.Series(building_plan_area)


def building_surface_area(
    wall_length: pd.DataFrame, building_height: pd.Series, building_area: pd.Series
) -> pd.Series:
    """Calculate the building surface area for each building in a Panda Series. In naturf, the building footprint area is the
    same as the roof area.

    :param wall_length:                   Wall length in each cardinal direction for each building.
    :type wall_length:                    pd.DataFrame

    :param building_height:               Building height for each building.
    :type building_height:                pd.Series

    :param building_area:                 Building area field.
    :type building_area:                  pd.Series

    :return:                              Panda Series with building surface area.
    """

    wall_area = wall_length.mul(building_height, axis=0).sum(axis=1)

    return wall_area + building_area


def building_surface_area_to_plan_area_ratio(
    building_surface_area: pd.Series, total_plan_area: pd.Series
) -> pd.Series:
    """Calculate the building surface area to plan area ratio for each building in a Pandas Series. In naturf, the building footprint area is the
    same as the roof area.

    :param building_surface_area:         Building surface area for each building.
    :type building_surface_area:          pd.Series

    :param total_plan_area:               Total plan area for each building.
    :type total_plan_area:                pd.Series

    :return:                              Panda Series with building surface area to plan area ratio.
    """

    return building_surface_area / total_plan_area


def complete_aspect_ratio(
    building_surface_area: pd.Series, total_plan_area: pd.Series, building_plan_area: pd.Series
) -> pd.Series:
    """Calculate the complete aspect ratio for each building in a Pandas Series. In naturf, the building footprint area is the
    same as the roof area, and the exposed ground is the difference between total plan area and building plan area.

    :param building_surface_area:         Building surface area for each building.
    :type building_surface_area:          pd.Series

    :param total_plan_area:               Total plan area for each building.
    :type total_plan_area:                pd.Series

    :param building_plan_area:            Building plan area for each building.
    :type building_plan_area:             pd.Series

    :return:                              Panda Series with complete aspect ratio.
    """

    exposed_ground = total_plan_area - building_plan_area

    return (building_surface_area + exposed_ground) / total_plan_area


def distance_between_buildings(buildings_intersecting_plan_area: gpd.GeoDataFrame) -> pd.Series:
    """Calculate the distance between each building and its neighbor as defined in buildings_intersecting_plan_area.

    :param buildings_intersecting_plan_area:    Geometry field for the neighboring buildings from the spatially
                                                joined data.
    :type buildings_intersecting_plan_area:     gpd.GeoDataFrame

    :return:                                    The distance between each building and its neighbors in a Pandas Series.
    """

    neighbor_geometry = buildings_intersecting_plan_area[Settings.NEIGHBOR_GEOMETRY_FIELD]

    return buildings_intersecting_plan_area.distance(neighbor_geometry).rename(
        Settings.DISTANCE_BETWEEN_BUILDINGS
    )


@extract_columns(*[Settings.ID_FIELD, Settings.HEIGHT_FIELD, Settings.GEOMETRY_FIELD])
def filter_height_range(standardize_column_names_df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Filter out any zero height buildings and reindex the data frame.  Extract the building_id,
    building_height, and geometry fields to nodes.

    :param standardize_column_names_df:             GeoDataFrame of the input shapefile with renamed columns.
    :type standardize_column_names_df:              gpd.GeoDataFrame

    :return:                                        GeoDataFrame

    """

    standardize_column_names_df.loc[
        standardize_column_names_df[Settings.HEIGHT_FIELD] > Settings.MAX_BUILDING_HEIGHT,
        Settings.HEIGHT_FIELD,
    ] = Settings.MAX_BUILDING_HEIGHT

    return standardize_column_names_df.loc[
        standardize_column_names_df[Settings.HEIGHT_FIELD] > 0
    ].reset_index(drop=True)


def frontal_area(frontal_length: pd.DataFrame, building_height: pd.Series) -> pd.DataFrame:
    """Calculate the frontal area for each building in a Pandas DataFrame in each cardinal direction.

    :param frontal_length:                Frontal length in each cardinal direction for each building.
    :type frontal_length:                 pd.DataFrame

    :param building_height:               Building height for each building.
    :type building_height:                pd.Series

    :return:                              Pandas DataFrame with frontal area in each cardinal direction.
    """

    frontal_area = frontal_length.mul(building_height, axis=0)

    frontal_area.columns = [
        Settings.FRONTAL_AREA_NORTH,
        Settings.FRONTAL_AREA_EAST,
        Settings.FRONTAL_AREA_SOUTH,
        Settings.FRONTAL_AREA_WEST,
    ]

    return frontal_area


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
                    building_frontal_length[Settings.FRONTAL_LENGTH_NORTH]
                    * Settings.BUILDING_HEIGHT_INTERVAL
                    / total_plan_area[building]
                )
                frontal_area_east[building][
                    int(building_height_index / Settings.BUILDING_HEIGHT_INTERVAL)
                ] = (
                    building_frontal_length[Settings.FRONTAL_LENGTH_EAST]
                    * Settings.BUILDING_HEIGHT_INTERVAL
                    / total_plan_area[building]
                )
                frontal_area_south[building][
                    int(building_height_index / Settings.BUILDING_HEIGHT_INTERVAL)
                ] = (
                    building_frontal_length[Settings.FRONTAL_LENGTH_SOUTH]
                    * Settings.BUILDING_HEIGHT_INTERVAL
                    / total_plan_area[building]
                )
                frontal_area_west[building][
                    int(building_height_index / Settings.BUILDING_HEIGHT_INTERVAL)
                ] = (
                    building_frontal_length[Settings.FRONTAL_LENGTH_WEST]
                    * Settings.BUILDING_HEIGHT_INTERVAL
                    / total_plan_area[building]
                )
            else:
                frontal_area_north[building][
                    int(building_height_index / Settings.BUILDING_HEIGHT_INTERVAL)
                ] = (
                    building_frontal_length[Settings.FRONTAL_LENGTH_NORTH]
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
                    building_frontal_length[Settings.FRONTAL_LENGTH_EAST]
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
                    building_frontal_length[Settings.FRONTAL_LENGTH_SOUTH]
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
                    building_frontal_length[Settings.FRONTAL_LENGTH_WEST]
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
            f"{Settings.FRONTAL_AREA_NORTH}_{i}"
            for i in range(int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL))
        ],
        [
            f"{Settings.FRONTAL_AREA_EAST}_{i}"
            for i in range(int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL))
        ],
        [
            f"{Settings.FRONTAL_AREA_SOUTH}_{i}"
            for i in range(int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL))
        ],
        [
            f"{Settings.FRONTAL_AREA_WEST}_{i}"
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


def frontal_area_index(frontal_area: pd.DataFrame, total_plan_area: pd.Series) -> pd.DataFrame:
    """Calculate the frontal area index for each building in a Pandas DataFrame in each cardinal direction.

    :param frontal_area:                  Frontal area in each cardinal direction for each building.
    :type frontal_area:                   pd.DataFrame

    :param total_plan_area:               Total plan area for each building.
    :type total_plan_area:                pd.Series

    :return:                              Pandas DataFrame with frontal area index in each cardinal direction.
    """

    frontal_area_index = frontal_area.div(total_plan_area, axis=0)
    frontal_area_index.columns = [
        Settings.FRONTAL_AREA_INDEX_NORTH,
        Settings.FRONTAL_AREA_INDEX_EAST,
        Settings.FRONTAL_AREA_INDEX_SOUTH,
        Settings.FRONTAL_AREA_INDEX_WEST,
    ]

    return frontal_area_index


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
            buildings_intersecting_plan_area[Settings.TARGET_ID_FIELD] == target_building_id
        ].reset_index()

        # Sum frontal length for each cardinal direction
        frontal_length_north[index] = target_building_gdf[
            f"{Settings.WALL_LENGTH_NORTH}_{Settings.NEIGHBOR}"
        ].sum()
        frontal_length_east[index] = target_building_gdf[
            f"{Settings.WALL_LENGTH_EAST}_{Settings.NEIGHBOR}"
        ].sum()
        frontal_length_south[index] = target_building_gdf[
            f"{Settings.WALL_LENGTH_SOUTH}_{Settings.NEIGHBOR}"
        ].sum()
        frontal_length_west[index] = target_building_gdf[
            f"{Settings.WALL_LENGTH_WEST}_{Settings.NEIGHBOR}"
        ].sum()

        index += 1

    return pd.concat(
        [
            pd.Series(frontal_length_north, name=Settings.FRONTAL_LENGTH_NORTH),
            pd.Series(frontal_length_east, name=Settings.FRONTAL_LENGTH_EAST),
            pd.Series(frontal_length_south, name=Settings.FRONTAL_LENGTH_SOUTH),
            pd.Series(frontal_length_west, name=Settings.FRONTAL_LENGTH_WEST),
        ],
        axis=1,
    )


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
    mean_building_height: pd.Series, average_distance_between_buildings: pd.Series
) -> pd.Series:
    """Calculate the height to width ratio for each building.

    :param mean_building_height:           Series of mean building height for all buildings within the target building's plan area
    :type mean_building_height:            pd.Series

    :param average_distance_between_buildings: Series of average distance from each building to all neighboring buildings
    :type average_distance_between_buildings:  pd.Series

    :return:                                   pd.Series

    """

    return mean_building_height / average_distance_between_buildings


def input_shapefile_df(input_shapefile: str) -> gpd.GeoDataFrame:
    """Import shapefile to GeoDataFrame using only desired columns.

    :params input_shapefile:                        Full path with file name and extension to the input shapefile.
    :type input_shapefile:                          str

    :return:                                        GeoDataFrame

    """

    gdf = gpd.read_file(input_shapefile)[
        [
            Settings.DATA_ID_FIELD_NAME,
            Settings.DATA_HEIGHT_FIELD_NAME,
            Settings.DATA_GEOMETRY_FIELD_NAME,
        ]
    ].set_geometry(Settings.DATA_GEOMETRY_FIELD_NAME)

    return gdf


def lot_area(
    buildings_intersecting_plan_area: gpd.GeoDataFrame, building_surface_area: pd.Series
) -> pd.Series:
    """Calculate the lot area for each building in a Panda Series. Lot area is the total surface area of all buildings
    within a given building's plan area divided by the number of buildings in the plan area."

    :param buildings_intersecting_plan_area:    Geometry field for the neighboring buildings from the spatially
                                                joined data.
    :type buildings_intersecting_plan_area:     gpd.GeoDataFrame

    :param building_surface_area:               Building surface area for each building.
    :type building_surface_area:                pd.Series

    :return:                                    Panda Series of lot area for each building.
    """

    df = buildings_intersecting_plan_area.join(
        building_surface_area.rename(Settings.BUILDING_SURFACE_AREA),
        on=f"index_{Settings.NEIGHBOR}",
        how="left",
    )
    df = df.groupby(Settings.TARGET_ID_FIELD)[Settings.BUILDING_SURFACE_AREA].mean()

    return pd.Series(df.values)


def macdonald_displacement_height(
    building_height: pd.Series, plan_area_fraction: pd.Series
) -> pd.Series:
    """Calculate the Macdonald et al. displacement height for each building in a Pandas Series.

    :param building_height:               Building height for each building.
    :type building_height:                pd.Series

    :param plan_area_fraction:            Plan area fraction for each building.
    :type plan_area_fraction:             pd.Series
    """

    alpha_coefficient = Settings.ALPHACOEFFICIENT

    plan_area_minus_one = plan_area_fraction - 1

    alpha_exponent = alpha_coefficient ** (-plan_area_fraction)

    right_side = 1 + alpha_exponent * plan_area_minus_one

    return right_side * building_height


def macdonald_roughness_length(
    building_height: pd.Series,
    macdonald_displacement_height: pd.Series,
    frontal_area: pd.DataFrame,
    lot_area: pd.Series,
) -> pd.DataFrame:
    """Calculate the Macdonald et al. roughness length for each building in a Pandas Series.

    :param building_height:               Building height for each building.
    :type building_height:                pd.Series

    :param macdonald_displacement_height: Macdonald displacement height for each building.
    :type macdonald_displacement_height:  pd.Series

    :param frontal_area:                  Frontal area  for each building in each cardinal direction.
    :type frontal_area:                   pd.DataFrame

    :param lot_area:                      Lot area for each building.
    :type lot_area:                       pd.Series

    :return:                              Panda Series with Macdonald roughness length for each building in each cardinal direction.
    """

    obstacle_drag_coefficient = Settings.OBSTACLEDRAGCOEFFICIENT
    von_karman_constant = Settings.VONKARMANCONSTANT
    beta_coefficient = Settings.BETACOEFFICIENT

    one_minus_height_ratio = 1 - macdonald_displacement_height / building_height

    drag_over_von_karman = obstacle_drag_coefficient / von_karman_constant**2

    frontal_divided_by_lot = frontal_area.div(lot_area, axis=0)

    inside_exponential = -frontal_divided_by_lot.mul(
        0.5 * beta_coefficient * drag_over_von_karman * one_minus_height_ratio, axis=0
    ) ** (-0.5)

    exponential = np.exp(inside_exponential)

    right_side = exponential.mul(one_minus_height_ratio, axis=0)

    macdonald_roughness_length = right_side.mul(building_height, axis=0)

    macdonald_roughness_length.columns = [
        Settings.MACDONALD_ROUGHNESS_LENGTH_NORTH,
        Settings.MACDONALD_ROUGHNESS_LENGTH_EAST,
        Settings.MACDONALD_ROUGHNESS_LENGTH_SOUTH,
        Settings.MACDONALD_ROUGHNESS_LENGTH_WEST,
    ]

    return macdonald_roughness_length


def mean_building_height(buildings_intersecting_plan_area: gpd.GeoDataFrame) -> pd.Series:
    """Calculate the mean building height for all buildings within the target building's total plan area.

    :param buildings_intersecting_plan_area:    Geometry field for the neighboring buildings from the spatially
                                                joined data.
    :type buildings_intersecting_plan_area:     gpd.GeoDataFrame

    :return:                                    The mean building height for all buildings within the target building's plan area.
    """

    df = buildings_intersecting_plan_area.groupby(Settings.TARGET_ID_FIELD)[
        Settings.NEIGHBOR_HEIGHT_FIELD
    ].mean()

    return pd.Series(df.values)


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
        f"{Settings.PLAN_AREA_DENSITY}_{i}"
        for i in range(int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL))
    ]
    return pd.DataFrame(plan_area_density, columns=columns_plan_area_density)


def plan_area_fraction(building_plan_area: pd.Series, total_plan_area: pd.Series) -> pd.Series:
    """Calculate the plan area fraction for each building in a Pandas Series. Plan area fraction is the building plan area at ground level
    for each building divided by the total plan area.

    :param building_plan_area:            Building plan area for each building.
    :type building_plan_area:             pd.Series

    :param total_plan_area:               Total plan area for each building.
    :type total_plan_area:                pd.Series

    :return:                              Pandas Series with plan area fraction for each building.
    """

    return building_plan_area / total_plan_area


def raupach_displacement_height(
    building_height: pd.Series, frontal_area_index: pd.DataFrame
) -> pd.DataFrame:
    """Calculate the Raupach displacement height for each building in each cardinal direction in a Panda Series. Default values for constants are set
    in the config file.

    :param building_height:               Building height for each building.
    :type building_height:                pd.Series

    :param frontal_area_index:            Frontal area index for each building in each cardinal direction.
    :type frontal_area_index:             pd.DataFrame

    :return:                              Pandas DataFrame with Raupach displacement height in each cardinal direction.
    """

    constant_75 = Settings.CONSTANT_75
    capital_lambda = frontal_area_index.mul(2, axis=0)

    sqrt_constant_lambda = np.sqrt(capital_lambda.mul(constant_75, axis=0))
    numerator = 1 - np.exp(-sqrt_constant_lambda)

    raupach_displacement_height = (1 - numerator / sqrt_constant_lambda).mul(
        building_height, axis=0
    )

    raupach_displacement_height.columns = [
        Settings.RAUPACH_DISPLACEMENT_HEIGHT_NORTH,
        Settings.RAUPACH_DISPLACEMENT_HEIGHT_EAST,
        Settings.RAUPACH_DISPLACEMENT_HEIGHT_SOUTH,
        Settings.RAUPACH_DISPLACEMENT_HEIGHT_WEST,
    ]

    return raupach_displacement_height


def raupach_roughness_length(
    building_height: pd.Series,
    frontal_area_index: pd.DataFrame,
    raupach_displacement_height: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate the Raupach roughness length for each building in each cardinal direction in a Panda Series. Default values for constants are set
    in the config file.

    :param building_height:               Building height for each building.
    :type building_height:                pd.Series

    :param frontal_area_index:            Frontal area index for each building in each cardinal direction.
    :type frontal_area_index:             pd.DataFrame

    :param raupach_displacment_height:    Raupach displacment height for each building in each cardinal direction.
    :type raupach_displacment_height:     pd.DataFrame

    :return:                              Pandas DataFrame with Raupach roughness length in each cardinal direction.
    """

    cols = [
        Settings.RAUPACH_ROUGHNESS_LENGTH_NORTH,
        Settings.RAUPACH_ROUGHNESS_LENGTH_EAST,
        Settings.RAUPACH_ROUGHNESS_LENGTH_SOUTH,
        Settings.RAUPACH_ROUGHNESS_LENGTH_WEST,
    ]

    cols_fai = frontal_area_index.columns
    cols_rdh = raupach_displacement_height.columns

    von_karman_constant = Settings.VONKARMANCONSTANT
    drag_coefficient_03 = Settings.DRAGCOEFFICIENT_03
    drag_coefficient_0003 = Settings.DRAGCOEFFICIENT_0003
    psi_h = Settings.PSI_H

    frontal_area_index.columns = cols
    raupach_displacement_height.columns = cols

    denominator = np.sqrt(drag_coefficient_0003 + drag_coefficient_03 * frontal_area_index)

    one_minus_displacement_height = 1 - raupach_displacement_height.div(building_height, axis=0)

    exponential = np.exp(-von_karman_constant / denominator - psi_h)

    raupach_roughness_length = exponential.mul(one_minus_displacement_height, axis=0).mul(
        building_height, axis=0
    )

    frontal_area_index.columns = cols_fai
    raupach_displacement_height.columns = cols_rdh

    return raupach_roughness_length


def rooftop_area_density(plan_area_density: pd.DataFrame) -> pd.DataFrame:
    """Calculate the rooftop area density for each building in a Pandas DataFrame. Rooftop area density is the roof area
    of all buildings within the total plan area  at a specified height increment divided by the total plan area. naturf
    projects building footprints vertically to the building height, meaning that rooftop area density is equal to the plan area
    density.

    :param plan_area_density:            Plan area density at each specified height increment.
    :type plan_area_density:             pd.DataFrame

    :return:                             Pandas DataFrame with rooftop area density for each BUILDING_HEIGHT_INTERVAL for each building.
    """

    columns_rooftop_area_density = [
        f"{Settings.ROOFTOP_AREA_DENSITY}_{i}"
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


def standard_deviation_of_building_heights(
    buildings_intersecting_plan_area: gpd.GeoDataFrame,
) -> pd.Series:
    """Calculate the standard deviation of building heights for all buildings within the target building's total plan area.

    :param buildings_intersecting_plan_area:    Geometry field for the neighboring buildings from the spatially
                                                joined data.
    :type buildings_intersecting_plan_area:     gpd.GeoDataFrame

    :return:                                    The standard deviation of building heights for all buildings within the target building's plan area.
    """

    df = (
        buildings_intersecting_plan_area.groupby(Settings.TARGET_ID_FIELD)[
            Settings.NEIGHBOR_HEIGHT_FIELD
        ]
        .std()
        .fillna(0)
    )

    return pd.Series(df.values)


def standardize_column_names_df(input_shapefile_df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Standardize field names so use throughout code will be consistent throughout.

    :params input_shapefile_df:                     GeoDataFrame of from the input shapefile.
    :type input_shapefile_df:                       gpd.GeoDataFrame

    :return:                                        GeoDataFrame

    """

    # standardize field names from data to reference names in code
    input_shapefile_df.rename(
        columns={
            Settings.DATA_ID_FIELD_NAME: Settings.ID_FIELD,
            Settings.DATA_HEIGHT_FIELD_NAME: Settings.HEIGHT_FIELD,
            Settings.DATA_GEOMETRY_FIELD_NAME: Settings.GEOMETRY_FIELD,
        },
        inplace=True,
    )

    return input_shapefile_df.set_geometry(Settings.GEOMETRY_FIELD)


def target_crs(input_shapefile_df: gpd.GeoDataFrame) -> CRS:
    """Extract coordinate reference system from geometry.

    :params input_shapefile_df:                     GeoDataFrame of from the input shapefile.
    :type input_shapefile_df:                       gpd.GeoDataFrame

    :return:                                        pyproj Coordinate Reference System (CRS) object

    """

    return input_shapefile_df.set_geometry(Settings.GEOMETRY_FIELD).crs


def total_plan_area(total_plan_area_geometry: gpd.GeoSeries) -> pd.Series:
    """Calculate the total plan area for each building in a GeoPandas GeoSeries.

    :param geometry:                    Geometry for a series of buildings.
    :type geometry:                     gpd.GeoSeries

    :return:                            Pandas Series with total plan area for each building.

    """

    return total_plan_area_geometry.area


def total_plan_area_geometry(
    building_geometry: pd.Series, radius: int = Settings.RADIUS, cap_style: int = Settings.CAP_STYLE
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


def vertical_distribution_of_building_heights(building_height: pd.Series) -> pd.DataFrame:
    """Represent the location of buildings at 5m increments from ground level to 75m unless otherwise specified. If is within a
    given height bin, it will be given a 1 and it will be given a 0 otherwise."

    :param building_height:               Building height for each building.
    :type building_height:                pd.Series

    :return:                              Pandas DataFrame with the distribution of building heights at each
                                          BUILDING_HEIGHT_INTERVAL for each building.
    """

    rows, cols = (
        len(building_height.index),
        int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL),
    )
    vertical_distribution_of_building_heights = [[0 for i in range(cols)] for j in range(rows)]

    for building in range(building_height.size):
        building_height_counter = 0

        while building_height_counter < building_height[building]:
            vertical_distribution_of_building_heights[building][
                int(building_height_counter / Settings.BUILDING_HEIGHT_INTERVAL)
            ] = 1.0
            building_height_counter += Settings.BUILDING_HEIGHT_INTERVAL

    columns_vertical_distribution_of_building_heights = [
        f"{Settings.VERTICAL_DISTRIBUTION_OF_BUILDING_HEIGHTS}_{i}"
        for i in range(int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL))
    ]

    return pd.DataFrame(
        vertical_distribution_of_building_heights,
        columns=columns_vertical_distribution_of_building_heights,
    )


def wall_angle_direction_length(building_geometry: pd.Series) -> pd.DataFrame:
    """Calculate the wall angle, direction, and length for each building in a GeoPandas GeoSeries.

    :param geometry:                    Geometry for a series of buildings.
    :type geometry:                     pd.Series

    :return:                            Pandas DataFrame with wall angle, direction, and length for each building.

    """

    wall_angle, wall_direction, wall_length = (
        [[] for x in range(building_geometry.size)],
        [[] for x in range(building_geometry.size)],
        [[] for x in range(building_geometry.size)],
    )

    for building in range(building_geometry.size):
        points_in_polygon = building_geometry.values[building].exterior.xy

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
                    wall_direction[building].append(Settings.WEST)
                elif (
                    Settings.SOUTHEAST_DEGREES_ARCTAN
                    <= wall_angle[building][index - 1]
                    < Settings.NORTHEAST_DEGREES
                ):
                    wall_direction[building].append(Settings.NORTH)
                elif (
                    Settings.SOUTHWEST_DEGREES_ARCTAN
                    <= wall_angle[building][index - 1]
                    < Settings.SOUTHEAST_DEGREES_ARCTAN
                ):
                    wall_direction[building].append(Settings.EAST)
                else:
                    wall_direction[building].append(Settings.SOUTH)

                wall_length[building].append(np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2))

                # Reset start coordinates.
                x1, y1 = x, y

    return pd.concat(
        [
            pd.Series(wall_angle, name=Settings.WALL_ANGLE),
            pd.Series(wall_direction, name=Settings.WALL_DIRECTION),
            pd.Series(wall_length, name=Settings.WALL_LENGTH),
        ],
        axis=1,
    )


def wall_length(wall_angle_direction_length: pd.DataFrame) -> pd.DataFrame:
    """Calculate the wall length for each building in a GeoPandas GeoSeries.

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
        for j in range(len(row[Settings.WALL_DIRECTION])):
            if row[Settings.WALL_DIRECTION][j] == Settings.NORTH:
                wall_length_north[index] += row[Settings.WALL_LENGTH][j]
            elif row[Settings.WALL_DIRECTION][j] == Settings.EAST:
                wall_length_east[index] += row[Settings.WALL_LENGTH][j]
            elif row[Settings.WALL_DIRECTION][j] == Settings.SOUTH:
                wall_length_south[index] += row[Settings.WALL_LENGTH][j]
            else:
                wall_length_west[index] += row[Settings.WALL_LENGTH][j]

    return pd.concat(
        [
            pd.Series(wall_length_north, name=Settings.WALL_LENGTH_NORTH),
            pd.Series(wall_length_east, name=Settings.WALL_LENGTH_EAST),
            pd.Series(wall_length_south, name=Settings.WALL_LENGTH_SOUTH),
            pd.Series(wall_length_west, name=Settings.WALL_LENGTH_WEST),
        ],
        axis=1,
    )
