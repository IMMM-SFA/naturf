from config import *
from sys import exit
from time import time
from math import sqrt
from math import ceil
from numpy import array, arange, transpose, set_printoptions, zeros, uint8, uint16, indices, where, empty, float64, \
    column_stack, savetxt
from skimage.draw import polygon
import osr
from PIL import Image
from scipy import ndimage

try:
    from osgeo import gdal, ogr
    from osgeo.gdalconst import *
except ImportError:
    import gdal
    import ogr
    from gdalconst import *

start_time = time()

#path = r'C:\ORNL Spring\Census Tracts\Tracts 51-60\005803-005877\005844\005844.shp'

# get the shapefile driver
driver = ogr.GetDriverByName('ESRI Shapefile')

datasource2 = driver.Open(path, 0)
if datasource2 is None:
    print('Could not open shapefile')
    exit(1)

# register all of the GDAL drivers
gdal.AllRegister()

layer2 = datasource2.GetLayer()

extent2 = layer2.GetExtent()

xOrigin = extent2[0]
yOrigin = extent2[3]

PIXEL_SIZE = 0.5

IMAGE_SIZE_X = (2 * ceil(extent2[3]-extent2[2])) + 100
IMAGE_SIZE_Y = (2 * ceil(extent2[1]-extent2[0])) + 100

pixelWidth = PIXEL_SIZE
pixelHeight = -PIXEL_SIZE

start_x = int(xOrigin)
start_y = ceil(yOrigin)

start_x_p = int((start_x - xOrigin) / pixelWidth)
start_y_p = int((start_y - yOrigin) / pixelHeight)

driver_out = gdal.GetDriverByName('GTiff')
imgOut = driver_out.Create(r'Buildings_Raster.tif',
                           IMAGE_SIZE_Y, IMAGE_SIZE_X, 1, 1)

proj = osr.SpatialReference()
proj.SetWellKnownGeogCS("WGS84")
proj.SetUTM(11, False)

bandOut1 = imgOut.GetRasterBand(1)

data1 = empty((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint8)
data1.fill(255)

ids = empty((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint16)
ids.fill(255)

buils = empty((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint16)
buils.fill(255)

tempxyz = empty((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)

distarr = empty((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
distarr.fill(0)

ind = indices(data1.shape)

ys = 0
yl = 0
xs = 0
xl = 0

# radius = 15

# loop through the buildings
feature_buil = layer2.GetNextFeature()

while feature_buil:
    geomb = feature_buil.GetGeometryRef()
    ring = geomb.GetGeometryRef(0)
    numpoints = ring.GetPointCount()

    if numpoints != 0:
        nx, ny, _ = ring.GetPoint(0)

        # print(nx, ny)
        # print(xOrigin, yOrigin)

        xOffset = int((nx - xOrigin) / pixelWidth)
        yOffset = int((ny - yOrigin) / pixelHeight)

        # print(xOffset, yOffset)

        parr = [[xOffset, yOffset]]
        parrx = [[xOffset]]
        parry = [[yOffset]]

        # print(parrx)
        # print(parry)
        # print(ring.GetPointCount())

        for i in range(1, numpoints):
            bpt = ring.GetPoint(i)

            xoff = int((bpt[0] - xOrigin) / pixelWidth)
            yoff = int((bpt[1] - yOrigin) / pixelHeight)

            parrx.append([xoff])
            parry.append([yoff])

        # print(parrx)
        # print(parry)

        parrx[:] = [x[0] - start_x_p for x in parrx]
        parry[:] = [y[0] - start_y_p for y in parry]

        # print(parrx)
        # print(parry)

        parrx = array(parrx)
        parry = array(parry)
        rr, cc = polygon(parrx, parry, [IMAGE_SIZE_Y, IMAGE_SIZE_X])
        # print(rr, cc)
        buils[cc, rr] = 127

    feature_buil.Destroy()
    feature_buil = layer2.GetNextFeature()


data1 = where(buils != 127, data1, 127)

bandOut1.WriteArray(data1, 0, 0)

imgOut.SetGeoTransform((start_x, pixelWidth, 0, start_y, 0, pixelHeight))
imgOut.SetProjection(proj.ExportToWkt())

print("Script 1 took", str(time() - start_time), "seconds to run")
