class Settings:
    """
    This class is used to define variables for the naturf application.
    """

    BUILDING_HEIGHT_INTERVAL = 5
    VONKARMANCONSTANT = 0.4
    OBSTACLEDRAGCOEFFICIENT = 1.12
    PSI_H = 0.193
    DRAGCOEFFICIENT_03 = 0.3
    DRAGCOEFFICIENT_0003 = 0.003
    ALPHACOEFFICIENT = 3.59
    BETACOEFFICIENT = 1.0
    CAP_STYLE = 3
    CONSTANT_15 = 15
    CONSTANT_75 = 7.5
    DEGREES_IN_CIRCLE = 360
    DILAREA_DEFAULT = 10000
    DISPLACEMENT_HEIGHT_FACTOR = 0.67
    MAX_BUILDING_HEIGHT = 75
    NORTHEAST_DEGREES = 45
    NORTHWEST_DEGREES = 135
    OUTPUT_CRS = "EPSG:4326"
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
    DEFAULT_STREET_WIDTH = 15
    DEFAULT_OUTPUT_RESOLUTION = [0.00083333333, 0.00083333333]
    DEFAULT_FILL_VALUE = 0
    SCALING_FACTOR = 4

    DATA_ID_FIELD_NAME = "OBJECTID"
    DATA_HEIGHT_FIELD_NAME = "Max_HOUSE_"
    DATA_GEOMETRY_FIELD_NAME = "geometry"
    TARGET = "target"
    NEIGHBOR = "neighbor"
    NORTH = "north"
    EAST = "east"
    SOUTH = "south"
    WEST = "west"
    NORTH_SOUTH = "north_south"
    EAST_WEST = "east_west"

    ID_FIELD = "building_id"
    HEIGHT_FIELD = "building_height"
    GEOMETRY_FIELD = "building_geometry"
    AREA_FIELD = "building_area"
    BUILDING_PLAN_AREA_FIELD = "building_plan_area"
    CENTROID_FIELD = "building_centroid"
    BUFFERED_FIELD = "building_buffered"
    TOTAL_PLAN_AREA = "total_plan_area"
    TOTAL_PLAN_AREA_GEOMETRY = "total_plan_area_geometry"
    VOLUME_FIELD = "volume_field"

    TARGET_HEIGHT_FIELD = f"{HEIGHT_FIELD}_{TARGET}"
    NEIGHBOR_HEIGHT_FIELD = f"{HEIGHT_FIELD}_{NEIGHBOR}"
    TARGET_ID_FIELD = f"{ID_FIELD}_{TARGET}"
    NEIGHBOR_ID_FIELD = f"{ID_FIELD}_{NEIGHBOR}"
    TARGET_AREA_FIELD = f"{AREA_FIELD}_{TARGET}"
    NEIGHBOR_AREA_FIELD = f"{AREA_FIELD}_{NEIGHBOR}"
    TARGET_GEOMETRY_FIELD = f"{GEOMETRY_FIELD}_{TARGET}"
    NEIGHBOR_GEOMETRY_FIELD = f"{GEOMETRY_FIELD}_{NEIGHBOR}"
    TARGET_CENTROID_FIELD = f"{CENTROID_FIELD}_{TARGET}"
    NEIGHBOR_CENTROID_FIELD = f"{CENTROID_FIELD}_{NEIGHBOR}"
    NEIGHBOR_VOLUME_FIELD = f"{VOLUME_FIELD}_{NEIGHBOR}"

    TARGET_BUFFERED_FIELD = f"{BUFFERED_FIELD}_{TARGET}"

    DISTANCE_TO_NEIGHBOR_BY_CENTROID = f"distance_to_{NEIGHBOR}_by_centroid"
    DISTANCE_BETWEEN_BUILDINGS = "distance_between_buildings"
    AVERAGE_DISTANCE_BETWEEN_BUILDINGS = "average_distance_between_buildings"

    SPATIAL_JOIN_LIST = [
        TARGET_HEIGHT_FIELD,
        NEIGHBOR_HEIGHT_FIELD,
        TARGET_ID_FIELD,
        NEIGHBOR_ID_FIELD,
        TARGET_AREA_FIELD,
        NEIGHBOR_AREA_FIELD,
        TARGET_GEOMETRY_FIELD,
        NEIGHBOR_GEOMETRY_FIELD,
    ]

    WALL_ANGLE = "wall_angle"
    WALL_DIRECTION = "wall_direction"
    WALL_LENGTH = "wall_length"
    WALL_LENGTH_NORTH = "wall_length_north"
    WALL_LENGTH_EAST = "wall_length_east"
    WALL_LENGTH_SOUTH = "wall_length_south"
    WALL_LENGTH_WEST = "wall_length_west"
    FRONTAL_LENGTH_NORTH = "frontal_length_north"
    FRONTAL_LENGTH_EAST = "frontal_length_east"
    FRONTAL_LENGTH_SOUTH = "frontal_length_south"
    FRONTAL_LENGTH_WEST = "frontal_length_west"
    FRONTAL_AREA_NORTH = "frontal_area_north"
    FRONTAL_AREA_EAST = "frontal_area_east"
    FRONTAL_AREA_SOUTH = "frontal_area_south"
    FRONTAL_AREA_WEST = "frontal_area_west"
    PLAN_AREA_DENSITY = "plan_area_density"
    ROOFTOP_AREA_DENSITY = "rooftop_area_density"
    PLAN_AREA_FRACTION = "plan_area_fraction"
    MEAN_BUILDING_HEIGHT = "mean_building_height"
    STANDARD_DEVIATION_OF_BUILDING_HEIGHTS = "standard_deviation_of_building_heights"
    AREA_WEIGHTED_MEAN_OF_BUILDING_HEIGHTS = "area_weighted_mean_of_building_heights"
    BUILDING_SURFACE_AREA = "building_surface_area"
    BUILDING_SURFACE_AREA_TO_PLAN_AREA_RATIO = "building_surface_area_to_plan_area_ratio"
    FRONTAL_AREA_INDEX_NORTH = "frontal_area_index_north"
    FRONTAL_AREA_INDEX_EAST = "frontal_area_index_east"
    FRONTAL_AREA_INDEX_SOUTH = "frontal_area_index_south"
    FRONTAL_AREA_INDEX_WEST = "frontal_area_index_west"
    COMPLETE_ASPECT_RATIO = "complete_aspect_ratio"
    HEIGHT_TO_WIDTH_RATIO = "height_to_width_ratio"
    SKY_VIEW_FACTOR = "sky_view_factor"
    GRIMMOND_OKE_ROUGHNESS_LENGTH = "grimmond_oke_roughness_length"
    GRIMMOND_OKE_DISPLACEMENT_HEIGHT = "grimmond_oke_displacement_height"
    RAUPACH_DISPLACEMENT_HEIGHT_NORTH = "raupach_displacement_height_north"
    RAUPACH_DISPLACEMENT_HEIGHT_EAST = "raupach_displacement_height_east"
    RAUPACH_DISPLACEMENT_HEIGHT_SOUTH = "raupach_displacement_height_south"
    RAUPACH_DISPLACEMENT_HEIGHT_WEST = "raupach_displacement_height_west"
    RAUPACH_ROUGHNESS_LENGTH_NORTH = "raupach_roughness_length_north"
    RAUPACH_ROUGHNESS_LENGTH_EAST = "raupach_roughness_length_east"
    RAUPACH_ROUGHNESS_LENGTH_SOUTH = "raupach_roughness_length_south"
    RAUPACH_ROUGHNESS_LENGTH_WEST = "raupach_roughness_length_west"
    MACDONALD_ROUGHNESS_LENGTH_NORTH = "macdonald_roughness_length_north"
    MACDONALD_ROUGHNESS_LENGTH_EAST = "macdonald_roughness_length_east"
    MACDONALD_ROUGHNESS_LENGTH_SOUTH = "macdonald_roughness_length_south"
    MACDONALD_ROUGHNESS_LENGTH_WEST = "macdonald_roughness_length_west"
    MACDONALD_DISPLACEMENT_HEIGHT = "macdonald_displacement_height"
    VERTICAL_DISTRIBUTION_OF_BUILDING_HEIGHTS = "vertical_distribution_of_building_heights"
