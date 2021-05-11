import os

import pandas as pd
import geopandas as gpd

from shapely.geometry import Polygon


def polygon_from_bounds(gdf):
    """Create a polygon from the bounds of all geometries in a geodataframe.
    :param gdf:                                         Geopandas dataframe of polygons.
    :return:                                            Shapely Polygon Object
    """

    # get the bounds of all geometries
    minx, miny, maxx, maxy = gdf.geometry.total_bounds

    # construct a bounding box
    boundary = [(minx, miny),
                (maxx, miny),
                (maxx, maxy),
                (minx, maxy),
                (minx, miny)]

    # convert to a polygon object
    return Polygon(boundary)


def clip_method(buildings_gdf, target_gdf):
    """Clip buildings to the target geometries.  This method subsets the buildings data first based on the bounding
    box around the target geometries to speed things up a bit.  Still a slower method.
    :param buildings_gdf:                               The input buildings polygon geodataframe.
    :type buildings_gdf:                                GeoDataFrame
    :param target_gdf:                                  Input target polygon features geodataframe.
    :type target_gdf:                                   GeoDataFrame
    :return:                                            A clipped geodataframe with the target buildings geometries
    """

    # create a polygon for the bounds of the target data
    target_poly = polygon_from_bounds(target_gdf)

    # create a valid field where 1 is in the bonding box and 0 is not
    buildings_gdf['valid'] = buildings_gdf.geometry.apply(lambda x:  1 if x.intersects(target_poly) else 0)

    # create a subset of buildings polygons that can be used to speed up the clip functionality
    buildings_subset_gdf = buildings_gdf.loc[buildings_gdf['valid'] == 1]

    # clip buildings by the target geometries
    return gpd.clip(buildings_subset_gdf, target_gdf)


def sjoin_method(buildings_gdf, target_gdf, join_type='left', topology='intersects'):
    """Spatially join (left) the intersecting geometries of the buildings data for the target features.
    :param buildings_gdf:                               The input buildings polygon geodataframe.
    :type buildings_gdf:                                GeoDataFrame
    :param target_gdf:                                  Input target polygon features geodataframe.
    :type target_gdf:                                   GeoDataFrame
    :param join_type:                                   The type of join:
                                                        ‘left’: use keys from left_df; retain only left_df geometry
                                                        column
                                                        ‘right’: use keys from right_df; retain only right_df geometry
                                                        column
                                                        ‘inner’: use intersection of keys from both dfs; retain only
                                                        left_df geometry column
    :type join_type:                                    str
    :param topology:                                    Binary predicate, one of {‘intersects’, ‘contains’, ‘within’}.
                                                        See http://shapely.readthedocs.io/en/latest/manual.html#binary-predicates.
    :type topology:                                     str
    :return:                                            A geodataframe with the target buildings geometries
    """

    return gpd.sjoin(left_df=target_gdf, right_df=buildings_gdf, how=join_type, op=topology)


