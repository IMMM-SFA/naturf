import math
import os
import shutil
import tempfile
import unittest

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon
import xarray as xr

import naturf.output as output
from naturf.config import Settings


class TestNodes(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    INPUTS = {
        "input_shapefile": os.path.join("naturf", "data", "C-5.shp"),
        "radius": 100,
        "cap_style": 1,
    }

    def test_aggregate_rasters(self):
        "Test that the function `aggregate_rasters()` returns the correct Xarray."
        rasterize_parameters = xr.Dataset(
            data_vars=dict(
                var0=(["x", "y"], np.array([[0, 1], [2, 3]])),
                var1=(["x", "y"], np.array([[10, 15.5], [314159, 75]])),
                building_count=(["x", "y"], np.array([[0, 1], [10, 75]])),
            ),
            coords=dict(
                lat=(["x"], [0, 1]),
                lon=(["y"], [0, 1]),
            ),
        )
        expected = xr.Dataset(
            data_vars=dict(
                var0=(["x", "y"], np.array([[0.0, 1.0], [0.2, 0.04]])),
                var1=(["x", "y"], np.array([[math.inf, 15.5], [31415.9, 1.0]])),
                building_count=(["x", "y"], np.array([[0.0, 1.0], [1.0, 1.0]])),
            ),
            coords=dict(
                lat=(["x"], [0, 1]),
                lon=(["y"], [0, 1]),
            ),
        )
        actual = output.aggregate_rasters(rasterize_parameters)
        xr.testing.assert_equal(expected, actual)

    def test_merge_parameters(self):
        """Test the function `merge_parameters()` to ensure it outputs the right type and shape GeoDataFrame."""

        frontal_area_density = pd.DataFrame(
            {
                Settings.FRONTAL_AREA_NORTH: [0.1, 0.2],
                Settings.FRONTAL_AREA_EAST: [0.3, 0.4],
                Settings.FRONTAL_AREA_SOUTH: [0.5, 0.6],
                Settings.FRONTAL_AREA_WEST: [0.7, 0.8],
            }
        )
        plan_area_density = pd.DataFrame({Settings.PLAN_AREA_DENSITY: [0.5, 0.6]})
        rooftop_area_density = pd.DataFrame({Settings.ROOFTOP_AREA_DENSITY: [0.9, 1.0]})
        plan_area_fraction = pd.Series([0.5, 0.5])
        mean_building_height = pd.Series([10, 20])
        standard_deviation_of_building_heights = pd.Series([2, 3])
        area_weighted_mean_of_building_heights = pd.Series([12, 22])
        building_surface_area_to_plan_area_ratio = pd.Series([1.2, 1.3])
        frontal_area_index = pd.DataFrame(
            {
                Settings.FRONTAL_AREA_INDEX_NORTH: [0.0, 0.1],
                Settings.FRONTAL_AREA_INDEX_EAST: [0.2, 0.3],
                Settings.FRONTAL_AREA_INDEX_SOUTH: [0.4, 0.5],
                Settings.FRONTAL_AREA_INDEX_WEST: [0.6, 0.7],
            }
        )
        complete_aspect_ratio = pd.Series([1.5, 1.6])
        height_to_width_ratio = pd.Series([1.7, 1.8])
        sky_view_factor = pd.Series([0.9, 0.8])
        grimmond_oke_roughness_length = pd.Series([0.7, 0.6])
        grimmond_oke_displacement_height = pd.Series([0.5, 0.4])
        raupach_roughness_length = pd.DataFrame(
            {
                Settings.RAUPACH_ROUGHNESS_LENGTH_NORTH: [0.3, 0.2],
                Settings.RAUPACH_ROUGHNESS_LENGTH_EAST: [0.2, 0.3],
                Settings.RAUPACH_ROUGHNESS_LENGTH_SOUTH: [0.4, 0.5],
                Settings.RAUPACH_ROUGHNESS_LENGTH_WEST: [0.6, 0.7],
            }
        )
        raupach_displacement_height = pd.DataFrame(
            {
                Settings.RAUPACH_DISPLACEMENT_HEIGHT_NORTH: [0.0, 0.1],
                Settings.RAUPACH_DISPLACEMENT_HEIGHT_EAST: [0.2, 0.3],
                Settings.RAUPACH_DISPLACEMENT_HEIGHT_SOUTH: [0.4, 0.5],
                Settings.RAUPACH_DISPLACEMENT_HEIGHT_WEST: [0.6, 0.7],
            }
        )
        macdonald_roughness_length = pd.DataFrame(
            {
                Settings.MACDONALD_ROUGHNESS_LENGTH_NORTH: [0.0, 0.1],
                Settings.MACDONALD_ROUGHNESS_LENGTH_EAST: [0.2, 0.3],
                Settings.MACDONALD_ROUGHNESS_LENGTH_SOUTH: [0.4, 0.5],
                Settings.MACDONALD_ROUGHNESS_LENGTH_WEST: [0.6, 0.7],
            }
        )
        macdonald_displacement_height = pd.Series([0.8, 0.9])
        vertical_distribution_of_building_heights = pd.DataFrame(
            {Settings.VERTICAL_DISTRIBUTION_OF_BUILDING_HEIGHTS: [10, 20]}
        )
        building_geometry = pd.Series([Point(0, 0), Point(1, 1)])
        target_crs = Settings.OUTPUT_CRS

        result = output.merge_parameters(
            frontal_area_density,
            plan_area_density,
            rooftop_area_density,
            plan_area_fraction,
            mean_building_height,
            standard_deviation_of_building_heights,
            area_weighted_mean_of_building_heights,
            building_surface_area_to_plan_area_ratio,
            frontal_area_index,
            complete_aspect_ratio,
            height_to_width_ratio,
            sky_view_factor,
            grimmond_oke_roughness_length,
            grimmond_oke_displacement_height,
            raupach_roughness_length,
            raupach_displacement_height,
            macdonald_roughness_length,
            macdonald_displacement_height,
            vertical_distribution_of_building_heights,
            building_geometry,
            target_crs,
        )

        assert isinstance(result, gpd.GeoDataFrame), "Output is not a GeoDataFrame"
        assert list(result.columns) == [
            "frontal_area_north",
            "frontal_area_east",
            "frontal_area_south",
            "frontal_area_west",
            "plan_area_density",
            "rooftop_area_density",
            "plan_area_fraction",
            "mean_building_height",
            "standard_deviation_of_building_heights",
            "area_weighted_mean_of_building_heights",
            "building_surface_area_to_plan_area_ratio",
            "frontal_area_index_north",
            "frontal_area_index_east",
            "frontal_area_index_south",
            "frontal_area_index_west",
            "complete_aspect_ratio",
            "height_to_width_ratio",
            "sky_view_factor",
            "grimmond_oke_roughness_length",
            "grimmond_oke_displacement_height",
            "raupach_roughness_length_north",
            "raupach_displacement_height_north",
            "raupach_roughness_length_east",
            "raupach_displacement_height_east",
            "raupach_roughness_length_south",
            "raupach_displacement_height_south",
            "raupach_roughness_length_west",
            "raupach_displacement_height_west",
            "macdonald_roughness_length_north",
            "macdonald_roughness_length_east",
            "macdonald_roughness_length_south",
            "macdonald_roughness_length_west",
            "macdonald_displacement_height",
            "vertical_distribution_of_building_heights",
            "building_geometry",
        ], "Output columns are not as expected"
        assert result.crs == target_crs, "Output CRS is not as expected"

    def test_numpy_to_binary(self):
        """Test the function `numpy_to_binary()` to ensure it outputs the right type and length binary file."""

        test_array = np.array([[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [10, 11, 12]]])

        binary_output = output.numpy_to_binary(test_array)

        assert isinstance(binary_output, bytes), "Output is not of type 'bytes'"
        assert len(binary_output) == 48, "Binary output length is not as expected"

    def test_raster_to_numpy(self):
        """Test the function `raster_to_numpy()` to ensure it outputs the right type and shape numpy array."""

        aggregate_rasters = xr.Dataset(
            {
                "parameter1": (("x", "y"), np.random.rand(5, 5)),
                "parameter2": (("x", "y"), np.random.rand(5, 5)),
                "building_count": (("x", "y"), np.random.randint(0, 10, (5, 5))),
            },
            coords={"x": range(5), "y": range(5)},
        )

        result = output.raster_to_numpy(aggregate_rasters)

        assert isinstance(result, np.ndarray), "Output is not a numpy array"
        assert result.shape == (132, 5, 5), "Output shape is not as expected"
        assert result.dtype == np.float32, "Output dtype is not np.float32"

    def test_rasterize_parameters(self):
        """Test the function `rasterize_parameters()` to ensure it outputs the right type and shape xr.Dataset."""

        merge_parameters = gpd.GeoDataFrame(
            {
                "parameter1": [1, 2, 3],
                "parameter2": [4, 5, 6],
                Settings.GEOMETRY_FIELD: [Point(0, 0), Point(1, 1), Point(2, 2)],
            }
        )

        result = output.rasterize_parameters(merge_parameters)

        assert isinstance(result, xr.Dataset), "Output is not an xr.Dataset"
        assert list(result.keys()) == [
            "parameter1",
            "parameter2",
            "building_count",
        ], "Output keys are not as expected"
        assert result["parameter1"].shape == (
            2400,
            2400,
        ), "Output shape for 'parameter1' is not as expected"
        assert result["parameter2"].shape == (
            2400,
            2400,
        ), "Output shape for 'parameter2' is not as expected"

    def test_write_binary(self):
        """Test that the function `write_binary()` writes a binary file correctly."""

        raster_to_numpy = np.zeros((132, 10, 10))
        test_binary_filename = "00001-00010.00001-00010"
        numpy_to_binary = raster_to_numpy.tobytes()

        output.write_binary(numpy_to_binary, raster_to_numpy)

        assert os.path.exists(test_binary_filename), "Binary file was not created."
        with open(test_binary_filename, "rb") as binary_file:
            content = binary_file.read()
            assert len(content) == 105648, "Content length is not as expected"

        os.remove(test_binary_filename)

    def test_write_index(self):
        """Test that the function `write_index()` writes an index file and contains the correct values."""

        raster_to_numpy = np.zeros((132, 10, 10))
        polygon1 = Polygon([[0, 0], [0, 1], [1, 1], [1, 0]])
        polygon2 = Polygon([[3, 3], [3, 4], [4, 4], [4, 3]])
        building_geometry = pd.Series([polygon1, polygon2])
        target_crs = "epsg:3857"
        test_index_filename = "test_index"

        file_path = self.test_dir + "/" + test_index_filename
        output.write_index(raster_to_numpy, building_geometry, target_crs, index_filename=file_path)

        assert os.path.exists(file_path), "Index file was not created."
        with open(file_path, "r") as index:
            content = index.read()
            assert "type=continuous" in content, "Index file type is not as expected."
            assert "projection=albers_nad83" in content, "Index file projection is not as expected."
            assert (
                "missing_value=-999900." in content
            ), "Index file missing_value is not as expected."
            assert "dy=0.00083333333" in content, "Index file dy is not as expected."
            assert "dx=0.00083333333" in content, "Index file dx is not as expected."
            assert "known_x=1" in content, "Index file known_x is not as expected."
            assert "known_y=1" in content, "Index file known_y is not as expected."
            assert "known_lat=0.0" in content, "Index file known_lat is not as expected."
            assert "known_lon=0.0" in content, "Index file known_lon is not as expected."
            assert "truelat1=45.5" in content, "Index file truelat1 is not as expected."
            assert "truelat2=29.5" in content, "Index file truelat2 is not as expected."
            assert (
                "stdlon=1.7966305682390428e-05" in content
            ), "Index file stdlon is not as expected."
            assert "wordsize=4" in content, "Index file wordsize is not as expected."
            assert "endian=big" in content, "Index file endian is not as expected."
            assert "signed=no" in content, "Index file signed is not as expected."
            assert "tile_x=10" in content, "Index file tile_x is not as expected."
            assert "tile_y=10" in content, "Index file tile_y is not as expected."
            assert "tile_z=132" in content, "Index file tile_z is not as expected."
            assert 'units="dimensionless"' in content, "Index file units is not as expected."
            assert "scale_factor=0.0001" in content, "Index file scale_factor is not as expected."
            assert (
                'description="Urban_Parameters"' in content
            ), "Index file description is not as expected."


if __name__ == "__main__":
    unittest.main()
