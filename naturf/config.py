

class Settings:

    data_id_field_name = "OBJECTID"
    data_height_field_name = "Max_HOUSE_"
    data_geometry_field_name = "geometry"

    id_field = "object_id"
    height_field = "height"
    geometry_field = "geometry"
    area_field = "area"
    centroid_field = "centroid"
    buffered_field = "buffered"
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


