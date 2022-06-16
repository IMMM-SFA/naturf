import os
from typing import Union

import geopandas as gpd
from geocube.api.core import make_geocube
import xarray as xr


def rasterize_polygon_shapefile(input_shapefile: str,
                                target_cell_size: Union[float, int],
                                save_raster: bool = True,
                                output_raster_directory: Union[str, None] = None,
                                target_field: str = "footprint",
                                default_value: Union[float, int] = 127,
                                no_data_value: int = 255) -> xr.Dataset:
    """Rasterize polygon shapefile to desired resolution.

    :param input_shapefile:                         Full path with file name and extension to the input shapefile.
    :type input_shapefile:                          str

    :param target_cell_size:                        Target cell size of the output raster.
    :type target_cell_size:                         Union[float, int]

    :param save_raster:                             True, if writing raster to file. False, if not.
    :type save_raster:                              bool

    :param output_raster_directory:                 If save_raster is True, the full path to the directory to write the
                                                    output raster file to.
    :type output_raster_directory:                  Union[str, None]

    :param target_field:                            Field name to use for rasterization.  Default field "footprint" will
                                                    be used if none specified and written to file using the value of
                                                    the default_value argument.
    :type target_field:                             str

    :param default_value:                           Value used to write to the target field if it does not exist in the
                                                    input shapefile.
    :type default_value:                            Union[float, int]

    :param no_data_value:                           No data value to use as the fill value for non-populated cells.
    :type no_data_value:                            int

    :return:                                        An xarray Dataset object of the rasterized polygon.

    """

    # read in shapefile as a geodataframe
    gdf = gpd.read_file(input_shapefile)

    # add in field for raster value if not exists with a default value
    if target_field not in gdf.columns:
        gdf[target_field] = default_value

    # rasterize the polygon data into an xarray object
    cube = make_geocube(vector_data=gdf,
                        measurements=[target_field],
                        resolution=(target_cell_size, -target_cell_size),
                        fill=no_data_value)

    # save raster file if so desired
    if save_raster:

        # get the file name of the input shapefile
        basename = os.path.basename(input_shapefile)

        # get the file name sans extension
        basename_no_extension = os.path.splitext(basename)

        # construct the output raster name
        output_raster = os.path.join(output_raster_directory, f"{basename_no_extension}_{target_field}.tif")

        # write raster to file
        cube.raster_value.rio.to_raster(output_raster)

    return cube
