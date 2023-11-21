import geopandas as gpd

from naturf.config import Settings
import naturf.nodes as nodes

from hamilton import driver

if __name__ == "__main__":
    # Load in shapefile
    path = "example/shapefile/C-5.shp"

    input_shapefile_df = gpd.read_file(path)
    input_shapefile_df = nodes.standardize_column_names_df(input_shapefile_df)
    input_shapefile_df = nodes.filter_zero_height_df(input_shapefile_df)
    input_shapefile_df = nodes.apply_max_building_height(input_shapefile_df)

    dr = driver.Driver(Settings.__dict__, nodes)

    output_columns = ["building_area"]

    df = dr.execute(output_columns, inputs=[input_shapefile_df])

    print(df)
