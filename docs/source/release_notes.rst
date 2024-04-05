Release notes
=============

This is the list of changes to **naturf** between each release. For full details,
see the `commit logs <https://github.com/IMMM-SFA/naturf/commits>`_.

Version 1.0.2
_____________

- See the `v1.0.2 release notes <https://github.com/IMMM-SFA/naturf/releases/tag/v1.0.2>`_.


Version 1.0.1
_____________

- See the `v1.0.1 release notes <https://github.com/IMMM-SFA/naturf/releases/tag/v1.0.1>`_.


Version 1.0.0
_____________

- Restructures **naturf** to use *hamilton* and *geopandas*
- Urban parameters are calculated for each building simultaneously in a GeoDataFrame
- Uses *hamilton* to organize and visualize workflow, allows for the full workflow to be run using just one command
- Capable of handling large input shapefiles
- Removes need for splitting of study area into multiple smaller shapefiles, resolving issues of splitting individual buildings into different files
- Outputs binary file in coordinate system easier for WRF to correctly allocate

Version 0.0.0
_____________

- Initial release
- Converts input shapefile to *numpy* array using *gdal*
- Calculates urban parameters in series of ``if`` and ``while`` loops
- Creates output binary and index files for input to WRF
- For large study areas, requires input shapefile to be split into several smaller shapefiles using square tessellations with sides a power of 2 (meters or kilometers)
- Output binary files named in accordance to each input file's position in tessellation
- Many shapefiles can be processed at once in parallel
