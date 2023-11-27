import os
import geopandas as gpd
import math
import numpy as np
import pandas as pd
from pyproj.crs import CRS
from hamilton.function_modifiers import extract_columns
import xarray as xr
import struct

from functools import partial
from rasterio.enums import MergeAlg
from geocube.api.core import make_geocube
from geocube.rasterize import rasterize_image

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


def aggregate_rasters(rasterize_parameters: xr.Dataset) -> xr.Dataset:
    """Divide each raster by the number of buildings in the cell to get the average parameter value for each cell.

    :param rasterize_parameters:                    Xr.Dataset with rasterized parameters summed at the defined resolution.
    :type rasterize_parameters:                     Xr.Dataset

    :return:                                        Xr.Dataset containing rasterized parameter values averaged at the defined resolution.
    """

    return (rasterize_parameters / rasterize_parameters["building_count"]).fillna(0)


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

    buildings_intersecting_plan_area[Settings.neighbor_volume_field] = (
        buildings_intersecting_plan_area[Settings.neighbor_height_field]
        * buildings_intersecting_plan_area[Settings.neighbor_area_field]
    )

    volume_sum = buildings_intersecting_plan_area.groupby(Settings.target_id_field)[
        Settings.neighbor_volume_field
    ].sum()
    area_sum = buildings_intersecting_plan_area.groupby(Settings.target_id_field)[
        Settings.neighbor_area_field
    ].sum()

    df = volume_sum / area_sum

    return pd.Series(df.values)


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


