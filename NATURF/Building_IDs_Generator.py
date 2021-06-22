from config import *
from sys import exit
from time import time
from math import sqrt
from math import ceil
from numpy import array, arange, transpose, set_printoptions, zeros, uint8, uint16, uint32, indices, where, empty, float64, \
    column_stack, savetxt, save
from skimage.draw import polygon
import osr
from PIL import Image
from scipy import ndimage
import csv
from tempfile import TemporaryFile

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
imgOut = driver_out.Create(r'Building_IDs.tif',
                           IMAGE_SIZE_Y, IMAGE_SIZE_X, 1, gdal.GDT_Int32)

proj = osr.SpatialReference()
proj.SetWellKnownGeogCS("WGS84")
proj.SetUTM(11, False)

bandOut1 = imgOut.GetRasterBand(1)

data1 = empty((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint8)
data1.fill(255)

ids = empty((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint32)
ids.fill(0)

buils = empty((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint16)
buils.fill(255)

tempxyz = empty((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)

distarr = empty((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
distarr.fill(0)

ind = indices(data1.shape)

names = []
heights = []
widths = []
ratios = []

cnt = 1

# radius = 15

# loop through the buildings
feature_buil = layer2.GetNextFeature()

while feature_buil:
    bid = feature_buil.GetFieldAsString('ID')

    geomb = feature_buil.GetGeometryRef()
    ring = geomb.GetGeometryRef(0)
    numpoints = ring.GetPointCount()

    if numpoints != 0:
        nx, ny, nz = ring.GetPoint(0)

        xOffset = int((nx - xOrigin) / pixelWidth)
        yOffset = int((ny - yOrigin) / pixelHeight)

        parr = [[xOffset, yOffset]]
        parrx = [[xOffset]]
        parry = [[yOffset]]

        for bi in range(1, ring.GetPointCount()):
            bpt = ring.GetPoint(bi)

            xoff = int((bpt[0] - xOrigin) / pixelWidth)
            yoff = int((bpt[1] - yOrigin) / pixelHeight)

            parr.append([xoff, yoff])
            parrx.append([xoff])
            parry.append([yoff])

        parrx[:] = [x[0] - start_x_p for x in parrx]
        parry[:] = [y[0] - start_y_p for y in parry]

        parrx = array(parrx)
        parry = array(parry)
        rr, cc = polygon(parrx, parry, [IMAGE_SIZE_Y, IMAGE_SIZE_X])

        buils[cc, rr] = 127

        bid = float(bid)
        bid = int(bid)

        ids[cc, rr] = where(ids[cc, rr] != 0, ids[cc, rr], cnt)

        # print cnt

        cnt += 1
    feature_buil.Destroy()
    feature_buil = layer2.GetNextFeature()

data1 = where(buils != 127, data1, 127)

bandOut1.WriteArray(ids, 0, 0)

imgOut.SetGeoTransform((start_x, pixelWidth, 0, start_y, 0, pixelHeight))
imgOut.SetProjection(proj.ExportToWkt())
del imgOut

print("Script 2 took", str(time() - start_time), "seconds to run")
