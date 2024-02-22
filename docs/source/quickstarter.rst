
Quickstarter
============


Data input
----------

The only input data required for `naturf` is a shapefile with building footprints and height data. There should be a field with a unique ID for each building the shapefile, and it should be in a projected coordinate system such as Alber Equal Area Conic. For input to the Weather Research and Forecasting model (WRF), the computed parameters for each building will be projected into WGS 84.

Either check out our interactive `quickstarter <quickstarter.rst>`_, or continue below to run `naturf` using a python file.

Install `naturf`
-----------------

In a clean virtual or Conda environment, install `naturf`. NOTE: For Conda environments using Python 3.12, the `setuptools` package does not work as intended. One workaround is to create a Conda environment in Python 3.11.

.. code:: bash

    pip install naturf

Edit config variables and create run script
-------------------------------------------

The `config` module in `naturf` sets the default names for variables used in the `naturf` workflow. The two variables below need to be modified to reflect the ID field and the building height field of the input shapefile. Instructions on changing field names will be given further below.

.. code:: python

    DATA_ID_FIELD_NAME
    DATA_HEIGHT_FIELD_NAME

Create a python script called `run.py` to run `naturf`. The code below runs the example data.

.. code:: python3

    from importlib.resources import files
    from naturf import driver

    input_shapefile_path = str(files("naturf.data").joinpath("C-5.shp"))
    inputs = {"input_shapefile": input_shapefile_path}
    outputs = ["write_binary", "write_index"]
    model = driver.Model(inputs, outputs)

    df = model.execute()
    model.graph()

To run data other than the example data, create the `run.py` below.

.. code:: python3

    from naturf import driver
    from naturf.config import Settings

    Settings.DATA_ID_FIELD_NAME = "YOUR_ID_FIELD_NAME_HERE"
    Settings.DATA_HEIGHT_FIELD_NAME = "YOUR_HEIGHT_FIELD_NAME_HERE"

    input_shapefile_path = "PATH_TO_YOUR_DATA"
    inputs = {"input_shapefile": input_shapefile_path}
    outputs = ["write_binary", "write_index"]
    model = driver.Model(inputs, outputs)

    df = model.execute()
    model.graph()

Run `naturf`
------------
This will run all functions required to create the output specified in the `run.py` `output_columns` variable. Currently `write_binary` and `write_index`. The `path` variable should point towards the input shapefile.

.. code:: bash

    python run.py
