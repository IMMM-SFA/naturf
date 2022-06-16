import math
from numpy import array, zeros, uint8, uint16, where, empty, sum, unique, rint
from skimage.draw import polygon
from scipy import ndimage
                        
def get_pixels2_c(IMAGE_SIZE_X, IMAGE_SIZE_Y, x1, y1, x2, y2):
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

def inter4p(x1, y1, x2, y2, rad1):

    dx = x1-x2
    dy = y1-y2
    dist = math.sqrt(dx*dx + dy*dy)
    dx /= (dist + 0.00000000000000000000001)
    dy /= (dist + 0.00000000000000000000001)

    if y1 > y2:
        x1r = x1 - rad1*dy
        y1r = y1 + rad1*dx
    else:
        x1r = x1 + rad1*dy
        y1r = y1 - rad1*dx

    return x1r, y1r


def inter4n(x1, y1, x2, y2, rad1):

    dx = x1-x2
    dy = y1-y2
    dist = math.sqrt(dx*dx + dy*dy)
    dx /= (dist + 0.00000000000000000000001)
    dy /= (dist + 0.00000000000000000000001)

    if y1 > y2:
        x1l = x1 + rad1*dy
        y1l = y1 - rad1*dx
    else:
        x1l = x1 - rad1*dy
        y1l = y1 + rad1*dx

    return x1l, y1l


def ang2lines(linea, lineb):
    # returns [0, 360]

    va = [(linea[0][0]-linea[1][0]), (linea[0][1]-linea[1][1])]
    vb = [(lineb[0][0]-lineb[1][0]), (lineb[0][1]-lineb[1][1])]

    angle = math.atan2(va[1], va[0]) - math.atan2(vb[1], vb[0])
    angle = angle * 360 / (2 * math.pi)

    if angle < 0:
        angle += 360

    return angle


def ang2points(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1

    r = math.atan2(dy, dx)
    degr = math.degrees(r)

    if degr < 0:
        degr += 360

    return degr


def get_cents_hts(IMAGE_SIZE_X, IMAGE_SIZE_Y, layer2, ids, PIXEL_SIZE, height_field):
    cents1 = {}
    heights = {}
    areas = {}
    i2arr = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint8)
    cnt = 1

    layer2.ResetReading()
    feature_buil = layer2.GetNextFeature()

    while feature_buil:
        ht = feature_buil.GetFieldAsString(height_field)

        if ht != '':
            ht = float(ht)
            # print cnt
            heights[cnt] = ht

            geom = feature_buil.GetGeometryRef()
            ring = geom.GetGeometryRef(0)
            numpoints = ring.GetPointCount()

            if numpoints != 0:

                cent = geom.Centroid()
                centx = cent.GetX()
                centy = cent.GetY()

                centx = float(centx)
                centy = float(centy)

                cents1[cnt] = [centx, centy]

                builarea = 0

                i2arr.fill(0)
                if len(ids[ids == cnt]) != 0:
                    i2arr[ids == cnt] = 1
                    builarea = sum(i2arr) * PIXEL_SIZE**2

                areas[cnt] = builarea

        cnt += 1

        feature_buil.Destroy()
        feature_buil = layer2.GetNextFeature()

    return cents1, heights, areas


