import os
import pkg_resources
import unittest

import numpy as np
import geopandas as gpd

from naturf.driver import Model


class TestNodes(unittest.TestCase):

    INPUTS = {"input_shapefile": pkg_resources.resource_filename("naturf", os.path.join("data", "inputs", "C-5.shp")),
              "radius": 100,
              "cap_style": 1}

    def test_input_shapefile_df(self):
        """Test the functionality of the input_shapefile_df function."""

        # instantiate DAG asking for the output of input_shapefile_df()
        dag = Model(inputs=TestNodes.INPUTS,
                    outputs=["input_shapefile_df"])

        # generate the output data frame from the driver
        df = dag.execute()

        # check shape of data frame
        self.assertEqual((260, 3),
                         df.shape,
                         "`input_shapefile_df` shape does not match expected")

        # check data types
        fake_geodataframe = gpd.GeoDataFrame({"a": np.array([], dtype=np.int64),
                                              "b": np.array([], dtype=np.float64),
                                              "geometry": np.array([], dtype=gpd.array.GeometryDtype)})

        np.testing.assert_array_equal(fake_geodataframe.dtypes.values,
                                      df.dtypes.values,
                                      "`input_shapefile_df` column data types do not match expected")

        self.assertEqual(type(fake_geodataframe),
                         type(df),
                         "`input_shapefile_df` data type not matching expected")


if __name__ == '__main__':
    unittest.main()
