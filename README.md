[![DOI](https://zenodo.org/badge/487911703.svg)](https://zenodo.org/badge/latestdoi/487911703)


## naturf

NATURF: Neighborhood Adaptive Tissues for Urban Resilience Futures

## Description

The Neighborhood Adaptive Tissues for Urban Resilience Futures tool (NATURF) is
a Python workflow that generates data readable by the Weather Research and
Forecasting (WRF) model. The NATURF Python modules use shapefiles containing
building footprint and height data as input to calculate 132 building parameters
at any resolution and converts the parameters into a binary file format.

NATURF was created to:

  - addresses the knowledge gap of the effect of the geometry of a neighborhood on the local meteorology and
  -  translate neighborhood morphology (building footprints, heights, spacing, etc.) representations to the WRF-readable urban parameters so that meteorological processes at urban scale can interact with the built environment.

## Example Data

The example data provided with this package includes a shapefile containing building footprints and heights for one 3.2km by 3.2km tile of
Washington, D.C. (C-5.shp) and a CSV file that lists the index name for each tile in Washington, D.C. (DC_Indices.csv).

NATURF requires the center latitude and longitude of the study area in order to correctly project the output data,
but these values are already included in `scripts/workflow.py` for the example data.

Outputs from the example data should include a binary file named `00065-00096.00065-00096`, an `index` file,
a CSV file with urban parameter values for each building, two NumPy files, several pickle files that are
used in the compilation of the binary file, and a directory of TIF rasters that represent each of the
132 calculated urban parameters.

## Workflow

1. Example data is provided in this repository in the `example` directory
2. Setup paths and settings in `scripts/workflow.py`
3. Run `scripts/workflow.py` in a Python 3.8 or greater environment

## Citation

> Allen-Dumas, Melissa Ree, Sweet-Breu, Levi, Seals, Matthew, Berres, Andy, Vernon, Chris R., Rexer, Emily, and USDOE Office of Science. NATURF. Computer software. https://www.osti.gov//servlets/purl/1879628. Vers. 0. USDOE Office of Science (SC), Biological and Environmental Research (BER). Earth and Environmental Systems Science Division. 31 Aug. 2022. Web. doi:10.11578/dc.20220803.4.


# Developer Setup
To get started on development, install the pre-commit hooks to format code.

```bash
$ brew install pre-commit
```
Then install the hooks within the repo:
```bash
$ cd /PATH/TO/NATURF
$ pre-commit install
```
