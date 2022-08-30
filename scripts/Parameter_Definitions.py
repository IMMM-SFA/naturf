import math
from numpy import array, zeros, uint8, uint16, where, empty, sum, unique, rint, array_equiv
from skimage.draw import polygon
from scipy import ndimage


def get_pixels2_c(IMAGE_SIZE_X, IMAGE_SIZE_Y, x1, y1, x2, y2):

    SMALL_DECIMAL = 0.0000000000000000000000000000001

    slope = (float(y1) - float(y2)) / (float(x1) - float(x2) + SMALL_DECIMAL) # Finds the slope between two points
    yint = float(y1) - (slope * float(x1)) # todo: what is yint
    px_func, py_func = []

    if abs(slope) <= 1: 
        if x1 > x2:
            x1, x2 = x2, x1
            
        for i in range(x1, x2 + 1): # All x integers between x1 and x2
            yp = int(round(slope * i + yint)) # the y integers for the x integers

            bx = i # The current x coordinate
            by = yp # The current y coordinate

            if 0 <= bx < IMAGE_SIZE_Y and 0 <= by < IMAGE_SIZE_X: # Checks if the current coordinate is in quad 1 and within the tile
                px_func.append(i) # Appends the x coordinate
                py_func.append(yp) # Appends the y coordinate

    else: # the absolute value of the slope is > 1
        if y1 > y2:
            y1, y2 = y2, y1
            
        for i in range(y1, y2 + 1): # All y integers between y1 and y2 
            xp = int(round((i - yint) / slope)) # The x integers for the y integers

            bx = xp # The current x coordinate
            by = i # The current y coordinate

            if 0 <= bx < IMAGE_SIZE_Y and 0 <= by < IMAGE_SIZE_X: # Checks if the current coordinate is in quad 1 and within the tile
                px_func.append(xp)
                py_func.append(i)

    return px_func, py_func # Returns the coordinates for all integers within each wall

def inter4p(x1, y1, x2, y2, rad1):
    SMALL_DECIMAL = 0.0000000000000000000000000000001

    dx = x1-x2 # The distance between the x coordinates
    dy = y1-y2 # The distance between the y coordinates
    dist = math.sqrt(dx*dx + dy*dy) # The distance between the two points
    dx /= (dist + SMALL_DECIMAL) # The ratio of the horizontal distance to the hypotenuse
    dy /= (dist + SMALL_DECIMAL) # The ratio of the vertical distance to the hypotenuse

    if y1 > y2:
        x1r = x1 - rad1*dy
        y1r = y1 + rad1*dx
    else:
        x1r = x1 + rad1*dy
        y1r = y1 - rad1*dx

    return x1r, y1r


def inter4n(x1, y1, x2, y2, rad1):
    SMALL_DECIMAL = 0.0000000000000000000000000000001

    dx = x1-x2
    dy = y1-y2
    dist = math.sqrt(dx*dx + dy*dy)
    dx /= (dist + SMALL_DECIMAL)
    dy /= (dist + SMALL_DECIMAL)

    if y1 > y2:
        x1l = x1 + rad1*dy
        y1l = y1 - rad1*dx
    else:
        x1l = x1 - rad1*dy
        y1l = y1 + rad1*dx

    return x1l, y1l


def ang2lines(linea, lineb):
    """Finds the angle between two lines."""
    # returns [0, 360]
    DEGREES_IN_CIRCLE = 360

    va = [(linea[0][0]-linea[1][0]), (linea[0][1]-linea[1][1])]
    vb = [(lineb[0][0]-lineb[1][0]), (lineb[0][1]-lineb[1][1])]

    angle = math.atan2(va[1], va[0]) - math.atan2(vb[1], vb[0])
    angle *= DEGREES_IN_CIRCLE / (2 * math.pi)

    if angle < 0:
        angle += DEGREES_IN_CIRCLE

    return angle


def ang2points(x1, y1, x2, y2):
    """Finds the angle between two points."""
    DEGREES_IN_CIRCLE = 360

    dx = x2 - x1 # The distance between the x coordinates
    dy = y2 - y1 # The distance between the y coordinates

    angle_in_radians = math.atan2(dy, dx) # The angle facing the y coordinate (theta-y) in radians
    angle_in_degrees = math.degrees(angle_in_radians) # Theta-y in degrees

    if angle_in_degrees < 0:
        angle_in_degrees += DEGREES_IN_CIRCLE

    return angle_in_degrees


def get_cents_hts(IMAGE_SIZE_X, IMAGE_SIZE_Y, layer2, ids, PIXEL_SIZE, height_field):
    '''
    Loop through all buildings in the shapefile and append their centroids, heights, and areas to dictionaries.

    Parameters
    ----------
    IMAGE_SIZE_X : int
        Length of the shapefile in the x-direction.
    IMAGE_SIZE_Y : int
        Length of the shapefile in the y-direction.
    layer2 : osgeo.ogr.Layer
        The target layer of the shapefile, automatically generated in Parameter_Calulcations.py.
    ids : numpy.ndarray
        Array where the buildings in the shapefile are represented by unique ids, automatically generated in Parameter_Calulcations.py.
    PIXEL_SIZE : float
        Pixel size of the building raster.
    height_field : str
        Name of height field in study shapefile.

    Returns
    ----------
    centroids : dict
        Centroid of every building in the shapefile
    heights : dict
        Height of every building in the shapefile
    areas : dict
        Area of every building in the shapefile

    '''
    centroids = {}
    heights = {}
    areas = {}
    i2arr = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint8)
    count = 1

    layer2.ResetReading()
    feature_buil = layer2.GetNextFeature()

    # todo: replace with for loop to remove count variable
    while feature_buil:
        height = feature_buil.GetFieldAsString(height_field)

        if height != '':
            height = float(height)
            heights[count] = height

            geom = feature_buil.GetGeometryRef()
            ring = geom.GetGeometryRef(0)
            numpoints = ring.GetPointCount()

            if numpoints != 0:

                cent = geom.Centroid()
                centx = cent.GetX()
                centy = cent.GetY()

                centx = float(centx)
                centy = float(centy)

                centroids[count] = [centx, centy]

                building_area = 0

                i2arr.fill(0)
                if len(ids[ids == count]) != 0:
                    i2arr[ids == count] = 1
                    building_area = sum(i2arr) * PIXEL_SIZE**2

                areas[count] = building_area

        count += 1

        feature_buil.Destroy()
        feature_buil = layer2.GetNextFeature()

    return centroids, heights, areas


