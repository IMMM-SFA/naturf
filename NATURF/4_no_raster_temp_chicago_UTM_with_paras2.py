from sys import exit
from time import time
from math import sqrt
from numpy import array, arange, transpose, set_printoptions, zeros, uint8, uint16, indices, where, empty, float64, \
    column_stack, savetxt, isnan, mean, shape, ones, int32, save, float32, double
from skimage.draw import polygon
import osr
from PIL import Image
from scipy import ndimage, misc
import pickle
import sklearn.preprocessing
import struct

try:
    from osgeo import gdal, ogr
    from osgeo.gdalconst import *
except ImportError:
    import gdal
    import ogr
    from gdalconst import *

set_printoptions(threshold='nan')
start_time = time()


def get_pixels(x1, y1, x2, y2):

    m = (float(y1) - float(y2)) / (float(x1) - float(x2) + 0.000000000000000000000000000000001)
    yint = float(y1) - (m * float(x1))

    slope_arr = []

    if abs(x1-x2) > abs(y1-y2) or abs(x1-x2) == abs(y1-y2):
        if x1 > x2:
            for si in range(x2, x1+1):
                sy = m*si+yint
                sy = int(round(sy))
                small = [si, sy]
                slope_arr.append(small)
        if x1 < x2:
            for si in range(x1, x2+1):
                sy = m*si+yint
                sy = int(round(sy))
                small = [si, sy]
                slope_arr.append(small)

    if abs(x1-x2) < abs(y1-y2):
        if y1 > y2:
            for si in range(y2, y1+1):
                sx = (si - yint) / m
                sx = int(round(sx))
                small = [sx, si]
                slope_arr.append(small)
        if y1 < y2:
            for si in range(y1, y2+1):
                sx = (si - yint) / m
                sx = int(round(sx))
                small = [sx, si]
                slope_arr.append(small)

    return slope_arr


def get_pixels_new(x1, y1, x2, y2):

    m = (float(y1) - float(y2)) / (float(x1) - float(x2) + 0.00000000000000000000000000000001)
    yint = float(y1) - (m * float(x1))

    if abs(x1-x2) > abs(y1-y2) or abs(x1-x2) == abs(y1-y2):
        if x1 > x2:
            arrx = arange(x2, x1+1)
            arry = m * arrx + yint
        if x1 <= x2:
            arrx = arange(x1, x2+1)
            arry = m * arrx + yint

    if abs(x1-x2) < abs(y1-y2):
        if y1 > y2:
            arry = arange(y2, y1+1)
            arrx = (arry - yint) / m
        if y1 <= y2:
            arry = arange(y1, y2+1)
            arrx = (arry - yint) / m

    arr1 = array((arrx, arry))
    arr1 = transpose(arr1)

    return arr1


