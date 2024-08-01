import math
import os
import unittest

from dataclasses import dataclass
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, JOIN_STYLE
from typing import List

from naturf.driver import Model
import naturf.nodes as nodes
from naturf.config import Settings


class TestNodes(unittest.TestCase):
    INPUTS = {
        "input_shapefile": os.path.join("naturf", "data", "C-5.shp"),
        "radius": 100,
        "cap_style": 1,
    }

    def test_area_weighted_mean_of_building_heights(self):
        "Test that the function `area_weighted_mean_of_building_heights()` returns the correct value."
        # ID 0: one building
        # ID 1: two buildings
        # ID 2: multiple buildings, decimal values
        data = [[0, 10, 10], [1, 2, 10], [1, 1, 10], [2, 0.1, 10], [2, 0.9, 30], [2, 12, 0.25]]
        buildings_intersecting_plan_area = pd.DataFrame(
            data,
            columns=[
                Settings.TARGET_ID_FIELD,
                Settings.NEIGHBOR_HEIGHT_FIELD,
                Settings.NEIGHBOR_AREA_FIELD,
            ],
        )
        expected = pd.Series([10.0, 1.5, 0.7701863354037267])
        actual = nodes.area_weighted_mean_of_building_heights(buildings_intersecting_plan_area)
        pd.testing.assert_series_equal(
            expected,
            actual,
            f"area_weighted_mean_of_building_heights test failed, expected {expected}, actual {actual}",
        )

    def test_average_distance_between_buildings(self):
        "Test that the function `average_distance_between_buildings()` returns the correct distance."

        # Each ID number refers to a particular building and test case.
        # Buildings 0, 1, and 2 test that the mean function is working correctly.
        # Building 3 tests that a distance of zero (representing a building considered its own neighbor) does not affect the mean.
        # Building 4 tests that a building with only itself as a neighbor returns the default street width.

        index = pd.Index([0, 0, 1, 1, 2, 2, 3, 3, 3, 4], name=Settings.NEIGHBOR_ID_FIELD)
        distance = pd.Series(
            [1, 2, 1, 3, 1, 1, 3, 0, 3, 0], index, name=Settings.DISTANCE_BETWEEN_BUILDINGS
        )

        default_street_width = Settings.DEFAULT_STREET_WIDTH

        expected = pd.Series(
            [1.5, 2.0, 1.0, 3.0, default_street_width],
            name=Settings.AVERAGE_DISTANCE_BETWEEN_BUILDINGS,
        )

        actual = nodes.average_distance_between_buildings(distance)

        pd.testing.assert_series_equal(
            expected,
            actual,
            f"average_distance_between_buildings test failed, expected {expected}, actual {actual}",
        )

    def test_buildings_intersecting_plan_area(self):
        """Test that the function `buildings_intersecting_plan_area()` returns the correct intersecting buildings."""

        polygon1 = Polygon([[0, 0], [0, 1], [1, 1], [1, 0]])
        polygon2 = Polygon([[3, 3], [3, 4], [4, 4], [4, 3]])
        building_id = pd.Series([0, 1])
        building_height = pd.Series([5, 10])
        building_geometry = pd.Series([polygon1, polygon2])
        building_area = pd.Series([polygon1.area, polygon2.area])
        crs = "epsg:3857"

        wall_length_north = pd.Series([1.0, 1.0], name=Settings.WALL_LENGTH_NORTH)
        wall_length_east = pd.Series([1.0, 1.0], name=Settings.WALL_LENGTH_EAST)
        wall_length_south = pd.Series([1.0, 1.0], name=Settings.WALL_LENGTH_SOUTH)
        wall_length_west = pd.Series([1.0, 1.0], name=Settings.WALL_LENGTH_WEST)

        wall_length = pd.concat(
            [
                wall_length_north,
                wall_length_east,
                wall_length_south,
                wall_length_west,
            ],
            axis=1,
        )

        total_plan_area_geometry_no_overlap = pd.Series([polygon1.buffer(1), polygon2.buffer(1)])
        total_plan_area_geometry_some_overlap = pd.Series(
            [polygon1.buffer(3.5), polygon2.buffer(3.5)]
        )
        total_plan_area_geometry_total_overlap = pd.Series([polygon1.buffer(5), polygon2.buffer(5)])

        no_overlap_output_gdf = gpd.GeoDataFrame(
            {
                "building_id_neighbor": building_id,
                "building_id_target": building_id,
                "building_height_target": building_height,
                "building_area_target": building_area,
                "building_geometry": building_geometry,
                "building_buffered_target": gpd.GeoSeries(total_plan_area_geometry_no_overlap),
                "wall_length_north_target": wall_length_north,
                "wall_length_east_target": wall_length_east,
                "wall_length_south_target": wall_length_south,
                "wall_length_west_target": wall_length_west,
                "index_neighbor": building_id,
                "building_height_neighbor": building_height,
                "building_area_neighbor": building_area,
                "building_buffered_neighbor": total_plan_area_geometry_no_overlap,
                "wall_length_north_neighbor": wall_length_north,
                "wall_length_east_neighbor": wall_length_east,
                "wall_length_south_neighbor": wall_length_south,
                "wall_length_west_neighbor": wall_length_west,
                "building_geometry_neighbor": gpd.GeoSeries(building_geometry),
            },
            geometry="building_geometry",
        ).set_index("building_id_neighbor")

        some_overlap_output_gdf = gpd.GeoDataFrame(
            {
                "building_id_neighbor": pd.Series([0, 0, 1, 1]),
                "building_id_target": pd.Series([0, 1, 0, 1]),
                "building_height_target": pd.Series([5, 10, 5, 10]),
                "building_area_target": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "building_geometry": gpd.GeoSeries(
                    [
                        building_geometry[0],
                        building_geometry[1],
                        building_geometry[0],
                        building_geometry[1],
                    ]
                ),
                "building_buffered_target": gpd.GeoSeries(
                    [
                        total_plan_area_geometry_some_overlap[0],
                        total_plan_area_geometry_some_overlap[1],
                        total_plan_area_geometry_some_overlap[0],
                        total_plan_area_geometry_some_overlap[1],
                    ]
                ),
                "wall_length_north_target": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "wall_length_east_target": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "wall_length_south_target": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "wall_length_west_target": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "index_neighbor": pd.Series([0, 0, 1, 1]),
                "building_height_neighbor": pd.Series([5, 5, 10, 10]),
                "building_area_neighbor": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "building_buffered_neighbor": pd.Series(
                    [
                        total_plan_area_geometry_some_overlap[0],
                        total_plan_area_geometry_some_overlap[0],
                        total_plan_area_geometry_some_overlap[1],
                        total_plan_area_geometry_some_overlap[1],
                    ]
                ),
                "wall_length_north_neighbor": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "wall_length_east_neighbor": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "wall_length_south_neighbor": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "wall_length_west_neighbor": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "building_geometry_neighbor": gpd.GeoSeries(
                    [
                        building_geometry[0],
                        building_geometry[0],
                        building_geometry[1],
                        building_geometry[1],
                    ]
                ),
            },
            geometry="building_geometry",
        ).set_index("building_id_neighbor")

        total_overlap_output_gdf = gpd.GeoDataFrame(
            {
                "building_id_neighbor": pd.Series([0, 0, 1, 1]),
                "building_id_target": pd.Series([0, 1, 0, 1]),
                "building_height_target": pd.Series([5, 10, 5, 10]),
                "building_area_target": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "building_geometry": gpd.GeoSeries(
                    [
                        building_geometry[0],
                        building_geometry[1],
                        building_geometry[0],
                        building_geometry[1],
                    ]
                ),
                "building_buffered_target": gpd.GeoSeries(
                    [
                        total_plan_area_geometry_total_overlap[0],
                        total_plan_area_geometry_total_overlap[1],
                        total_plan_area_geometry_total_overlap[0],
                        total_plan_area_geometry_total_overlap[1],
                    ]
                ),
                "wall_length_north_target": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "wall_length_east_target": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "wall_length_south_target": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "wall_length_west_target": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "index_neighbor": pd.Series([0, 0, 1, 1]),
                "building_height_neighbor": pd.Series([5, 5, 10, 10]),
                "building_area_neighbor": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "building_buffered_neighbor": pd.Series(
                    [
                        total_plan_area_geometry_total_overlap[0],
                        total_plan_area_geometry_total_overlap[0],
                        total_plan_area_geometry_total_overlap[1],
                        total_plan_area_geometry_total_overlap[1],
                    ]
                ),
                "wall_length_north_neighbor": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "wall_length_east_neighbor": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "wall_length_south_neighbor": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "wall_length_west_neighbor": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "building_geometry_neighbor": gpd.GeoSeries(
                    [
                        building_geometry[0],
                        building_geometry[0],
                        building_geometry[1],
                        building_geometry[1],
                    ]
                ),
            },
            geometry="building_geometry",
        ).set_index("building_id_neighbor")

        @dataclass
        class TestCase:
            name: str
            input: pd.Series
            expected: gpd.GeoDataFrame

        testcases = [
            TestCase(
                name="no overlap",
                input=total_plan_area_geometry_no_overlap,
                expected=no_overlap_output_gdf,
            ),
            TestCase(
                name="some overlap",
                input=total_plan_area_geometry_some_overlap,
                expected=some_overlap_output_gdf,
            ),
            TestCase(
                name="total overlap",
                input=total_plan_area_geometry_total_overlap,
                expected=total_overlap_output_gdf,
            ),
        ]

        for case in testcases:
            actual = nodes.buildings_intersecting_plan_area(
                building_id,
                building_height,
                building_geometry,
                building_area,
                case.input,
                wall_length,
                crs,
            )
            expected = case.expected
            pd.testing.assert_frame_equal(
                expected,
                actual,
                f"buildings_intersecting_plan_area test {case.name} failed, expected {expected}, actual {actual}",
            )

    def test_building_plan_area(self):
        """Test that the function `building_plan_area()` returns the correct area."""

        polygon1 = Polygon([[0, 0], [0, 1], [1, 1], [1, 0]])
        polygon2 = Polygon([[3, 3], [3, 4], [4, 4], [4, 3]])
        building_id = pd.Series([0, 1])
        building_height = pd.Series([5, 10])
        building_geometry = pd.Series([polygon1, polygon2])
        building_area = pd.Series([polygon1.area, polygon2.area])

        total_plan_area_geometry_no_overlap = pd.Series([polygon1.buffer(1), polygon2.buffer(1)])
        total_plan_area_geometry_some_overlap = pd.Series(
            [
                polygon1.buffer(2.5, join_style=JOIN_STYLE.mitre),
                polygon2.buffer(2.5, join_style=JOIN_STYLE.mitre),
            ]
        )
        total_plan_area_geometry_total_overlap = pd.Series([polygon1.buffer(5), polygon2.buffer(5)])

        no_overlap_gdf = gpd.GeoDataFrame(
            {
                "building_id_neighbor": building_id,
                "building_id_target": building_id,
                "building_height_target": building_height,
                "building_area_target": building_area,
                "building_geometry": building_geometry,
                "building_buffered_target": gpd.GeoSeries(total_plan_area_geometry_no_overlap),
                "index_neighbor": building_id,
                "building_height_neighbor": building_height,
                "building_area_neighbor": building_area,
                "building_buffered_neighbor": total_plan_area_geometry_no_overlap,
                "building_geometry_neighbor": gpd.GeoSeries(building_geometry),
            },
            geometry="building_geometry",
        ).set_index("building_id_neighbor")

        some_overlap_gdf = gpd.GeoDataFrame(
            {
                "building_id_neighbor": pd.Series([0, 0, 1, 1]),
                "building_id_target": pd.Series([0, 1, 0, 1]),
                "building_height_target": pd.Series([5, 10, 5, 10]),
                "building_area_target": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "building_geometry": gpd.GeoSeries(
                    [
                        building_geometry[0],
                        building_geometry[1],
                        building_geometry[0],
                        building_geometry[1],
                    ]
                ),
                "building_buffered_target": gpd.GeoSeries(
                    [
                        total_plan_area_geometry_some_overlap[0],
                        total_plan_area_geometry_some_overlap[1],
                        total_plan_area_geometry_some_overlap[0],
                        total_plan_area_geometry_some_overlap[1],
                    ]
                ),
                "index_neighbor": pd.Series([0, 0, 1, 1]),
                "building_height_neighbor": pd.Series([5, 5, 10, 10]),
                "building_area_neighbor": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "building_buffered_neighbor": pd.Series(
                    [
                        total_plan_area_geometry_some_overlap[0],
                        total_plan_area_geometry_some_overlap[0],
                        total_plan_area_geometry_some_overlap[1],
                        total_plan_area_geometry_some_overlap[1],
                    ]
                ),
                "building_geometry_neighbor": gpd.GeoSeries(
                    [
                        building_geometry[0],
                        building_geometry[0],
                        building_geometry[1],
                        building_geometry[1],
                    ]
                ),
            },
            geometry="building_geometry",
        ).set_index("building_id_neighbor")

        total_overlap_gdf = gpd.GeoDataFrame(
            {
                "building_id_neighbor": pd.Series([0, 0, 1, 1]),
                "building_id_target": pd.Series([0, 1, 0, 1]),
                "building_height_target": pd.Series([5, 10, 5, 10]),
                "building_area_target": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "building_geometry": gpd.GeoSeries(
                    [
                        building_geometry[0],
                        building_geometry[1],
                        building_geometry[0],
                        building_geometry[1],
                    ]
                ),
                "building_buffered_target": gpd.GeoSeries(
                    [
                        total_plan_area_geometry_total_overlap[0],
                        total_plan_area_geometry_total_overlap[1],
                        total_plan_area_geometry_total_overlap[0],
                        total_plan_area_geometry_total_overlap[1],
                    ]
                ),
                "index_neighbor": pd.Series([0, 0, 1, 1]),
                "building_height_neighbor": pd.Series([5, 5, 10, 10]),
                "building_area_neighbor": pd.Series([1.0, 1.0, 1.0, 1.0]),
                "building_buffered_neighbor": pd.Series(
                    [
                        total_plan_area_geometry_total_overlap[0],
                        total_plan_area_geometry_total_overlap[0],
                        total_plan_area_geometry_total_overlap[1],
                        total_plan_area_geometry_total_overlap[1],
                    ]
                ),
                "building_geometry_neighbor": gpd.GeoSeries(
                    [
                        building_geometry[0],
                        building_geometry[0],
                        building_geometry[1],
                        building_geometry[1],
                    ]
                ),
            },
            geometry="building_geometry",
        ).set_index("building_id_neighbor")

        @dataclass
        class TestCase:
            name: str
            input: gpd.GeoDataFrame
            expected: List[float]

        testcases = [
            TestCase(name="no overlap", input=no_overlap_gdf, expected=[1.0, 1.0]),
            TestCase(name="some overlap", input=some_overlap_gdf, expected=[1.25, 1.25]),
            TestCase(name="total overlap", input=total_overlap_gdf, expected=[2.0, 2.0]),
        ]

        for case in testcases:
            actual = nodes.building_plan_area(case.input)
            expected = pd.Series(case.expected)
            pd.testing.assert_series_equal(
                expected,
                actual,
                f"building_plan_area test {case.name} failed, expected {expected}, actual {actual}",
            )

    def test_building_surface_area_to_plan_area_ratio(self):
        """Test that the function `building_surface_area_to_plan_area_ratio()` returns the correct value."""

        building_surface_area = pd.Series([0, 1.5, 75, 0, 1.5, 75])
        total_plan_area = pd.Series([0, 0, 1.5, 1.5, 75, 75])
        expected = pd.Series([math.nan, math.inf, 50.0, 0.0, 0.02, 1.0])
        actual = nodes.building_surface_area_to_plan_area_ratio(
            building_surface_area, total_plan_area
        )
        pd.testing.assert_series_equal(
            expected,
            actual,
            f"building_surface_area_to_plan_area_ratio test failed, expected {expected}, actual {actual}",
        )

    def test_complete_aspect_ratio(self):
        """Test that the function `complete_aspect_ratio()` returns the correct value."""

        building_surface_area = pd.Series([0, 0, 0, 1, 1, 1, 5.5, 5.5, 5.5, 75, 75, 75])
        total_plan_area = pd.Series([0, 1, 5.5, 75, 0, 1, 5.5, 75, 0, 1, 5.5, 75])
        building_plan_area = pd.Series([0, 0, 1, 1, 5.5, 5.5, 75, 75, 0, 1, 5.5, 75])
        expected = pd.Series(
            [
                float("nan"),
                1.0,
                0.8181818181818182,
                1.0,
                -float("inf"),
                -3.5,
                -11.636363636363637,
                0.07333333333333333,
                float("inf"),
                75.0,
                13.636363636363637,
                1.0,
            ]
        )
        actual = nodes.complete_aspect_ratio(
            building_surface_area, total_plan_area, building_plan_area
        )
        pd.testing.assert_series_equal(
            expected,
            actual,
            f"complete_aspect_ratio test failed, expected {expected}, actual {actual}",
        )

    def test_input_shapefile_df(self):
        """Test that the function `input_shapefile_df()` creates the right shape and type of DataFrame."""

        # instantiate DAG asking for the output of input_shapefile_df()
        dag = Model(inputs=TestNodes.INPUTS, outputs=["input_shapefile_df"])

        # generate the output data frame from the driver
        df = dag.execute()

        # check shape of data frame
        self.assertEqual((260, 3), df.shape, "`input_shapefile_df` shape does not match expected")

        # check data types
        fake_geodataframe = gpd.GeoDataFrame(
            {
                "a": np.array([], dtype=np.int64),
                "b": np.array([], dtype=np.float64),
                "geometry": np.array([], dtype=gpd.array.GeometryDtype),
            }
        )

        np.testing.assert_array_equal(
            fake_geodataframe.dtypes.values,
            df.dtypes.values,
            "`input_shapefile_df` column data types do not match expected",
        )

        self.assertEqual(
            type(fake_geodataframe),
            type(df),
            "`input_shapefile_df` doesn't match expected data type.",
        )

    def test_frontal_area(self):
        """Test that the function `frontal_area()` returns the correct values."""
        frontal_length = pd.DataFrame([[0, 0.25, 0.5, 7500], [0, 3.14159, 10.5, 100]])
        building_height = pd.Series([0.5, 75])
        expected = pd.DataFrame([[0.0, 0.125, 0.25, 3750.0], [0.0, 235.61925, 787.5, 7500.0]])
        actual = nodes.frontal_area(frontal_length, building_height)
        expected.columns = [
            Settings.FRONTAL_AREA_NORTH,
            Settings.FRONTAL_AREA_EAST,
            Settings.FRONTAL_AREA_SOUTH,
            Settings.FRONTAL_AREA_WEST,
        ]
        pd.testing.assert_frame_equal(
            expected,
            actual,
            f"frontal_area test failed, expected {expected}, actual {actual}",
        )

    def test_frontal_area_density(self):
        """Test that the function `frontal_area_density()` returns the correct value."""

        # This uses different heights to test the function.
        # Building 1 is 5m tall to test that using one height bin works correctly.
        # Building 2 is 4m tall to test that using a height less than a full bin works correctly.
        # Building 3 is 21m tall to test that using a height >5m but less than a full bin works correctly.
        # Building 4 is 75m tall to test that a full-height building works correctly.

        frontal_length_north = Settings.FRONTAL_LENGTH_NORTH
        frontal_length_east = Settings.FRONTAL_LENGTH_EAST
        frontal_length_south = Settings.FRONTAL_LENGTH_SOUTH
        frontal_length_west = Settings.FRONTAL_LENGTH_WEST

        frontal_lengths = pd.concat(
            [
                pd.Series([2.0, 2.0, 2.0, 2.0], name=frontal_length_north),
                pd.Series([4.0, 4.0, 4.0, 4.0], name=frontal_length_east),
                pd.Series([1.0, 1.0, 1.0, 1.0], name=frontal_length_south),
                pd.Series([3.0, 3.0, 3.0, 3.0], name=frontal_length_west),
            ],
            axis=1,
        )
        heights = pd.Series([5, 4, 21, 75])

        total_plan_area = pd.Series([100.0, 100.0, 100.0, 100.0])

        rows = 4
        cols = 15

        frontal_area_north, frontal_area_east, frontal_area_south, frontal_area_west = (
            [[0 for i in range(cols)] for j in range(rows)],
            [[0 for i in range(cols)] for j in range(rows)],
            [[0 for i in range(cols)] for j in range(rows)],
            [[0 for i in range(cols)] for j in range(rows)],
        )

        frontal_area_north[0][0] = 0.1
        frontal_area_north[0][1] = 0.0

        frontal_area_east[0][0] = 0.2
        frontal_area_east[0][1] = 0.0

        frontal_area_south[0][0] = 0.05
        frontal_area_south[0][1] = 0.0

        frontal_area_west[0][0] = 0.15
        frontal_area_west[0][1] = 0.0

        frontal_area_north[1][0] = 0.08
        frontal_area_north[1][1] = 0.0

        frontal_area_east[1][0] = 0.16
        frontal_area_east[1][1] = 0.0

        frontal_area_south[1][0] = 0.04
        frontal_area_south[1][1] = 0.0

        frontal_area_west[1][0] = 0.12
        frontal_area_west[1][1] = 0.0

        for i in range(0, 4):
            frontal_area_north[2][i] = 0.1
        frontal_area_north[2][4] = 0.02

        for i in range(0, 4):
            frontal_area_east[2][i] = 0.20
        frontal_area_east[2][4] = 0.04

        for i in range(0, 4):
            frontal_area_south[2][i] = 0.05
        frontal_area_south[2][4] = 0.01

        for i in range(0, 4):
            frontal_area_west[2][i] = 0.15
        frontal_area_west[2][4] = 0.03

        for i in range(0, 15):
            frontal_area_north[3][i] = 0.1

        for i in range(0, 15):
            frontal_area_east[3][i] = 0.2

        for i in range(0, 15):
            frontal_area_south[3][i] = 0.05

        for i in range(0, 15):
            frontal_area_west[3][i] = 0.15

        columns_north, columns_east, columns_south, columns_west = (
            [
                f"{Settings.FRONTAL_AREA_NORTH}_{i}"
                for i in range(
                    int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL)
                )
            ],
            [
                f"{Settings.FRONTAL_AREA_EAST}_{i}"
                for i in range(
                    int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL)
                )
            ],
            [
                f"{Settings.FRONTAL_AREA_SOUTH}_{i}"
                for i in range(
                    int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL)
                )
            ],
            [
                f"{Settings.FRONTAL_AREA_WEST}_{i}"
                for i in range(
                    int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL)
                )
            ],
        )

        actual = nodes.frontal_area_density(frontal_lengths, heights, total_plan_area)
        expected = pd.concat(
            [
                pd.DataFrame(frontal_area_north, columns=columns_north),
                pd.DataFrame(frontal_area_east, columns=columns_east),
                pd.DataFrame(frontal_area_south, columns=columns_south),
                pd.DataFrame(frontal_area_west, columns=columns_west),
            ],
            axis=1,
        )
        # f"frontal_area_density test failed, expected {expected}, actual {actual}",
        pd.testing.assert_frame_equal(
            expected,
            actual,
        )

    def test_frontal_area_index(self):
        """Test that the function `frontal_area_index()` returns the correct value in each cardinal direction."""

        frontal_area = pd.DataFrame(
            [
                [0, 1, 5.5, 75],
                [0, 1, 5.5, 75],
                [0, 1, 5.5, 75],
            ]
        )
        total_plan_area = pd.Series([0, 1.5, 75])
        expected = pd.DataFrame(
            [
                [math.nan, math.inf, math.inf, math.inf],
                [0.0, 0.6666666666666666, 3.6666666666666665, 50.0],
                [0.0, 0.013333333333333334, 0.07333333333333333, 1.0],
            ]
        )
        expected.columns = [
            Settings.FRONTAL_AREA_INDEX_NORTH,
            Settings.FRONTAL_AREA_INDEX_EAST,
            Settings.FRONTAL_AREA_INDEX_SOUTH,
            Settings.FRONTAL_AREA_INDEX_WEST,
        ]
        actual = nodes.frontal_area_index(frontal_area, total_plan_area)
        # f"frontal_area_index test failed, expected {expected}, actual {actual}",
        pd.testing.assert_frame_equal(
            expected,
            actual,
        )

    def test_frontal_length(self):
        """Test that the function `frontal_length()` returns the correct length."""

        polygon1 = Polygon([[0, 0], [0, 1], [1, 1], [1, 0]])
        polygon2 = Polygon([[3, 3], [3, 4], [4, 4], [4, 3]])
        building_id = pd.Series([0, 1])
        building_height = pd.Series([5, 10])
        building_geometry = pd.Series([polygon1, polygon2])
        building_area = pd.Series([polygon1.area, polygon2.area])
        crs = "epsg:3857"

        # The wall lengths listed below are the test cases.
        # wall_length_north and wall_length_east test that the addition is working correctly.
        # wall_length_south tests that addition works correctly when one building does not have a wall facing a given direction.
        # wall_length_west tests that addition works correctly when neither building has a wall facing a given direction.

        wall_length_north = pd.Series([1.0, 1.0], name=Settings.WALL_LENGTH_NORTH)
        wall_length_east = pd.Series([1.0, 3.0], name=Settings.WALL_LENGTH_EAST)
        wall_length_south = pd.Series([0, 1.0], name=Settings.WALL_LENGTH_SOUTH)
        wall_length_west = pd.Series([0, 0], name=Settings.WALL_LENGTH_WEST)

        wall_length = pd.concat(
            [
                wall_length_north,
                wall_length_east,
                wall_length_south,
                wall_length_west,
            ],
            axis=1,
        )

        frontal_length_north = Settings.FRONTAL_LENGTH_NORTH
        frontal_length_east = Settings.FRONTAL_LENGTH_EAST
        frontal_length_south = Settings.FRONTAL_LENGTH_SOUTH
        frontal_length_west = Settings.FRONTAL_LENGTH_WEST

        total_plan_area_geometry = pd.Series([polygon1.buffer(5), polygon2.buffer(5)])

        input_gdf = nodes.buildings_intersecting_plan_area(
            building_id,
            building_height,
            building_geometry,
            building_area,
            total_plan_area_geometry,
            wall_length,
            crs,
        )

        actual = nodes.frontal_length(input_gdf)
        expected = pd.concat(
            [
                pd.Series([2.0, 2.0], name=frontal_length_north),
                pd.Series([4.0, 4.0], name=frontal_length_east),
                pd.Series([1.0, 1.0], name=frontal_length_south),
                pd.Series([0, 0], name=frontal_length_west),
            ],
            axis=1,
        )
        # f"frontal_length test failed, expected {expected}, actual {actual}"
        pd.testing.assert_frame_equal(
            expected,
            actual,
        )

    def test_grimmond_oke_displacement_height(self):
        """Test that the function `grimmond_oke_displacement_height()` returns the correct value."""
        building_height = pd.Series([0, 1, 10.5, 75])
        expected = pd.Series([0.0, 0.67, 7.035, 50.25])
        actual = nodes.grimmond_oke_displacement_height(building_height)
        # f"grimmond_oke_displacement_height test failed, expected {expected}, actual {actual}",
        pd.testing.assert_series_equal(
            expected,
            actual,
        )

    def test_grimmond_oke_roughness_length(self):
        """Test that the function `grimmond_oke_roughness_length()` returns the correct value."""
        building_height = pd.Series([0, 1, 10.5, 75])
        expected = pd.Series([0.0, 0.1, 1.05, 7.5])
        actual = nodes.grimmond_oke_roughness_length(building_height)
        # f"grimmond_oke_roughness_length test failed, expected {expected}, actual {actual}",
        pd.testing.assert_series_equal(
            expected,
            actual,
        )

    def test_height_to_width_ratio(self):
        """Test that the function `height_to_width_ratio()` returns the correct value."""
        mean_building_height = pd.Series([0, 0, 1, 10.5, 75])
        average_distance_between_buildings = pd.Series([0, 1, 0, 10.5, 100])
        expected = pd.Series([float("nan"), 0.0, float("inf"), 1.0, 0.75])
        actual = nodes.height_to_width_ratio(
            mean_building_height, average_distance_between_buildings
        )
        # f"height_to_width_ratio test failed, expected {expected}, actual {actual}",
        pd.testing.assert_series_equal(
            expected,
            actual,
        )

    def test_lot_area(self):
        """Test that the function `lot_area()` returns the correct values."""

        buildings_intersecting_plan_area = gpd.GeoDataFrame(
            [[0, 0], [0, 1], [1, 0], [0, 2], [2, 2], [1, 1]]
        )
        buildings_intersecting_plan_area.columns = [
            Settings.TARGET_ID_FIELD,
            f"index_{Settings.NEIGHBOR}",
        ]
        building_surface_area = pd.Series([1, 10, 100])

        expected = pd.Series([37.0, 5.5, 100.0])
        actual = nodes.lot_area(buildings_intersecting_plan_area, building_surface_area)
        # f"lot_area test failed, expected {expected}, actual {actual}",
        pd.testing.assert_series_equal(
            expected,
            actual,
        )

    def test_macdonald_displacement_height(self):
        """Test that the function `macdonald_displacement_height()` returns the correct height."""
        alpha_coefficient = Settings.ALPHACOEFFICIENT
        building_height = pd.Series([0, 10, 10, 10, 75], copy=False)
        plan_area_fraction = pd.Series([0.5, 0.5, 0, 1, 0.5], copy=False)
        expected = pd.Series(
            [
                0,
                10 - (5 / math.pow(alpha_coefficient, 0.5)),
                0,
                10,
                75 - (37.5 / math.pow(alpha_coefficient, 0.5)),
            ],
            copy=False,
        )
        actual = nodes.macdonald_displacement_height(building_height, plan_area_fraction)
        # f"macdonald_displacement_height test failed, expected {expected}, actual {actual}",
        pd.testing.assert_series_equal(
            expected,
            actual,
        )

    def test_macdonald_roughness_length(self):
        """Test that the function `macdonald_roughness_length()` returns the correct values."""
        building_height = pd.Series([0, 10.5, 75])
        macdonald_displacement_height = pd.Series([1, 0.5, 0])
        frontal_area = pd.DataFrame(
            [[0, 1, 1.5, 75], [0, 1, 1.5, 75], [0, 1, 1.5, 75]],
            columns=[
                Settings.FRONTAL_AREA_INDEX_NORTH,
                Settings.FRONTAL_AREA_INDEX_EAST,
                Settings.FRONTAL_AREA_INDEX_SOUTH,
                Settings.FRONTAL_AREA_INDEX_WEST,
            ],
        )
        lot_area = pd.Series([10.5, 1, 1])
        expected = pd.DataFrame(
            [
                [math.nan, math.nan, math.nan, math.nan],
                [0.0, 5.7826527777812675, 6.39407319161897, 9.387129414165152],
                [0.0, 43.94617676155573, 48.47520029599251, 70.51086232991824],
            ]
        )
        expected.columns = [
            Settings.MACDONALD_ROUGHNESS_LENGTH_NORTH,
            Settings.MACDONALD_ROUGHNESS_LENGTH_EAST,
            Settings.MACDONALD_ROUGHNESS_LENGTH_SOUTH,
            Settings.MACDONALD_ROUGHNESS_LENGTH_WEST,
        ]
        actual = nodes.macdonald_roughness_length(
            building_height, macdonald_displacement_height, frontal_area, lot_area
        )
        # f"macdonald_displacement_height test failed, expected {expected}, actual {actual}",
        pd.testing.assert_frame_equal(
            expected,
            actual,
        )

    def test_mean_building_height(self):
        """Test that the function `mean_building_height()` returns the correct values."""

        buildings_intersecting_plan_area = gpd.GeoDataFrame(
            [[0, 10], [0, 5], [1, 0], [2, 3.14], [2, 11358], [0, 15]]
        )
        buildings_intersecting_plan_area.columns = [
            Settings.TARGET_ID_FIELD,
            Settings.NEIGHBOR_HEIGHT_FIELD,
        ]
        expected = pd.Series([10, 0.0, 5680.57])
        actual = nodes.mean_building_height(buildings_intersecting_plan_area)
        # f"mean_building_height test failed, expected {expected}, actual {actual}",
        pd.testing.assert_series_equal(
            expected,
            actual,
        )

    def test_plan_area_density(self):
        """Test that the function `plan_area_density()` returns the correct value."""

        # This uses different heights to test the function.
        # Plan area density should be the same whether the building height falls at or within the bins, which all buildings test.
        # Height bins that are greater than the building height should have a plan area density of zero.

        building_plan_area = pd.Series([20, 25, 30, 35])
        building_height = pd.Series([5, 4, 21, 75])
        total_plan_area = pd.Series([100, 100, 100, 100])

        rows, cols = (
            len(building_height.index),
            int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL),
        )
        plan_area_density = [[0 for i in range(cols)] for j in range(rows)]

        plan_area_density[0][0] = 0.2

        plan_area_density[1][0] = 0.25

        for i in range(0, 4):
            plan_area_density[2][i] = 0.3
        plan_area_density[2][4] = 0.3

        for i in range(0, 15):
            plan_area_density[3][i] = 0.35

        columns_plan_area_density = [
            f"{Settings.PLAN_AREA_DENSITY}_{i}"
            for i in range(int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL))
        ]

        actual = nodes.plan_area_density(building_plan_area, building_height, total_plan_area)
        expected = pd.DataFrame(plan_area_density, columns=columns_plan_area_density)

        # f"plan_area_density test failed, expected {expected}, actual {actual}"
        pd.testing.assert_frame_equal(
            expected,
            actual,
        )

    def test_plan_area_fraction(self):
        """Test that the function `plan_area_fraction()` returns the correct value."""

        building_plan_area = pd.Series([0, 0.01, 70, 100])
        total_plan_area = pd.Series([1, 1, 0.1, 0])
        expected = pd.Series([0.0, 0.01, 700, math.inf])
        actual = nodes.plan_area_fraction(building_plan_area, total_plan_area)
        # f"plan_area_fraction test failed, expected {expected}, actual {actual}",
        pd.testing.assert_series_equal(
            expected,
            actual,
        )

    def test_raupach_displacement_height(self):
        """Test that the function `raupach_displacement_height()` returns the correct value for each cardinal direction."""

        constant_75 = Settings.CONSTANT_75
        building_height = pd.Series([1, 75])
        frontal_area_index = pd.DataFrame([[0.5, 0.0, 1, 10], [0.5, 0.0, 1, 10]])
        expected = pd.DataFrame(
            [
                [
                    1 - ((1 - math.exp(-math.sqrt(constant_75))) / math.sqrt(constant_75)),
                    math.nan,
                    1 - ((1 - math.exp(-math.sqrt(constant_75 * 2))) / math.sqrt(constant_75 * 2)),
                    1
                    - ((1 - math.exp(-math.sqrt(constant_75 * 20))) / math.sqrt(constant_75 * 20)),
                ],
                [
                    75 * (1 - ((1 - math.exp(-math.sqrt(constant_75))) / math.sqrt(constant_75))),
                    math.nan,
                    75
                    * (
                        1
                        - ((1 - math.exp(-math.sqrt(constant_75 * 2))) / math.sqrt(constant_75 * 2))
                    ),
                    75
                    * (
                        1
                        - (
                            (1 - math.exp(-math.sqrt(constant_75 * 20)))
                            / math.sqrt(constant_75 * 20)
                        )
                    ),
                ],
            ]
        )
        expected.columns = [
            Settings.RAUPACH_DISPLACEMENT_HEIGHT_NORTH,
            Settings.RAUPACH_DISPLACEMENT_HEIGHT_EAST,
            Settings.RAUPACH_DISPLACEMENT_HEIGHT_SOUTH,
            Settings.RAUPACH_DISPLACEMENT_HEIGHT_WEST,
        ]
        actual = nodes.raupach_displacement_height(building_height, frontal_area_index)
        # f"raupach_displacement_height test failed, expected {expected}, actual {actual}",
        pd.testing.assert_frame_equal(
            expected,
            actual,
        )

    def test_raupach_roughness_length(self):
        """Test that the function `raupach_roughness_length()` returns the correct values."""
        building_height = pd.Series([0, 0.5, 75])
        frontal_area_index = pd.DataFrame([[0, 0.5, 1.0, 75], [0, 0.5, 1.0, 75], [0, 0.5, 1.0, 75]])
        raupach_displacement_height = pd.DataFrame(
            [[0, 0.5, 1, 75], [0, 0.5, 1, 75], [0, 0.5, 1, 75]]
        )
        expected = pd.DataFrame(
            [
                [math.nan, math.nan, math.nan, math.nan],
                [0.0002776596113860747, 0.0, -0.1993248047654186, -56.45689024365426],
                [0.04164894170791121, 22.09119560552915, 29.500071105281958, 0.0],
            ]
        )
        expected.columns = [
            Settings.RAUPACH_ROUGHNESS_LENGTH_NORTH,
            Settings.RAUPACH_ROUGHNESS_LENGTH_EAST,
            Settings.RAUPACH_ROUGHNESS_LENGTH_SOUTH,
            Settings.RAUPACH_ROUGHNESS_LENGTH_WEST,
        ]
        actual = nodes.raupach_roughness_length(
            building_height, frontal_area_index, raupach_displacement_height
        )
        # f"raupach_roughness_length test failed, expected {expected}, actual {actual}",
        pd.testing.assert_frame_equal(
            expected,
            actual,
        )

    def test_rooftop_area_density(self):
        """Test that the function `rooftop_area_density()` returns the correct value."""

        plan_area_density = pd.DataFrame(
            [[0.0, 1, 0.1, math.nan, math.inf, 100.0, 3.14, 112358, 0.0, 75, 1, 1, 1, 1, 1]]
        )
        expected = pd.DataFrame(
            [
                [
                    0.0,
                    1.0,
                    0.1,
                    math.nan,
                    math.inf,
                    100.0,
                    3.14,
                    112358.0,
                    0.0,
                    75.0,
                    1.0,
                    1.0,
                    1.0,
                    1.0,
                    1.0,
                ]
            ]
        )
        columns_rooftop_area_density = [
            f"{Settings.ROOFTOP_AREA_DENSITY}_{i}"
            for i in range(int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL))
        ]
        expected.columns = columns_rooftop_area_density
        actual = nodes.rooftop_area_density(plan_area_density)
        # f"rooftop_area_density test failed, expected {expected}, actual {actual}",
        pd.testing.assert_frame_equal(
            expected,
            actual,
        )

    def test_sky_view_factor(self):
        """Test that the function `sky_view_factor()` returns the correct value."""

        building_height = pd.Series([0, 0.1, 5.5, 5.5, 75])
        average_distance_between_buildings = pd.Series([1, 1, 1, 0, 1])
        expected = pd.Series(
            [
                1.0,
                0.9805806756909201,
                0.09053574604251861,
                6.123233995736766e-17,
                0.0066665185234566545,
            ]
        )
        actual = nodes.sky_view_factor(building_height, average_distance_between_buildings)
        # f"sky_view_factor test failed, expected {expected}, actual {actual}",
        pd.testing.assert_series_equal(
            expected,
            actual,
        )

    def test_standard_deviation_of_building_heights(self):
        """Test that the function `standard_deviation_of_building_heights()` returns the correct value."""

        buildings_intersecting_plan_area = gpd.GeoDataFrame(
            [[0, 10], [0, 1], [1, 0.1], [1, 0], [2, 112358], [0, 100]]
        )
        buildings_intersecting_plan_area.columns = [
            Settings.TARGET_ID_FIELD,
            Settings.NEIGHBOR_HEIGHT_FIELD,
        ]
        expected = pd.Series([54.74486277268398, 0.07071067811865477, 0])

        actual = nodes.standard_deviation_of_building_heights(buildings_intersecting_plan_area)
        # f"standard_deviation_of_building_heights test failed, expected {expected}, actual {actual}",
        pd.testing.assert_series_equal(
            expected,
            actual,
        )

    def test_wall_angle_direction_length(self):
        """Test that the function `wall_angle_direction_length()` returns the correct angle, direction, and length."""

        polygon_exterior = [[0, 1], [1, 1], [1, 0], [0, 0], [0, 1]]
        polygon_interior = [[0.25, 0.25], [0.25, 0.75], [0.75, 0.75], [0.75, 0.25]]

        north = Settings.NORTH
        south = Settings.SOUTH
        east = Settings.EAST
        west = Settings.WEST

        wall_angle = Settings.WALL_ANGLE
        wall_direction = Settings.WALL_DIRECTION
        wall_length = Settings.WALL_LENGTH

        square_root_one_half = 0.7071067811865476

        @dataclass
        class TestCase:
            name: str
            input: List[Polygon]
            expected: List[int]

        testcases = [
            TestCase(
                name="square",
                input=[Polygon(polygon_exterior)],
                expected=pd.concat(
                    [
                        pd.Series([[0.0, -90.0, 180.0, 90.0]], name=wall_angle),
                        pd.Series([[north, east, south, west]], name=wall_direction),
                        pd.Series([[1.0, 1.0, 1.0, 1.0]], name=wall_length),
                    ],
                    axis=1,
                ),
            ),
            TestCase(
                name="square with inner ring",
                input=[Polygon(polygon_exterior, [polygon_interior])],
                expected=pd.concat(
                    [
                        pd.Series([[0.0, -90.0, 180.0, 90.0]], name=wall_angle),
                        pd.Series([[north, east, south, west]], name=wall_direction),
                        pd.Series([[1.0, 1.0, 1.0, 1.0]], name=wall_length),
                    ],
                    axis=1,
                ),
            ),
            TestCase(
                name="45 degree triangle",
                input=[
                    Polygon(
                        [
                            [0, 0],
                            [square_root_one_half, square_root_one_half],
                            [0, square_root_one_half],
                        ]
                    )
                ],
                expected=pd.concat(
                    [
                        pd.Series([[45.0, 180.0, -90.0]], name=wall_angle),
                        pd.Series([[west, south, east]], name=wall_direction),
                        pd.Series(
                            [[1.0, square_root_one_half, square_root_one_half]], name=wall_length
                        ),
                    ],
                    axis=1,
                ),
            ),
            TestCase(
                name="135 degree triangle",
                input=[
                    Polygon(
                        [
                            [0, 0],
                            [-square_root_one_half, square_root_one_half],
                            [0, square_root_one_half],
                        ]
                    )
                ],
                expected=pd.concat(
                    [
                        pd.Series([[135.0, 0.0, -90.0]], name=wall_angle),
                        pd.Series([[south, north, east]], name=wall_direction),
                        pd.Series(
                            [[1.0, square_root_one_half, square_root_one_half]], name=wall_length
                        ),
                    ],
                    axis=1,
                ),
            ),
            TestCase(
                name="225 degree triangle",
                input=[
                    Polygon(
                        [
                            [0, 0],
                            [-square_root_one_half, -square_root_one_half],
                            [-square_root_one_half, 0],
                        ]
                    )
                ],
                expected=pd.concat(
                    [
                        pd.Series([[-135.0, 90.0, 0.0]], name=wall_angle),
                        pd.Series([[east, west, north]], name=wall_direction),
                        pd.Series(
                            [[1.0, square_root_one_half, square_root_one_half]], name=wall_length
                        ),
                    ],
                    axis=1,
                ),
            ),
            TestCase(
                name="325 degree triangle",
                input=[
                    Polygon(
                        [
                            [0, 0],
                            [square_root_one_half, -square_root_one_half],
                            [0, -square_root_one_half],
                        ]
                    )
                ],
                expected=pd.concat(
                    [
                        pd.Series([[-45.0, 180.0, 90.0]], name=wall_angle),
                        pd.Series([[north, south, west]], name=wall_direction),
                        pd.Series(
                            [[1.0, square_root_one_half, square_root_one_half]], name=wall_length
                        ),
                    ],
                    axis=1,
                ),
            ),
        ]

        for case in testcases:
            actual = nodes.wall_angle_direction_length(gpd.GeoSeries(case.input))
            expected = case.expected
            pd.testing.assert_frame_equal(
                expected,
                actual,
                f"wall_angle_direction_length test {case.name} failed, expected {expected}, actual {actual}",
            )

    def test_vertical_distribution_of_building_heights(self):
        """Test that the function `vertical_distribution_of_building_heights()` returns the correct dataframe."""
        building_height = pd.Series([0, 5, 5, 6, 7.5, 75])
        [
            f"{Settings.VERTICAL_DISTRIBUTION_OF_BUILDING_HEIGHTS}_{i}"
            for i in range(int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL))
        ]
        expected = pd.DataFrame(
            [
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            ],
            columns=[
                f"{Settings.VERTICAL_DISTRIBUTION_OF_BUILDING_HEIGHTS}_{i}"
                for i in range(
                    int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL)
                )
            ],
        )
        actual = nodes.vertical_distribution_of_building_heights(building_height)
        # f"vertical_distribution_of_building_heights test failed, expected {expected}, actual {actual}",
        pd.testing.assert_frame_equal(
            expected,
            actual,
        )

    def test_wall_length(self):
        """Test that the function `wall_length()` returns the correct length."""

        north = Settings.NORTH
        south = Settings.SOUTH
        east = Settings.EAST
        west = Settings.WEST

        wall_angle = Settings.WALL_ANGLE
        wall_direction = Settings.WALL_DIRECTION
        wall_length = Settings.WALL_LENGTH

        wall_length_north = Settings.WALL_LENGTH_NORTH
        wall_length_south = Settings.WALL_LENGTH_SOUTH
        wall_length_east = Settings.WALL_LENGTH_EAST
        wall_length_west = Settings.WALL_LENGTH_WEST

        square_root_one_half = 0.7071067811865476

        square_input = pd.concat(
            [
                pd.Series([[0.0, -90.0, 180.0, 90.0]], name=wall_angle),
                pd.Series([[north, east, south, west]], name=wall_direction),
                pd.Series([[1.0, 1.0, 1.0, 1.0]], name=wall_length),
            ],
            axis=1,
        )
        triangle_input = pd.concat(
            [
                pd.Series([[45.0, 180.0, -90.0]], name=wall_angle),
                pd.Series([[west, south, east]], name=wall_direction),
                pd.Series([[1.0, square_root_one_half, square_root_one_half]], name=wall_length),
            ],
            axis=1,
        )
        eight_sided_input = pd.concat(
            [
                pd.Series([[0.0, -90.0, 180.0, 90.0, -45.0, -135.0, 135.0, 45.0]], name=wall_angle),
                pd.Series(
                    [[north, east, south, west, north, east, south, west]], name=wall_direction
                ),
                pd.Series([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]], name=wall_length),
            ],
            axis=1,
        )

        @dataclass
        class TestCase:
            name: str
            input: pd.DataFrame
            expected: pd.DataFrame

        testcases = [
            TestCase(
                name="square",
                input=square_input,
                expected=pd.concat(
                    [
                        pd.Series([1.0], name=wall_length_north),
                        pd.Series([1.0], name=wall_length_east),
                        pd.Series([1.0], name=wall_length_south),
                        pd.Series([1.0], name=wall_length_west),
                    ],
                    axis=1,
                ),
            ),
            TestCase(
                name="triangle",
                input=triangle_input,
                expected=pd.concat(
                    [
                        pd.Series([0], name=wall_length_north),
                        pd.Series([square_root_one_half], name=wall_length_east),
                        pd.Series([square_root_one_half], name=wall_length_south),
                        pd.Series([1.0], name=wall_length_west),
                    ],
                    axis=1,
                ),
            ),
            TestCase(
                name="eight sided",
                input=eight_sided_input,
                expected=pd.concat(
                    [
                        pd.Series([6.0], name=wall_length_north),
                        pd.Series([8.0], name=wall_length_east),
                        pd.Series([10.0], name=wall_length_south),
                        pd.Series([12.0], name=wall_length_west),
                    ],
                    axis=1,
                ),
            ),
        ]

        for case in testcases:
            actual = nodes.wall_length(case.input)
            expected = case.expected
            pd.testing.assert_frame_equal(
                expected,
                actual,
                f"wall_length test {case.name} failed, expected {expected}, actual {actual}",
            )


if __name__ == "__main__":
    unittest.main()
