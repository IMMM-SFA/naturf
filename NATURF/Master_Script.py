
shppath = r'C:/ORNL Spring/Shapefiles'
shpfiles = glob.iglob(os.path.join(shppath, "*.shp"))
for file in shpfiles:
    path = file
    name = 'LV_' + str(os.path.splitext(os.path.basename(file))[0])
    src = os.getcwd()
    dest = os.path.join(shppath, name)
    wrf = os.path.join(dest, name)
    tif = os.path.join(dest, 'Tifs')
    txt = os.path.join(dest, 'Text')
    npy = os.path.join(dest, 'Numpys')
    config = open("config.py", "w")
    config.write('path = ' + repr(path) + '\n' + 'name = ' + repr(name) + '\n' + 'src = ' + repr(src) + '\n' + 'dest = ' + repr(dest) + '\n' + 'dest = ' + repr(dest) + '\n' + 'wrf = ' + repr(wrf) + '\n' + 'tif = ' + repr(tif) + '\n' + 'txt = ' + repr(txt) + '\n' + 'npy = ' + repr(npy) + '\n')
    config.close()

    from Buildings_Raster_Generator import *
    from Building_IDs_Generator import *
    from Parameter_Calculations import *
    from Final_Outputs import *

    print("Master script took", str(time() - start_time), "seconds to run")