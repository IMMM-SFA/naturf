#!/bin/bash
FILES="/mnt/data/UrbanMorphology/im3_ornl/New_Vegas/Vegas_Top_Half/*.shp"
for f in $FILES
do
export path=$f

python << EOF
import os
path= os.environ['path']
name = 'LV_' + str(os.path.splitext(os.path.basename(path))[0])
src = r'/mnt/data/UrbanMorphology/im3_ornl/New_Vegas/Vegas_Top_Half/Scripts'
dest = os.path.join(r'/mnt/data/UrbanMorphology/im3_ornl/New_Vegas/Vegas_Top_Half', name)
wrf = os.path.join(dest, name)
tif = os.path.join(dest, 'Tifs')
txt = os.path.join(dest, 'Text')
npy = os.path.join(dest, 'Numpys')
config = open("config.py", "w")
config.write('path = ' + repr(path) + '\n' + 'name = ' + repr(name) + '\n' + 'src = ' + repr(src) + '\n' + 'dest = ' + repr(dest) + '\n' + 'dest = ' + repr(dest) + '\n' + 'wrf = ' + repr(wrf) + '\n' + 'tif = ' + repr(tif) + '\n' + 'txt = ' + repr(txt) + '\n' + 'npy = ' + repr(npy) + '\n')
config.close()

EOF

chmod 777 config.py

python Buildings_Raster_Generator.py
python Building_IDs_Generator.py
python Parameter_Calculations.py
python Final_Outputs.py

mv $f /mnt/data/UrbanMorphology/im3_ornl/New_Vegas/LV_Processed_Tracts

done