def get_pixels2(arr1, arr2, arr3, x1, y1, x2, y2, w):
    mx = (float(y1) - float(y2)) / (float(x1) - float(x2) + 0.0000000000000000000000000000001)
    yint = float(y1) - (mx * float(x1))

    if abs(x1 - x2) > abs(y1 - y2) or abs(x1 - x2) == abs(y1 - y2):
        if x1 > x2:
            for i in range(x2, x1 + 1):
                yp = int(round(mx * i + yint))

                bx = i - start_x_p
                by = yp - start_y_p

                if 0 <= bx < IMAGE_SIZE and 0 <= by < IMAGE_SIZE:
                    if w == 'b':
                        arr1[by][bx] = 0
                        arr2[by][bx] = 0
                        arr3[by][bx] = 255
                    if w == 'r':
                        arr1[by][bx] = 255
                        arr2[by][bx] = 0
                        arr3[by][bx] = 0

        if x1 < x2:
            for i in range(x1, x2 + 1):
                yp = int(round(mx * i + yint))

                bx = i - start_x_p
                by = yp - start_y_p

                if 0 <= bx < IMAGE_SIZE and 0 <= by < IMAGE_SIZE:
                    if w == 'b':
                        arr1[by][bx] = 0
                        arr2[by][bx] = 0
                        arr3[by][bx] = 255
                    if w == 'r':
                        arr1[by][bx] = 255
                        arr2[by][bx] = 0
                        arr3[by][bx] = 0

    if abs(x1 - x2) < abs(y1 - y2):
        if y1 > y2:
            for i in range(y2, y1 + 1):
                xp = int(round((i - yint) / mx))

                bx = xp - start_x_p
                by = i - start_y_p

                if 0 <= bx < IMAGE_SIZE and 0 <= by < IMAGE_SIZE:
                    if w == 'b':
                        arr1[by][bx] = 0
                        arr2[by][bx] = 0
                        arr3[by][bx] = 255
                    if w == 'r':
                        arr1[by][bx] = 255
                        arr2[by][bx] = 0
                        arr3[by][bx] = 0

        if y1 < y2:
            for i in range(y1, y2 + 1):
                xp = int(round((i - yint) / mx))

                bx = xp - start_x_p
                by = i - start_y_p

                if 0 <= bx < IMAGE_SIZE and 0 <= by < IMAGE_SIZE:
                    if w == 'b':
                        arr1[by][bx] = 0
                        arr2[by][bx] = 0
                        arr3[by][bx] = 255
                    if w == 'r':
                        arr1[by][bx] = 255
                        arr2[by][bx] = 0
                        arr3[by][bx] = 0


def get_pixels2_b(arr1, x1, y1, x2, y2, w):
    mx = (float(y1) - float(y2)) / (float(x1) - float(x2) + 0.0000000000000000000000000000001)
    yint = float(y1) - (mx * float(x1))

    if abs(x1 - x2) > abs(y1 - y2) or abs(x1 - x2) == abs(y1 - y2):
        if x1 > x2:
            for i in range(x2, x1 + 1):
                yp = int(round(mx * i + yint))

                bx = i - start_x_p
                by = yp - start_y_p

                if 0 <= bx < IMAGE_SIZE and 0 <= by < IMAGE_SIZE:
                    if w == 'b':
                        arr1[by][bx] = 1
                    if w == 'r':
                        arr1[by][bx] = 2
        if x1 < x2:
            for i in range(x1, x2 + 1):
                yp = int(round(mx * i + yint))

                bx = i - start_x_p
                by = yp - start_y_p

                if 0 <= bx < IMAGE_SIZE and 0 <= by < IMAGE_SIZE:
                    if w == 'b':
                        arr1[by][bx] = 1
                    if w == 'r':
                        arr1[by][bx] = 2

    if abs(x1 - x2) < abs(y1 - y2):
        if y1 > y2:
            for i in range(y2, y1 + 1):
                xp = int(round((i - yint) / mx))

                bx = xp - start_x_p
                by = i - start_y_p

                if 0 <= bx < IMAGE_SIZE and 0 <= by < IMAGE_SIZE:
                    if w == 'b':
                        arr1[by][bx] = 1
                    if w == 'r':
                        arr1[by][bx] = 2
        if y1 < y2:
            for i in range(y1, y2 + 1):
                xp = int(round((i - yint) / mx))

                bx = xp - start_x_p
                by = i - start_y_p

                if 0 <= bx < IMAGE_SIZE and 0 <= by < IMAGE_SIZE:
                    if w == 'b':
                        arr1[by][bx] = 1
                    if w == 'r':
                        arr1[by][bx] = 2
                        
                        