def average_distance_between_buildings(distance_between_buildings: pd.Series) -> pd.Series:
    """Calculate the average distance from the target building to all neighboring buildings.

    :param distance_between_buildings:          distance from the target building to each
                                                neighbor building.
    :type distance_between_buildings:           pd.Series

    :return:                                    float

    """

    df = distance_between_buildings.replace(0, np.nan)
    df = (
        df.groupby(Settings.neighbor_id_field)
        .mean()
        .reset_index()
        .replace(np.nan, Settings.DEFAULT_STREET_WIDTH)
        .rename(
            columns={
                Settings.distance_between_buildings: Settings.average_distance_between_buildings
            }
        )
    )
    return df[Settings.average_distance_between_buildings]


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
    wall_length: pd.DataFrame,
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
            Settings.wall_length_north: wall_length[Settings.wall_length_north],
            Settings.wall_length_east: wall_length[Settings.wall_length_east],
            Settings.wall_length_south: wall_length[Settings.wall_length_south],
            Settings.wall_length_west: wall_length[Settings.wall_length_west],
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

    neighbor_geometry = buildings_intersecting_plan_area[Settings.neighbor_geometry_field]

    return buildings_intersecting_plan_area.distance(neighbor_geometry).rename(
        Settings.distance_between_buildings
    )


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
def filter_height_range(standardize_column_names_df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Filter out any zero height buildings and reindex the data frame.  Extract the building_id,
    building_height, and geometry fields to nodes.

    :param standardize_column_names_df:             GeoDataFrame of the input shapefile with renamed columns.
    :type standardize_column_names_df:              gpd.GeoDataFrame

    :return:                                        GeoDataFrame

    """

    standardize_column_names_df.loc[
        standardize_column_names_df[Settings.height_field] > Settings.MAX_BUILDING_HEIGHT,
        Settings.height_field,
    ] = Settings.MAX_BUILDING_HEIGHT

    return standardize_column_names_df.loc[
        standardize_column_names_df[Settings.height_field] > 0
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
        Settings.frontal_area_north,
        Settings.frontal_area_east,
        Settings.frontal_area_south,
        Settings.frontal_area_west,
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
        Settings.frontal_area_index_north,
        Settings.frontal_area_index_east,
        Settings.frontal_area_index_south,
        Settings.frontal_area_index_west,
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
            Settings.data_id_field_name,
            Settings.data_height_field_name,
            Settings.data_geometry_field_name,
        ]
    ].set_geometry(Settings.data_geometry_field_name)

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
        building_surface_area.rename(Settings.building_surface_area),
        on="index_neighbor",
        how="left",
    )
    df = df.groupby(Settings.target_id_field)[Settings.building_surface_area].mean()

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
        Settings.macdonald_roughness_length_north,
        Settings.macdonald_roughness_length_east,
        Settings.macdonald_roughness_length_south,
        Settings.macdonald_roughness_length_west,
    ]

    return macdonald_roughness_length


def mean_building_height(buildings_intersecting_plan_area: gpd.GeoDataFrame) -> pd.Series:
    """Calculate the mean building height for all buildings within the target building's total plan area.

    :param buildings_intersecting_plan_area:    Geometry field for the neighboring buildings from the spatially
                                                joined data.
    :type buildings_intersecting_plan_area:     gpd.GeoDataFrame

    :return:                                    The mean building height for all buildings within the target building's plan area.
    """

    df = buildings_intersecting_plan_area.groupby(Settings.target_id_field)[
        Settings.neighbor_height_field
    ].mean()

    return pd.Series(df.values)


def merge_parameters(
    frontal_area_density: pd.DataFrame,
    plan_area_density: pd.DataFrame,
    rooftop_area_density: pd.DataFrame,
    plan_area_fraction: pd.Series,
    mean_building_height: pd.Series,
    standard_deviation_of_building_heights: pd.Series,
    area_weighted_mean_of_building_heights: pd.Series,
    building_surface_area_to_plan_area_ratio: pd.Series,
    frontal_area_index: pd.DataFrame,
    complete_aspect_ratio: pd.Series,
    height_to_width_ratio: pd.Series,
    sky_view_factor: pd.Series,
    grimmond_oke_roughness_length: pd.Series,
    grimmond_oke_displacement_height: pd.Series,
    raupach_roughness_length: pd.DataFrame,
    raupach_displacement_height: pd.DataFrame,
    macdonald_roughness_length: pd.DataFrame,
    macdonald_displacement_height: pd.Series,
    vertical_distribution_of_building_heights: pd.DataFrame,
    building_geometry: pd.Series,
    target_crs: CRS,
) -> gpd.GeoDataFrame:
    """Merge all parameters into one Pandas DataFrame.

    :param frontal_area_density:                       Frontal area density at each specified height increment and each cardinal direction.
    :type frontal_area_density:                        pd.DataFrame

    :param plan_area_density:                          Plan area density at each specified height increment.
    :type plan_area_density:                           pd.DataFrame

    :param rooftop_area_density:                       Rooftop area density at each specified height increment.
    :type rooftop_area_density:                        pd.DataFrame

    :param plan_area_fraction:                         Plan area fraction for each building.
    :type plan_area_fraction:                          pd.Series

    :param mean_building_height:                      Series of mean building height for all buildings within the target building's total plan area.
    :type mean_building_height:                       pd.Series

    :param standard_deviation_of_building_heights:     Series of standard deviation of building height for all buildings within the target building's
                                                       total plan area.
    :type standard_deviation_of_building_heights:      pd.Series

    :param area_weighted_mean_of_building_heights:     Series of area weighted mean building heights for each building.
    :type area_weighted_mean_of_building_heights:      pd.Series

    :param building_surface_area_to_plan_area_ratio:   Series of building surface area to plan area ratio for each building.
    :type building_surface_area_to_plan_area_ratio:    pd.Series

    :param frontal_area_index:                         Frontal area index for each building in each cardinal direction.
    :type frontal_area_index:                          pd.DataFrame

    :param complete_aspect_ratio:                      Complete aspect ratio for each building.
    :type complete_aspect_ratio:                       pd.Series

    :param height_to_width_ratio:                      Height-to-width ratio for each building.
    :type height_to_width_ratio:                       pd.Series

    :param sky_view_factor:                            Sky view factor for each building.
    :type sky_view_factor:                             pd.Series

    :param grimmond_oke_roughness_length:              Grimmond & Oke roughness length for each building.
    :type grimmond_oke_roughness_length:               pd.Series

    :param grimmond_oke_displacement_height:           Grimmond & Oke displacement height for each building.
    :type grimmond_oke_displacement_height:            pd.Series

    :param raupach_roughness_length:                   Raupach roughness length for each building in each cardinal direction.
    :type raupach_roughness_length:                    pd.DataFrame

    :param raupach_displacment_height:                 Raupach displacment height for each building in each cardinal direction.
    :type raupach_displacment_height:                  pd.DataFrame

    :param macdonald_roughness_length:                 Macdonald roughness_length for each building in each cardinal direction.
    :type macdonald_roughness_length:                  pd.DataFrame

    :param macdonald_displacement_height:              Macdonald displacement height for each building.
    :type macdonald_displacement_height:               pd.Series

    :param vertical_distribution_of_building_heights:  Distribution of building heights for each building ata each height increment.
    :type vertical_distribution_of_building_heights:   pd.DataFrame

    :param building_geometry:                          Geometry field for the buildings.
    :type building_geometry:                           pd.Series

    :param target_crs:                                 Coordinate reference system field of the parent geometry.
    :type target_crs:                                  CRS

    :return:                                           Pandas DataFrame with all parameters merged together.
    """

    df = pd.concat([frontal_area_density, plan_area_density, rooftop_area_density], axis=1)

    df[Settings.plan_area_fraction] = plan_area_fraction
    df[Settings.mean_building_height] = mean_building_height
    df[Settings.standard_deviation_of_building_heights] = standard_deviation_of_building_heights
    df[Settings.area_weighted_mean_of_building_heights] = area_weighted_mean_of_building_heights
    df[Settings.building_surface_area_to_plan_area_ratio] = building_surface_area_to_plan_area_ratio

    df = pd.concat([df, frontal_area_index], axis=1)

    df[Settings.complete_aspect_ratio] = complete_aspect_ratio
    df[Settings.height_to_width_ratio] = height_to_width_ratio
    df[Settings.sky_view_factor] = sky_view_factor
    df[Settings.grimmond_oke_roughness_length] = grimmond_oke_roughness_length
    df[Settings.grimmond_oke_displacement_height] = grimmond_oke_displacement_height

    df[Settings.raupach_roughness_length_north] = raupach_roughness_length[
        Settings.raupach_roughness_length_north
    ]
    df[Settings.raupach_displacement_height_north] = raupach_displacement_height[
        Settings.raupach_displacement_height_north
    ]
    df[Settings.raupach_roughness_length_east] = raupach_roughness_length[
        Settings.raupach_roughness_length_east
    ]
    df[Settings.raupach_displacement_height_east] = raupach_displacement_height[
        Settings.raupach_displacement_height_east
    ]
    df[Settings.raupach_roughness_length_south] = raupach_roughness_length[
        Settings.raupach_roughness_length_south
    ]
    df[Settings.raupach_displacement_height_south] = raupach_displacement_height[
        Settings.raupach_displacement_height_south
    ]
    df[Settings.raupach_roughness_length_west] = raupach_roughness_length[
        Settings.raupach_roughness_length_west
    ]
    df[Settings.raupach_displacement_height_west] = raupach_displacement_height[
        Settings.raupach_displacement_height_west
    ]

    df = pd.concat([df, macdonald_roughness_length], axis=1)

    df[Settings.macdonald_displacement_height] = macdonald_displacement_height

    df = pd.concat([df, vertical_distribution_of_building_heights], axis=1)

    df[Settings.geometry_field] = building_geometry

    gdf = gpd.GeoDataFrame(df, geometry=Settings.geometry_field, crs=target_crs)

    return gdf


def numpy_to_binary(raster_to_numpy: np.ndarray) -> bytes:
    """Turn the master numpy array containing all 132 aggregated parameters into a binary stream.

    :param raster_to_numpy:         132 level numpy array with each level being an aggregated parameter.
    :type raster_to_numpy:          np.ndarray

    :return:                        Binary object containing the parameter data.
    """

    master_out = []

    for i in range(len(raster_to_numpy)):
        master_outi = bytes()
        for j in range(len(raster_to_numpy[i])):
            for k in range(len(raster_to_numpy[i][j])):
                master_outi += struct.pack(">i", int(raster_to_numpy[i][j][k]))
        master_out.append(master_outi)

    master_out_final = bytes()

    for i in range(len(master_out)):
        master_out_final += master_out[i]

    return master_out_final


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
            Settings.east_west,
            Settings.north_south,
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


def raster_to_numpy(aggregate_rasters: xr.Dataset) -> np.ndarray:
    """Stack all 132 rasterized parameters into one numpy array for conversion to a binary file.

    :param aggregate_rasters:                 Dataset with rasterized parameter values averaged at the defined resolution.
    :type aggregate_rasters:                  xr.Dataset

    :return:                                  132 level numpy array with each level being an aggregated parameter.
    """

    parameters = list(aggregate_rasters.keys())
    parameters.remove("building_count")
    rows = aggregate_rasters.dims["y"]
    cols = aggregate_rasters.dims["x"]
    master = np.zeros((132, rows, cols), dtype=np.float32)
    i = 0
    for parameter in parameters:
        master[i] = aggregate_rasters[parameter].to_numpy()
        i += 1

    return master * 10**Settings.SCALING_FACTOR


def rasterize_parameters(merge_parameters: gpd.GeoDataFrame) -> xr.Dataset:
    """Rasterize parameters in preparation for conversion to numpy arrays. Raster will be of resolution Settings.DEFAULT_OUTPUT_RESOLUTION
    and each cell will be the sum of each parameter value within. By default all_touched is True so that every building that is within a cell is
    included in the sum.

    :param merge_parameters:             Pandas.GeoDataFrame with all selected urban parameters for each building.
    :type merge_parameters:              Pandas.GeoDataFrame

    :return:                             Xr.Dataset containing rasterization of selected urban parameters.
    """

    merge_parameters["building_count"] = 1
    measurements = merge_parameters.columns[merge_parameters.columns != Settings.geometry_field]
    resolution = Settings.DEFAULT_OUTPUT_RESOLUTION
    fill = Settings.DEFAULT_FILL_VALUE

    return make_geocube(
        vector_data=merge_parameters.rename(
            columns={Settings.geometry_field: "geometry"}
        ).set_geometry("geometry"),
        measurements=measurements,
        resolution=resolution,
        fill=fill,
        rasterize_function=partial(rasterize_image, all_touched=True, merge_alg=MergeAlg.add),
    )


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
        Settings.raupach_displacement_height_north,
        Settings.raupach_displacement_height_east,
        Settings.raupach_displacement_height_south,
        Settings.raupach_displacement_height_west,
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
        Settings.raupach_roughness_length_north,
        Settings.raupach_roughness_length_east,
        Settings.raupach_roughness_length_south,
        Settings.raupach_roughness_length_west,
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
        buildings_intersecting_plan_area.groupby(Settings.target_id_field)[
            Settings.neighbor_height_field
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

    return input_shapefile_df.set_geometry(Settings.geometry_field).crs


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
        f"{Settings.vertical_distribution_of_building_heights}_{i}"
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


def write_binary(numpy_to_binary: bytes, raster_to_numpy: np.ndarray) -> None:
    """Write the binary file that will be input to WRF.

    :param numpy_to_binary:                 Binary object containing the parameter data.
    :type numpy_to_binary:                  bytes

    :param raster_to_numpy:                 132 level numpy array with each level being an aggregated parameter.
    :type raster_to_numpy:                  np.ndarray
    """

    np.save("temporary.npy", numpy_to_binary)

    rows = raster_to_numpy.shape[1]
    cols = raster_to_numpy.shape[2]

    first_y_index = "{:05d}".format(1)
    second_y_index = "{:05d}".format(rows)

    first_x_index = "{:05d}".format(1)
    second_x_index = "{:05d}".format(cols)

    out_binary_name = (
        first_x_index + "-" + second_x_index + "." + first_y_index + "-" + second_y_index
    )

    with open("temporary.npy", "rb") as tile, open(out_binary_name, "wb") as tile2:
        tile2.write(tile.read()[20 * 4 :])

    os.remove("temporary.npy")


def write_index(raster_to_numpy: np.ndarray, building_geometry: pd.Series, target_crs: CRS) -> str:
    """Write the index file that will accompany the output binary file.

    :param raster_to_numpy:                 132 level numpy array with each level being an aggregated parameter.
    :type raster_to_numpy:                  np.ndarray

    :param building_geometry:               Geometry field for the buildings.
    :type building_geometry:                pd.Series

    :param target_crs:                      Coordinate reference system field of the parent geometry.
    :type target_crs:                       crs
    """

    dy = float(Settings.DEFAULT_OUTPUT_RESOLUTION[0])
    dx = float(Settings.DEFAULT_OUTPUT_RESOLUTION[1])

    building_geometry = gpd.GeoSeries(building_geometry, crs=target_crs)

    building_geometry_project = building_geometry.to_crs(crs=4326)

    bounds = building_geometry_project.total_bounds

    known_lat = bounds[1]
    known_lon = bounds[0]

    stdlon = (bounds[0] + bounds[2]) / 2

    tile_x = raster_to_numpy.shape[2]
    tile_y = raster_to_numpy.shape[1]

    scale_factor = 10**-Settings.SCALING_FACTOR

    with open("index", "w") as index:
        index.writelines(
            [
                "type=continuous\n",
                "  projection=albers_nad83\n",
                "  missing_value=-999900.\n",
                "  dy=" + str(dy) + "\n",
                "  dx=" + str(dx) + "\n",
                "  known_x=1\n",
                "  known_y=1\n",
                "  known_lat=" + str(known_lat) + "\n",
                "  known_lon=" + str(known_lon) + "\n",
                "  truelat1=45.5\n",
                "  truelat2=29.5\n",
                "  stdlon=" + str(stdlon) + "\n",
                "  wordsize=4\n",
                "  endian=big\n",
                "  signed=no\n",
                "  tile_x=" + str(tile_x) + "\n",
                "  tile_y=" + str(tile_y) + "\n",
                "  tile_z=132\n",
                '  units="dimensionless"\n',
                "  scale_factor=" + str(scale_factor) + "\n",
                '  description="Urban_Parameters"\n',
            ]
        )
