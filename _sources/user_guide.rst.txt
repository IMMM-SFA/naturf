===============
User guide
===============

Data Requirements
-----------------

The only input data required for *naturf* is a shapefile with building footprints and height data. There should be a field with a unique ID for each building the shapefile, and it should be in a projected coordinate system such as Alber Equal Area Conic. For input to the Weather Research and Forecasting model (WRF), the computed parameters for each building will be projected into WGS 84. Single neighborhoods can be processed in seconds to minutes, but larger datasets (e.g. city-scale) can take several days to process, and are best suited for HPC.

Fundamental equations and concepts
----------------------------------

Supporting Parameters
~~~~~~~~~~~~~~~~~~~~~

The following parameters/concepts are not output from **naturf** by default, but they contribute to the calculation of the output parameters.

Plan Area
^^^^^^^^^

When calculating parameters, **naturf** creates a buffer around each target building called the plan (or dilated) area. Each building has its own plan area which identifies neighbors to that target building which are important for the calculation of parameters. For the parameter definitions below, *total plan area* refers to the area of that buffer around the target building, while *building plan area* refers to the sum of building footprints within the *total plan area*. *Total plan area* should always be a larger value than the *building plan area*.

Frontal Length
^^^^^^^^^^^^^^

For the urban parameters calculated by **naturf**, frontal length refers to the wall length perpendicular to a given direction for all buildings within the target building's total plan area.

Frontal Area
^^^^^^^^^^^^

For the urban parameters calculated by **naturf**, frontal area refers to the wall area perpendicular to a given direction for all buildings within the target building's total plan area.

Lot Area
^^^^^^^^

For the urban parameters calculated by **naturf**, lot area refers to the total surface area of all buildings
within a given building's total plan area divided by the number of buildings in the total plan area.

Building Height Limit
^^^^^^^^^^^^^^^^^^^^^

Following NUDAPT, **naturf** bins building heights into five meter increments from 0 to 75 meters. Any building with a height greater than 75 meters is considered as ending at 75 meters.

Glossary of Terms
~~~~~~~~~~~~~~~~~

* `FAD`: Frontal area density (unitless)
* :math:`A_f`: Frontal area of a wall from a given direction and height (:math:`m^2`)
* :math:`A_F`: Total frontal area of a wall from a given direction (:math:`m^2`)
* :math:`A_P`: Total plan area (:math:`m^2`)
* :math:`\lambda_p`: Plan area density (unitless)
* :math:`A_b`: Building plan area (:math:`m^2`)
* `AWMH`: Area weighted mean of building heights (`m`)
* :math:`z_h`: Building height (`m`)
* :math:`\lambda_f`: Frontal area index from a given direction (unitless)
* `CAR`: Complete aspect ratio (unitless)
* `BSA`: Building surface area (:math:`m^2`)
* :math:`\overline{\lambda_s}`: Average height-to-width ratio for given building and neighbors (unitless)
* :math:`\overline{z_h}`: Average building height for given building and neighbors (`m`)
* `SVF`: Sky-view factor (unitless)
* :math:`\overline{W}`: Average distance between given building and neighbors (`m`)
* :math:`rl_{go}`: Grimmond & Oke rougness length (`m`)
* :math:`dh_{go}`: Grimmond & Oke displacement height (`m`)
* :math:`rl_r`: Raupach roughness length (`m`)
* :math:`dh_r`: Raupach displacement height (`m`)
* :math:`\kappa`: von Kármán's constant = 0.4 (unitless)
* :math:`C_S`: Substrate-surface drag coefficient = 0.003 (unitless)
* :math:`C_R`: Roughness-element drag coefficient = 0.3 (unitless)
* :math:`\Psi_h`: Roughness-sublayer influence function = 0.193 (unitless)
* :math:`c_{d1}`: Constant = 7.5 (unitless)
* :math:`\Lambda`: Frontal area index times 2 (unitless)
* :math:`rl_m`: Macdonald roughness length (`m`)
* :math:`dh_m`: Macdonald displacement height (`m`)
* :math:`\beta` Beta coefficient = 1 (unitless)
* :math:`C_D` Obstacle drag coefficient = 1.12 (unitless)
* :math:`A_l` Lot area (:math:`m^2`)
* `A`: Constant = 3.59 (unitless)

