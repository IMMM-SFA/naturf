
Quickstarter
============


Input data
----------

The only input data required for `naturf` is a shapefile with building footprints and height data. There should be a field with a unique ID for each building the shapefile, and it should be in a projected coordinate system such as Alber Equal Area Conic. For input to the Weather Research and Forecasting model (WRF), the computed parameters for each building will be projected into WGS 84.

Either run the ipynb `quickstarter <https://github.com/IMMM-SFA/naturf/blob/main/notebooks/quickstarter.ipynb>`_, or continue below to run `naturf` using a python file.

.. note::
    Users need to `download graphviz <https://graphviz.org/download/>`_ to visualize the Directed Acyclic Graph (DAG).

1. Install `naturf`
-------------------

In a clean virtual or Conda environment, install `naturf`. NOTE: For Conda environments using Python 3.12, the `setuptools` package does not work as intended. One workaround is to create a Conda environment in Python 3.11.

.. code:: bash

    $ pip install naturf

2. Edit config variables and create run script
----------------------------------------------

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

3. Run `naturf`
---------------
This will run all functions required to create the output specified in the `run.py` `output_columns` variable. Currently `write_binary` and `write_index`. The `path` variable should point towards the input shapefile.

.. code:: bash

    $ python run.py


Track execution with the `Hamilton UI <https://github.com/dagworks-inc/hamilton/tree/main/ui>`_
___________________________________________________________________________________________________________
If you would like to track the execution of the `naturf` workflow, there is an interactive UI
available that allows you to track the progress of the workflow, view logs, and capture summary statistics of outputs.

1. Pre-requisites:

* Have the self-hosted Hamilton UI running and you have created a user and project. If not, follow the instructions in the `Hamilton UI README <https://github.com/dagworks-inc/hamilton/tree/main/ui>`_.
* Or, have a free account on `DAGWorks Inc. <https://www.dagworks.io/hamilton>`_, and have created a project and an API Key.
* Have the right SDK installed. If not, install it using the following command:

    .. code:: bash

        $ pip install sf-hamilton[sdk]  # if self-hosting the Hamilton UI
        $ pip install dagworks-sdk  # if using the hosted Hamilton UI via DAGWorks Inc.


2. Set the requisite environment variables:

.. code:: bash

    $ export HAMILTON_UI_USERNAME="<your username>"
    $ export HAMILTON_UI_PROJECT_ID="<your project ID>"
    $ export DAGWORKS_API_KEY="<your DAGWorks API key>"  # set this is you are using the hosted Hamilton UI via DAGWorks Inc.

3. Run the python file (again)!

Underneath, in naturf driver, the correct SDK will be invoked and the execution will be tracked on the Hamilton UI.

.. code:: bash

    $ python run.py

You should see logs emitted that provide a URL to click to see execution!