def get_pixels2_c(x1, y1, x2, y2):
    mx = (float(y1) - float(y2)) / (float(x1) - float(x2) + 0.0000000000000000000000000000001)
    yint = float(y1) - (mx * float(x1))
    px_func = []
    py_func = []

    if abs(x1 - x2) > abs(y1 - y2) or abs(x1 - x2) == abs(y1 - y2):
        if x1 > x2:
            for i in range(x2, x1 + 1):
                yp = int(round(mx * i + yint))

                bx = i
                by = yp

                if 0 <= bx < IMAGE_SIZE_Y and 0 <= by < IMAGE_SIZE_X:
                    px_func.append(i)
                    py_func.append(yp)
        if x1 < x2:
            for i in range(x1, x2 + 1):
                yp = int(round(mx * i + yint))

                bx = i
                by = yp

                if 0 <= bx < IMAGE_SIZE_Y and 0 <= by < IMAGE_SIZE_X:
                    px_func.append(i)
                    py_func.append(yp)

    if abs(x1 - x2) < abs(y1 - y2):
        if y1 > y2:
            for i in range(y2, y1 + 1):
                xp = int(round((i - yint) / mx))

                bx = xp
                by = i

                if 0 <= bx < IMAGE_SIZE_Y and 0 <= by < IMAGE_SIZE_X:
                    px_func.append(xp)
                    py_func.append(i)
        if y1 < y2:
            for i in range(y1, y2 + 1):
                xp = int(round((i - yint) / mx))

                bx = xp
                by = i

                if 0 <= bx < IMAGE_SIZE_Y and 0 <= by < IMAGE_SIZE_X:
                    px_func.append(xp)
                    py_func.append(i)

    return px_func, py_func


def bbox(x1, y1, x2, y2):
    minx = min([x1, x2])
    miny = min([y1, y2])
    maxx = max([x1, x2])
    maxy = max([y1, y2])

    minx2 = minx - start_x_p
    miny2 = miny - start_y_p
    maxx2 = maxx - start_x_p
    maxy2 = maxy - start_y_p

    # dataa = data[miny-wb:maxy+wb+1, minx-wb:maxx+wb+1]

    # print minx2, miny2, maxx2, maxy2

    return minx, miny, maxx, maxy, minx2, miny2, maxx2, maxy2


def bbox2(x1, y1, x2, y2):
    minx = min([x1, x2])
    # miny = min([y1, y2])
    maxx = max([x1, x2])
    # maxy = max([y1, y2])

    if minx == x1:
        miny = y1
        maxy = y2
    else:
        miny = y2
        maxy = y1

    minx2 = minx - start_x_p
    miny2 = miny - start_y_p
    maxx2 = maxx - start_x_p
    maxy2 = maxy - start_y_p

    # print minx2, miny2, maxx2, maxy2

    return minx, miny, maxx, maxy, minx2, miny2, maxx2, maxy2


def line_eq(x1, y1, x2, y2):
    x1 -= start_x_p
    y1 -= start_y_p
    x2 -= start_x_p
    y2 -= start_y_p

    a1 = float(y1 - y2)
    b1 = float(x2 - x1)
    c1 = float(x1 * y2) - float(x2 * y1)

    tempa = a1
    tempb = b1

    if a1 == 0:
        tempa = 999999999999

    if b1 == 0:
        tempb = 999999999999

    if tempa < tempb:
        mini = tempa
    elif tempb <= tempa:
        mini = tempb
    else:
        mini = 1

    a1 /= mini
    b1 /= mini
    c1 /= mini

    return a1, b1, c1


def l2p3(a1, b1, c1, indi, xmin, xmax, ymin, ymax):

    # print indi[0, ymin-wb:ymax+wb+1, xmin-wb:xmax+wb+1].shape, xmin, xmax, ymin, ymax

    ind2a = indi[0, ymin:ymax, xmin:xmax]
    ind2b = indi[1, ymin:ymax, xmin:xmax]

    ind2 = [ind2a, ind2b]

    da = a1*ind2[1] + b1*ind2[0] + c1
    db = float(sqrt(a1**2 + b1**2)) + 0.0000000000000000000000000000000000001

    d = da / db

    return d