Output Parameters
~~~~~~~~~~~~~~~~~

Frontal Area Density (1-60)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Frontal area density is the frontal area at a certain height increment divided by the total plan area. **naturf** calculates frontal area density from the four cardinal directions (east, north, west, south) and at 5 meter increments from ground level to 75 meters. Parameters 1-15 represent the north, parameters 16-30 represent the west, parameters 31-45 represent the south, and parameters 46-60 represent the east. For instance, parameter 1 gives the north-facing wall area for each building and its neighbors divided by the total plan area. [Burian2003]_ Eq. 14

.. math::
  FAD = \frac{A_{f}}{A_{P}}


Plan Area Density (61-75)
^^^^^^^^^^^^^^^^^^^^^^^^^

Plan area density is the ratio of building plan area to the total plan area, calculated in 5 meter increments from ground level to 75 meters. **naturf** projects the building footprint vertically to the building height, meaning plan area density is the same at every vertical level. [Burian2003]_ Eq. 7

.. math::
  \lambda_p = \frac{A_{b}}{A_{P}}


Rooftop Area Density (76-90)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Rooftop area density is the ratio of building rooftop area to the total plan area, calculated in 5 meter increments from ground level to 75 meters. Because **naturf** projects building footprints vertically to the building height, these parameters are equal to the plan area density. [Burian2003]_ Eq. 7

Plan Area Fraction (91)
^^^^^^^^^^^^^^^^^^^^^^^

Plan area fraction is the ratio of building plan area to the total plan area, calculated at ground level. For **naturf**, this is equal to plan area density at any height increment. [Burian2003]_ Eq. 4

Mean Building Height (92)
^^^^^^^^^^^^^^^^^^^^^^^^^

The average building height of all buildings within the total plan area.

Standard Deviation of Building Heights (93)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The standard deviation of building heights for all buildings within the total plan area.

Area Weighted Mean of Building Heights (94)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The average height of all buildings within the total plan area weighted by the total plan area. [Burian2003]_ Eq. 3

.. math::

  AWMH = \frac{\Sigma{A_{b} z_{h}}}{\Sigma{A_{b}}}


Building Surface Area to Plan Area Ratio (95)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ratio of all the surface areas of a building to the total plan area. [Burian2003]_ Eq. 16

Frontal Area Index (96-99)
^^^^^^^^^^^^^^^^^^^^^^^^^^

Frontal area index is the ratio of the entire frontal area of a building to the total plan area. **naturf** calculates the frontal area index from the four cardinal directions. Because buildings often do not face a cardinal direction head on, **naturf** uses the average alongwind and crosswind distance from the current building centroid to all other building centroids for the total plan area. [Burian2003]_ Eq. 12

.. math::
  \lambda_{f} = \frac{A_{F}}{A_{P}}


Complete Aspect Ratio (100)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ratio of building surface area and exposed ground area to the total plan area. [Burian2003]_ Eq. 15

.. math::
  CAR = \frac{BSA + (A_{P} - A_{b})}{A_{P}}


Height-to-Width Ratio (101)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ratio of the building height to the street width. **naturf** generalizes this as the ratio of average height of buildings in the total plan area to average distance from the current building to all other buildings in the total plan area. If a building has no other buildings in its total plan area, the average distance is set to a default value. [Burian2003]_ Eq. 18

.. math::
  \overline{\lambda_s} = \frac{\overline{z_h}}{\overline{W}}


Sky-View Factor (102)
^^^^^^^^^^^^^^^^^^^^^

