[![DOI](https://zenodo.org/badge/487911703.svg)](https://zenodo.org/badge/latestdoi/487911703)
[![codecov](https://codecov.io/gh/IMMM-SFA/naturf/graph/badge.svg?token=SoIfjdS6BL)](https://codecov.io/gh/IMMM-SFA/naturf)
[![build](https://github.com/IMMM-SFA/naturf/actions/workflows/build.yml/badge.svg)](https://github.com/IMMM-SFA/naturf/actions/workflows/build.yml)
[![Deploy Documentation](https://github.com/IMMM-SFA/naturf/actions/workflows/deploy.yml/badge.svg)](https://github.com/IMMM-SFA/naturf/actions/workflows/deploy.yml)

# naturf

#### Neighborhood Adaptive Tissues for Urban Resilience Futures (`naturf`) is an open-source geospatial Python package that calculates and compiles urban building parameters to be input to the Weather Research and Forecasting model (WRF).

### Purpose
`naturf` was created to:

  - Calculate 132 urban parameters based on building footprints and height,
  - Compile the parameters at sub-kilometer resolutions into binary files,
  - Prepare binary files to be fed into WRF to understand the effect of building morphology on the urban microclimate.

### Install

```bash
pip install naturf
```

### Check out a quickstart tutorial to run `naturf`

Run `naturf`! Check out the [`naturf` ipynb Quickstarter](https://github.com/IMMM-SFA/naturf/blob/main/notebooks/quickstarter.ipynb) or the [`naturf` Python Quickstarter](https://immm-sfa.github.io/naturf/quickstarter.html).

### User guide

Our [user guide](https://immm-sfa.github.io/naturf/user_guide.html) provides in-depth information on the key concepts of `naturf` with useful background information and explanation.

### Contributing

Whether you find a typo in the documentation, find a bug, or want to develop functionality that you think will make `naturf` more robust, you are welcome to contribute! See our [Contribution Guidelines](https://immm-sfa.github.io/naturf/contributing.html)

### API reference

The reference guide contains a detailed description of the `naturf` API. The reference describes how the methods work and which parameters can be used. It assumes that you have an understanding of the key concepts. See [API Reference](https://immm-sfa.github.io/naturf/modules.html)

### Developer Setup

To get started on development, install the pre-commit hooks to format code.

First [install `pre-commit`](https://pre-commit.com/).

Then install the hooks within the repo:

```bash
$ cd /PATH/TO/NATURF
$ pre-commit install
```

### Code citation

> Allen-Dumas, Melissa Ree, Sweet-Breu, Levi, Seals, Matthew, Berres, Andy, Vernon, Chris R., Rexer, Emily, and USDOE Office of Science. NATURF. Computer software. https://www.osti.gov//servlets/purl/1879628. Vers. 0. USDOE Office of Science (SC), Biological and Environmental Research (BER). Earth and Environmental Systems Science Division. 31 Aug. 2022. Web. doi:10.11578/dc.20220803.4.

### Sample data citation

> OpenDataDC (2021) Open Data DC. URL https://opendata.dc.gov/datasets
