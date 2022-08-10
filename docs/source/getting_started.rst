Getting started
===============

About
-----

The Neighborhood Adaptive Tissues for Urban Resilience Futures tool (**naturf**) enables the examination of the effect of urban morphology at variable resolutions on the urban microclimate through the Weather Research and Forecasting model (WRF). Following the work of Ching et al. (citation) on NUDAPT/WUDAPT, **naturf** calculates 132 urban parameters based on shapefiles of building footprints and heights; however, **naturf** is capable of compiling these urban parameters at finer, sub-kilometer resolutions than offered by NUDAPT/WUDAPT.

**naturf** takes in building polygon shapefiles with height data and uses the Python package **geopandas** to calculate 132 urban parameters for each building that are compiled into a binary file. The name of the binary file as well as an automatically generated index file instructs WRF to place the binary data into the correct location in a geogrid. 

Currently, **naturf** requires the shapefile inputs to first be separated into regular tiles, and it also requires a csv containing a index number for each of the tiles in the study area (todo: clarify). In tests of Los Angeles, regular tiles of 3.2 km x 3.2 km proved to be the most computationally efficient tile sizes, but any tile size that is a power of two is recommended.

Python version support
----------------------

Officially Python 3.7, 3.8, and 3.9


Installation
------------

.. note::

  **naturf** is not officially supported for Ubuntu 18 users due to a system dependency (``GLIBC_2.29``) required by the ``whitebox`` package which **naturf** uses to conduct spatial analysis. Ubuntu 18 natively includes ``GLIBC_2.27``.  It may be possible for Ubuntu 18 users to upgrade to ``GLIBC_2.29`` but this should be done with careful consideration.  Instead, we officially support **naturf** use for Ubuntu users for versions 20.04.2 LTS and greater.

**naturf** can be installed via pip by running the following from a terminal window::

    pip install naturf

Conda/Miniconda users can utilize the ``environment.yml`` stored in the root of this repository by executing the following from a terminal window::

    conda env create --file environment.yml

It may be favorable to the user to create a virtual environment for the **naturf** package to minimize package version conflicts.  See `creating virtual environments <https://docs.python.org/3/library/venv.html>`_ to learn how these function and can be setup.

Installing package data
-----------------------

**naturf** requires package data to be installed from Zenodo to keep the package lightweight.  After **naturf** has been installed, run the following from a Python prompt:

**NOTE**:  The package data will require approximately 195 MB of storage.

.. code-block:: python

    import naturf

    naturf.install_package_data()

This will automatically download and install the package data necessary to run the examples in accordance with the version of **naturf** you are running.  You can pass an alternative directory to install the data into (default is to install it in the package data directory) using ``data_dir``.  When doing so, you must modify the configuration file to point to your custom paths. 


Dependencies
------------

=============   ================
Dependency      Minimum Version
=============   ================
numpy           1.19.4
pandas          1.1.4
rasterio        1.2.3
xarray          0.16.1
PyYAML          5.4.1
requests        2.25.1
joblib          1.0.1
matplotlib      3.3.3
seaborn         0.11.1
whitebox        1.5.1
fiona           1.8.19
pyproj          3.0.1
rtree           0.9.7
shapely         1.7.1
geopandas       0.9.0
=============   ================


Optional dependencies
---------------------

==================    ================
Dependency            Minimum Version
==================    ================
build                 0.5.1
nbsphinx              0.8.6
setuptools            57.0.0
sphinx                4.0.2
sphinx-panels         0.6.0
sphinx-rtd-theme      0.5.2
twine                 3.4.1
pytest                6.2.4
pytest-cov            2.12.1
==================    ================
