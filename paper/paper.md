---
title: 'naturf: a package for generating urban parameters for numerical weather modeling'
tags:
  - Python
  - building morphology
authors:
  - name: Levi T. Sweet-Breu
    orcid: 0000-0003-3325-8086
    affiliation: 1
  - name: Melissa R. Allen-Dumas
    orcid:
    affiliation: 1
affiliations:
 - name: Computational Sciences and Engineering Division, Oak Ridge National Laboratory, One Bethel Valley Road, Oak Ridge, TN. 37831
   index: 1
 - name: Plase of work, Portland, ME., USA
   index: 2
date: 8 August 2022
bibliography: paper.bib
---

# Summary
The Neighborhood Adaptive Tissues for Urban Resilience Futures tool (NATURF) is a Python workflow that generates files readable by the Weather Research and
Forecasting (WRF) model. NATURF uses several Python modules and shapefiles containing building footprint and height data to calculate 132 building parameters and
converts them into a binary file format. This approach is an adaptation of the National/World Urban Database and Access Portal Tool (NUDAPT/WUDAPT)
[@ching2009national][@mills2015introduction] that can be used with any study area at any spatial resolution. The climate modeling community and urban planners can identify the effects of building/neighborhood morphology on the microclimate using the urban parameters and WRF-readable files produced by NATURF.


We present the `naturf` Python package... [Figure 1].

![This is a figure.](figure_1.png)

# Statement of Need
NATURF serves many audiences: (i) urban climate modelers wanting to understand building effects on the urban microclimate at a fine scale, (ii) urban planners creating new developments, (iii) sociologists aiming to understand weather-based inequalities and stresses. Allen-Dumas et al.[@allen2020impacts] used NATURF to  demonstrate that simulated new developments in the Chicago Loop neighborhood affect temperature and energy use both in the new developments and the preexisting neighborhoods. Their findings show that building effects on the microclimate can be modeled at 90m resolution, and they quantify how different configurations of urban developments affect not only the developments themselves but also neighborhoods that already exist. Urban planners will be able to use NATURF in the same way as urban areas continue to grow.[
@united20182018] Likewise, NATURF will give climate modelers the tools to understand how urbanization will contribute to microclimate and broader global climate change, and sociologists will see how urban developments affect weather-related stresses.

NATURF utilizes the same urban parameters and WRF pathways as NUDAPT and WUDAPT, but it does so at a higher spatial resolution for more detailed predictions. WUDAPT in particular seeks to gather consistent data on a worldwide scale[@ching2018wudapt] while NATURF works at a city- or neighborhood-scale.

NATURF and the open-source toolbox GeoClimate[@bocher2021geoclimate] both aim to quantify the effect of urban features for climate models. Both tools provide outputs similar to the three levels of data associated with WUDAPT: level 0 data (local climate zones), level 1 data (sampling data with finer resolution), and level 2 data (precise urban parameter data).[ching2018wudapt] GeoClimate produces level 0 and level 1 data, while NATURF provides level 2 data. Where NATURF uses building height and footprint data to calculate urban parameters, GeoClimate uses OpenStreetMap data. GeoClimate also calculate different parameters from NATURF and considers the influences of vegetation and roads on the microclimate. NATURF and GeoClimate measure the effect of urban features on microclimate, but they use different source data and output different data products to do so.


# Design and Functionality
The NATURF workflow is operated by the im3Workflow.py script, which call functions from the following Python modules:
1. Buildings_Raster.py
2. Building_IDs.py
3a. Parameter_Calculations.py
3b. Parameter_Definitions.py
4. Binary.py
The first two modules create a tif raster and an image with unique building ID numbers of the study shapefile respectively (Figure 1).

![Raster of study shapefile.\label{fig:interactive}](Buildings_Raster.png){ width=80% }

The third module uses these images and functions defined in an accessory script (script 3b) to calculate 132 parameters defined by NUDAPT, and outputs them as
pickle files and a csv file. The fourth and final script turns those pickle files into individual tifs and compiles them
all into a single binary file (Figure 2).

![Frontal area density for a 5 meter slice of buildings at 100 meter resolution.\label{fig:interactive}](tile_1_visual.png){ width=80% }

The naming of the binary files is explained in depth in the accompanying GeoGrid_and_Indexing file. An index file containing several variables necessary for WRF
is also generated automatically. These inputs follow built-in pathways in WRF created by NUDAPT.

NATURF can be used for single neighborhoods or census tracts, but it has the capacity to run in parallel using the python *multiprocessing* package for study areas on a city- or county-scale. NATURF was run on a small group cluster to process the Los Angeles metropolitan area using 3200m x 3200m tiles. WRF requires input building data to be placed according to a defined geogrid, and experimentation found that regular square tiles is more easily input to WRF than variably sized census tracts. Further experimentation with different tile sizes found that smaller tiles could be processed quicker than larger tile sizes covering the same total area. For Los Angeles, 10.24 square kilometer tiles projected to complete processing quicker than 40.96 square kilometer and 163.84 square kilometer tiles despite having approximately 3.5 and 12 times more tiles, respectively. Tables 1 and 2 show the results of the tile experiment.

| Tile Size | GRID ID | Num of Buildings | Run Time (hr) | CPU Hours (hr) |
| --------- | ------- | ---------------- | ------------- | -------------- |
| 32x32 | X-8 | 209 | 0.162834167 | 0.0172925 |
| 32x32 | AE-7 | 747 | 0.752517778 | 0.085763056 |
| 32x32 | X-28 | 17642 | 25.97064944 | 4.319839444 |
| 64x64 | AA-4 | 223 | 0.751610556 | 0.077081944 |
| 64x64 | V-7 | 2993 | 11.57833056 | 1.233084722 |
| 64x64 | K-15 | 59000 | 335.3297203 | 51.973715 |
| 128x128 | L-13 | 220 | 1.694813611 | 0.185954722 |
| 128x128 | J-12 | 9503 | 27.2200375 | 3.850261944 |
| 128x128 | F-7 | 174256 | NA | NA |


| Tile Size | Num of Tiles | Avg Bldgs/Tile | Med Bldgs/Tile | Avg Time/Tile (hr) | Completion Time (days) |
| --------- | ------------ | -------------- | -------------- | ------------------ | ---------------------- |
| 32x32 | 1762 | 2384 | 747 | 8.962000463 | 657.9602007 |
| 64x64 | 505 | 8317 | 2993 | 115.8865538 | 2438.446236 |
| 128x128 | 144 | 19169 | 10248 | >220.9148511 | >1325.489107 |


We have a quickstarter and some documentation here for you [documentation](https://immm-sfa.github.io/naturf/).

# Acknowledgements
This research was supported by the U.S. Department of Energy, Office of Science, as part of research in MultiSector Dynamics, Earth and Environmental System Modeling Program.

Sponsored by the DOE Office of Science as a part of the research in Multi-Sector Dynamics within the Earth and Environmental System Modeling Program as part of
the Integrated Multiscale Multisector Modeling (IM3) Scientific Focus Area.
# References