def workflow(buildings_shp_file, target_shp_file, existing_shp_file, output_directory=None, x_offset=0, y_offset=0,
             write_outputs=True, geometry_field_name='geometry', subset_method='sjoin'):
    """The following is a workflow to conduct the following:
    [0] Clip input buildings to the polygons in the target shapefile
    [1] Offset the geometries in the clipped data by the x, y offset provided by the user
    [2] Merge the output of the clipped (or offset) operations with an input shapefile
    :param buildings_shp_file:                          The input buildings polygon shapefile path.
    :type buildings_shp_file:                           str
    :param target_shp_file:                             Input target polygon features shapefile path.
    :type target_shp_file:                              str
    :param existing_shp_file:                           An existing shapefile with the same field names as what will
                                                        the same was what is in the clipped output.
    :type existing_shp_file:                            str
    :param output_directory:                            Full path to an output directory to save outputs to.
    :type output_directory:                             str
    :param x_offset:                                    Number of map units on the X axis to offset the polygon centroid
                                                        by.  This should be in the units of the input file geometry.
    :type x_offset:                                     int; float
    :param y_offset:                                    Number of map units on the Y axis to offset the polygon centroid
                                                        by.  This should be in the units of the input file geometry.
    :type y_offset:                                     int; float
    :param write_outputs:                               Choose to write outputs to shapefiles.
    :type write_outputs:                                bool
    :param geometry_field_name:                         Field name for geometry.  Default:  `geometry`.
    :type geometry_field_name:                          str
    :param subset_method:                               A method to subset the buildings data using the target data as
                                                        as follows:
                                                        `sjoin`: Default.  Spatially join (left) the intersecting
                                                                 geometries of the buildings data for the target
                                                                 features.
                                                        `clip`:  Clip buildings to the target geometries.  This method
                                                                 subsets the buildings data first based on the bounding
                                                                 box around the target geometries to speed things up a
                                                                 bit.  Still a slower method.
    :param subset_method:                               str
    :return:                                            A geopandas dataframe of the merged output
    USAGE:
    buildings_shp_file = '<path to file with filename and extension>'
    target_shp_file = '<path to file with filename and extension>'
    existing_shp_file = '<path to file with filename and extension>'
    output_directory = '<path to directory>'
    x_offset = 1000
    y_offset = 1000
    write_outputs = True
    # which method to use for extracting the buildings data
    subset_method = 'sjoin'
    result_gdf = workflow(buildings_shp_file=buildings_shp_file,
                            target_shp_file=target_shp_file,
                            existing_shp_file=existing_shp_file,
                            output_directory=output_directory,
                            x_offset=x_offset,
                            y_offset=y_offset,
                            write_outputs=write_outputs,
                            subset_method=subset_method)
    """

    # import shapefiles to geopandas dataframes
    buildings_gdf = gpd.read_file(buildings_shp_file)
    target_gdf = gpd.read_file(target_shp_file)
    existing_gdf = gpd.read_file(existing_shp_file)

    # ensure coordinate systems match for the inputs
    if not (buildings_gdf.crs == target_gdf.crs == existing_gdf.crs):
        msg = f"Coordinate systems do not match for the input files."
        raise AttributeError(msg)

    # create a spatial subset of the buildings data from features in the target data with a user-preferred method
    if subset_method == 'sjoin':
        subset_gdf = sjoin_method(buildings_gdf, target_gdf)
    elif subset_method == 'clip':
        subset_gdf = clip_method(buildings_gdf, target_gdf)
    else:
        msg = f"`subset_method` '{subset_method}' not in available options: `sjoin`, `clip`"
        raise ValueError(msg)

    # offset the clipped geometries by the user specified amount
    if x_offset > 0 or y_offset > 0:
        subset_gdf[geometry_field_name] = subset_gdf.translate(xoff=x_offset, yoff=y_offset)

    # merge the result into an existing dataset
    merged_gdf = pd.concat([existing_gdf, subset_gdf]).pipe(gpd.GeoDataFrame)

    # write outputs if desired
    if write_outputs:
        subset_gdf.to_file(os.path.join(output_directory, 'subset_data.shp'))
        merged_gdf.to_file(os.path.join(output_directory, 'merged_data.shp'))

    return merged_gdf

# input files
buildings_shp_file = 'C:\ORNL Spring\Shapefiles\ClarkCounty_Project.shp'
target_shp_file = 'C:\ORNL Spring\Shapefiles\Sample_Data_Project.shp'
existing_shp_file = 'C:\ORNL Spring\Shapefiles\ClarkCounty_Project.shp'
output_directory = 'C:\ORNL Spring\Shapefiles'

# offset in map units
x_offset = 1000
y_offset = 1000

# choose to write outputs
write_outputs = True

# which method to use for extracting the buildings data
subset_method = 'sjoin'

# run it and return a geopandas dataframe
result_gdf = workflow(buildings_shp_file=buildings_shp_file,
                        target_shp_file=target_shp_file,
                        existing_shp_file=existing_shp_file,
                        output_directory=output_directory,
                        x_offset=x_offset,
                        y_offset=y_offset,
                        write_outputs=write_outputs,
                        subset_method=subset_method)