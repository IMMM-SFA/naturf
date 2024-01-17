import geopandas as gpd
import numpy as np
import os
import pandas as pd
from pyproj.crs import CRS
import struct
import xarray as xr

from functools import partial
from rasterio.enums import MergeAlg
from geocube.api.core import make_geocube
from geocube.rasterize import rasterize_image

from .config import Settings


def aggregate_rasters(rasterize_parameters: xr.Dataset) -> xr.Dataset:
    """Divide each raster by the number of buildings in the cell to get the average parameter value for each cell.

    :param rasterize_parameters:                    Xr.Dataset with rasterized parameters summed at the defined resolution.
    :type rasterize_parameters:                     Xr.Dataset

    :return:                                        Xr.Dataset containing rasterized parameter values averaged at the defined resolution.
    """

    return (rasterize_parameters / rasterize_parameters["building_count"]).fillna(0)


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

    df[Settings.PLAN_AREA_FRACTION] = plan_area_fraction
    df[Settings.MEAN_BUILDING_HEIGHT] = mean_building_height
    df[Settings.STANDARD_DEVIATION_OF_BUILDING_HEIGHTS] = standard_deviation_of_building_heights
    df[Settings.AREA_WEIGHTED_MEAN_OF_BUILDING_HEIGHTS] = area_weighted_mean_of_building_heights
    df[Settings.BUILDING_SURFACE_AREA_TO_PLAN_AREA_RATIO] = building_surface_area_to_plan_area_ratio

    df = pd.concat([df, frontal_area_index], axis=1)

    df[Settings.COMPLETE_ASPECT_RATIO] = complete_aspect_ratio
    df[Settings.HEIGHT_TO_WIDTH_RATIO] = height_to_width_ratio
    df[Settings.SKY_VIEW_FACTOR] = sky_view_factor
    df[Settings.GRIMMOND_OKE_ROUGHNESS_LENGTH] = grimmond_oke_roughness_length
    df[Settings.GRIMMOND_OKE_DISPLACEMENT_HEIGHT] = grimmond_oke_displacement_height

    df[Settings.RAUPACH_ROUGHNESS_LENGTH_NORTH] = raupach_roughness_length[
        Settings.RAUPACH_ROUGHNESS_LENGTH_NORTH
    ]
    df[Settings.RAUPACH_DISPLACEMENT_HEIGHT_NORTH] = raupach_displacement_height[
        Settings.RAUPACH_DISPLACEMENT_HEIGHT_NORTH
    ]
    df[Settings.RAUPACH_ROUGHNESS_LENGTH_EAST] = raupach_roughness_length[
        Settings.RAUPACH_ROUGHNESS_LENGTH_EAST
    ]
    df[Settings.RAUPACH_DISPLACEMENT_HEIGHT_EAST] = raupach_displacement_height[
        Settings.RAUPACH_DISPLACEMENT_HEIGHT_EAST
    ]
    df[Settings.RAUPACH_ROUGHNESS_LENGTH_SOUTH] = raupach_roughness_length[
        Settings.RAUPACH_ROUGHNESS_LENGTH_SOUTH
    ]
    df[Settings.RAUPACH_DISPLACEMENT_HEIGHT_SOUTH] = raupach_displacement_height[
        Settings.RAUPACH_DISPLACEMENT_HEIGHT_SOUTH
    ]
    df[Settings.RAUPACH_ROUGHNESS_LENGTH_WEST] = raupach_roughness_length[
        Settings.RAUPACH_ROUGHNESS_LENGTH_WEST
    ]
    df[Settings.RAUPACH_DISPLACEMENT_HEIGHT_WEST] = raupach_displacement_height[
        Settings.RAUPACH_DISPLACEMENT_HEIGHT_WEST
    ]

    df = pd.concat([df, macdonald_roughness_length], axis=1)

    df[Settings.MACDONALD_DISPLACEMENT_HEIGHT] = macdonald_displacement_height

    df = pd.concat([df, vertical_distribution_of_building_heights], axis=1)

    df[Settings.GEOMETRY_FIELD] = building_geometry

    gdf = gpd.GeoDataFrame(df, geometry=Settings.GEOMETRY_FIELD, crs=target_crs)

    return gdf.to_crs(Settings.OUTPUT_CRS)


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
    measurements = merge_parameters.columns[merge_parameters.columns != Settings.GEOMETRY_FIELD]
    resolution = Settings.DEFAULT_OUTPUT_RESOLUTION
    fill = Settings.DEFAULT_FILL_VALUE

    return make_geocube(
        vector_data=merge_parameters.rename(
            columns={Settings.GEOMETRY_FIELD: "geometry"}
        ).set_geometry("geometry"),
        measurements=measurements,
        resolution=resolution,
        fill=fill,
        rasterize_function=partial(rasterize_image, all_touched=True, merge_alg=MergeAlg.add),
    )


def write_index(
    raster_to_numpy: np.ndarray,
    building_geometry: pd.Series,
    target_crs: CRS,
    index_filename: str = "index",
) -> str:
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

    with open(index_filename, "w") as index:
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