def midpoint(x1, y1, x2, y2):
    # print 'x1 x2:', x1, x2, '\ny1 y2:', y1, y2
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2
    # print 'mx my:', mx, my

    return mx, my


def inter3(x1, y1, x2, y2, lrad1, rrad1):

    dx = x1-x2
    dy = y1-y2
    dist = sqrt(dx*dx + dy*dy)
    dx /= (dist + 0.00000000000000000000001)
    dy /= (dist + 0.00000000000000000000001)

    if y1 > y2:
        x1r = x1 - rrad1*dy
        y1r = y1 + rrad1*dx
        x1l = x1 + lrad1*dy
        y1l = y1 - lrad1*dx

        x2r = x2 - rrad1*dy
        y2r = y2 + rrad1*dx
        x2l = x2 + lrad1*dy
        y2l = y2 - lrad1*dx
    else:
        x1r = x1 + rrad1*dy
        y1r = y1 - rrad1*dx
        x1l = x1 - lrad1*dy
        y1l = y1 + lrad1*dx

        x2r = x2 + rrad1*dy
        y2r = y2 - rrad1*dx
        x2l = x2 - lrad1*dy
        y2l = y2 + lrad1*dx

    return x1r, y1r, x1l, y1l, x2r, y2r, x2l, y2l


def trans(data, bbox_d, xmin, xmax, ymin, ymax, wb):
    data[ymin-wb:ymax+wb+1, xmin-wb:xmax+wb+1] = bbox_d


def roads_func(ti):
    tpt = geom.GetPoint(ti)

    xoff = int((tpt[0] - xOrigin) / pixelWidth)
    yoff = int((tpt[1] - yOrigin) / pixelHeight)

    parr.append([xoff, yoff])


def builds_func(bi):
    bpt = ring.GetPoint(bi)

    xoff = int((bpt[0] - xOrigin) / pixelWidth)
    yoff = int((bpt[1] - yOrigin) / pixelHeight)

    parr.append([xoff, yoff])
    parrx.append([xoff])
    parry.append([yoff])


# get the shapefile driver
driver = ogr.GetDriverByName('ESRI Shapefile')

# open the data source
datasource = driver.Open(r'chicago_roads_utm.shp', 0)
if datasource is None:
    print 'Could not open' + r'chicago_roads_utm.shp'
    exit(1)

datasource2 = driver.Open(r'ChicagoLoop_Morph3_utm.shp', 0)
if datasource2 is None:
    print 'Could not open ' + r'ChicagoLoop_Morph.shp'
    exit(1)

# register all of the GDAL drivers
gdal.AllRegister()

# img = gdal.Open(r'C:\Users\mbq\Documents\1 ORNL\Work\2621_warped_copy.tif', GA_ReadOnly)
# if img is None:
#     print 'Could not open 2621.tif'
#     exit(1)

layer = datasource.GetLayer()

extent = layer.GetExtent()

xOrigin = extent[0]
yOrigin = extent[3]

x = extent[1]
y = extent[2]

FACTOR = 10 / 0.5

PIXEL_SIZE = 0.5 * FACTOR

IMAGE_SIZE_X = 372
IMAGE_SIZE_Y = 274

pixelWidth = PIXEL_SIZE
pixelHeight = -PIXEL_SIZE

start_x = 446768
start_y = 4637947

start_x_p = int((start_x - xOrigin) / pixelWidth)
start_y_p = int((start_y - yOrigin) / pixelHeight)

layer2 = datasource2.GetLayer()

driver_out = gdal.GetDriverByName('GTiff')

proj = osr.SpatialReference()
proj.SetWellKnownGeogCS("WGS84")
proj.SetUTM(16)

