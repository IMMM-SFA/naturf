

import geopandas as gpd
import pandas as pd
from hamilton import driver

import naturf.nodes as nodes
from naturf.config import Settings


class Model:

    def __init__(self, input_shapefile: str):

        # dictionary of parameter inputs required to construct the nodes
        self.input_parameters = {"input_shapefile": input_shapefile,
                                 "radius": 100,
                                 "cap_style": 1}  # regular external buffer

        # target parameters
        # target_parameter_list = ["target_crs"] + ["distance_to_neighbor"] + Settings.spatial_join_list
        self.target_parameter_list = ["distance_to_neighbor", "angle_in_degrees_to_neighbor"]

        # instantiate driver with function definitions
        self.dr = driver.Driver(self.input_parameters, nodes)

    def generate(self) -> pd.DataFrame:
        """Run the driver."""

        # generate initial data frame
        df = self.dr.execute(self.target_parameter_list)

        return df

    def graph(self):
        """Show the DAG."""

        self.dr.visualize_execution(final_vars=self.target_parameter_list,
                                    output_file_path="/Users/d3y010/Desktop/graph.dot",
                                    render_kwargs={'view': True})

    def list_parameters(self):
        """List all available parameters."""

        return self.dr.list_available_variables()


