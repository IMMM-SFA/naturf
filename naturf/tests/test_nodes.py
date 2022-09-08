import pkg_resources
import unittest


class TestNodes(unittest.TestCase):

    INPUTS = {"input_shapefile": pkg_resources.resource_filename("naturf", "data", "inputs", "C-5.shp"),
              "radius": 100,
              "cap_style": 1}

    OUTPUTS = ["distance_to_neighbor", "angle_in_degrees_to_neighbor", "orientation_to_neighbor"]

    def test_something(self):

        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
