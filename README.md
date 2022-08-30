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

## Workflow

1. Download example data:  [Example Data](www.google.com)
2. Setup paths and settings in `scripts/workflow.py`
3. Run `scripts/workflow.py` in a Python 3.8 or greater environment

## Citation

Allen-Dumas, Melissa Ree, Sweet-Breu, Levi, Seals, Matthew, Berres, Andy, Vernon, Chris R., Rexer, Emily, and USDOE Office of Science. NATURF. Computer software. https://www.osti.gov//servlets/purl/1879628. Vers. 0. USDOE Office of Science (SC), Biological and Environmental Research (BER). Earth and Environmental Systems Science Division. 31 Aug. 2022. Web. doi:10.11578/dc.20220803.4.
