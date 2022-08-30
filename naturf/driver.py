

import geopandas as gpd
from hamilton import driver

import naturf.nodes as nodes
from naturf.config import Settings


def generate(input_shapefile: str) -> gpd.GeoDataFrame:
    """Run the driver."""

    # dictionary of parameter inputs required to construct the nodes
    input_parameters = {"input_shapefile": input_shapefile,
                        "radius": 100,
                        "cap_style": 3}

    # instantiate driver with function definitions
    dr = driver.Driver(input_parameters, nodes)

    # target parameters
    # target_parameter_list = [Settings.id_field,
    #                          Settings.height_field,
    #                          Settings.geometry_field,
    #                          Settings.area_field,
    #                          Settings.centroid_field,
    #                          Settings.buffered_field,
    #                          "target_crs"] + Settings.spatial_join_list

    target_parameter_list = ["get_neighboring_buildings_df"]

    # generate initial data frame
    df = dr.execute(target_parameter_list)

    dr.visualize_execution(final_vars=target_parameter_list,
                           output_file_path="/Users/d3y010/Desktop/graph.dot",
                           render_kwargs={'view': True})

    return df
