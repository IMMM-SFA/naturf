from sys import exit
from time import time
from math import sqrt
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
    dy /= (dist + 0.00000000000000000000001);

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
    print 'Could not open ' + r'chicago_roads_utm.shp'
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

dlon = abs(extent[0] - extent[1])  # wide
dlat = abs(extent[2] - extent[3])  # tall

xOrigin = extent[0]
yOrigin = extent[3]

x = extent[1]
y = extent[2]

PIXEL_SIZE = 0.5

IMAGE_SIZE_X = 6300
IMAGE_SIZE_Y = 3000

pixelWidth = PIXEL_SIZE
pixelHeight = -PIXEL_SIZE

p2500x = PIXEL_SIZE * IMAGE_SIZE_X / 2
p2500y = PIXEL_SIZE * IMAGE_SIZE_Y / 2

dlon_div_2 = dlon / 2
dlat_div_2 = dlat / 2

start_x = 446861
start_y = 4637537

end_x = start_x + p2500x + p2500x
end_y = start_y - p2500y - p2500y

rows_new = int((end_x - start_x) / pixelWidth)
cols_new = int(round((end_y - start_y) / -pixelHeight))

start_x_p = int((start_x - xOrigin) / pixelWidth)
start_y_p = int((start_y - yOrigin) / pixelHeight)

end_x_p = int((end_x - xOrigin) / pixelWidth)
end_y_p = int((end_y - yOrigin) / pixelHeight)

# print start_x_p, end_x_p, start_y_p, end_y_p

rows = int((x - xOrigin) / pixelWidth)
cols = int((y - yOrigin) / pixelHeight)

layer2 = datasource2.GetLayer()

driver_out = gdal.GetDriverByName('GTiff')
imgOut = driver_out.Create(r'no_raster_temp_chicago_UTM_new.tif',
                           IMAGE_SIZE_Y, IMAGE_SIZE_X, 1, 1)

proj = osr.SpatialReference()
proj.SetWellKnownGeogCS("WGS84")
proj.SetUTM(16)

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

        buils[cc, rr] = 127

    feature_buil.Destroy()
    feature_buil = layer2.GetNextFeature()

