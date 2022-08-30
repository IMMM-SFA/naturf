

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

    # # read in shapefile and only keep necessary fields
    # gdf = gpd.read_file(input_shapefile)[[Settings.data_id_field_name,
    #                                       Settings.data_height_field_name,
    #                                       Settings.data_geometry_field_name]]
    #
    # # standardize field names from data to reference names in code
    # gdf.rename(columns={id_field: Settings.id_field,
    #                     height_field: Settings.height_field,
    #                     geometry_field: Settings.geometry_field},
    #            inplace=True)

    # instantiate driver with function definitions
    dr = driver.Driver({"input_shapefile": input_shapefile}, params)

    # generate initial data frame
    df = dr.execute(Settings.spatial_join_list + ["neighbor_centroid"])

    dr.visualize_execution(final_vars=Settings.spatial_join_list + ["neighbor_centroid"],
                           output_file_path="/Users/d3y010/Desktop/graph.dot",
                           render_kwargs={'view': False})

    return df
