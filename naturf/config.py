

class Settings:

    NORTHWEST_DEGREES = 135
    NORTHEAST_DEGREES = 45
    SOUTHWEST_DEGREES = 225
    SOUTHEAST_DEGREES = 315
    DEGREES_IN_CIRCLE = 360
    START_OF_CIRCLE_DEGREES = 0

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

    data_id_field_name = "OBJECTID"
    data_height_field_name = "Max_HOUSE_"
    data_geometry_field_name = "geometry"

    id_field = "building_id"
    height_field = "building_height"
    geometry_field = "building_polygon_geometry"
    area_field = "building_area"
    centroid_field = "building_centroid"
    buffered_field = "building_buffered"
    radius = 100

    target_height_field = f"{height_field}_target"
    neighbor_height_field = f"{height_field}_neighbor"
    target_id_field = f"{id_field}_target"
    neighbor_id_field = f"{id_field}_neighbor"
    target_area_field = f"{area_field}_target"
    neighbor_area_field = f"{area_field}_neighbor"
    target_geometry_field = f"{geometry_field}_target"
    neighbor_geometry_field = f"{geometry_field}_neighbor"
    target_centroid_field = f"{centroid_field}_target"
    neighbor_centroid_field = f"{centroid_field}_neighbor"

    spatial_join_list = [target_height_field,
                         neighbor_height_field,
                         target_id_field,
                         neighbor_id_field,
                         target_area_field,
                         neighbor_area_field,
                         target_geometry_field,
                         neighbor_geometry_field]


