from config import *
from WRF_Calculations import *
from sys import exit
from time import time
from math import sqrt
from math import ceil
from numpy import array, arange, transpose, set_printoptions, zeros, uint8, uint16, indices, where, empty, float64, \
    column_stack, savetxt, isnan, mean, shape, ones, int32, save, float32, double, diff
from skimage.draw import polygon
import osr
from PIL import Image
from scipy import ndimage, misc
import pickle
import sklearn.preprocessing
import struct
import csv
import os
import glob
import shutil

try:
    from osgeo import gdal, ogr
    from osgeo.gdalconst import *
except ImportError:
    import gdal
    import ogr
    from gdalconst import *

start_time = time()

filename = "%s.npy" % name

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

FACTOR = 100/0.5

PIXEL_SIZE = 0.5 * FACTOR

IMAGE_SIZE_X = tiley
IMAGE_SIZE_Y = tilex

pixelWidth = PIXEL_SIZE
pixelHeight = -PIXEL_SIZE

start_x = int(xOrigin)
start_y = ceil(yOrigin)

start_x_p = int((start_x - xOrigin) / pixelWidth)
start_y_p = int((start_y - yOrigin) / pixelHeight)

driver_out = gdal.GetDriverByName('GTiff')

proj = osr.SpatialReference()
proj.SetWellKnownGeogCS("WGS84")
proj.SetUTM(11, False)

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

afile = open(r'names2.pkl', 'rb')
names2 = pickle.load(afile)
afile.close()

afile = open(r'fad_out2.pkl', 'rb')
fad_out2 = pickle.load(afile)
afile.close()

afile = open(r'builfrac_out2.pkl', 'rb')
builfrac_out2 = pickle.load(afile)
afile.close()

afile = open(r'paf_out2.pkl', 'rb')
paf_out2 = pickle.load(afile)
afile.close()

afile = open(r'fai_out2.pkl', 'rb')
fai_out2 = pickle.load(afile)
afile.close()

afile = open(r'rdh_out2.pkl', 'rb')
rdh_out2 = pickle.load(afile)
afile.close()

afile = open(r'rrl_out2.pkl', 'rb')
rrl_out2 = pickle.load(afile)
afile.close()

afile = open(r'mdh_out2.pkl', 'rb')
mdh_out2 = pickle.load(afile)
afile.close()

afile = open(r'mrl_out2.pkl', 'rb')
mrl_out2 = pickle.load(afile)
afile.close()

afile = open(r'bs2par_out2.pkl', 'rb')
bs2par_out2 = pickle.load(afile)
afile.close()

afile = open(r'zo_out2.pkl', 'rb')
zo_out2 = pickle.load(afile)
afile.close()

afile = open(r'zd_out2.pkl', 'rb')
zd_out2 = pickle.load(afile)
afile.close()

afile = open(r'mean_ht_out2.pkl', 'rb')
mean_ht_out2 = pickle.load(afile)
afile.close()

afile = open(r'std_ht_out2.pkl', 'rb')
std_ht_out2 = pickle.load(afile)
afile.close()

afile = open(r'awmh_out2.pkl', 'rb')
awmh_out2 = pickle.load(afile)
afile.close()

afile = open(r'h2w_out2.pkl', 'rb')
h2w_out2 = pickle.load(afile)
afile.close()

afile = open(r'car_out2.pkl', 'rb')
car_out2 = pickle.load(afile)
afile.close()

bldgs = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=double)

# loop through the buildings
feature_buil = layer2.GetNextFeature()

while feature_buil:
    bid = feature_buil.GetFieldAsString('ID')

    if bid in names2:

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

            for i in range(1, numpoints):
                bpt = ring.GetPoint(i)

                xoff = int((bpt[0] - xOrigin) / pixelWidth)
                yoff = int((bpt[1] - yOrigin) / pixelHeight)

                parrx.append([xoff])
                parry.append([yoff])

            parrx[:] = [x[0] - start_x_p for x in parrx]
            parry[:] = [y[0] - start_y_p for y in parry]

            parrx = array(parrx)
            parry = array(parry)
            rr, cc = polygon(parrx, parry, [IMAGE_SIZE_Y, IMAGE_SIZE_X])

            bldgs[cc, rr] = bid

            cnt += 1

    feature_buil.Destroy()
    feature_buil = layer2.GetNextFeature()

