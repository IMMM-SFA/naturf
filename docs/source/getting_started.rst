Getting started
===============

About
-----

The Neighborhood Adaptive Tissues for Urban Resilience Futures tool (**naturf**) enables the examination of the effect of urban morphology at variable resolutions on the urban microclimate through the Weather Research and Forecasting model (WRF). Following the work of Ching et al. (citation) on NUDAPT/WUDAPT, **naturf** calculates 132 urban parameters based on shapefiles of building footprints and heights; however, **naturf** is capable of compiling these urban parameters at finer, sub-kilometer resolutions than offered by NUDAPT/WUDAPT.

**naturf** takes in building polygon shapefiles with height data and uses the Python package **geopandas** to calculate 132 urban parameters for each building that are compiled into a binary file. The name of the binary file as well as an automatically generated index file instructs WRF to place the binary data into the correct location in a geogrid.  **naturf** also uses **hamilton** as a means of organizing, streamlining, and visualizing its workflow.

Currently, **naturf** requires the shapefile inputs to first be separated into regular tiles, and it also requires a csv containing a index number for each of the tiles in the study area (todo: clarify). In tests of Los Angeles, regular tiles of 3.2 km x 3.2 km proved to be the most computationally efficient tile sizes, but any tile size that is a power of two is recommended.


Dependencies
------------

.. list-table::
    :widths: 25 25
    :header-rows: 1

    * - Dependency
      - Minimum Version
    * - numpy
      - 1.22.4
    * - pandas
      - 1.4.2
    * - geocube
      - 0.3.1
    * - rasterio
      - 1.2.10
    * - xarray
      - 2022.3.0
    * - joblib
      - 1.0.1
    * - fiona
      - 1.8.19
    * - pyproj
      - 3.0.1
    * - rtree
      - 1.0.0
    * - shapely
      - 1.8.2, <2
    * - geopandas
      - 0.10.2
    * - sf-hamilton[visualization]
      - 1.10

=============   ================
Dependency      Minimum Version
=============   ================
numpy           1.22.4
pandas          1.4.2
geocube         0.3.1
rasterio        1.2.10
xarray          2022.3.0
joblib          1.0.1
fiona           1.8.19
pyproj          3.0.1
rtree           1.0.0
shapely         1.8.2, <2
geopandas       0.10.2
sf-hamilton[visualization]  1.10
=============   ================
