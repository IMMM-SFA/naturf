from time import time
start_time = time()
import winsound


from Buildings_Raster_Generator import *
from Building_IDs_Generator import *
from Parameter_Calculations import *
from Final_Outputs import *

print("Master script took", str(time() - start_time), "seconds to run")
winsound.Beep(1000,1000)