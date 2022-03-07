import multiprocessing
import pandas as pd
import pathlib
import Buildings_Raster as BR
import Building_IDs as BI
import Parameter_Calculations as PC
import Binary

def processFile(shapeFile):
    folder = shapeFile.parent.parent # directory housing output subdirectories
    scenario = shapeFile.parent.parent.stem # first part of output directory name
    buildingTile = shapeFile.stem # filename without extension
    outputDir = folder/'{}_{}'.format(scenario, buildingTile) # create output directory named according to tile
    tifDir = outputDir/'Tifs'
    tifDir.mkdir(parents=True, exist_ok=True) # automatically also creates outputDir

    indexfile = filenames[buildingTile][0] # binary file name
    cenlat = 34.0 # Center latitude of the study area
    cenlon = -118.0 # Center longitude of the study area
    id_field = 'ID' # Name of the field containing ID data in shapefile
    height_field = 'Height' # Name of the field containing height data in shapefile
    
    BR.make_raster(shapeFile, tifDir, cenlat, cenlon)
    BI.make_ids_image(shapeFile, tifDir, cenlat, cenlon, id_field)
    PC.calculate_parameters(shapeFile, tifDir, outputDir, buildingTile, height_field, id_field)
    Binary.make_binary(buildingTile, shapeFile, tifDir, cenlat, cenlon, outputDir, id_field, height_field, indexfile)

    print(buildingTile + " has finished")
    
basePath = pathlib.Path('/mnt/data/UrbanMorphology/data/32x32/dilarea_testing/Shapefiles') # Path to directory containing shapefiles
shapeFiles = list(basePath.glob('*.shp')) # Creates a list of all the shapefile paths
grid = pd.read_csv(pathlib.Path('/mnt/data/UrbanMorphology/data/32x32/LA_Indices.csv')) # Path to geogrid csv
filenames = grid.set_index('GRID_ID').T.to_dict("list") # Creates a dictionary from the csv where grid IDs and the names are values

try:
    cpus = min(50, len(shapeFiles))
except NotImplementedError:
    cpus = 1
    #cpus = 96   # max
pool = multiprocessing.Pool(processes=cpus)

pool.map(processFile, shapeFiles)