bldgsh = zeros((15, IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=double)

layer2.ResetReading()
feature_buil = layer2.GetNextFeature()

while feature_buil:
    bid = feature_buil.GetFieldAsString('ID')
    ht = feature_buil.GetFieldAsString('Height')

    if bid in names2:
        if ht != '':
            ht = float(ht)
            cnt = 0

            for asdf in range(0, 75, 5):
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

                        for i in range(1, numpoints):
                            bpt = ring.GetPoint(i)

                            xoff = int((bpt[0] - xOrigin) / pixelWidth)
                            yoff = int((bpt[1] - yOrigin) / pixelHeight)

                            parrx.append([xoff])
                            parry.append([yoff])

                        parrx[:] = [x[0] - start_x_p for x in parrx]
                        parry[:] = [y[0] - start_y_p for y in parry]

                        parrx = array(parrx)
                        parry = array(parry)
                        rr, cc = polygon(parrx, parry, [IMAGE_SIZE_Y, IMAGE_SIZE_X])

                        bldgsh[cnt, cc, rr] = bid

                cnt += 1

    feature_buil.Destroy()
    feature_buil = layer2.GetNextFeature()

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

for i in range(len(fad_out2)):
    for j in range(len(fad_out2[i]['n'])):
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

for i in range(len(h2w_out2)):
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

for i in range(len(fad_out2)):
    for j in range(len(bldgsh)):
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

for i in range(len(master)):
    master[i][isnan(master[i])] = 0

# print master[0]

for i in range(len(master)):

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

master0 = master[0][master[0] != 0]

master_out = []

mast = zeros((132, IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=float32)

for i in range(len(master)):
    master_outi = bytes()
    for j in range(len(master[i])):
        for k in range(len(master[i][j])):
            master_outi += struct.pack('>i', int(master[i][len(master[i]) - j - 1][k]))

            # print('Progress (inner loop): ', k, '/', len(master[i][j]))
        # print('Progress (middle loop): ', j, '/', len(master[i]))
    master_out.append(master_outi)
    print('Progress (outer loop): ', i, '/', len(master))

master_out_final = bytes()

for i in range(len(master_out)):
    master_out_final += master_out[i]

afile = save('temp', master_out_final)

with open('temp.npy', 'rb') as tile, open(filename, 'wb') as tile2:
    tile2.write(tile.read()[20*4:])

tilex = str(tilex)
tiley = str(tiley)

txtname = "%s.txt" % name

with open('index.txt','w') as index:
    index.write('type=continuous\n')
    index.write('  projection=regular_ll\n')
    index.write('  missing_value=-999900.\n')
    index.write('  dy=0.08333333333\n')
    index.write('  dx=0.08333333333\n')
    index.write('  known_x=1\n')
    index.write('  known_y=1\n')
    index.write('  known_lat=0.0\n')
    index.write('  known_lon=-180.0\n')
    index.write('  wordsize=4\n')
    index.write('  endian=big\n')
    index.write('  signed=no\n')
    index.write('  tile_x=')
    index.write(tilex + '\n')
    index.write('  tile_y=')
    index.write(tiley + '\n')
    index.write('  tile_z=132\n')
    index.write('  units="dimensionless"\n')
    index.write('  scale_factor=0.0001\n')
    index.write('  description="Urban_Parameters"\n')

with open('index.txt', 'r') as index, open(txtname, 'w') as index2:
    index2.write(index.read())

minlr = str(min(gridleft,gridright))
maxlr = str(max(gridleft,gridright))
mintb = str(min(gridbottom,gridtop))
maxtb = str(max(gridbottom,gridtop))

indexname = minlr + "-" + maxlr
indexext = mintb + "-" + maxtb

indexfile = "%s.%s" % (indexname,indexext)

with open(filename, 'rb') as tile, open(indexfile, 'wb') as tile2:
    tile2.write(tile.read())

#print("WRF Index:", min(gridleft,gridright), "-", max(gridleft,gridright), ".", min(gridbottom,gridtop), "-", max(gridbottom,gridtop))
#print("Tile Size:", tilex, "X", tiley)

os.mkdir(wrf)
os.mkdir(txt)
os.mkdir(tif)

srcfiles = os.listdir(src)
for file_name in srcfiles:
    full_file_name = os.path.join(src, file_name)
    if os.path.isfile(full_file_name):
        shutil.copy(full_file_name, dest)

binary = os.path.join(dest, indexfile)
shutil.copy2(binary, wrf)
index = os.path.join(dest, 'index.txt')
shutil.copy2(index, wrf)

txtfiles = glob.iglob(os.path.join(dest, "*.txt"))
for file in txtfiles:
    if os.path.isfile(file):
        shutil.move(file, txt)

tiffiles = glob.iglob(os.path.join(dest, "*.tif"))
for file in tiffiles:
    if os.path.isfile(file):
        shutil.move(file, tif)

npyfiles = glob.iglob(os.path.join(dest, "*.npy"))
for file in npyfiles:
    if os.path.isfile(file):
        shutil.move(file, npy)

print("Script 4 took", str(time() - start_time), "seconds to run")
