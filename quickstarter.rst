
Quickstarter
============


Data input
----------

The only input data required for *naturf* is a shapefile with building footprints and height data. There should be a field with a unique ID for each building the shapefile, and it should be in a projected coordinate system such as Alber Equal Area Conic. For input to the Weather Research and Forecasting model (WRF), the computed parameters for each building will be projected into WGS 84.

Clone git repository
--------------------

.. code:: bash

    git clone https://github.com/IMMM-SFA/naturf.git

Install dependencies
--------------------
In the directory where the *naturf* repository was cloned, run the following command to install all dependencies in the current environment.

.. code:: bash

    pip install .

Edit config file
----------------

The *config.py* file in the naturf/ directory sets the default names for variables used in the *naturf* workflow. The two variables below need to be modified to reflect the ID field and the building height field of the input shapefile.

.. code:: python

    data_id_field_name
    data_height_field_name


Run `naturf` using hamilton
---------------------------
This will run all functions required to create the output specified in `hamilton_run.py` `output_columns` variable. Currently `write_binary` and `write_index`. The `path` variable should point towards the input shapefile.

.. code:: bash

    python hamilton_run.py