def avg_building_dist(IMAGE_SIZE_X, IMAGE_SIZE_Y, layer2, ids,  PIXEL_SIZE, height_field, heights, ars, cents):

    i2arr = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint8)
    dils = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint8)
    narr = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint8)
    struct = ndimage.generate_binary_structure(2, 2)
    rad = 100
    sumareas = 0
    cntr = 1
    parea = 0
    avgns = 0
    avgew = 0

    cns_out = {}
    cew_out = {}
    meanht_out = []
    stdht_out = []
    awmh1_out = []
    pareas = {}

    layer2.ResetReading()
    feature_buil = layer2.GetNextFeature()

    while feature_buil:
        ht = feature_buil.GetFieldAsString(height_field)

        avgns = 0
        avgew = 0

        sumarhts = 0
        sumareas2 = 0

        hts1 = []

        if ht != '':

            geomb = feature_buil.GetGeometryRef()
            ring = geomb.GetGeometryRef(0)
            numpoints = ring.GetPointCount()

            if numpoints != 0:

                i2arr.fill(0)
                dils.fill(0)
                narr.fill(0)
                if len(ids[ids == cntr]) != 0:
                    i2arr[ids == cntr] = 1
                    builarea = sum(i2arr) * PIXEL_SIZE**2
                    i2arr = ndimage.binary_dilation(i2arr, structure=struct, iterations=rad).astype(i2arr.dtype)
                    # dilarea = sum(i2arr) * PIXEL_SIZE**2
                    dibuils = unique(ids[where(i2arr == 1)])

                    sumareas += builarea

                    # print dibuils

                    if len(dibuils) != 0:
                        currcx = cents[cntr][0]  # current building centroid
                        currcy = cents[cntr][1]
                        # print currcx, currcy

                        te, tn, ts, tw = 0., 0., 0., 0.
                        ce, cn, cs, cw = 0., 0., 0., 0.

                        for asdf in dibuils:
                            if asdf != 0 and asdf in heights:
                                hts1.append(heights[asdf])
                                dils[(ids == asdf) & (i2arr == 1)] = 1

                                sumarhts += ars[asdf] * heights[asdf]
                                sumareas2 += ars[asdf]

                                if asdf != cntr:
                                    cx = cents[asdf][0]
                                    cy = cents[asdf][1]

                                    d = math.hypot((currcx - cx), (currcy - cy))
                                    angle = ang2points(currcx, currcy, cx, cy)

                                    if (315 <= angle <= 360 or 0 <= angle < 45) and d != 0:  # east
                                        te += d
                                        ce += 1

                                    if 135 <= angle < 225 and d != 0:  # west
                                        tw += d
                                        cw += 1

                                    if 45 <= angle < 135 and d != 0:  # north
                                        tn += d
                                        cn += 1

                                    if 225 <= angle < 315 and d != 0:  # south
                                        ts += d
                                        cs += 1

                        if cn != 0 or cs != 0:
                            avgns = (tn + ts) / (cn + cs)
                        else:
                            avgns = 0

                        if ce != 0 or cw != 0:
                            avgew = (te + tw) / (ce + cw)
                        else:
                            avgew = 0

                        # print avgns, avgew

                        narr[(dils == 1) & (i2arr == 1)] = 1
                        parea = sum(narr) * PIXEL_SIZE**2

                        pareas[cntr] = [ht, parea]  # #######################################################

                        # if parea > dilarea:
                        # print parea, dilarea

            if len(hts1) != 0:
                hts1 = array(hts1)
                meanht_out.append(hts1.mean())
                stdht_out.append(hts1.std())
            else:
                meanht_out.append(ht)
                stdht_out.append(ht)

            cns_out[cntr] = avgns
            cew_out[cntr] = avgew

            if sumareas2 != 0:
                awmh1_out.append(sumarhts / sumareas2)
            else:
                awmh1_out.append(0)

        cntr += 1

        feature_buil.Destroy()
        feature_buil = layer2.GetNextFeature()

    avgsa = sumareas / cntr  # sum of all of the surface areas in shapefile (used in a parameter)

    return cns_out, cew_out, avgsa, pareas, meanht_out, stdht_out, awmh1_out


