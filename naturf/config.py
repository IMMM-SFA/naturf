class Settings:
    BUILDING_HEIGHT_INTERVAL = 5
    CONSTANT_04 = 0.4
    CONSTANT_0193 = 0.193
    CONSTANT_0303 = 0.303
    CONSTANT_359 = 3.59
    CONSTANT_15 = 15
    CONSTANT_75 = 7.5
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
    SOUTHEAST_DEGREES_ARCTAN = -45
    SOUTHWEST_DEGREES = 225
    SOUTHWEST_DEGREES_ARCTAN = -135
    START_OF_CIRCLE_DEGREES = 0
    ZXCV_FACTOR = 3.5
    DEFAULT_STREET_WIDTH = 15

    data_id_field_name = "OBJECTID"
    data_height_field_name = "Max_HOUSE_"
    data_geometry_field_name = "geometry"
    target = "target"
    neighbor = "neighbor"
    north = "north"
    east = "east"
    south = "south"
    west = "west"

    id_field = "building_id"
    height_field = "building_height"
    geometry_field = "building_geometry"
    area_field = "building_area"
    building_plan_area_field = "building_plan_area"
    centroid_field = "building_centroid"
    buffered_field = "building_buffered"
    total_plan_area = "total_plan_area"
    total_plan_area_geometry = "total_plan_area_geometry"
    volume_field = "volume_field"

    target_height_field = f"{height_field}_{target}"
    neighbor_height_field = f"{height_field}_{neighbor}"
    target_id_field = f"{id_field}_{target}"
    neighbor_id_field = f"{id_field}_{neighbor}"
    target_area_field = f"{area_field}_{target}"
    neighbor_area_field = f"{area_field}_{neighbor}"
    target_geometry_field = f"{geometry_field}_{target}"
    neighbor_geometry_field = f"{geometry_field}_{neighbor}"
    target_centroid_field = f"{centroid_field}_{target}"
    neighbor_centroid_field = f"{centroid_field}_{neighbor}"
    neighbor_volume_field = f"{volume_field}_{neighbor}"

    target_buffered_field = f"{buffered_field}_{target}"

    distance_to_neighbor_by_centroid = f"distance_to_{neighbor}_by_centroid"
    distance_between_buildings = "distance_between_buildings"
    average_distance_between_buildings = "average_distance_between_buildings"

    spatial_join_list = [
        target_height_field,
        neighbor_height_field,
        target_id_field,
        neighbor_id_field,
        target_area_field,
        neighbor_area_field,
        target_geometry_field,
        neighbor_geometry_field,
    ]

    wall_angle = "wall_angle"
    wall_direction = "wall_direction"
    wall_length = "wall_length"
    wall_length_north = "wall_length_north"
    wall_length_east = "wall_length_east"
    wall_length_south = "wall_length_south"
    wall_length_west = "wall_length_west"
    frontal_length_north = "frontal_length_north"
    frontal_length_east = "frontal_length_east"
    frontal_length_south = "frontal_length_south"
    frontal_length_west = "frontal_length_west"
    frontal_area_north = "frontal_area_north"
    frontal_area_east = "frontal_area_east"
    frontal_area_south = "frontal_area_south"
    frontal_area_west = "frontal_area_west"
    plan_area_density = "plan_area_density"
    rooftop_area_density = "rooftop_area_density"
    frontal_area_index_north = "frontal_area_index_north"
    frontal_area_index_east = "frontal_area_index_east"
    frontal_area_index_south = "frontal_area_index_south"
    frontal_area_index_west = "frontal_area_index_west"

    grimmond_oke_displacement_height = "grimmond_oke_displacement_height"
    grimmond_oke_roughness_length = "grimmond_oke_roughness_length"
    sky_view_factor = "sky_view_factor"
