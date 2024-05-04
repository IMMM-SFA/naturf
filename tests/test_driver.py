import os
import unittest
from unittest.mock import patch

from naturf import driver


class TestDriverGuardAgainstSDK(unittest.TestCase):
    INPUTS = {
        "input_shapefile": os.path.join("naturf", "data", "C-5.shp"),
        "radius": 100,
        "cap_style": 1,
    }

    # mock the driver module variables
    @patch("naturf.driver.HAMILTON_UI_PROJECT_ID", "3")
    @patch("naturf.driver.HAMILTON_UI_USERNAME", "test@test")
    def tests_sdk_not_installed(self):
        """tests that things work if the sdk is not installed"""
        # this line running without error means that our checks worked
        driver.Model(inputs=TestDriverGuardAgainstSDK.INPUTS, outputs=["input_shapefile_df"])

    @patch("naturf.driver.HAMILTON_UI_PROJECT_ID", "3")
    @patch("naturf.driver.HAMILTON_UI_USERNAME", "test@test")
    @patch("naturf.driver.DAGWORKS_API_KEY", "some-api-key")
    def tests_sdk_not_installed_DW(self):
        """tests that things work if the sdk is not installed for the DW path"""
        # this line running without error means that our checks worked
        driver.Model(inputs=TestDriverGuardAgainstSDK.INPUTS, outputs=["input_shapefile_df"])


if __name__ == "__main__":
    unittest.main()
