from config import *
import math
import utm
import osr
try:
    from osgeo import gdal, ogr
    from osgeo.gdalconst import *
except ImportError:
    import gdal
    import ogr
    from gdalconst import *

#path = r'C:\ORNL Spring\Census Tracts\Tracts 51-60\005803-005877\005844\005844.shp'

driver = ogr.GetDriverByName('ESRI Shapefile')

datasource2 = driver.Open(path, 0)
if datasource2 is None:
    print('Could not open ' + r'ChicagoLoop_Morph.shp')
    exit(1)

# register all of the GDAL drivers
gdal.AllRegister()

layer2 = datasource2.GetLayer()
extent2 = layer2.GetExtent()

# Define the extent in UTM coordinates, the desired spatial resolution in meters, and also the UTM zone of the study area
top = extent2[3]
bottom = extent2[2]
left = extent2[0]
right = extent2[1]
resolution = 100
zone = 11

# Coverts the UTM coordinates to latitude and longitude
northwest = (top,left)
southeast = (bottom,right)
latlontl = utm.to_latlon(northwest[1],northwest[0],zone, northern=True)
latlonbr = utm.to_latlon(southeast[1],southeast[0],zone, northern=True)
#print(latlontl,latlonbr)

# Assigns variables to the new coordinates
newtop = latlontl[0]
newbottom = latlonbr[0]
newleft = latlontl[1]
newright = latlonbr[1]

# Calculates the values for the WRF index number
gridtop = math.ceil(newtop * 120)
gridbottom = int(newbottom * 120)
gridleft = int((newleft + 180) * 120)
gridright = math.ceil((newright + 180) * 120)

# This prints out the WRF index number (with spaces added)
#print("WRF Index:", min(gridleft,gridright), "-", max(gridleft,gridright), ".", min(gridbottom,gridtop), "-", max(gridbottom,gridtop))

# Uses the grid numbers to calculate new latitude and longitude coordinates
newlonglatleft = (gridleft/120) - 180
newlonglatright = (gridright/120) - 180
newlonglattop = (gridtop/120)
newlonglatbottom = (gridbottom/120)

# Converts the new latitude and longitude coordinates back to UTM coordinates
topleft = (newlonglattop,newlonglatleft)
bottomright = (newlonglatbottom,newlonglatright)
utmtl = utm.from_latlon(topleft[0],topleft[1],zone)
utmbr = utm.from_latlon(bottomright[0],bottomright[1],zone)
#print(utmtl)
#print(utmbr)

# Finds the difference between the eastings and the northings
eastings = abs(utmtl[0]-utmbr[0])
northings = abs(utmtl[1]-utmbr[1])

# Calculates the tile size for the script
tilex = round(eastings/resolution)
tiley = round(northings/resolution)
#print("Tile Size:", tilex, "X", tiley)
