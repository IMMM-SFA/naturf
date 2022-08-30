

import geopandas as gpd
from hamilton import driver

import naturf.params as params
from naturf.config import Settings


def generate(input_shapefile: str,
             id_field: str = "OBJECTID",
             height_field: str = "Max_HOUSE_",
             geometry_field: str = "geometry",
             area_field: str = "area",
             centroid_field: str = "centroid",
             buffered_field: str = "buffered",
             radius: int = 100) -> gpd.GeoDataFrame:
    """Run the driver."""

    # instantiate driver with function definitions
    dr = driver.Driver({"input_shapefile": input_shapefile}, params)

    # target parameters
    target_parameter_list = [Settings.id_field,
                             Settings.height_field,
                             Settings.geometry_field,
                             Settings.area_field,
                             Settings.centroid_field,
                             Settings.buffered_field] + Settings.spatial_join_list

    # generate initial data frame
    df = dr.execute(target_parameter_list)

    dr.visualize_execution(final_vars=target_parameter_list,
                           output_file_path="/Users/d3y010/Desktop/graph.dot",
                           render_kwargs={'view': True})

    return df
