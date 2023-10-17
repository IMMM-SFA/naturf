import math
import os
import pkg_resources
import unittest

from dataclasses import dataclass
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon, JOIN_STYLE
from typing import List

from naturf.driver import Model
import naturf.nodes as nodes
from naturf.config import Settings


class TestNodes(unittest.TestCase):
    INPUTS = {
        "input_shapefile": pkg_resources.resource_filename(
            "naturf", os.path.join("data", "inputs", "C-5.shp")
        ),
        "radius": 100,
        "cap_style": 1,
    }

    def test_angle_in_degrees_to_neighbor(self):
        "Test that the function `angle_in_degrees_to_neighbor()` returns the correct angle."

        @dataclass
        class TestCase:
            name: str
            target_input: List[Point]
            neighbor_input: List[Point]
            expected: List[int | float | str]

        testcases = [
            TestCase(
                name="same_centroid",
                target_input=[Point(1, 1), Point(0, 0)],
                neighbor_input=[Point(1, 1), Point(0, 0)],
                expected=[0.0, 0.0],
            ),
            TestCase(
                name="east",
                target_input=[Point(0, 0)],
                neighbor_input=[Point(1, 0)],
                expected=[0.0],
            ),
            TestCase(
                name="west",
                target_input=[Point(0, 0)],
                neighbor_input=[Point(-1, 0)],
                expected=[180.0],
            ),
            TestCase(
                name="north",
                target_input=[Point(0, 0)],
                neighbor_input=[Point(0, 1)],
                expected=[90.0],
            ),
            TestCase(
                name="south",
                target_input=[Point(0, 0)],
                neighbor_input=[Point(0, -1)],
                expected=[270.0],
            ),
            TestCase(
                name="northeast",
                target_input=[Point(0, 0)],
                neighbor_input=[Point(10, 10 * np.sqrt(3))],
                expected=[60.0],
            ),
            TestCase(
                name="northwest",
                target_input=[Point(0, 0)],
                neighbor_input=[Point(-10, 10 * np.sqrt(3))],
                expected=[120.0],
            ),
            TestCase(
                name="southeast",
                target_input=[Point(0, 0)],
                neighbor_input=[Point(10, -10 * np.sqrt(3))],
                expected=[300.0],
            ),
            TestCase(
                name="southwest",
                target_input=[Point(0, 0)],
                neighbor_input=[Point(-10, -10 * np.sqrt(3))],
                expected=[240.0],
            ),
        ]

        for case in testcases:
            actual = nodes.angle_in_degrees_to_neighbor(
                gpd.GeoSeries(case.target_input), gpd.GeoSeries(case.neighbor_input)
            )
            expected = pd.Series(case.expected)
            pd.testing.assert_series_equal(
                expected,
                actual,
                f"angle_in_degrees_to_neighbor test {case.name} failed, expected {expected}, actual {actual}",
            )

    def test_area_weighted_mean_of_building_heights(self):
        "Test that the function `area_weighted_mean_of_building_heights()` returns the correct value."
        # ID 0: one building
        # ID 1: two buildings
        # ID 2: multiple buildings, decimal values
        data = [[0, 10, 10], [1, 2, 10], [1, 1, 10], [2, 0.1, 10], [2, 0.9, 30], [2, 12, 0.25]]
        buildings_intersecting_plan_area = pd.DataFrame(
            data,
            columns=[
                Settings.target_id_field,
                Settings.neighbor_height_field,
                Settings.neighbor_area_field,
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

        index = pd.Index([0, 0, 1, 1, 2, 2, 3, 3, 3, 4], name=Settings.neighbor_id_field)
        distance = pd.Series(
            [1, 2, 1, 3, 1, 1, 3, 0, 3, 0], index, name=Settings.distance_between_buildings
        )

        default_street_width = Settings.DEFAULT_STREET_WIDTH

        expected = pd.Series(
            [1.5, 2.0, 1.0, 3.0, default_street_width],
            name=Settings.average_distance_between_buildings,
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

        wall_length_north = pd.Series([1.0, 1.0], name=Settings.wall_length_north)
        wall_length_east = pd.Series([1.0, 1.0], name=Settings.wall_length_east)
        wall_length_south = pd.Series([1.0, 1.0], name=Settings.wall_length_south)
        wall_length_west = pd.Series([1.0, 1.0], name=Settings.wall_length_west)

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
            "`input_shapefile_df` data type not matching expected",
        )

    def test_frontal_area_density(self):
        """Test that the function `frontal_area_density()` returns the correct value."""

        # This uses different heights to test the function.
        # Building 1 is 5m tall to test that using one height bin works correctly.
        # Building 2 is 4m tall to test that using a height less than a full bin works correctly.
        # Building 3 is 21m tall to test that using a height >5m but less than a full bin works correctly.
        # Building 4 is 75m tall to test that a full-height building works correctly.

        frontal_length_north = Settings.frontal_length_north
        frontal_length_east = Settings.frontal_length_east
        frontal_length_south = Settings.frontal_length_south
        frontal_length_west = Settings.frontal_length_west

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
                f"{Settings.frontal_area_north}_{i}"
                for i in range(
                    int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL)
                )
            ],
            [
                f"{Settings.frontal_area_east}_{i}"
                for i in range(
                    int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL)
                )
            ],
            [
                f"{Settings.frontal_area_south}_{i}"
                for i in range(
                    int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL)
                )
            ],
            [
                f"{Settings.frontal_area_west}_{i}"
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
        pd.testing.assert_frame_equal(
            expected,
            actual,
            f"frontal_area_density test failed, expected {expected}, actual {actual}",
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

        wall_length_north = pd.Series([1.0, 1.0], name=Settings.wall_length_north)
        wall_length_east = pd.Series([1.0, 3.0], name=Settings.wall_length_east)
        wall_length_south = pd.Series([0, 1.0], name=Settings.wall_length_south)
        wall_length_west = pd.Series([0, 0], name=Settings.wall_length_west)

        wall_length = pd.concat(
            [
                wall_length_north,
                wall_length_east,
                wall_length_south,
                wall_length_west,
            ],
            axis=1,
        )

        frontal_length_north = Settings.frontal_length_north
        frontal_length_east = Settings.frontal_length_east
        frontal_length_south = Settings.frontal_length_south
        frontal_length_west = Settings.frontal_length_west

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
        pd.testing.assert_frame_equal(
            expected, actual, f"frontal_length test failed, expected {expected}, actual {actual}"
        )

    def test_grimmond_oke_displacement_height(self):
        """Test that the function `grimmond_oke_displacement_height()` returns the correct value."""
        building_height = pd.Series([0, 1, 10.5, 75])
        expected = pd.Series([0.0, 0.67, 7.035, 50.25])
        actual = nodes.grimmond_oke_displacement_height(building_height)
        pd.testing.assert_series_equal(
            expected,
            actual,
            f"grimmond_oke_displacement_height test failed, expected {expected}, actual {actual}",
        )

    def test_grimmond_oke_roughness_length(self):
        """Test that the function `grimmond_oke_roughness_length()` returns the correct value."""
        building_height = pd.Series([0, 1, 10.5, 75])
        expected = pd.Series([0.0, 0.1, 1.05, 7.5])
        actual = nodes.grimmond_oke_roughness_length(building_height)
        pd.testing.assert_series_equal(
            expected,
            actual,
            f"grimmond_oke_roughness_length test failed, expected {expected}, actual {actual}",
        )

    def test_height_to_width_ratio(self):
        """Test that the function `height_to_width_ratio()` returns the correct value."""
        mean_building_height = pd.Series([0, 0, 1, 10.5, 75])
        average_distance_between_buildings = pd.Series([0, 1, 0, 10.5, 100])
        expected = pd.Series([float("nan"), 0.0, float("inf"), 1.0, 0.75])
        actual = nodes.height_to_width_ratio(
            mean_building_height, average_distance_between_buildings
        )
        pd.testing.assert_series_equal(
            expected,
            actual,
            f"height_to_width_ratio test failed, expected {expected}, actual {actual}",
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
        pd.testing.assert_series_equal(
            expected,
            actual,
            f"macdonald_displacement_height test failed, expected {expected}, actual {actual}",
        )

    def test_orientation_to_neighbor(self):
        """Test that the function `orientation_to_neighbor()` returns either `north_south` or `east_west` correctly."""

        @dataclass
        class TestCase:
            name: str
            input: List[int | float]
            expected: List[int | str]

        east_west = Settings.east_west
        north_south = Settings.north_south

        testcases = [
            TestCase(name="zero_degrees", input=[0.0, -0.0], expected=[east_west, east_west]),
            TestCase(name="north_south", input=[90, 270], expected=[north_south, north_south]),
            TestCase(
                name="east_west",
                input=[45, 135, 225, 315, 360],
                expected=[east_west, east_west, east_west, east_west, east_west],
            ),
        ]

        for case in testcases:
            actual = nodes.orientation_to_neighbor(pd.Series(case.input))
            expected = pd.Series(case.expected)
            pd.testing.assert_series_equal(
                expected,
                actual,
                f"orientation_to_neighbor test {case.name} failed, expected {expected}, actual {actual}",
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
            f"{Settings.plan_area_density}_{i}"
            for i in range(int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL))
        ]

        actual = nodes.plan_area_density(building_plan_area, building_height, total_plan_area)
        expected = pd.DataFrame(plan_area_density, columns=columns_plan_area_density)

        pd.testing.assert_frame_equal(
            expected, actual, f"plan_area_density test failed, expected {expected}, actual {actual}"
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
                    float("nan"),
                    1 - ((1 - math.exp(-math.sqrt(constant_75 * 2))) / math.sqrt(constant_75 * 2)),
                    1
                    - ((1 - math.exp(-math.sqrt(constant_75 * 20))) / math.sqrt(constant_75 * 20)),
                ],
                [
                    75 * (1 - ((1 - math.exp(-math.sqrt(constant_75))) / math.sqrt(constant_75))),
                    float("nan"),
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
            Settings.raupach_displacement_height_north,
            Settings.raupach_displacement_height_east,
            Settings.raupach_displacement_height_south,
            Settings.raupach_displacement_height_west,
        ]
        actual = nodes.raupach_displacement_height(building_height, frontal_area_index)
        pd.testing.assert_frame_equal(
            expected,
            actual,
            f"raupach_displacement_height test failed, expected {expected}, actual {actual}",
        )

    def test_wall_angle_direction_length(self):
        """Test that the function `wall_angle_direction_length()` returns the correct angle, direction, and length."""

        polygon_exterior = [[0, 1], [1, 1], [1, 0], [0, 0], [0, 1]]
        polygon_interior = [[0.25, 0.25], [0.25, 0.75], [0.75, 0.75], [0.75, 0.25]]

        north = Settings.north
        south = Settings.south
        east = Settings.east
        west = Settings.west

        wall_angle = Settings.wall_angle
        wall_direction = Settings.wall_direction
        wall_length = Settings.wall_length

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
            f"{Settings.vertical_distribution_of_building_heights}_{i}"
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
                f"{Settings.vertical_distribution_of_building_heights}_{i}"
                for i in range(
                    int(Settings.MAX_BUILDING_HEIGHT / Settings.BUILDING_HEIGHT_INTERVAL)
                )
            ],
        )
        actual = nodes.vertical_distribution_of_building_heights(building_height)
        pd.testing.assert_frame_equal(
            expected,
            actual,
            f"vertical_distribution_of_building_heights test failed, expected {expected}, actual {actual}",
        )

    def test_wall_length(self):
        """Test that the function `wall_length()` returns the correct length."""

        north = Settings.north
        south = Settings.south
        east = Settings.east
        west = Settings.west

        wall_angle = Settings.wall_angle
        wall_direction = Settings.wall_direction
        wall_length = Settings.wall_length

        wall_length_north = Settings.wall_length_north
        wall_length_south = Settings.wall_length_south
        wall_length_east = Settings.wall_length_east
        wall_length_west = Settings.wall_length_west

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
