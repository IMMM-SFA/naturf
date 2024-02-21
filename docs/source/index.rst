:notoc:

naturf documentation
====================

**Date**: |today| **Version**: |version|

**Useful links**:
`Source Repository <https://github.com/immm-sfa/naturf>`_ |
`Issues & Ideas <https://github.com/immm-sfa/naturf/issues>`_ |
`Interactive Quickstarter <quickstarter.rst>`_

**naturf** is an open-source geospatial Python package for calculating urban building parameters to be compiled and input to the Weather Research and Forecasting model (WRF).  **naturf** was created to:

 1) Calculate 132 urban parameters based on building footprints and height,

 2) Compile the parameters at sub-kilometer resolutions into binary files,

 3) Prepare binary files to be fed into WRF to understand the effect of building morphology on the urban microclimate.


About
-----

The Neighborhood Adaptive Tissues for Urban Resilience Futures tool (**naturf**) enables the examination of the effect of urban morphology at variable resolutions on the urban microclimate through the Weather Research and Forecasting model (WRF). Following the work of Ching et al. (citation) on NUDAPT/WUDAPT, **naturf** calculates 132 urban parameters based on shapefiles of building footprints and heights; however, **naturf** is capable of compiling these urban parameters at finer, sub-kilometer resolutions than offered by NUDAPT/WUDAPT.

**naturf** takes in building polygon shapefiles with height data and uses the Python package **geopandas** to calculate 132 urban parameters for each building that are compiled into a binary file. The name of the binary file as well as an automatically generated index file instructs WRF to place the binary data into the correct location in a geogrid.  **naturf** also uses **hamilton** as a means of organizing, streamlining, and visualizing its workflow.


.. grid:: 2
    :gutter: 4

    .. grid-item-card::  Quickstarter
        :img-top: _static/index_quickstarter.svg
        :text-align: center

        New to **naturf**?  Follow the quickstarter for a quick start.

        .. button-ref:: quickstarter
                :click-parent:
                :color: primary
                :expand:

                Get started!

    .. grid-item-card:: User Guide
        :img-top: _static/index_user_guide.svg
        :text-align: center

        The user guide provides in-depth information on the
        key concepts of **naturf**.

        .. button-ref:: user_guide
                :click-parent:
                :color: primary
                :expand:

                See the User Guide

    .. grid-item-card:: API Reference
        :img-top: _static/index_api.svg
        :text-align: center

        The reference guide contains a detailed description of
        the **naturf** API. The reference describes how the methods
        work and which parameters can be used.

        .. button-ref:: naturf
                :click-parent:
                :color: primary
                :expand:

                See the Reference Guide

    .. grid-item-card:: Contributing to naturf
        :img-top: _static/index_contribute.svg
        :text-align: center

        Saw a typo in the documentation? Want to improve
        existing functionalities? The contributing guidelines will guide
        you through the process of improving **naturf**.

        .. button-ref:: contributing
                :click-parent:
                :color: primary
                :expand:

                See the development guide


.. toctree::
   :maxdepth: 2
   :hidden:

   quickstarter
   user_guide
   modules
   contributing
   release_notes
   publications
   how_to_cite
   authors
   license
   footer
