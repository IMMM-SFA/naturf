# GRID and BINS (WRF Pre-Processing)
from Parameter_Definitions import *
from sys import exit
import math
from numpy import array, zeros, uint8, mean
from PIL import Image
import csv
import warnings
import pickle

try:
    from osgeo import gdal, ogr
    from osgeo.gdalconst import *
except ImportError:
    import gdal
    import ogr
    from gdalconst import *


def calculate_parameters(path, tifDir, outputDir, name, height_field, id_field):
    '''
    Use functions defined in Parameter_Definitions.py to calculate urban parameters, pickle them, and create a csv.
    
    Parameters
    ----------
    path : PosixPath or str
        Path to study shapefile. 
    tifDir : PosixPath or str
        Path to directory for tif outputs.
    outputDir : PosixPath or str
        Path to directory for pickle and csv outputs.
    name : str
        Name of output csv with no extension.
    height_field : str
        Name of height field in study shapefile.
    id_field : str
        Name of ID field in study shapefile.
    '''
    if type(path) != 'str':
        path = str(path) 
    if type(tifDir) != 'str':
        tifDir = str(tifDir)

    # get the shapefile driver
    gdal.AllRegister()
    driver = ogr.GetDriverByName('ESRI Shapefile')
    buils_shp = path
    datasource2 = driver.Open(buils_shp, 0)
    if datasource2 is None:
        print('Could not open shapefile')
        exit(1)

    buils_raster = tifDir +'/Buildings_Raster.tif'
    img = gdal.Open(buils_raster, GA_ReadOnly)
    if img is None:
        print('Could not open image')
        exit(1)

    # register all of the GDAL drivers
    gdal.AllRegister()

    layer2 = datasource2.GetLayer()

    extent2 = layer2.GetExtent()

    xOrigin = extent2[0]
    yOrigin = extent2[3]

    PIXEL_SIZE = 0.5

    IMAGE_SIZE_X = (2 * math.ceil(extent2[3]-extent2[2])) + 100
    IMAGE_SIZE_Y = (2 * math.ceil(extent2[1]-extent2[0])) + 100

    pixelWidth = PIXEL_SIZE
    pixelHeight = -PIXEL_SIZE

    start_x = int(xOrigin)
    start_y = math.ceil(yOrigin)


    start_x_p = int((start_x - xOrigin) / pixelWidth)
    start_y_p = int((start_y - yOrigin) / pixelHeight)

    i2arr = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint8)

    buils_ids = tifDir +'/Building_IDs.tif'
    ids = Image.open(buils_ids)

    ids = array(ids)

    import rasterio

    with rasterio.open(tifDir +'/Building_IDs.tif') as src:

        arr_ids = src.read(1)


    filename = "%s.csv" % name

    wi = math.hypot((extent2[0] - extent2[1]), (extent2[2] - extent2[2]))

    he = math.hypot((extent2[0] - extent2[0]), (extent2[3] - extent2[2]))

    car = wi / he

    cents, hts, areas = get_cents_hts(IMAGE_SIZE_X, IMAGE_SIZE_Y, layer2, ids, PIXEL_SIZE, height_field)

    cents_ns, cents_ew, avgsa, nbarea, mean_ht_out, std_ht_out, awmh_out = avg_building_dist(IMAGE_SIZE_X, IMAGE_SIZE_Y, layer2, ids, PIXEL_SIZE, height_field, hts, areas, cents)

    fad_out, builfrac_out, fai_out, rdh_out, rrl_out, mdh_out, mrl_out, bs2par_out,\
        zo_out, zd_out, car_out = parameters1(IMAGE_SIZE_X, IMAGE_SIZE_Y, layer2, ids, PIXEL_SIZE, height_field, 'south', 0, nbarea, cents_ns, cents_ew, avgsa)

    # print car_out

    # print fad_out, builfrac_out, fai_out

    h2wratios, names = h2w(IMAGE_SIZE_X, IMAGE_SIZE_Y, layer2, xOrigin, yOrigin, pixelWidth, pixelHeight, start_x_p, start_y_p, PIXEL_SIZE, height_field, id_field)

    paras_out = [['Name', 'Frontal Area Density', 'Plan Area Density', 'Roof Area Density',
                'Plan Area Fraction', 'Mean Building Height', 'Standard Deviation of Building Heights',
                'Area Weighted Mean of Building Heights', 'Building Surface to Plan Area Ratio',
                'Frontal Area Index', 'Grimmond and Oke (GO) Roughness Length', 'GO Displacement Height',
                'Raupach Roughness Length', 'Raupach Displacement Height', 'MacDonald et al. Roughness Length',
                'MacDonald et al. Displacement Height', 'Height to Width Ratio', 'Complete Aspect Ratio']]

    # #$%#$%#$%#$%#$%#$%#$%#$%#$%#$%#$%#$%#$%#$%

    names2, fad_out2, builfrac_out2, paf_out2, fai_out2, rdh_out2, rrl_out2, mdh_out2, mrl_out2, bs2par_out2, zo_out2,\
        zd_out2, mean_ht_out2, std_ht_out2, awmh_out2, h2w_out2, car_out2 = [], [], [], [], [], [], [], [], [], [], [],\
                                                                            [], [], [], [], [], []

    # #$%#$%#$%#$%#$%#$%#$%#$%#$%#$%#$%#$%#$%#$%

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)

        for i in range(len(names)):

            n1 = names[i]

            # print n1

            if len(fad_out[i]) != 0:

                for qw in range(len(builfrac_out[i])):
                    builfrac_out[i][qw] = mean(builfrac_out[i][qw])

                bui1 = builfrac_out[i]  # 15

                bs21 = mean(bs2par_out[i])  # 1

                for qw in range(15):

                    fad_out[i]['n'][qw] = mean(fad_out[i]['n'][qw])
                    fad_out[i]['w'][qw] = mean(fad_out[i]['w'][qw])
                    fad_out[i]['s'][qw] = mean(fad_out[i]['s'][qw])
                    fad_out[i]['e'][qw] = mean(fad_out[i]['e'][qw])

                fad1 = fad_out[i]  # 15 * 4

                fai_out[i]['n'] = mean(fai_out[i]['n'])
                fai_out[i]['w'] = mean(fai_out[i]['w'])
                fai_out[i]['s'] = mean(fai_out[i]['s'])
                fai_out[i]['e'] = mean(fai_out[i]['e'])

                rrl_out[i]['n'] = mean(rrl_out[i]['n'])
                rrl_out[i]['w'] = mean(rrl_out[i]['w'])
                rrl_out[i]['s'] = mean(rrl_out[i]['s'])
                rrl_out[i]['e'] = mean(rrl_out[i]['e'])

                rdh_out[i]['n'] = mean(rdh_out[i]['n'])
                rdh_out[i]['w'] = mean(rdh_out[i]['w'])
                rdh_out[i]['s'] = mean(rdh_out[i]['s'])
                rdh_out[i]['e'] = mean(rdh_out[i]['e'])

                mrl_out[i]['n'] = mean(mrl_out[i]['n'])
                mrl_out[i]['w'] = mean(mrl_out[i]['w'])
                mrl_out[i]['s'] = mean(mrl_out[i]['s'])
                mrl_out[i]['e'] = mean(mrl_out[i]['e'])

                fai1 = fai_out[i]  # 4
                rrl1 = rrl_out[i]  # 4
                rdh1 = rdh_out[i]  # 4
                mrl1 = mrl_out[i]  # 4

                paf = mean(builfrac_out[i])

                mdh1 = mean(mdh_out[i])  # 1?

                mea1 = mean_ht_out[i]  # 1 mbh
                std1 = std_ht_out[i]  # 1 stdev
                awm1 = awmh_out[i]  # 1 awm
                zo1 = mean(zo_out[i])  # 1 grl
                zd1 = mean(zd_out[i])  # 1 gdh
                h2w1 = h2wratios[i]  # 1 h2w
                car1 = car_out[i]

                # print n1, fad1, bui1, paf, mea1, std1, awm1, bs21, fai1, zo1, zd1, rrl1, rdh1, mrl1, mdh1, h2w1, car1

                names2.append(n1)
                fad_out2.append(fad1)
                builfrac_out2.append(bui1)
                paf_out2.append(paf)
                fai_out2.append(fai1)
                rdh_out2.append(rdh1)
                rrl_out2.append(rrl1)
                mdh_out2.append(mdh1)
                mrl_out2.append(mrl1)
                bs2par_out2.append(bs21)
                zo_out2.append(zo1)
                zd_out2.append(zd1)
                mean_ht_out2.append(mea1)
                std_ht_out2.append(std1)
                awmh_out2.append(awm1)
                h2w_out2.append(h2w1)
                car_out2.append(car1)

                paras_out.append([n1, fad1, bui1, bui1, paf, mea1, std1, awm1, bs21, fai1, zo1, zd1, rrl1, rdh1,
                                mrl1, mdh1, h2w1, car1])

    
    c = open(outputDir/filename, 'w')
    wr = csv.writer(c)
    wr.writerows(paras_out)
    c.close()

    afile = open(outputDir/'names2.pkl', 'wb')
    pickle.dump(names2, afile)
    afile.close()

    afile = open(outputDir/'fad_out2.pkl', 'wb')
    pickle.dump(fad_out2, afile)
    afile.close()

    afile = open(outputDir/'builfrac_out2.pkl', 'wb')
    pickle.dump(builfrac_out2, afile)
    afile.close()

    afile = open(outputDir/'paf_out2.pkl', 'wb')
    pickle.dump(paf_out2, afile)
    afile.close()

    afile = open(outputDir/'fai_out2.pkl', 'wb')
    pickle.dump(fai_out2, afile)
    afile.close()

    afile = open(outputDir/'rdh_out2.pkl', 'wb')
    pickle.dump(rdh_out2, afile)
    afile.close()

    afile = open(outputDir/'rrl_out2.pkl', 'wb')
    pickle.dump(rrl_out2, afile)
    afile.close()

    afile = open(outputDir/'mdh_out2.pkl', 'wb')
    pickle.dump(mdh_out2, afile)
    afile.close()

    afile = open(outputDir/'mrl_out2.pkl', 'wb')
    pickle.dump(mrl_out2, afile)
    afile.close()

    afile = open(outputDir/'bs2par_out2.pkl', 'wb')
    pickle.dump(bs2par_out2, afile)
    afile.close()

    afile = open(outputDir/'zo_out2.pkl', 'wb')
    pickle.dump(zo_out2, afile)
    afile.close()

    afile = open(outputDir/'zd_out2.pkl', 'wb')
    pickle.dump(zd_out2, afile)
    afile.close()

    afile = open(outputDir/'mean_ht_out2.pkl', 'wb')
    pickle.dump(mean_ht_out2, afile)
    afile.close()

    afile = open(outputDir/'std_ht_out2.pkl', 'wb')
    pickle.dump(std_ht_out2, afile)
    afile.close()

    afile = open(outputDir/'awmh_out2.pkl', 'wb')
    pickle.dump(awmh_out2, afile)
    afile.close()

    afile = open(outputDir/'h2w_out2.pkl', 'wb')
    pickle.dump(h2w_out2, afile)
    afile.close()

    afile = open(outputDir/'car_out2.pkl', 'wb')
    pickle.dump(car_out2, afile)
    afile.close()