

class Settings:

    data_id_field_name = "OBJECTID"
    data_height_field_name = "Max_HOUSE_"
    data_geometry_field_name = "geometry"

    id_field = "building_id"
    height_field = "building_height"
    geometry_field = "building_polygon_geometry"
    area_field = "building_area"
    centroid_field = "building_centroid"
    buffered_field = "building_centroid_buffered"
    radius = 100

    target_height_field = f"{height_field}_target"
    neighbor_height_field = f"{height_field}_neighbors"
    target_id_field = f"{id_field}_target"
    neighbor_id_field = f"{id_field}_neighbors"
    target_area_field = f"{area_field}_target"
    neighbor_area_field = f"{area_field}_neighbors"

    spatial_join_list = [target_height_field,
                         neighbor_height_field,
                         target_id_field,
                         neighbor_id_field,
                         target_area_field,
                         neighbor_area_field]