The fraction of visible sky in a given area. **naturf** generalizes the distance between buildings to be the average distance between the current building and all other buildings in the total plan area.  [Dirksen2019]_ Eq. 1

.. math::
  SVF = cos(arctan(\frac{z_{h}}{0.5\overline{W}}))


Grimmond & Oke Roughness Length (103)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

[GrimmondOke1999]_ Eq. 2

.. math::
  rl_{go} = 0.1 \cdot z_{h}


Grimmond & Oke Displacement Height (104)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

[GrimmondOke1999]_ Eq. 1

.. math::
  dh_{go} = 0.67 \cdot z_{h}



Raupach Roughness Length (105, 107, 109, 111)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

[Raupach1994]_ Eq. 4

.. math::
  rl_{r} = z_{h} \cdot (1 - \frac{dh_{r}}{z_{h}}) \cdot exp(-\kappa \cdot (C_{S} + C_{R} \cdot \lambda_{f})^{-0.5} - \Psi_{h})


Raupach Displacment Height (106, 108, 110, 112)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

[Raupach1994]_ Eq. 8

.. math::
  dh_{r} = z_{h} \cdot (1 - (\frac{1 - \exp(-\sqrt(c_{d1} \cdot \Lambda))}{\sqrt(c_{d1} \cdot \Lambda)}))


Macdonald et al. Roughness Length (113-116)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

[Macdonald1998]_ Eq. 22

.. math::
  rl_{m} = z_{h} \cdot (1 - \frac{dh_{m}}{z_{h}})\exp(-(0.5*\beta\frac{C_{D}}{\kappa^2}(1 - \frac{MDH}{z_{h}})\frac{A_{F}}{A_{l}})^{-0.5})


Macdonald et al. Displacement Height (117)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

[Macdonald1998]_ Eq. 23

.. math::
  dh_{m} = z_{h} \cdot (1 + \frac{1}{A^\lambda_{p}} \cdot (\lambda_{p} - 1))


Vertical Distribution of Building Heights (118-132)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The vertical distribution of building heights is a representation of where buildings are located at each vertical level. **naturf** represents buildings as arbitrary float values in an array, and each vertical dimension of the array shows how many buildings reach that height. [Burian2003]_

Dependencies
____________

==========================  ===============
Dependency                  Minimum Version
==========================  ===============
fiona                       1.8.19
geocube                     0.3.1
geopandas                   0.10.2
joblib                      1.0.1
numpy                       1.22.4
pandas                      1.4.2
pyproj                      3.0.1
rasterio                    1.2.10
rtree                       1.0.0
sf-hamilton[visualization]  1.45
shapely                     1.8.2, <2
tqdm                        4.66.1
xarray                      2022.3.0
==========================  ===============

References
----------

.. [Burian2003] Burian, S. J., Han, W. S., & Brown, M. J. (2003). Morphological analyses using 3D building databases: Houston, Texas. Department of Civil and Environmental Engineering, University of Utah.

.. [Dirksen2019] Dirksen, M., Ronda, R. J., Theeuwes, N. E., & Pagani, G. A. (2019). Sky view factor calculations and its application in urban heat island studies. Urban Climate, 30, 100498.

.. [GrimmondOke1999] Grimmond, C. S. B., & Oke, T. R. (1999). Aerodynamic properties of urban areas derived from analysis of surface form. Journal of Applied Meteorology and Climatology, 38(9), 1262-1292.

.. [Macdonald1998] Macdonald, R. W., Griffiths, R. F., & Hall, D. J. (1998). An improved method for the estimation of surface roughness of obstacle arrays. Atmospheric environment, 32(11), 1857-1864.

.. [Raupach1994] Raupach, M. R. (1994). Simplified expressions for vegetation roughness length and zero-plane displacement as functions of canopy height and area index. Boundary-layer meteorology, 71(1), 211-216.