def parameters1(IMAGE_SIZE_X, IMAGE_SIZE_Y, layer2, ids, PIXEL_SIZE, height_field, direc, bid, newbarea, cents_ns, cents_ew, avgsa):  # if bid == 0, loops through all of the buildings

    i2arr = zeros((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint8)
    struct = ndimage.generate_binary_structure(2, 2)
    rad = 100

    dist = -1
    builarea = 0
    dilarea = 0

    sumarhts = 0
    sumareas = 0
    counter = 1

    fad_out_inc = []
    builfrac_out_inc = []
    fai_out_inc = []
    rdh_out_inc = []
    rrl_out_inc = []
    mdh_out_inc = []
    mrl_out_inc = []
    bs2par_out_inc = []
    zo_out_inc = []
    zd_out_inc = []
    car_out_inc = []

    if bid != 0:
        layer2.ResetReading()
        feature_buil = layer2.GetNextFeature()
        while feature_buil:
            ht = feature_buil.GetFieldAsString(height_field)

            fad_out = []
            builfrac_out = []
            fai_out = []
            rdh_out = []
            rrl_out = []
            mdh_out = []
            mrl_out = []
            bs2par_out = []
            zo_out = []
            zd_out = []

            if ht != '':
                ht = float(ht)
                for asdf in range(5, 75, 5):
                    if (ht - asdf) > 0:
                        nht = 5
                    elif (ht - asdf + 5) > 0:
                        nht = ht - asdf + 5
                    else:
                        nht = 0.000000000000000001

                    zh = ht
                    if zh == 0:
                        zh = 0.000000000000000001

                    zo = 0.1 * zh
                    zd = 0.67 * zh

                    zo_out.append(zo)
                    zd_out.append(zd)

                    fads = []
                    builfracs = []
                    fais = []
                    rdhs = []
                    rrls = []
                    mdhs = []
                    mrls = []
                    bs2pars = []

                    if bid == counter:

                        geomb = feature_buil.GetGeometryRef()
                        ring = geomb.GetGeometryRef(0)
                        numpoints = ring.GetPointCount()

                        if numpoints != 0:

                            i2arr.fill(0)
                            builarea = 0
                            dilarea = 0

                            if len(ids[ids == bid]) != 0:
                                i2arr[ids == bid] = 1
                                builarea = sum(i2arr) * PIXEL_SIZE**2
                                i2arr = ndimage.binary_dilation(i2arr, structure=struct, iterations=rad).astype(i2arr.dtype)
                                # i2arr[(ids != bid) & (iarr == 127)] = 0
                                dilarea = sum(i2arr) * PIXEL_SIZE**2

                                sumarhts += builarea * nht
                                sumareas += builarea

                            nx, ny, nz = ring.GetPoint(0)

                            parrxc = [[nx]]
                            parryc = [[ny]]

                            for bi in range(1, ring.GetPointCount()):
                                bpt = ring.GetPoint(bi)

                                parrxc.append([bpt[0]])
                                parryc.append([bpt[1]])

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
                                    breadth = dist

                                    if breadth >= 1:

                                        # if 315 <= deg <= 360 or 0 <= deg < 45:
                                        #     direc2 = 'East'
                                        # if 45 <= deg < 135:
                                        #     direc2 = 'South'
                                        # if 135 <= deg < 225:
                                        #     direc2 = 'West'
                                        # if 225 <= deg < 315:
                                        #     direc2 = 'North'
                                        #
                                        # if prevdir == direc2:
                                        #     dist += prevdist

                                        if (direc.lower() == 'east') and (315 <= deg <= 360 or 0 <= deg < 45):
                                            if ((dist / 10) - 1) > 0:
                                                wallarea = dist * nht

                                                if dilarea == 0:
                                                    break

                                                fad = wallarea / dilarea


                                                if newbarea[counter][0] > ht:
                                                    builfrac = newbarea[counter][1] / dilarea
                                                else:
                                                    builfrac = 0

                                                if (cents_ns[counter] * cents_ew[counter]) != 0:
                                                    fai = (breadth * zh) / (cents_ns[counter] * cents_ew[counter])
                                                    rdh = zh * (1 - (1 - math.exp(-math.sqrt(7.5 * 2 * fai))/math.sqrt(7.5 * 2 * fai)))
                                                    rrl = zh * ((1 - rdh) * math.exp(-0.4 * (1 / math.sqrt(0.003 + 0.3 * fai)) - 0.193))
                                                else:
                                                    fai = 0
                                                    rdh = 0
                                                    rrl = 0

                                                mdh = zh * (1 + (1 / 3.59 ** builfrac) * (builfrac - 1))
                                                zxcv = 0.5 * (1.12 / 0.4 ** 2) * (1 - rdh) * (wallarea / avgsa)

                                                if zxcv >= 0:
                                                    mrl = zh * (1 - rdh) * math.exp(-1 / (math.sqrt(0.5 * (1.12 / 0.4 ** 2) *
                                                                                                (1 - rdh) * (wallarea / avgsa))))
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

                                                # print bid, 'East', wallarea, dilarea, fad, builfrac, fai

                                        if (direc.lower() == 'north') and (45 <= deg < 135):
                                            if ((dist / 10) - 1) > 0:
                                                wallarea = dist * nht

                                                if dilarea == 0:
                                                    break

                                                fad = wallarea / dilarea

                                                if newbarea[counter][0] > ht:
                                                    builfrac = newbarea[counter][1] / dilarea
                                                else:
                                                    builfrac = 0

                                                if (cents_ns[counter] * cents_ew[counter]) != 0:
                                                    fai = (breadth * zh) / (cents_ns[counter] * cents_ew[counter])
                                                    rdh = zh * (1 - (1 - math.exp(-math.sqrt(7.5 * 2 * fai))/math.sqrt(7.5 * 2 * fai)))
                                                    rrl = zh * ((1 - rdh) * math.exp(-0.4 * (1 / math.sqrt(0.003 + 0.3 * fai)) - 0.193))
                                                else:
                                                    fai = 0
                                                    rdh = 0
                                                    rrl = 0

                                                mdh = zh * (1 + (1 / 3.59 ** builfrac) * (builfrac - 1))
                                                zxcv = 0.5 * (1.12 / 0.4 ** 2) * (1 - rdh) * (wallarea / avgsa)

                                                if zxcv >= 0:
                                                    mrl = zh * (1 - rdh) * math.exp(-1 / (math.sqrt(0.5 * (1.12 / 0.4 ** 2) *
                                                                                                (1 - rdh) * (wallarea / avgsa))))
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

                                                # print bid, 'North', wallarea, dilarea, fad, builfrac, fai

                                        if (direc.lower() == 'west') and (135 <= deg < 225):
                                            if ((dist / 10) - 1) > 0:
                                                wallarea = dist * nht
                                                
                                                if dilarea == 0:
                                                    break

                                                fad = wallarea / dilarea

                                                if newbarea[counter][0] > ht:
                                                    builfrac = newbarea[counter][1] / dilarea
                                                else:
                                                    builfrac = 0

                                                if (cents_ns[counter] * cents_ew[counter]) != 0:
                                                    fai = (breadth * zh) / (cents_ns[counter] * cents_ew[counter])
                                                    rdh = zh * (1 - (1 - math.exp(-math.sqrt(7.5 * 2 * fai))/math.sqrt(7.5 * 2 * fai)))
                                                    rrl = zh * ((1 - rdh) * math.exp(-0.4 * (1 / math.sqrt(0.003 + 0.3 * fai)) - 0.193))
                                                else:
                                                    fai = 0
                                                    rdh = 0
                                                    rrl = 0

                                                mdh = zh * (1 + (1 / 3.59 ** builfrac) * (builfrac - 1))
                                                zxcv = 0.5 * (1.12 / 0.4 ** 2) * (1 - rdh) * (wallarea / avgsa)

                                                if zxcv >= 0:
                                                    mrl = zh * (1 - rdh) * math.exp(-1 / (math.sqrt(0.5 * (1.12 / 0.4 ** 2) *
                                                                                                (1 - rdh) * (wallarea / avgsa))))
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

                                                # print bid, 'West', wallarea, dilarea, fad, builfrac, fai

                                        if (direc.lower() == 'south') and (225 <= deg < 315):
                                            if ((dist / 10) - 1) > 0:
                                                wallarea = dist * nht

                                                if dilarea == 0:
                                                    break

                                                fad = wallarea / dilarea

                                                if newbarea[counter][0] > ht:
                                                    builfrac = newbarea[counter][1] / dilarea
                                                else:
                                                    builfrac = 0

                                                if (cents_ns[counter] * cents_ew[counter]) != 0:
                                                    fai = (breadth * zh) / (cents_ns[counter] * cents_ew[counter])
                                                    rdh = zh * (1 - (1 - math.exp(-math.sqrt(7.5 * 2 * fai))/math.sqrt(7.5 * 2 * fai)))
                                                    rrl = zh * ((1 - rdh) * math.exp(-0.4 * (1 / math.sqrt(0.003 + 0.3 * fai)) - 0.193))
                                                else:
                                                    fai = 0
                                                    rdh = 0
                                                    rrl = 0

                                                mdh = zh * (1 + (1 / 3.59 ** builfrac) * (builfrac - 1))
                                                zxcv = 0.5 * (1.12 / 0.4 ** 2) * (1 - rdh) * (wallarea / avgsa)

                                                if zxcv >= 0:
                                                    mrl = zh * (1 - rdh) * math.exp(-1 / (math.sqrt(0.5 * (1.12 / 0.4 ** 2) *
                                                                                                (1 - rdh) * (wallarea / avgsa))))
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

                                                # print bid, 'South', wallarea, dilarea, fad, builfrac, fai

                                        # prevdir = direc2
                                        # prevdist = dist

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
                zo_out_inc.append(zo_out)
                zd_out_inc.append(zd_out)

            counter += 1

            feature_buil.Destroy()
            feature_buil = layer2.GetNextFeature()

    else:
        layer2.ResetReading()
        feature_buil = layer2.GetNextFeature()
        while feature_buil:
            ht = feature_buil.GetFieldAsString(height_field)

            if ht != '':
                ht = float(ht)

                fad_out = {'n': [], 'w': [], 's': [], 'e': []}
                fai_out = {'n': [], 'w': [], 's': [], 'e': []}
                rdh_out = {'n': [], 'w': [], 's': [], 'e': []}
                rrl_out = {'n': [], 'w': [], 's': [], 'e': []}
                mrl_out = {'n': [], 'w': [], 's': [], 'e': []}

                builfrac_out = []
                mdh_out = []
                bs2par_out = []
                zo_out = []
                zd_out = []

                edist = 0
                wdist = 0
                sdist = 0

                for asdf in range(0, 75, 5):
                    if (ht - asdf) >= 5:
                        nht = 5
                    elif 0 < (ht - asdf) < 5:
                        nht = ht - asdf
                    else:
                        nht = 0.00000000000000000000000000000001

                    # print ht, asdf, nht

                    zh = ht
                    if zh == 0:
                        zh = 0.000000000000000001

                    zo = 0.1 * zh
                    zd = 0.67 * zh

                    zo_out.append(zo)
                    zd_out.append(zd)

                    fads = []
                    fade = []
                    fadn = []
                    fadw = []

                    fais = []
                    fain = []
                    faie = []
                    faiw = []

                    rdhs = []
                    rdhn = []
                    rdhe = []
                    rdhw = []

                    rrls = []
                    rrln = []
                    rrle = []
                    rrlw = []

                    mrls = []
                    mrln = []
                    mrle = []
                    mrlw = []

                    builfracs = []
                    mdhs = []
                    bs2pars = []

                    geomb = feature_buil.GetGeometryRef()
                    ring = geomb.GetGeometryRef(0)
                    numpoints = ring.GetPointCount()

                    if numpoints != 0:

                        # print unique(ids)  # len(ids[ids == counter])

                        i2arr.fill(0)
                        builarea = 0
                        dilarea = 0
                        # print counter
                        if len(ids[ids == counter]) != 0:
                            i2arr[ids == counter] = 1
                            builarea = sum(i2arr) * PIXEL_SIZE**2

                            # i2arr[(ids != counter) & (iarr == 127)] = 0
                            dilarea = sum(i2arr) * PIXEL_SIZE**2

                            sumarhts += builarea * nht
                            sumareas += builarea

                            if dilarea == 0:
                                dilarea = builarea


                        nx, ny, nz = ring.GetPoint(0)

                        parrxc = [[nx]]
                        parryc = [[ny]]

                        for bi in range(1, ring.GetPointCount()):
                            bpt = ring.GetPoint(bi)

                            parrxc.append([bpt[0]])
                            parryc.append([bpt[1]])

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

                                dist = math.sqrt((p2x - p1x)**2 + (p2y - p1y)**2)

                                breadth = dist

                                if breadth >= 1:

                                    # if 315 <= deg <= 360 or 0 <= deg < 45:
                                    #     direc2 = 'East'
                                    # if 45 <= deg < 135:
                                    #     direc2 = 'South'
                                    # if 135 <= deg < 225:
                                    #     direc2 = 'West'
                                    # if 225 <= deg < 315:
                                    #     direc2 = 'North'
                                    #
                                    # if prevdir == direc2:
                                    #     dist += prevdist

                                    if 315 <= deg <= 360 or 0 <= deg < 45:
                                        if ((dist / 10) - 1) > 0:
                                            edist = dist
                                            wallarea = dist * nht

                                            if dilarea == 0:
                                                    break
                                            
                                            fad = wallarea / dilarea

                                            if (cents_ns[counter] * cents_ew[counter]) != 0:
                                                fai = (breadth * zh) / (cents_ns[counter] * cents_ew[counter])
                                                rdh = zh * (1 - (1 - math.exp(-math.sqrt(7.5 * 2 * fai))/math.sqrt(7.5 * 2 * fai)))
                                                rrl = zh * (1 - rdh) * math.exp(-0.4 * (1 / math.sqrt(0.003 + 0.3 * fai)) - 0.193)
                                            else:
                                                fai = 0
                                                rdh = 0
                                                rrl = 0

                                            zxcv = 0.5 * (1.12 / 0.4 ** 2) * (1 - rdh) * (wallarea / avgsa)

                                            if zxcv >= 0:
                                                mrl = zh * (1 - rdh) * math.exp(-1 / (math.sqrt(0.5 * (1.12 / 0.4 ** 2) *
                                                                                            (1 - rdh) * (wallarea / avgsa))))
                                            else:
                                                mrl = 0

                                            if rrl > 3 or rrl < 0:
                                                rrl = 0
                                            if rdh > 3 or rdh < 0:
                                                rdh = 0

                                            faie.append(fai)
                                            rdhe.append(rdh)
                                            rrle.append(rrl)
                                            mrle.append(mrl)

                                            if float(fad) < 0.00000000000000000001:
                                                fade.append(0)
                                            else:
                                                fade.append(fad)

                                    if 45 <= deg < 135:
                                        if ((dist / 10) - 1) > 0:
                                            wallarea = dist * nht
                                            if asdf == 0:
                                                dilarea = 10000

                                            if dilarea == 0:
                                                    break

                                            fad = wallarea / dilarea

                                            if (cents_ns[counter] * cents_ew[counter]) != 0:
                                                fai = (breadth * zh) / (cents_ns[counter] * cents_ew[counter])
                                                rdh = zh * (1 - (1 - math.exp(-math.sqrt(7.5 * 2 * fai))/math.sqrt(7.5 * 2 * fai)))
                                                rrl = zh * (1 - rdh) * math.exp(-0.4 * (1 / math.sqrt(0.003 + 0.3 * fai)) - 0.193)
                                            else:
                                                fai = 0
                                                rdh = 0
                                                rrl = 0

                                            zxcv = 0.5 * (1.12 / 0.4 ** 2) * (1 - rdh) * (wallarea / avgsa)

                                            if zxcv >= 0:
                                                mrl = zh * (1 - rdh) * math.exp(-1 / (math.sqrt(0.5 * (1.12 / 0.4 ** 2) *
                                                                                            (1 - rdh) * (wallarea / avgsa))))
                                            else:
                                                mrl = 0

                                            if rrl > 3 or rrl < 0:
                                                rrl = 0
                                            if rdh > 3 or rdh < 0:
                                                rdh = 0

                                            fain.append(fai)
                                            rdhn.append(rdh)
                                            rrln.append(rrl)
                                            mrln.append(mrl)

                                            if float(fad) < 0.00000000000000000001:
                                                fadn.append(0)
                                            else:
                                                fadn.append(fad)

                                    if 135 <= deg < 225:
                                        if ((dist / 10) - 1) > 0:
                                            wdist = dist
                                            wallarea = dist * nht

                                            if dilarea == 0:
                                                    break
                                            
                                            fad = wallarea / dilarea

                                            if (cents_ns[counter] * cents_ew[counter]) != 0:
                                                fai = (breadth * zh) / (cents_ns[counter] * cents_ew[counter])
                                                rdh = zh * (1 - (1 - math.exp(-math.sqrt(7.5 * 2 * fai))/math.sqrt(7.5 * 2 * fai)))
                                                rrl = zh * (1 - rdh) * math.exp(-0.4 * (1 / math.sqrt(0.003 + 0.3 * fai)) - 0.193)
                                            else:
                                                fai = 0
                                                rdh = 0
                                                rrl = 0

                                            zxcv = 0.5 * (1.12 / 0.4 ** 2) * (1 - rdh) * (wallarea / avgsa)

                                            if zxcv >= 0:
                                                mrl = zh * (1 - rdh) * math.exp(-1 / (math.sqrt(0.5 * (1.12 / 0.4 ** 2) *
                                                                                            (1 - rdh) * (wallarea / avgsa))))
                                            else:
                                                mrl = 0

                                            if rrl > 3 or rrl < 0:
                                                rrl = 0
                                            if rdh > 3 or rdh < 0:
                                                rdh = 0

                                            faiw.append(fai)
                                            rdhw.append(rdh)
                                            rrlw.append(rrl)
                                            mrlw.append(mrl)

                                            if float(fad) < 0.00000000000000000001:
                                                fadw.append(0)
                                            else:
                                                fadw.append(fad)

                                    if (direc.lower() == 'south') and (225 <= deg < 315):
                                        if ((dist / 10) - 1) > 0:
                                            sdist = dist
                                            wallarea = dist * nht

                                            if dilarea == 0:
                                                break
                                            
                                            fad = wallarea / dilarea


                                            # print newbarea[counter][0], float(asdf), float(newbarea[counter][0]) > float(asdf)

                                            if float(newbarea[counter][0]) > float(asdf):
                                                builfrac = newbarea[counter][1] / dilarea
                                            else:
                                                builfrac = 0

                                            if (cents_ns[counter] * cents_ew[counter]) != 0:
                                                fai = (breadth * zh) / (cents_ns[counter] * cents_ew[counter])
                                                rdh = zh * (1 - (1 - math.exp(-math.sqrt(7.5 * 2 * fai))/math.sqrt(7.5 * 2 * fai)))
                                                rrl = zh * (1 - rdh) * math.exp(-0.4 * (1 / math.sqrt(0.003 + 0.3 * fai)) - 0.193)
                                            else:
                                                fai = 0
                                                rdh = 0
                                                rrl = 0

                                            mdh = zh * (1 + (1 / 3.59 ** builfrac) * (builfrac - 1))
                                            zxcv = 0.5 * (1.12 / 0.4 ** 2) * (1 - rdh) * (wallarea / avgsa)

                                            if zxcv >= 0:
                                                mrl = zh * (1 - rdh) * math.exp(-1 / (math.sqrt(0.5 * (1.12 / 0.4 ** 2) *
                                                                                            (1 - rdh) * (wallarea / avgsa))))
                                            else:
                                                mrl = 0

                                            bs2par = newbarea[counter][1] / newbarea[counter][1]  # currently always 1

                                            if rrl > 3 or rrl < 0:
                                                rrl = 0
                                            if rdh > 3 or rdh < 0:
                                                rdh = 0

                                            if float(fad) < 0.00000000000000000001:
                                                fads.append(0)
                                            else:
                                                fads.append(fad)
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

                #  incremental arrays #
                fad_out_inc.append(fad_out)
                builfrac_out_inc.append(builfrac_out)
                fai_out_inc.append(fai_out)
                rdh_out_inc.append(rdh_out)
                rrl_out_inc.append(rrl_out)
                mdh_out_inc.append(mdh_out)
                mrl_out_inc.append(mrl_out)
                bs2par_out_inc.append(bs2par_out)
                zo_out_inc.append(zo_out)
                zd_out_inc.append(zd_out)

                # print sdist, edist, wdist

                if edist != 0:
                    car_out_inc.append(float(sdist) / float(edist))
                elif edist == 0 and wdist != 0:
                    car_out_inc.append(float(sdist) / float(wdist))
                else:
                    car_out_inc.append(1)

            counter += 1

            feature_buil.Destroy()
            feature_buil = layer2.GetNextFeature()

    awmh = sumarhts / sumareas

    return fad_out_inc, builfrac_out_inc, fai_out_inc, rdh_out_inc, rrl_out_inc, mdh_out_inc, mrl_out_inc, \
        bs2par_out_inc, zo_out_inc, zd_out_inc, car_out_inc


def h2w(IMAGE_SIZE_X, IMAGE_SIZE_Y, layer2, xOrigin, yOrigin, pixelWidth, pixelHeight, start_x_p, start_y_p, PIXEL_SIZE, height_field, id_field):
    names = []
    heights = []
    widths = []
    cnt = 1
    idsa = []
    ratios = []

    buils = empty((IMAGE_SIZE_X, IMAGE_SIZE_Y), dtype=uint16)
    buils.fill(255)

    layer2.ResetReading()
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

            for bi in range(1, ring.GetPointCount()):
                bpt = ring.GetPoint(bi)

                xoff = int((bpt[0] - xOrigin) / pixelWidth)
                yoff = int((bpt[1] - yOrigin) / pixelHeight)

                parr.append([xoff, yoff])
                parrx.append([xoff])
                parry.append([yoff])

            parrx[:] = [x[0] - start_x_p for x in parrx]
            parry[:] = [y[0] - start_y_p for y in parry]

            parrx = array(parrx)
            parry = array(parry)
            rr, cc = polygon(parrx, parry, [IMAGE_SIZE_Y, IMAGE_SIZE_X])

            buils[cc, rr] = 127

        feature_buil.Destroy()
        feature_buil = layer2.GetNextFeature()

    layer2.ResetReading()
    feature_buil = layer2.GetNextFeature()

    while feature_buil:
        ht = feature_buil.GetFieldAsString(height_field)
        bid = feature_buil.GetFieldAsString(id_field)

        if ht != '':
            idsa.append(cnt)

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

                nx, ny, nz = ring.GetPoint(0)

                xOffset = int((nx - xOrigin) / pixelWidth)
                yOffset = int((ny - yOrigin) / pixelHeight)

                parr = [[xOffset, yOffset]]
                parrx = [[xOffset]]
                parry = [[yOffset]]

                parrxc = [[nx]]
                parryc = [[ny]]

                for bi in range(1, ring.GetPointCount()):
                    bpt = ring.GetPoint(bi)

                    xoff = int((bpt[0] - xOrigin) / pixelWidth)
                    yoff = int((bpt[1] - yOrigin) / pixelHeight)

                    parr.append([xoff, yoff])
                    parrx.append([xoff])
                    parry.append([yoff])

                    parrxc.append([bpt[0]])
                    parryc.append([bpt[1]])

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

                    if ((len(xarr)/20)-1) > 0:

                        for nb in range(0, int(rint((len(xarr)/20.)-1))):

                            tempa = 0
                            x1 = xarr[(nb*20)+1]
                            y1 = yarr[(nb*20)+1]

                            x2 = xarr[((nb+1)*20)+1]
                            y2 = yarr[((nb+1)*20)+1]

                            for tg in range(1, 200):
                                perp1x, perp1y = inter4p(x1, y1, x2, y2, tg)

                                if perp1x < 0:
                                    perp1x = 0
                                if perp1y < 0:
                                    perp1y = 0

                                if int(round(perp1x)) >= IMAGE_SIZE_Y:
                                    perp1x = IMAGE_SIZE_Y - 1
                                if int(round(perp1y)) >= IMAGE_SIZE_X:
                                    perp1y = IMAGE_SIZE_X - 1

                                if buils[int(round(perp1y)), int(round(perp1x))] == 127:
                                    tempa = tg
                                    if tempa > 4:
                                        # print 'p'
                                        break
                                else:
                                    tempa = tg

                            if tempa == 5:
                                for tg in range(1, 200):
                                    perp1x, perp1y = inter4n(p1x, p1y, p2x, p2y, tg)

                                    if perp1x < 0:
                                        perp1x = 0
                                    if perp1y < 0:
                                        perp1y = 0

                                    if int(round(perp1x)) >= IMAGE_SIZE_Y:
                                        perp1x = IMAGE_SIZE_Y - 1
                                    if int(round(perp1y)) >= IMAGE_SIZE_X:
                                        perp1y = IMAGE_SIZE_X - 1

                                    if buils[int(round(perp1y)), int(round(perp1x))] == 127:
                                        tempa = tg
                                        if tempa > 4:
                                            # print 'n'
                                            break
                                    else:
                                        tempa = tg

                            # print tempa

                            if tempa != 5 and tempa != 199:
                                cntr1 += 1
                                summ1 += tempa
                                # print tempa

                            if cntr1 != 0:
                                aveg1 = summ1 / cntr1
                                # print aveg1
                            else:
                                aveg1 = 0
                    elif len(xarr) != 0:
                        tempa = 0
                        x1 = xarr[1]
                        y1 = yarr[1]

                        x2 = xarr[1]
                        y2 = yarr[1]

                        for tg in range(1, 200):
                            perp1x, perp1y = inter4p(x1, y1, x2, y2, tg)

                            if perp1x < 0:
                                perp1x = 0
                            if perp1y < 0:
                                perp1y = 0

                            if int(round(perp1x)) >= IMAGE_SIZE_Y:
                                perp1x = IMAGE_SIZE_Y - 1
                            if int(round(perp1y)) >= IMAGE_SIZE_X:
                                perp1y = IMAGE_SIZE_X - 1

                            if buils[int(round(perp1y)), int(round(perp1x))] == 127:
                                tempa = tg
                                if tempa > 4:
                                    # print 'p'
                                    break
                            else:
                                tempa = tg

                        if tempa == 5:
                            for tg in range(1, 200):
                                perp1x, perp1y = inter4n(p1x, p1y, p2x, p2y, tg)

                                if perp1x < 0:
                                    perp1x = 0
                                if perp1y < 0:
                                    perp1y = 0

                                if int(round(perp1x)) >= IMAGE_SIZE_Y:
                                    perp1x = IMAGE_SIZE_Y - 1
                                if int(round(perp1y)) >= IMAGE_SIZE_X:
                                    perp1y = IMAGE_SIZE_X - 1

                                if buils[int(round(perp1y)), int(round(perp1x))] == 127:
                                    tempa = tg
                                    if tempa > 4:
                                        # print 'n'
                                        break
                                else:
                                    tempa = tg

                        # print tempa

                        if tempa != 5 and tempa != 199:
                            cntr1 += 1
                            summ1 += tempa
                            # print tempa

                        if cntr1 != 0:
                            aveg1 = summ1 / cntr1
                            # print aveg1
                        else:
                            aveg1 = 0

            cntr2 += 1
            summ2 += aveg1

            if cntr2 != 0 and summ2 != 0:
                aveg2 = summ2 / cntr2
                # print name, '=', aveg2*PIXEL_SIZE  # , '\n'

            heights.append(float(ht))
            widths.append(aveg2*PIXEL_SIZE)
            names.append(bid)

        cnt += 1
        feature_buil.Destroy()
        feature_buil = layer2.GetNextFeature()

    for qw in range(0, len(heights)):
        if widths[qw] != 0:
            ratio = heights[qw] / widths[qw]
        else:
            ratio = 0

        ratios.append(ratio)

    return ratios, names