import os
from typing import Union, List

from geocube.api.core import make_geocube
import geopandas as gpd
import xarray as xr


def write_raster(xarray_cube: xr.Dataset,
                 input_shapefile: str,
                 output_raster_directory: str,
                 target_field: str):
    """Write xarray cube to an output raster for a target variable.

    :param xarray_cube:                             Xarray cube of rasterized data containing variables matching the
                                                    target field.
    :type xarray_cube:                              xr.Dataset

    :param input_shapefile:                         Full path with file name and extension to the input shapefile.
    :type input_shapefile:                          str

    :param output_raster_directory:                 If save_raster is True, the full path to the directory to write the
                                                    output raster file to.
    :type output_raster_directory:                  str

    :param target_field:                            Field name to use for rasterization.
    :type target_field:                             str


    """

    # get the file name of the input shapefile
    basename = os.path.basename(input_shapefile)

    # get the file name sans extension
    basename_no_extension = os.path.splitext(basename)

    # construct the output raster name
    output_raster = os.path.join(output_raster_directory, f"{basename_no_extension}_{target_field}.tif")

    # write raster to file
    xarray_cube.raster_value.rio.to_raster(output_raster)

    return output_raster


def set_target_field_list(geodataframe: gpd.GeoDataFrame,
                          fields: Union[str, List[str]] = "footprint",
                          default_value: Union[float, int] = 127) -> Union[gpd.GeoDataFrame, List[str]]:
    """Generate a list of fields to rasterize.

    :param geodataframe:                            A geopandas GeoDataFrame of the input shapefile.
    :type geodataframe:                             gpd.GeoDataFrame

    :param fields:                                  Field name to use for rasterization.  Default field "footprint" will
                                                    be used if none specified and written to file using the value of
                                                    the default_value argument.
    :type fields:                                   str

    :param default_value:                           Value used to write to the target field if it does not exist in the
                                                    input shapefile.
    :type default_value:                            Union[float, int]

    :returns:                                       [0] modified geodataframe
                                                    [1] list of field names to rasterize

    """

    fields_type = type(fields)

    # see if single string was passed for the target field
    if fields_type is str:

        # add in field for raster value if not exists with a default value
        if fields not in geodataframe.columns:
            geodataframe[fields] = default_value

        # place in list
        return geodataframe, [fields]

    # if target field was passed as a list, check for default assignment
    elif fields_type is list:

        for field in fields:

            # add in field for raster value if not exists with a default value
            if field not in geodataframe.columns:
                geodataframe[field] = default_value
                print(f"Rasterization field '{field}' added with default value of '{default_value}'.")

        return geodataframe, fields

    else:
        msg = f"'target_field' type '{fields_type}' not recognized.  Expecting Union[str, List[str]]."
        raise TypeError(msg)


def rasterize_polygon_shapefile(input_shapefile: str,
                                target_cell_size: Union[float, int],
                                save_raster: bool = True,
                                output_raster_directory: Union[str, None] = None,
                                target_field: Union[str, List[str]] = "footprint",
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

    # generate a field list to rasterize and ensure the fields are in the input geodataframe
    gdf, field_list = set_target_field_list(geodataframe=gdf,
                                            fields=target_field,
                                            default_value=default_value)

    # rasterize the polygon data into an xarray object
    cube = make_geocube(vector_data=gdf,
                        measurements=field_list,
                        resolution=(target_cell_size, -target_cell_size),
                        fill=no_data_value)

    # save raster file if so desired
    if save_raster:

        for field in field_list:
            raster_file = write_raster(xarray_cube=cube,
                                       input_shapefile=input_shapefile,
                                       output_raster_directory=output_raster_directory,
                                       target_field=field)

            print(f"Generated raster file:  {raster_file}")

    return cube
