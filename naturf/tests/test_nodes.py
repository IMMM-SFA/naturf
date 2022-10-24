import os
import pkg_resources
import unittest

from dataclasses import dataclass
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from typing import List


from naturf.driver import Model
from naturf.nodes import angle_in_degrees_to_neighbor, orientation_to_neighbor


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

    def test_angle_in_degrees_to_neighbor(self):
        """Test that the returned angle is correct."""
        @dataclass
        class TestCase:
            name: str
            target_input: List[Point]
            neighbor_input: List[Point]
            expected: List[int]

        testcases = [
            TestCase(name="same_centroid", target_input=[Point(1, 1), Point(0, 0)], neighbor_input=[Point(1, 1), Point(0, 0)], expected=[0.0, 0.0]),
            TestCase(name="east", target_input=[Point(0, 0)], neighbor_input=[Point(1, 0)], expected=[0.0]),
            TestCase(name="west", target_input=[Point(0, 0)], neighbor_input=[Point(-1, 0)], expected=[180.0]),
            TestCase(name="north", target_input=[Point(0, 0)], neighbor_input=[Point(0, 1)], expected=[90.0]),
            TestCase(name="south", target_input=[Point(0, 0)], neighbor_input=[Point(0, -1)], expected=[270.0]),
            TestCase(name="northeast", target_input=[Point(0, 0)], neighbor_input=[Point(10, 10*np.sqrt(3))], expected=[60.0]),
            TestCase(name="northwest", target_input=[Point(0, 0)], neighbor_input=[Point(-10, 10*np.sqrt(3))], expected=[120.0]),
            TestCase(name="southeast", target_input=[Point(0, 0)], neighbor_input=[Point(10, -10*np.sqrt(3))], expected=[300.0]),
            TestCase(name="southwest", target_input=[Point(0, 0)], neighbor_input=[Point(-10, -10*np.sqrt(3))], expected=[240.0]),
            ]

        for case in testcases:
            actual = angle_in_degrees_to_neighbor(gpd.GeoSeries(case.target_input), gpd.GeoSeries(case.neighbor_input))
            expected = pd.Series(case.expected)
            pd.testing.assert_series_equal(
                expected,
                actual,
                "failed test {} expected {}, actual {}".format(
                    case.name, expected, actual
                ),
            )

    def test_orientation_to_neighbor(self):
        """Test that the function `orientation_to_neighbor returns either `east_west` or `north_south` correctly."""
        @dataclass
        class TestCase:
            name: str
            input: List[int]
            expected: List[int]

        east_west = "east_west"
        north_south = "north_south"

        testcases = [
            TestCase(name="zero_degrees", input=[0.0, -0.0], expected=[east_west, east_west]),
            TestCase(name="north_south", input=[90, 270], expected=[north_south, north_south]),
            TestCase(name="east_west", input=[45, 135, 225, 315, 360], expected=[east_west, east_west, east_west, east_west, east_west]),
            ]

        for case in testcases:
            actual = orientation_to_neighbor(pd.Series(case.input))
            expected = pd.Series(case.expected)
            pd.testing.assert_series_equal(
                expected,
                actual,
                f"failed test {case.name} expected {expected}, actual {actual}"
            )


if __name__ == '__main__':
    unittest.main()
