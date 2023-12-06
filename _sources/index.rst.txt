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


.. panels::
    :card: + intro-card text-center
    :column: col-lg-6 col-md-6 col-sm-6 col-xs-12 d-flex


    ---
    :img-top: _static/index_getting_started.svg

    Getting Started
    ^^^^^^^^^^^^^^^

    New to **naturf**?  Get familiar with what **naturf** is all about.

    +++

    .. link-button:: getting_started
            :type: ref
            :text: What naturf is all about
            :classes: btn-block btn-secondary stretched-link

    ---
    :img-top: _static/index_user_guide.svg

    User Guide
    ^^^^^^^^^^

    The user guide provides in-depth information on the
    key concepts of **naturf**.

    +++

    .. link-button:: user_guide
            :type: ref
            :text: To the user guide
            :classes: btn-block btn-secondary stretched-link

    ---
    :img-top: _static/index_api.svg

    API Reference
    ^^^^^^^^^^^^^

    The reference guide contains a detailed description of
    the **naturf** API. The reference describes how the methods
    work and which parameters can be used.

    +++

    .. link-button:: naturf
            :type: ref
            :text: To the reference guide
            :classes: btn-block btn-secondary stretched-link

    ---
    :img-top: _static/index_contribute.svg

    Contributing to naturf
    ^^^^^^^^^^^^^^^^^^^^^^

    Saw a typo in the documentation? Want to improve
    existing functionalities? The contributing guidelines will guide
    you through the process of improving **naturf**.

    +++

    .. link-button:: contributing
            :type: ref
            :text: To the development guide
            :classes: btn-block btn-secondary stretched-link


.. toctree::
   :maxdepth: 2
   :hidden:

   getting_started
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
