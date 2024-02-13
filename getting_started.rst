Getting started
===============

About
-----

The Neighborhood Adaptive Tissues for Urban Resilience Futures tool (**naturf**) enables the examination of the effect of urban morphology at variable resolutions on the urban microclimate through the Weather Research and Forecasting model (WRF). Following the work of Ching et al. (citation) on NUDAPT/WUDAPT, **naturf** calculates 132 urban parameters based on shapefiles of building footprints and heights; however, **naturf** is capable of compiling these urban parameters at finer, sub-kilometer resolutions than offered by NUDAPT/WUDAPT.

**naturf** takes in building polygon shapefiles with height data and uses the Python package **geopandas** to calculate 132 urban parameters for each building that are compiled into a binary file. The name of the binary file as well as an automatically generated index file instructs WRF to place the binary data into the correct location in a geogrid.  **naturf** also uses **hamilton** as a means of organizing, streamlining, and visualizing its workflow.


Dependencies
------------

.. list-table::
    :widths: 25 25
    :header-rows: 1

    * - Dependency
      - Minimum Version
    * - affine
      - 2.4.0
    * - appdirs
      - 1.4.4
    * - attrs
      - 23.1.0
    * - cachetools
      - 5.3.1
    * - certifi
      - 2023.7.22
    * - click
      - 8.1.7
    * - click-plugins
      - 1.1.1
    * - cligj
      - 0.7.2
    * - Fiona
      - 1.9.4.post1
    * - geocube
      - 0.4.2
    * - geopandas
      - 0.14.0
    * - graphvix
      - 0.20.1
    * - joblib
      - 1.3.2
    * - my-py-extensions
      - 1.0.0
    * - networkx
      - 3.1
    * - numpy
      - 1.26.0
    * - odc-geo
      - 0.4.1
    * - packaging
      - 23.1
    * - pandas
      - 2.1.0
    * - pyparsing
      - 3.1.1
    * - pyproj
      - 3.6.0
    * - python-dateutil
      - 2.8.2
    * - pytz
      - 2023.3.post1
    * - rasterio
      - 1.3.8
    * - rioxarray
      - 0.15.0
    * - Rtree
      - 1.0.1
    * - scipy
      - 1.11.2
    * - sf-hamilton
      - 1.29.0
    * - Shapely
      - 1.8.5.post1
    * - six
      - 1.16.0
    * - snuggs
      - 1.4.7
    * - typing-inspect
      - 0.9.0
    * - typing_extensions
      - 0.9.0
    * - tzdata
      - 2023.3
    * - xarray
      - 2023.8.0

==========================  ===============
Dependency                  Minimum Version
==========================  ===============
numpy                       1.22.4
pandas                      1.4.2
geocube                     0.3.1
rasterio                    1.2.10
xarray                      2022.3.0
joblib                      1.0.1
fiona                       1.8.19
pyproj                      3.0.1
rtree                       1.0.0
shapely                     1.8.2, <2
geopandas                   0.10.2
sf-hamilton[visualization]  1.10
==========================  ===============
