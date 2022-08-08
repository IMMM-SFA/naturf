import unittest

import pandas as pd
import geopandas as gpd

import naturf.utils as utils


class TestUtils(unittest.TestCase):

    SAMPLE_GDF = gpd.GeoDataFrame({"fid": [1, 2],
                                   "field_1": [1, 2],
                                   "field_2": [3, 4],
                                   "geometry": [0, 0]})
    # expected data outcomes
    GDF_1 = gpd.GeoDataFrame({"fid": [1, 2],
                              "field_1": [1, 2],
                              "field_2": [3, 4],
                              "geometry": [0, 0]})

    FIELDS_1 = ['field_1', 'field_2']

    GDF_2 = gpd.GeoDataFrame({"fid": [1, 2],
                              "field_1": [1, 2],
                              "field_2": [3, 4],
                              "geometry": [0, 0]})

    FIELDS_2 = ['field_1']

    GDF_3 = gpd.GeoDataFrame({"fid": [1, 2],
                              "field_1": [1, 2],
                              "field_2": [3, 4],
                              "geometry": [0, 0],
                              "field_x": [127, 127]})

    FIELDS_3 = ['field_x']



    def test_target_field_list(self):
        """Ensure expected functionlaity of the target field list function."""

        # evaluate case with two fields passed as list
        gdf_1, fields_1 = utils.set_target_field_list(geodataframe=self.SAMPLE_GDF,
                                                      fields=["field_1", "field_2"],
                                                      default_value=127)

        pd.testing.assert_frame_equal(self.GDF_1, gdf_1)
        self.assertEqual(self.FIELDS_1, fields_1)

        # evaluate case with one field passed as string
        gdf_2, fields_2 = utils.set_target_field_list(geodataframe=self.SAMPLE_GDF,
                                                      fields="field_1",
                                                      default_value=127)

        pd.testing.assert_frame_equal(self.GDF_2, gdf_2)
        self.assertEqual(self.FIELDS_2, fields_2)

        # evaluate case with one field not in gdf passed as string
        gdf_3, fields_3 = utils.set_target_field_list(geodataframe=self.SAMPLE_GDF,
                                                      fields="field_x",
                                                      default_value=127)

        pd.testing.assert_frame_equal(self.GDF_3, gdf_3)
        self.assertEqual(self.FIELDS_3, fields_3)

        # evaluate case with one field not in gdf passed as integer, expect failure
        with self.assertRaises(TypeError):

            gdf_4, fields_4 = utils.set_target_field_list(geodataframe=self.SAMPLE_GDF,
                                                          fields=123,
                                                          default_value=127)


if __name__ == '__main__':
    unittest.main()