def avg_building_dist(IMAGE_SIZE_X, IMAGE_SIZE_Y, layer2, ids, PIXEL_SIZE, height_field, heights, areas, centroids):
    '''
    Loops through all the buildings in the shapefile to calculate distances between buildings and other information used in
    calculating urban parameters. Calculates urban parameters 92-94.

    Parameters
    ----------
    IMAGE_SIZE_X : int
        Length of the shapefile in the x-direction.
    IMAGE_SIZE_Y : int
        Length of the shapefile in the y-direction.
    layer2 : osgeo.ogr.Layer
        The target layer of the shapefile, automatically generated in Parameter_Calulcations.py.
    ids : numpy.ndarray
        Array where the buildings in the shapefile are represented by unique ids, automatically generated in Parameter_Calulcations.py.
    PIXEL_SIZE : float
        Pixel size of the building raster.
    height_field : str
        Name of height field in the shapefile.
    heights : dict
        Height of every building in the shapefile.
    areas : dict
        Area of every building in the shapefile.
    centroids : dict
        Centroid of every building in the shapefile.

    Returns
    ----------
    average_north_south_building_distances : dict
        Average north/south distance from each building to every other building.
    average_east_west_building_distances : dict
        Average east/west distance from each building to every other building.
    average_building_area : float
        Average building area for the shapefile.
    footprint_building_areas : dict
        Height and building footprint areas within the plan area for each building.
    average_building_heights : list
        Average height of the buildings.
    standard_deviation_building_heights : list
        Standard deviation of heights of the buildings.
    area_weighted_average_building_heights : list
        Area-weighted mean building heights.

    '''

    i2arr = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint8)
    dils = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint8)
    narr = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint8)
    struct = ndimage.generate_binary_structure(2, 2)
    RADIUS = 100
    NORTHWEST_DEGREES = 135
    NORTHEAST_DEGREES = 45
    SOUTHWEST_DEGREES = 225
    SOUTHEAST_DEGREES = 315
    DEGREES_IN_CIRCLE = 360
    START_OF_CIRCLE_DEGREES = 0
    sumareas = 0
    counter = 1
    average_north_south = 0
    average_east_west = 0

    average_north_south_building_distances = {}
    average_east_west_building_distances = {}
    average_building_heights = []
    standard_deviation_building_heights = []
    area_weighted_average_building_heights = []
    footprint_building_areas = {}

    layer2.ResetReading()
    feature_buil = layer2.GetNextFeature()

    while feature_buil:
        height = feature_buil.GetFieldAsString(height_field)

        average_north_south = 0
        average_east_west = 0

        sumarhts = 0
        sumareas2 = 0

        current_building_heights = []

        if height != '':

            geomb = feature_buil.GetGeometryRef()
            ring = geomb.GetGeometryRef(0)
            numpoints = ring.GetPointCount()

            if numpoints != 0:

                i2arr.fill(0)
                dils.fill(0)
                narr.fill(0)
                if len(ids[ids == counter]) != 0:
                    i2arr[ids == counter] = 1 # Puts a 1 wherever the current counter corresponds with the IDs file
                    builarea = sum(i2arr) * PIXEL_SIZE**2 # Sums up the 1s and multiplies by the pixel area to get the current building area
                    i2arr = ndimage.binary_dilation(i2arr, structure=struct, iterations=RADIUS).astype(i2arr.dtype) # Dilates the i2arr to get a square with radius 100 pixels
                    building_ids = unique(ids[where(i2arr == 1)]) # A list of the unique building IDs found in the current dilated area
                    sumareas += builarea

                    if len(building_ids) != 0:
                        currcx = centroids[counter][0] # current building centroid x coordinate
                        currcy = centroids[counter][1] # current building centroid y coordinate

                        te, tn, ts, tw = 0., 0., 0., 0.
                        ce, cn, cs, cw = 0., 0., 0., 0.
                        
                        for building_id in building_ids: # loops through every building and calculates the distance and angle from that building to all other buildings
                            if building_id != 0 and building_id in heights: # Checks that the unique ID is not 0 (because height indexing begins at 1) and that it is in the heights list
                                current_building_heights.append(heights[building_id]) # Appends the current building height to the current_building_heights list
                                dils[(ids == building_id) & (i2arr == 1)] = 1 # Creates an array with 1s where the current ID is within the dilated area

                                sumarhts += areas[building_id] * heights[building_id] # Multiplies the current building area and height together, and then adds it to a rolling sum for the tile
                                sumareas2 += areas[building_id] # Adds the current building height to a rolling sum
                                #print("counter", counter)

                                if building_id != counter: # Loops through every building except for the current one
                                    cx = centroids[building_id][0] # The centroid x coordinate of the other building
                                    cy = centroids[building_id][1] # The centroid y coordinate of the other building
                                    d = math.hypot((currcx - cx), (currcy - cy)) # The distance between the two centroids
                                    angle = ang2points(currcx, currcy, cx, cy) # The angle for the y coordinate
                                    
                                    # The angles correspond to a circle where 0/360 degrees is directly east, and the degrees increase counter-clockwise
                                    if (SOUTHEAST_DEGREES <= angle <= DEGREES_IN_CIRCLE or START_OF_CIRCLE_DEGREES <= angle < NORTHEAST_DEGREES) and d != 0:  # east
                                        te += d
                                        ce += 1
                                    elif NORTHWEST_DEGREES <= angle < SOUTHWEST_DEGREES and d != 0:  # west
                                        tw += d
                                        cw += 1
                                    elif NORTHEAST_DEGREES <= angle < NORTHWEST_DEGREES and d != 0:  # north
                                        tn += d
                                        cn += 1
                                    elif SOUTHWEST_DEGREES <= angle < SOUTHEAST_DEGREES and d != 0:  # south 
                                        ts += d
                                        cs += 1
                                    else:
                                        raise Exception("Angle isn't between 0 and 360.")

                        if cn != 0 or cs != 0:
                            average_north_south = (tn + ts) / (cn + cs) # The mean north and south distance from the current building to all other buildings
                        else:
                            average_north_south = 0

                        if ce != 0 or cw != 0:
                            average_east_west = (te + tw) / (ce + cw) # The mean west and east distance from the current building to all other buildings
                        else:
                            average_east_west = 0

                        narr[(dils == 1) & (i2arr == 1)] = 1 # Creates an array with 1s only where the buildings are
                        plan_area = sum(narr) * PIXEL_SIZE**2 # Calculates the area of all buildings within the plan area 

                        footprint_building_areas[counter] = [height, plan_area]  # Creates a dictionary where the counter corresponds to the height and plan area of each building

            if len(current_building_heights) != 0:
                current_building_heights = array(current_building_heights)
                average_building_heights.append(current_building_heights.mean())
                standard_deviation_building_heights.append(current_building_heights.std())
            else:
                average_building_heights.append(height)

                # TODO:  wouldn't the standard deviation of a single value be 0 and not the value itself?
                standard_deviation_building_heights.append(height)

            average_north_south_building_distances[counter] = average_north_south
            average_east_west_building_distances[counter] = average_east_west

            if sumareas2 != 0:
                area_weighted_average_building_heights.append(sumarhts / sumareas2)
            else:
                area_weighted_average_building_heights.append(0)

        counter += 1

        feature_buil.Destroy()
        feature_buil = layer2.GetNextFeature()

    average_building_area = sumareas / counter  # sum of all of the surface areas in shapefile (used in a parameter)

    return average_north_south_building_distances, \
           average_east_west_building_distances, \
           average_building_area, \
           footprint_building_areas, \
           average_building_heights, \
           standard_deviation_building_heights, \
           area_weighted_average_building_heights