# loop through the roads
feature_road = layer.GetNextFeature()
while feature_road:
    road_type = feature_road.GetFieldAsString('type')
    rid = feature_road.GetFieldAsString('osm_id')

    if rid == '236806530':

        if road_type == 'motorway':
            radius = 20
        elif road_type == 'trunk':
            radius = 18
        elif road_type == 'primary':
            radius = 16
        elif road_type == 'secondary':
            radius = 14
        elif road_type == 'tertiary':
            radius = 12
        elif road_type == 'unclassified':
            radius = 10
        elif road_type == 'residential':
            radius = 8
        elif road_type == 'service':
            radius = 6
        else:
            radius = 3

        thres = 0

        # print radius

        lradius = radius  # - thres
        rradius = radius  # - thres

        geom = feature_road.GetGeometryRef()
        nameg = geom.GetGeometryName()

        if nameg == 'MULTILINESTRING':

            for i in range(geom.GetGeometryCount()):
                mgeom = geom.GetGeometryRef(i)
                x = mgeom.GetX()
                y = mgeom.GetY()

                xOffset = int((x - xOrigin) / pixelWidth)
                yOffset = int((y - yOrigin) / pixelHeight)

                parr = [[xOffset, yOffset]]

                for j in range(1, mgeom.GetPointCount()):
                    tpt = mgeom.GetPoint(j)

                    xoff = int((tpt[0] - xOrigin) / pixelWidth)
                    yoff = int((tpt[1] - yOrigin) / pixelHeight)

                    parr.append([xoff, yoff])

        elif nameg == 'LINESTRING':

            x = geom.GetX()
            y = geom.GetY()

            xOffset = int((x - xOrigin) / pixelWidth)
            yOffset = int((y - yOrigin) / pixelHeight)

            parr = [[xOffset, yOffset]]

            for j in range(1, geom.GetPointCount()):
                    tpt = geom.GetPoint(j)

                    xoff = int((tpt[0] - xOrigin) / pixelWidth)
                    yoff = int((tpt[1] - yOrigin) / pixelHeight)

                    parr.append([xoff, yoff])

        for i in range(len(parr)-1):
            if (start_x_p <= parr[i][0] < end_x_p) or (start_y_p <= parr[i][1] < end_y_p):  # and \
                    # (parr[i][0] != parr[i+1][0] and parr[i][1] != parr[i+1][1]):

                x1, y1, x2, y2 = parr[i][0] - start_x_p, parr[i][1] - start_y_p, parr[i+1][0] - start_x_p, parr[i+1][1] - start_y_p

                # print x1, y1, x2, y2

                xmi, ymi, xma, yma, xmi2, ymi2, xma2, yma2 = bbox(parr[i][0], parr[i][1], parr[i+1][0], parr[i+1][1])

                a, b, c = line_eq(parr[i][0], parr[i][1], parr[i+1][0], parr[i+1][1])

                if xmi2 - radius < 0:
                    xmi2 = 0
                else:
                    xmi2 -= radius
                if ymi2 - radius < 0:
                    ymi2 = 0
                else:
                    ymi2 -= radius

                if xmi2 >= IMAGE_SIZE_Y:
                    xmi2 = IMAGE_SIZE_Y - 1
                if ymi2 >= IMAGE_SIZE_X:
                    ymi2 = IMAGE_SIZE_X - 1

                if xma2 + radius + 1 < 0:
                    xma2 = 0
                if yma2 + radius + 1 < 0:
                    yma2 = 0

                if xma2 + radius + 1 >= IMAGE_SIZE_Y:
                    xma2 = IMAGE_SIZE_Y - 1
                else:
                    xma2 += radius + 1
                if yma2 + radius + 1 >= IMAGE_SIZE_X:
                    yma2 = IMAGE_SIZE_X - 1
                else:
                    yma2 += radius + 1

                # print xmi2, ymi2, xma2, yma2, radius+1

                if xmi2 <= xma2 and (((xma2 - xmi2) > (radius+1)) and ((yma2 - ymi2) > (radius+1))):

                    if ymi2 > yma2:
                        tempdgj = yma2
                        yma2 = ymi2
                        ymi2 = tempdgj

                    dist = l2p3(a, b, c, ind, xmi2, xma2, ymi2, yma2)

                    # savetxt(r'no_raster_dist.txt', dist, '%lf')

                    index = column_stack(where(buils[ymi2:yma2, xmi2:xma2] == 127))

                    # print index, '\n'

                    # calculates how far the building is from the road
                    if len(index) != 0:
                        dist_r_to_b = dist[index[:, 0], index[:, 1]]
                        index2 = dist_r_to_b[abs(dist_r_to_b) <= radius]

                        indexa = index2[index2 >= 0]  # positive
                        indexb = index2[index2 < 0]  # negative

                        # print indexa, indexb, '\n'

                        if len(indexa) != 0 and len(indexb) != 0:
                            lradius = abs(indexa.min()) - thres
                            rradius = abs(indexb.max()) - thres
                        elif len(indexa) != 0 and len(indexb) == 0:
                            lradius = abs(indexa.min()) - thres
                            rradius = radius - (abs(indexa.min()) - thres) + radius
                        elif len(indexa) == 0 and len(indexb) != 0:
                            rradius = abs(indexb.max()) - thres
                            lradius = radius - (abs(indexb.max()) - thres) + radius
                        else:
                            lradius = float(radius)
                            rradius = float(radius)

                        index3a = dist_r_to_b[abs(dist_r_to_b) <= lradius]  # pos
                        index3b = dist_r_to_b[abs(dist_r_to_b) <= rradius]  # neg

                        # print index3a, index3b

                        ina = index3a[index3a >= 0]
                        inb = index3b[index3b < 0]

                        # print ina, inb

                        if len(ina) != 0:
                            lradius = abs(ina.min()) - thres

                        if len(inb) != 0:
                            rradius = abs(inb.max()) - thres

                # print lradius, rradius, '\n'

                x1r, y1r, x1l, y1l, x2r, y2r, x2l, y2l = inter3(x1, y1, x2, y2, lradius, rradius)

                xf1, yf1 = midpoint(x1r, y1r, x1l, y1l)
                xf2, yf2 = midpoint(x2r, y2r, x2l, y2l)

                rad = sqrt((x1r - xf1)**2 + (y1r - yf1)**2)

                # print rad

                # print xf1, yf1, xf2, yf2

                if rad >= 1 and ((xf1 >= 0 and yf1 >= 0) and
                                 (xf2 >= 0 and yf2 >= 0) and
                                 (xf1 < IMAGE_SIZE_Y and yf1 < IMAGE_SIZE_X) and
                                 (xf2 < IMAGE_SIZE_Y and yf2 < IMAGE_SIZE_X)):
                    # print 'here'

                    xarr, yarr = get_pixels2_c(int(xf1), int(yf1), int(xf2), int(yf2))

                    tempxyz.fill(255)
                    tempxyz[yarr, xarr] = 0

                    distarr.resize((yma2-ymi2, xma2-xmi2))

                    distarr = ndimage.distance_transform_edt(tempxyz[ymi2:yma2, xmi2:xma2])

                    # print distarr

                    distarr[data1[ymi2:yma2, xmi2:xma2] == 1] = 0

                    data1[ymi2:yma2, xmi2:xma2] = where(distarr > rad, tempxyz[ymi2:yma2, xmi2:xma2], 1)

                    xs = xmi2
                    ys = ymi2
                    xl = xma2
                    yl = yma2
    
    feature_road.Destroy()
    feature_road = layer.GetNextFeature()

data1 = where(buils != 127, data1, 127)

bandOut1.WriteArray(data1, 0, 0)

imgOut.SetGeoTransform((start_x, pixelWidth, 0, start_y, 0, pixelHeight))
imgOut.SetProjection(proj.ExportToWkt())

# close the data source
datasource.Destroy()

print "Script took", str(time() - start_time), "seconds to run"