data1 = empty((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint8)
data1.fill(255)
ids = empty((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint16)
ids.fill(255)

tempxyz = empty((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)

distarr = empty((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
distarr.fill(0)

ind = indices(data1.shape)

cnt = 0

# radius = 15

afile = open(r'names2_chicago.pkl', 'rb')
names2 = pickle.load(afile)
afile.close()

afile = open(r'fad_out2_chicago.pkl', 'rb')
fad_out2 = pickle.load(afile)
afile.close()

afile = open(r'builfrac_out2_chicago.pkl', 'rb')
builfrac_out2 = pickle.load(afile)
afile.close()

afile = open(r'paf_out2_chicago.pkl', 'rb')
paf_out2 = pickle.load(afile)
afile.close()

afile = open(r'fai_out2_chicago.pkl', 'rb')
fai_out2 = pickle.load(afile)
afile.close()

afile = open(r'rdh_out2_chicago.pkl', 'rb')
rdh_out2 = pickle.load(afile)
afile.close()

afile = open(r'rrl_out2_chicago.pkl', 'rb')
rrl_out2 = pickle.load(afile)
afile.close()

afile = open(r'mdh_out2_chicago.pkl', 'rb')
mdh_out2 = pickle.load(afile)
afile.close()

afile = open(r'mrl_out2_chicago.pkl', 'rb')
mrl_out2 = pickle.load(afile)
afile.close()

afile = open(r'bs2par_out2_chicago.pkl', 'rb')
bs2par_out2 = pickle.load(afile)
afile.close()

afile = open(r'zo_out2_chicago.pkl', 'rb')
zo_out2 = pickle.load(afile)
afile.close()

afile = open(r'zd_out2_chicago.pkl', 'rb')
zd_out2 = pickle.load(afile)
afile.close()

afile = open(r'mean_ht_out2_chicago.pkl', 'rb')
mean_ht_out2 = pickle.load(afile)
afile.close()

afile = open(r'std_ht_out2_chicago.pkl', 'rb')
std_ht_out2 = pickle.load(afile)
afile.close()

afile = open(r'awmh_out2_chicago.pkl', 'rb')
awmh_out2 = pickle.load(afile)
afile.close()

afile = open(r'h2w_out2_chicago.pkl', 'rb')
h2w_out2 = pickle.load(afile)
afile.close()

afile = open(r'car_out2_chicago.pkl', 'rb')
car_out2 = pickle.load(afile)
afile.close()

bldgs = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=double)

# loop through the buildings
feature_buil = layer2.GetNextFeature()

while feature_buil:
    bid = feature_buil.GetFieldAsString('BLDGID')

    # print bid, names2[cnt]

    if bid in names2:
        # print bid, names2[cnt]

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

            map(builds_func, xrange(1, ring.GetPointCount()))

            parrx[:] = [x[0] - start_x_p for x in parrx]
            parry[:] = [y[0] - start_y_p for y in parry]

            parrx = array(parrx)
            parry = array(parry)
            rr, cc = polygon(parrx, parry, [IMAGE_SIZE_Y, IMAGE_SIZE_X])

            bldgs[cc, rr] = bid

            # print bid

            cnt += 1

    feature_buil.Destroy()
    feature_buil = layer2.GetNextFeature()

bldgsh = zeros((15, IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=double)

layer2.ResetReading()
feature_buil = layer2.GetNextFeature()

while feature_buil:
    bid = feature_buil.GetFieldAsString('BLDGID')
    ht = feature_buil.GetFieldAsString('MEAN_AVGHT')

    # print ht

    if bid in names2:
        if ht != '':
            ht = float(ht)
            cnt = 0

            for asdf in xrange(0, 75, 5):
                if ((ht - asdf) >= 5) or (0 < (ht - asdf) < 5):

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

                        map(builds_func, xrange(1, ring.GetPointCount()))

                        parrx[:] = [x[0] - start_x_p for x in parrx]
                        parry[:] = [y[0] - start_y_p for y in parry]

                        parrx = array(parrx)
                        parry = array(parry)
                        rr, cc = polygon(parrx, parry, [IMAGE_SIZE_Y, IMAGE_SIZE_X])

                        bldgsh[cnt, cc, rr] = bid

                cnt += 1

    feature_buil.Destroy()
    feature_buil = layer2.GetNextFeature()

# print bldgs[bldgs != 0]

# print names2

fadn = zeros((15, IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
fadw = zeros((15, IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
fads = zeros((15, IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
fade = zeros((15, IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)

pad = zeros((15, IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
rad = zeros((15, IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)

fai = zeros((4, IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
rrl = zeros((4, IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
rdh = zeros((4, IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
mrl = zeros((4, IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)

for i in xrange(len(fad_out2)):
    for j in xrange(len(fad_out2[i]['n'])):
        fadn[j][bldgs == double(names2[i])] = fad_out2[i]['n'][j]
        fadw[j][bldgs == double(names2[i])] = fad_out2[i]['w'][j]
        fads[j][bldgs == double(names2[i])] = fad_out2[i]['s'][j]
        fade[j][bldgs == double(names2[i])] = fad_out2[i]['e'][j]

        pad[j][bldgs == double(names2[i])] = builfrac_out2[i][j]
        rad[j][bldgs == double(names2[i])] = builfrac_out2[i][j]

    fai[0][bldgs == double(names2[i])] = fai_out2[i]['n']
    fai[1][bldgs == double(names2[i])] = fai_out2[i]['w']
    fai[2][bldgs == double(names2[i])] = fai_out2[i]['s']
    fai[3][bldgs == double(names2[i])] = fai_out2[i]['e']

    rrl[0][bldgs == double(names2[i])] = rrl_out2[i]['n']
    rrl[1][bldgs == double(names2[i])] = rrl_out2[i]['w']
    rrl[2][bldgs == double(names2[i])] = rrl_out2[i]['s']
    rrl[3][bldgs == double(names2[i])] = rrl_out2[i]['e']

    rdh[0][bldgs == double(names2[i])] = rdh_out2[i]['n']
    rdh[1][bldgs == double(names2[i])] = rdh_out2[i]['w']
    rdh[2][bldgs == double(names2[i])] = rdh_out2[i]['s']
    rdh[3][bldgs == double(names2[i])] = rdh_out2[i]['e']

    mrl[0][bldgs == double(names2[i])] = mrl_out2[i]['n']
    mrl[1][bldgs == double(names2[i])] = mrl_out2[i]['w']
    mrl[2][bldgs == double(names2[i])] = mrl_out2[i]['s']
    mrl[3][bldgs == double(names2[i])] = mrl_out2[i]['e']

paf = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
mea = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
std = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
awm = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
b2p = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
h2w = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
grl = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
gdh = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
mdh = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)
car = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)

for i in xrange(len(h2w_out2)):
    h2w[bldgs == double(names2[i])] = h2w_out2[i]
    paf[bldgs == double(names2[i])] = paf_out2[i]
    mea[bldgs == double(names2[i])] = mean_ht_out2[i]
    std[bldgs == double(names2[i])] = std_ht_out2[i]
    awm[bldgs == double(names2[i])] = awmh_out2[i]
    b2p[bldgs == double(names2[i])] = bs2par_out2[i]
    grl[bldgs == double(names2[i])] = zo_out2[i]
    gdh[bldgs == double(names2[i])] = zd_out2[i]
    mdh[bldgs == double(names2[i])] = mdh_out2[i]
    car[bldgs == double(names2[i])] = car_out2[i]

dbh = zeros((15, IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)

for i in xrange(len(fad_out2)):
    for j in xrange(len(bldgsh)):
        dbh[j][bldgsh[j] == double(names2[i])] += float(1) / float(len(fad_out2))

master = zeros((132, IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64)

master[0:15] = fadn[0:15]
master[15:30] = fadw[0:15]
master[30:45] = fads[0:15]
master[45:60] = fade[0:15]
master[60:75] = pad[0:15]
master[75:90] = rad[0:15]

master[90] = paf
master[91] = mea
master[92] = std
master[93] = awm
master[94] = b2p

master[95:99] = fai[0:4]

master[99] = car

master[100] = h2w

master[101] = ones((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float64) * 0.99

master[102] = grl
master[103] = gdh

master[104] = rrl[0]
master[105] = rdh[0]
master[106] = rrl[1]
master[107] = rdh[1]
master[108] = rrl[2]
master[109] = rdh[2]
master[110] = rrl[3]
master[111] = rdh[3]

master[112:116] = mrl[0:4]
master[116] = mdh

master[117:132] = dbh[0:15]

for i in xrange(len(master)):
    master[i][isnan(master[i])] = 0

# print master[0]

for i in xrange(len(master)):

    s = 'tile_' + str(i+1) + '.tif'

    imgOut = driver_out.Create(s, IMAGE_SIZE_Y, IMAGE_SIZE_X, 1, gdal.GDT_Float64)
    bandOut1 = imgOut.GetRasterBand(1)
    bandOut1.WriteArray(master[i], 0, 0)
    imgOut.SetGeoTransform((start_x, pixelWidth, 0, start_y, 0, pixelHeight))
    imgOut.SetProjection(proj.ExportToWkt())

    svis = 'tile_' + str(i+1) + '_visual.tif'

    master[i] *= 10000

    imgOut = driver_out.Create(svis, IMAGE_SIZE_Y, IMAGE_SIZE_X, 1, 1)
    bandOut1 = imgOut.GetRasterBand(1)
    bandOut1.WriteArray(master[i], 0, 0)
    imgOut.SetGeoTransform((start_x, pixelWidth, 0, start_y, 0, pixelHeight))
    imgOut.SetProjection(proj.ExportToWkt())

master = array(master)
master = master.astype(float32)

b = master[0][::5][::5]

# print b

# master[0] += 10

# print master[0][master[0] != 0]
master0 = master[0][master[0] != 0]

# print master0

master_out = bytes()

mast = zeros((132, IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float32)

for i in xrange(len(master)):
    for j in xrange(len(master[i])):
        for k in xrange(len(master[i][j])):
            # print type(master[i][j][k])
            master_out += struct.pack('>i', master[i][len(master[i]) - j - 1][k])

# for i in xrange(len(master)):
#     for j in xrange(len(master[i])):
#         for k in xrange(len(master[i][j])):
#             # print type(master[i][j][k])
#             mast[i][j][k] = master[i][len(master[i]) - j - 1][k]
#
# print mast[0][::5][::5]

# master_out = struct.pack('=%si' % master.size, *master)

afile = save('master_out_chicago', master_out)

with open('master_out_chicago.npy', 'rb') as tile, open('master_out2_chicago.npy', 'wb') as tile2:
    tile2.write(tile.read()[20*4:])

# afile = open(r'master_out.pkl', 'wb')
# pickle.dump(master_out, afile)
# afile.close()

# imgOut = driver_out.Create('Output\\h2w_out2.tif',
#                            IMAGE_SIZE_Y, IMAGE_SIZE_X, 1, gdal.GDT_Float64)
#
# bandOut1 = imgOut.GetRasterBand(1)
# bandOut1.WriteArray(h2w, 0, 0)
# imgOut.SetGeoTransform((start_x, pixelWidth, 0, start_y, 0, pixelHeight))
# imgOut.SetProjection(proj.ExportToWkt())

# for i, dic in enumerate(fad_out2):
#     print i, double(names2[i])
#     for key in dic:
#         for cntr, asdf in enumerate(dic[key]):
#             s = double(names2[i]) + '_' + str(key) + '_fad_out2_' + str(cntr+1)
#
#             print s
#
#             h2w = where(bldgs != double(names2[i]), data1, asdf)

# close the data source
datasource.Destroy()

print "Script took", str(time() - start_time), "seconds to run"