def parameters1(IMAGE_SIZE_X, IMAGE_SIZE_Y, layer2, ids, PIXEL_SIZE, height_field, direc, building_id, newbarea, cents_ns, cents_ew, average_building_area):  # if building_id == 0, loops through all of the buildings
    '''
    Takes variables from previous functions and calculates urban parameters 1-91, 95, 96-100, 103-117.

    Parameters
    ----------
    IMAGE_SIZE_X : int
        Length of the shapefile in the x-direction.
    IMAGE_SIZE_Y : int
        Length of the shapefile in the y-direction.
    layer2 : osgeo.ogr.Layer
        The target layer of the shapefile, automatically generated in Parameter_Calulcations.py.
    ids : numpy.ndarray
        Array where the buildings in the shapefile are represented by unique ids, automatically generated in Parameter_Calulcations.py.
    PIXEL_SIZE : float
        Pixel size of the building raster.
    height_field : str
        Name of height field in the shapefile.
    direc : str
        Direction used to calculate certain parameters. (NOTE: Current default is south)
    building_id : int or float
        Unique building ID; if 0, loops through all buildings. (NOTE: Current default is 0)
    newbarea : dict
        Height and building footprint areas within the plan area for each building. (NOTE: This is the same as footprint_building_areas from the previous function)
    cents_ns : dict
        Average north/south distance from each building to every other building. (NOTE: This is the same as average_north_south_building_distances from the previous function)
    cents_es : dict
        Average east/west distance from each building to every other building. (NOTE: This is the same as average_east_west_building_distances from the previous function)
    average_building_area : float
        Average building area for the shapefile.
 
    Returns
    ----------
    fad_out_inc : list
        Frontal area density for each building from each direction and vertical level.
    builfrac_out_inc : list
        Plan area density for each building at each vertical level.
    fai_out_inc : list
        Frontal area index for each building from each direction.
    rdh_out_inc : list
        Raupach displacement height for each building from each direction.
    rrl_out_inc : list
        Raupach roughness length for each building from each direction.
    mdh_out_inc : list
        Macdonald et al. displacement height for each building, calculated from one direction (south).
    mrl_out_inc : list
        Macdonald et al. roughness length for each building, calculated from each direction.
    bs2par_out_inc : list
        Building surface area to plan area ratio for each building (currently 1 for each building).
    roughness_length_out_inc : list
        Grimmond & Oke roughness length for each building.
    displacement_height_out_inc : list
        Grimmond & Oke displacement height for each building.
    car_out_inc: list
        Complete aspect ratio for each building.
    '''
    BUILDING_HEIGHT_INTERVAL = 5
    CONSTANT_NEG_04 = -0.4
    CONSTANT_0193 = 0.193
    CONSTANT_0303 = 0.303
    CONSTANT_359 = 3.59
    CONSTANT_15 = 15
    DEGREES_IN_CIRCLE = 360
    DILAREA_DEFAULT = 10000
    DISPLACEMENT_HEIGHT_FACTOR = 0.67
    MAX_BUILDING_HEIGHT = 75
    NORTHEAST_DEGREES = 45
    NORTHWEST_DEGREES = 135
    RADIUS = 100
    RDH_THRESHOLD_MAX = 3
    RDH_THRESHOLD_MIN = 0 
    ROUGHNESS_LENGTH_FACTOR = 0.1
    RRL_THRESHOLD_MAX = 3
    RRL_THRESHOLD_MIN = 0
    SMALL_DECIMAL = 0.0000000000000000000000000000001
    SOUTHEAST_DEGREES = 315
    SOUTHWEST_DEGREES = 225
    START_OF_CIRCLE_DEGREES = 0
    ZXCV_FACTOR = 3.5
    
    dist = -1
    builarea = 0
    dilarea = 0

    sumarhts = 0
    sumareas = 0
    counter = 1

    i2arr = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint8)
    struct = ndimage.generate_binary_structure(2, 2)
    fad_out_inc = []
    builfrac_out_inc = []
    fai_out_inc = []
    rdh_out_inc = []
    rrl_out_inc = []
    mdh_out_inc = []
    mrl_out_inc = []
    bs2par_out_inc = []
    roughness_length_out_inc = []
    displacement_height_out_inc = []
    car_out_inc = []

    ################
    # The "if" portion of this loop is never called from `Parameter_Calculations`; "building_id" is hardcoded as zero, meaning the else statement always runs.
    ################

    layer2.ResetReading()
    feature_buil = layer2.GetNextFeature()

    if building_id != 0:
        while feature_buil:
            height = feature_buil.GetFieldAsString(height_field)

            fad_out = []
            builfrac_out = []
            fai_out = []
            rdh_out = []
            rrl_out = []
            mdh_out = []
            mrl_out = []
            bs2par_out = []
            roughness_length_out = []
            displacement_height_out = []

            # todo: is this checking if height(int) is null?
            if height != '':


                height = float(height)


                for vertical_height in range(BUILDING_HEIGHT_INTERVAL, MAX_BUILDING_HEIGHT, BUILDING_HEIGHT_INTERVAL):

                    if (height - vertical_height) > 0:
                        nht = BUILDING_HEIGHT_INTERVAL
                    elif (height - vertical_height + BUILDING_HEIGHT_INTERVAL) > 0:
                        nht = height - vertical_height + BUILDING_HEIGHT_INTERVAL
                    else:
                        nht = SMALL_DECIMAL

                    if height == 0:
                        zh = SMALL_DECIMAL
                    else:
                        zh = height

                    roughness_length = ROUGHNESS_LENGTH_FACTOR * zh
                    displacement_height = DISPLACEMENT_HEIGHT_FACTOR * zh

                    roughness_length_out.append(roughness_length)
                    displacement_height_out.append(displacement_height)

                    fads = []
                    fais = []
                    rdhs = []
                    rrls = []
                    mrls = []
                    builfracs, mdhs, bs2pars = [], [], []

                    if building_id == counter:

                        geomb = feature_buil.GetGeometryRef()
                        ring = geomb.GetGeometryRef(0)
                        numpoints = ring.GetPointCount()

                        if numpoints != 0:

                            i2arr.fill(0)
                            builarea = 0
                            dilarea = 0

                            if len(ids[ids == building_id]) != 0:
                                i2arr[ids == building_id] = 1
                                builarea = sum(i2arr) * PIXEL_SIZE**2
                                dilarea = builarea
                                i2arr = ndimage.binary_dilation(i2arr, structure=struct, iterations=RADIUS).astype(i2arr.dtype)

                                sumarhts += builarea * nht
                                sumareas += builarea

                            nx, ny, _ = ring.GetPoint(0)

                            parrxc = [[nx]]
                            parryc = [[ny]]

                            for point_index in range(1, ring.GetPointCount()):
                                point = ring.GetPoint(point_index)

                                parrxc.append([point[0]])
                                parryc.append([point[1]])

                            parrxc = array(parrxc)
                            parryc = array(parryc)

                            for na in range(0, len(parrxc)-1):
                                p1x = parrxc[na]
                                p1y = parryc[na]

                                p2x = parrxc[na+1]
                                p2y = parryc[na+1]

                                if (p1x, p1y) != (p2x, p2y):

                                    perpx0 = parrxc[na]

                                    if parryc[na] + 1 < IMAGE_SIZE_X:
                                        perpy0 = parryc[na] + 1
                                    else:
                                        perpy0 = IMAGE_SIZE_X

                                    line1 = [[p1x, p1y], [p2x, p2y]]
                                    line0deg = [[p1x, p1y], [perpx0, perpy0]]

                                    deg = ang2lines(line1, line0deg)
                                    dist = math.hypot((p2x - p1x), (p2y - p1y))

                                    # todo: do we need the latter 2 conditionals?
                                    if dist >= 1 and (direc.lower() in {"east", "north", "west", "south"}) and START_OF_CIRCLE_DEGREES <= deg <= DEGREES_IN_CIRCLE:
                                        if ((dist / 10) - 1) > 0:
                                            wallarea = dist * nht

                                            if dilarea == 0:
                                                break

                                            fad = wallarea / dilarea

                                            if newbarea[counter][0] > height:
                                                builfrac = newbarea[counter][1] / dilarea
                                            else:
                                                builfrac = 0

                                            if (cents_ns[counter] * cents_ew[counter]) != 0:
                                                fai = (dist * zh) / (cents_ns[counter] * cents_ew[counter])
                                                rdh = zh * (1 - (1 - math.exp(-math.sqrt(CONSTANT_15 * fai))/math.sqrt(CONSTANT_15 * fai)))
                                                rrl = zh * ((1 - rdh) * math.exp(CONSTANT_NEG_04 * (1 / math.sqrt(CONSTANT_0303 * fai)) - CONSTANT_0193))
                                            else:
                                                fai = 0
                                                rdh = 0
                                                rrl = 0

                                            mdh = zh * (1 + (1 / CONSTANT_359 ** builfrac) * (builfrac - 1))
                                            # todo: what is zxcv
                                            zxcv = ZXCV_FACTOR * (1 - rdh) * (wallarea / average_building_area)

                                            if zxcv >= 0:
                                                mrl = zh * (1 - rdh) * math.exp(-1 / (math.sqrt(zxcv)))
                                            else:
                                                mrl = 0

                                            bs2par = newbarea[counter][1] / newbarea[counter][1]  # currently always 1

                                            fads.append(fad)
                                            builfracs.append(builfrac)
                                            fais.append(fai)
                                            rdhs.append(rdh)
                                            rrls.append(rrl)
                                            mdhs.append(mdh)
                                            mrls.append(mrl)
                                            bs2pars.append(bs2par)

                    fad_out.append(fads)
                    builfrac_out.append(builfracs)
                    fai_out.append(fais)
                    rdh_out.append(rdhs)
                    rrl_out.append(rrls)
                    mdh_out.append(mdhs)
                    mrl_out.append(mrls)
                    bs2par_out.append(bs2pars)

                fad_out_inc.append(fad_out)
                builfrac_out_inc.append(builfrac_out)
                fai_out_inc.append(fai_out)
                rdh_out_inc.append(rdh_out)
                rrl_out_inc.append(rrl_out)
                mdh_out_inc.append(mdh_out)
                mrl_out_inc.append(mrl_out)
                bs2par_out_inc.append(bs2par_out)
                roughness_length_out_inc.append(roughness_length_out)
                displacement_height_out_inc.append(displacement_height_out)

            counter += 1

            feature_buil.Destroy()
            feature_buil = layer2.GetNextFeature()

    else:
        while feature_buil:
            height = feature_buil.GetFieldAsString(height_field)

            if height != '':
                height = float(height)

                fad_out = {'n': [], 'w': [], 's': [], 'e': []}
                fai_out = {'n': [], 'w': [], 's': [], 'e': []}
                rdh_out = {'n': [], 'w': [], 's': [], 'e': []}
                rrl_out = {'n': [], 'w': [], 's': [], 'e': []}
                mrl_out = {'n': [], 'w': [], 's': [], 'e': []}

                builfrac_out = []
                mdh_out = []
                bs2par_out = []
                roughness_length_out = []
                displacement_height_out = []

                edist = 0
                wdist = 0
                sdist = 0

                ##############
                # "vertical_height" represents the current vertical level, from 0 to MAX_BUILDING_HEIGHT meters.
                # "nht" is used for some parameters when we only want to look at a BUILDING_HEIGHT_INTERVAL m section of a building.
                # If the building height is greater than the current vertical level by at least BUILDING_HEIGHT_INTERVAL m, then nht is BUILDING_HEIGHT_INTERVAL.
                # If the building height is greater than the current vertical level by less than BUILDING_HEIGHT_INTERVAL, then nht is that difference.
                # Otherwise, we set nht to be just above 0.
                ##############

                for vertical_height in range(0, MAX_BUILDING_HEIGHT, BUILDING_HEIGHT_INTERVAL): 
                    if (height - vertical_height) >= BUILDING_HEIGHT_INTERVAL:
                        nht = BUILDING_HEIGHT_INTERVAL
                    elif 0 < (height - vertical_height) < BUILDING_HEIGHT_INTERVAL:
                        nht = height - vertical_height
                    else:
                        nht = SMALL_DECIMAL

                    ##############
                    # "zh" represents the entire building height, which we want to use for some parameters.
                    # "roughness_length" and "displacement_height" represent Grimmond & Oke roughness length and displacement height, respectively.
                    # "roughness_length" is parameter 103 and "displacement_height" is parameter 104.

                    if height == 0:
                        zh = SMALL_DECIMAL
                    else:
                        zh = height

                    roughness_length = ROUGHNESS_LENGTH_FACTOR * zh
                    displacement_height = DISPLACEMENT_HEIGHT_FACTOR * zh

                    roughness_length_out.append(roughness_length)
                    displacement_height_out.append(displacement_height)

                    fads, fade, fadn, fadw = [], [], [], []
                    fais, fain, faie, faiw = [], [], [], []
                    rdhs, rdhn, rdhe, rdhw = [], [], [], []
                    rrls, rrln, rrle, rrlw = [], [], [], []
                    mrls, mrln, mrle, mrlw = [], [], [], []
                    builfracs, mdhs, bs2pars = [], [], []

                    geomb = feature_buil.GetGeometryRef()
                    ring = geomb.GetGeometryRef(0)
                    numpoints = ring.GetPointCount()

                    if numpoints != 0:

                        i2arr.fill(0)
                        builarea = 0
                        dilarea = 0

                        ##############
                        # This if statement creates four variables used for various parameters: "builarea", "dilarea", "sumarhts", and "sumareas".
                        # They all use "i2arr", which I believe is an array the size of the shapefile with 1s where the current building is in the "ids" array.
                        # "builarea" is the sum of all the 1s in "i2arr" multiplied by the pixel area, meaning the footprint area of the current building.
                        # "i2arr" is then dilated to put a buffer around the current building.
                        # "dilarea" is the sum of all the 1s in the dilated "i2arr" multiplied by the pixel area, meaning the plan area for the current building.
                        # "sumarhts" is the rolling sum of the building footprint areas multiplied by "nht"
                        # "sumareas" is the rolling sum of the building footprint areas
                        ##############

                        if len(ids[ids == counter]) != 0:
                            i2arr[ids == counter] = 1 # Puts a 1 wherever the current counter corresponds with the IDs file
                            builarea = sum(i2arr) * PIXEL_SIZE**2 # Sums up the 1s and multiplies by the pixel area to get the current building area
                            dilarea = builarea
                            i2arr = ndimage.binary_dilation(i2arr, structure=struct, iterations=RADIUS).astype(i2arr.dtype) # Dilates the i2arr to get a square with radius 100 pixels

                            sumarhts += builarea * (nht + 1)

                        nx, ny, _ = ring.GetPoint(0) # The minimum x and y for each building
                        parrxc = [[nx]] # Puts the minimum x into a list of lists
                        parryc = [[ny]] # Puts the minimum y into a list of lists
                        
                        for point_index in range(1, ring.GetPointCount()):
                            point = ring.GetPoint(point_index) # Finds the coordinates for each point in the building polygon

                            parrxc.append([point[0]]) # Appends the x coordinates to the parrxc list
                            parryc.append([point[1]]) # Appends the y coordinates to the parrxc list
                            
                        parrxc = array(parrxc)
                        parryc = array(parryc)
                        
                        for na in range(0, len(parrxc)-1):
                            p1x = parrxc[na] # Extracts the x coordinate corresponding to na
                            p1y = parryc[na] # Extracts the y coordinate corresponding to na

                            p2x = parrxc[na+1] # Extracts the x coordinate corresponding to na + 1
                            p2y = parryc[na+1] # Extracts the y coordinate corresponding to na + 1

                            if (p1x, p1y) != (p2x, p2y):

                                perpx0 = parrxc[na] # Sets the origin x coordinate to p1x
                                if parryc[na] + 1 < IMAGE_SIZE_X:
                                    perpy0 = parryc[na] + 1 # Sets the origin y coordinate to p1y + 1 if it is less than the width of the study area
                                else:
                                    perpy0 = IMAGE_SIZE_X # Otherwise, sets the origin y coordinate to the width of the study area

                                line1 = [[p1x, p1y], [p2x, p2y]] # Creates a line from the na point to the na + 1 point
                                line0deg = [[p1x, p1y], [perpx0, perpy0]] # Creates a line from the na point to 
                                deg = ang2lines(line1, line0deg) # Returns the direction of the wind normal to the wall
                                dist = math.sqrt((p2x - p1x)**2 + (p2y - p1y)**2) # The length of the wall

                                if dist >= 1:

                                    ##############
                                    # The calculation of frontal area density, frontal area index, Raupach roughness length and displacement height,
                                    # Macdonald et al. roughness length and displacement height, complete aspect ratio, and plan area density start here.
                                    # We define the direction of the wind normal to the wall in the mathematical plane, which is calculated above for each
                                    # wall of the current building.
                                    #
                                    # East/West/South
                                    #
                                    # The length of walls facing east, west, and south are captured with the variable "edist", "wdist", and "sdist". They
                                    # will be used later on for the complete aspect ratio. 
                                    #
                                    # East/North/West/South
                                    #
                                    # The area of the wall at the current vertical level is captured by "wallarea", and is divided by the plan area for the
                                    # current building to calculate frontal area density. 
                                    # The frontal area index is calculated using the length of the current wall, the total building height, and the average
                                    # north/south and east/west distances to the other buildings.
                                    # Raupach displacement height is calculated from the total building height and the frontal area index.
                                    # Raupach roughness length is then calculated from the total building height, Raupach displacement height, and frontal 
                                    # area index.
                                    # Macdonald et al. roughness length is calculated from the total building height, Raupach displacement height, the wall area,
                                    # and the average building area for the shapefile.
                                    # 
                                    # South
                                    # 
                                    # The plan area fraction/density/rooftop area density is calculated (as "builfrac") using the building areas calculated prior and 
                                    # the current plan area.
                                    # Macdonald et al. displacement height is calculated using the total building height and the plan area fraction. 
                                    ##############

                                    if ((dist / 10) - 1) > 0:
                                        if SOUTHEAST_DEGREES <= deg <= DEGREES_IN_CIRCLE or START_OF_CIRCLE_DEGREES <= deg < NORTHEAST_DEGREES:
                                            edist = dist # Used for calculation of complete aspect ratio
                                        elif NORTHEAST_DEGREES <= deg < NORTHWEST_DEGREES:
                                            if vertical_height == 0:
                                                dilarea = DILAREA_DEFAULT
                                        elif NORTHWEST_DEGREES <= deg < SOUTHWEST_DEGREES:
                                            wdist = dist # Used for calculation of complete aspect ratio
                                        # todo: why does only this conditional have direc.lower()?
                                        elif (direc.lower() == 'south') and (SOUTHWEST_DEGREES <= deg < SOUTHEAST_DEGREES):
                                            sdist = dist # Used for calculation of complete aspect ratio

                                        wallarea = dist * nht # The area of the wall at the current 5m slice

                                        if dilarea == 0:
                                            break
                                        
                                        fad = wallarea / dilarea

                                        if (direc.lower() == 'south') and (SOUTHWEST_DEGREES <= deg < SOUTHEAST_DEGREES):
                                            if float(newbarea[counter][0]) > float(vertical_height): # Checks if the height of the current building is greater than the current 5m slice
                                                builfrac = newbarea[counter][1] / dilarea # Divides the plan area by the dilated area to calculate the ratio of building area to dilated area
                                            else:
                                                builfrac = 0
                                            
                                            mdh = zh * (1 + (1 / 3.59 ** builfrac) * (builfrac - 1))
                                            bs2par = newbarea[counter][1] / newbarea[counter][1]  # currently always 1

                                        
                                        if (cents_ns[counter] * cents_ew[counter]) != 0:
                                            fai = (dist * zh) / (cents_ns[counter] * cents_ew[counter])
                                            rdh = zh * (1 - (1 - math.exp(-math.sqrt(CONSTANT_15 * fai))/math.sqrt(CONSTANT_15 * fai)))
                                            rrl = zh * (1 - rdh) * math.exp(CONSTANT_NEG_04 * (1 / math.sqrt(CONSTANT_0303 * fai)) - CONSTANT_0193)
                                        else:
                                            fai = 0
                                            rdh = 0
                                            rrl = 0

                                        # todo: what is zxcv?
                                        zxcv = ZXCV_FACTOR * (1 - rdh) * (wallarea / average_building_area)

                                        if zxcv >= 0:
                                            mrl = zh * (1 - rdh) * math.exp(-1 / (math.sqrt(zxcv)))
                                        else:
                                            mrl = 0

                                        if rrl > RRL_THRESHOLD_MAX or rrl < RRL_THRESHOLD_MIN:
                                            rrl = 0
                                        if rdh > RDH_THRESHOLD_MAX or rdh < RDH_THRESHOLD_MIN:
                                            rdh = 0

                                        faie.append(fai)
                                        rdhe.append(rdh)
                                        rrle.append(rrl)
                                        mrle.append(mrl)

                                        if float(fad) < SMALL_DECIMAL:
                                            if SOUTHEAST_DEGREES <= deg <= DEGREES_IN_CIRCLE or START_OF_CIRCLE_DEGREES <= deg < NORTHEAST_DEGREES:
                                                fade.append(0)
                                            elif NORTHEAST_DEGREES <= deg < NORTHWEST_DEGREES:
                                                fadn.append(0)
                                            elif NORTHWEST_DEGREES <= deg < SOUTHWEST_DEGREES:
                                                fadw.append(0)
                                            elif (direc.lower() == 'south') and (SOUTHWEST_DEGREES <= deg < SOUTHEAST_DEGREES):
                                                fads.append(0)

                                        else:
                                            if SOUTHEAST_DEGREES <= deg <= DEGREES_IN_CIRCLE or START_OF_CIRCLE_DEGREES <= deg < NORTHEAST_DEGREES:
                                                fade.append(fad)
                                            elif NORTHEAST_DEGREES <= deg < NORTHWEST_DEGREES:
                                                fadn.append(fad)
                                            elif NORTHWEST_DEGREES <= deg < SOUTHWEST_DEGREES:
                                                fadw.append(fad)
                                            elif (direc.lower() == 'south') and (SOUTHWEST_DEGREES <= deg < SOUTHEAST_DEGREES):
                                                fads.append(fad)
                                        
                                        if (direc.lower() == 'south') and (SOUTHWEST_DEGREES <= deg < SOUTHEAST_DEGREES):
                                            builfracs.append(builfrac)
                                            fais.append(fai)
                                            rdhs.append(rdh)
                                            rrls.append(rrl)
                                            mdhs.append(mdh)
                                            mrls.append(mrl)
                                            bs2pars.append(bs2par)

                    fad_out['n'].append(fadn)
                    fad_out['w'].append(fadw)
                    fad_out['s'].append(fads)
                    fad_out['e'].append(fade)

                    fai_out['n'].append(fain)
                    fai_out['w'].append(faiw)
                    fai_out['s'].append(fais)
                    fai_out['e'].append(faie)

                    rdh_out['n'].append(rdhn)
                    rdh_out['w'].append(rdhw)
                    rdh_out['s'].append(rdhs)
                    rdh_out['e'].append(rdhe)

                    rrl_out['n'].append(rrln)
                    rrl_out['w'].append(rrlw)
                    rrl_out['s'].append(rrls)
                    rrl_out['e'].append(rrle)

                    mrl_out['n'].append(mrln)
                    mrl_out['w'].append(mrlw)
                    mrl_out['s'].append(mrls)
                    mrl_out['e'].append(mrle)

                    builfrac_out.append(builfracs)
                    mdh_out.append(mdhs)
                    bs2par_out.append(bs2pars)

                # incremental arrays
                fad_out_inc.append(fad_out)
                builfrac_out_inc.append(builfrac_out)
                fai_out_inc.append(fai_out)
                rdh_out_inc.append(rdh_out)
                rrl_out_inc.append(rrl_out)
                mdh_out_inc.append(mdh_out)
                mrl_out_inc.append(mrl_out)
                bs2par_out_inc.append(bs2par_out)
                roughness_length_out_inc.append(roughness_length_out)
                displacement_height_out_inc.append(displacement_height_out)

                ##############
                # The complete aspect ratio is calculated here using the length of the south wall of the current building and either
                # the east or west wall.
                ##############

                if edist != 0:
                    car_out_inc.append(float(sdist) / float(edist)) # The ratio of the length of the south wall to the east wall
                elif edist == 0 and wdist != 0:
                    car_out_inc.append(float(sdist) / float(wdist)) # The ratio of the length of the south wall to the west wall
                else:
                    car_out_inc.append(1)

            counter += 1

            feature_buil.Destroy()
            feature_buil = layer2.GetNextFeature()

    return fad_out_inc, builfrac_out_inc, fai_out_inc, rdh_out_inc, rrl_out_inc, mdh_out_inc, mrl_out_inc, \
        bs2par_out_inc, roughness_length_out_inc, displacement_height_out_inc, car_out_inc


def h2w(IMAGE_SIZE_X, IMAGE_SIZE_Y, layer2, xOrigin, yOrigin, pixelWidth, pixelHeight, start_x_p, start_y_p, PIXEL_SIZE, height_field, id_field):
    '''
    Calculates urban parameter 101, height-to-width ratio.

    Parameters
    ----------
    IMAGE_SIZE_X : int
        Length of the shapefile in the x-direction.
    IMAGE_SIZE_Y : int
        Length of the shapefile in the y-direction.
    layer2 : osgeo.ogr.Layer
        The target layer of the shapefile, automatically generated in Parameter_Calulcations.py.
    xOrigin : float
        Minimum x coordinate of the shapefile.
    yOrigin : float
        Maximum y coordinate of the shapefile.
    pixelWidth : float
        Width of the building raster pixels (equal to PIXEL_SIZE).
    pixelHeight : float
        Height of the building raster pixels (equal to -PIXEL_SIZE).
    start_x_p : int
        Starting pixel x coordinate?
    start_y_p : int
        Starting pixel y coordinate?
    PIXEL_SIZE : float
        Pixel size of the building raster.
    height_field : str
        Name of height field in the shapefile.
    id_field : str
        Name of ID field in study shapefile.
 
    Returns
    ----------
    ratios : list
        Height-to-width ratio for each building.
    names : list
        Unique building ID for each building as listed in the shapefile.
    '''

    THRESHOLD_POINTS_IN_WALL = 20.
    # TODO: rename constant
    CONSTANT_127 = 127

    names = []
    heights = []
    widths = []
    idsa = []
    ratios = []
    count = 1

    buils = empty((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint16)
    buils.fill(255)

    layer2.ResetReading()
    feature_buil = layer2.GetNextFeature()

    while feature_buil:
        geomb = feature_buil.GetGeometryRef()
        ring = geomb.GetGeometryRef(0)
        numpoints = ring.GetPointCount()

        if numpoints != 0:
            nx, ny, _ = ring.GetPoint(0) # The minimum x and y coordinates for the current building

            xOffset = int((nx - xOrigin) / pixelWidth) # The distance from the minimum x coordinate to the left extent of the tile
            yOffset = int((ny - yOrigin) / pixelHeight) # The distance from the minimum y coordinate to the top extent of the tile

            parr = [[xOffset, yOffset]] 
            parrx = [[xOffset]]
            parry = [[yOffset]]

            for point_index in range(1, ring.GetPointCount()):
                point = ring.GetPoint(point_index) # Finds the coordinates for each point in the building polygon

                xoff = int((point[0] - xOrigin) / pixelWidth) # Calculates the xoffset for each point in the building polygon
                yoff = int((point[1] - yOrigin) / pixelHeight) # Calculates the yoffset for each point in the building polygon

                parr.append([xoff, yoff])
                parrx.append([xoff])
                parry.append([yoff])

            parrx[:] = [x[0] - start_x_p for x in parrx] 
            parry[:] = [y[0] - start_y_p for y in parry]

            parrx = array(parrx)
            parry = array(parry)
            rr, cc = polygon(parrx, parry, [IMAGE_SIZE_Y, IMAGE_SIZE_X]) # Uses the offsets to creates arrays of polygon coordinates

            buils[cc, rr] = CONSTANT_127 # Creates an array with 127 where the polygon coordinates dictate

        feature_buil.Destroy()
        feature_buil = layer2.GetNextFeature()

    layer2.ResetReading()
    feature_buil = layer2.GetNextFeature()

    while feature_buil:
        height = feature_buil.GetFieldAsString(height_field)
        building_id = feature_buil.GetFieldAsString(id_field)

        if height != '':
            idsa.append(count)

            cntr2 = 0
            summ2 = 0
            aveg2 = 0
            aveg1 = 0

            geomb = feature_buil.GetGeometryRef()
            ring = geomb.GetGeometryRef(0)
            numpoints = ring.GetPointCount()

            if numpoints != 0:
                cntr1 = 0
                summ1 = 0

                nx, ny, _ = ring.GetPoint(0)  # The minimum x and y coordinates for the current building

                xOffset = int((nx - xOrigin) / pixelWidth) # The distance from the minimum x coordinate to the left extent of the tile
                yOffset = int((ny - yOrigin) / pixelHeight) # The distance from the minimum y coordinate to the top extent of the tile

                parr = [[xOffset, yOffset]]
                parrx = [[xOffset]]
                parry = [[yOffset]]

                parrxc = [[nx]]
                parryc = [[ny]]

                for i in range(1, ring.GetPointCount()):
                    point = ring.GetPoint(i) # Finds the coordinates for each point in the building polygon

                    xoff = int((point[0] - xOrigin) / pixelWidth) # Calculates the xoffset for each point in the building polygon
                    yoff = int((point[1] - yOrigin) / pixelHeight) # Calculates the yoffset for each point in the building polygon

                    parr.append([xoff, yoff])
                    parrx.append([xoff])
                    parry.append([yoff])

                    parrxc.append([point[0]])
                    parryc.append([point[1]])

                parrx[:] = [x[0] - start_x_p for x in parrx]
                parry[:] = [y[0] - start_y_p for y in parry]

                parrx = array(parrx)
                parry = array(parry)

                for na in range(0, len(parrx)-1):
                    p1x = parrx[na]
                    p1y = parry[na]

                    p2x = parrx[na+1]
                    p2y = parry[na+1]

                    xarr, yarr = get_pixels2_c(IMAGE_SIZE_X, IMAGE_SIZE_Y, int(p1x), int(p1y), int(p2x), int(p2y))

                    if ((len(xarr)/THRESHOLD_POINTS_IN_WALL)-1) > 0: # If there are more than THRESHOLD_POINTS_IN_WALL points in the wall:

                        for nb in range(0, int(rint((len(xarr)/THRESHOLD_POINTS_IN_WALL)-1))): 
                            x1 = xarr[(nb*THRESHOLD_POINTS_IN_WALL)+1] # Find a starting x coordinate
                            y1 = yarr[(nb*THRESHOLD_POINTS_IN_WALL)+1] # Find a starting y coordinate
                            x2 = xarr[((nb+1)*THRESHOLD_POINTS_IN_WALL)+1] # Find the x coordinate THRESHOLD_POINTS_IN_WALL away from the starting coordinate
                            y2 = yarr[((nb+1)*THRESHOLD_POINTS_IN_WALL)+1] # Find the y coordinate THRESHOLD_POINTS_IN_WALL away from the starting coordinate

                            aveg1, cntr1, summ1 = calculate_aveg1(buils, cntr1, summ1, IMAGE_SIZE_X, IMAGE_SIZE_Y, x1, y1, x2, y2, p1x, p1y, p2x, p2y)

                    elif len(xarr) != 0:
                        x1 = xarr[1]
                        y1 = yarr[1]
                        x2 = xarr[1]
                        y2 = yarr[1]

                        aveg1, cntr1, summ1 = calculate_aveg1(buils, cntr1, summ1, IMAGE_SIZE_X, IMAGE_SIZE_Y, x1, y1, x2, y2, p1x, p1y, p2x, p2y)

            cntr2 += 1
            summ2 += aveg1

            if cntr2 != 0 and summ2 != 0:
                aveg2 = summ2 / cntr2

            heights.append(float(height))
            widths.append(aveg2*PIXEL_SIZE)
            names.append(building_id)

        count += 1
        feature_buil.Destroy()
        feature_buil = layer2.GetNextFeature()

    for qw in range(0, len(heights)):
        if widths[qw] != 0:
            ratio = heights[qw] / widths[qw]
        else:
            ratio = 0

        ratios.append(ratio)

    return ratios, names


def calculate_aveg1(buils, cntr1, summ1, IMAGE_SIZE_X, IMAGE_SIZE_Y, x1, y1, x2, y2, p1x, p1y, p2x, p2y):
    """Calculates the parameter aveg1, which is the sum of the index over the number of times we call this function and end up wtih tempa between TEMPA_THRESHOLD and CONSTANT_200. """
    # TODO: rename constants
    CONSTANT_2OO = 200
    CONSTANT_127 = 127
    TEMPA_THRESHOLD = 5

    tempa = 0

    for tg in range(1, CONSTANT_2OO):
        perp1x, perp1y = inter4p(x1, y1, x2, y2, tg)

        if perp1x < 0:
            perp1x = 0
        if perp1y < 0:
            perp1y = 0

        if int(round(perp1x)) >= IMAGE_SIZE_Y:
            perp1x = IMAGE_SIZE_Y - 1
        if int(round(perp1y)) >= IMAGE_SIZE_X:
            perp1y = IMAGE_SIZE_X - 1

        tempa = tg
        if buils[int(round(perp1y)), int(round(perp1x))] == CONSTANT_127 and tempa > (TEMPA_THRESHOLD - 1):
            break

    if tempa == TEMPA_THRESHOLD:
        for tg in range(1, CONSTANT_2OO):
            perp1x, perp1y = inter4n(p1x, p1y, p2x, p2y, tg)

            if perp1x < 0:
                perp1x = 0
            if perp1y < 0:
                perp1y = 0

            if int(round(perp1x)) >= IMAGE_SIZE_Y:
                perp1x = IMAGE_SIZE_Y - 1
            if int(round(perp1y)) >= IMAGE_SIZE_X:
                perp1y = IMAGE_SIZE_X - 1

            tempa = tg
            if buils[int(round(perp1y)), int(round(perp1x))] == CONSTANT_127 and tempa > (TEMPA_THRESHOLD - 1):
                break


    if tempa != TEMPA_THRESHOLD and tempa != (CONSTANT_2OO - 1):
        cntr1 += 1
        summ1 += tempa

    if cntr1 != 0:
        aveg1 = summ1 / cntr1
    else:
        aveg1 = 0

    return aveg1, cntr1, summ1
