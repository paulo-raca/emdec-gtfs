from typing import List
from .csvmodel import CsvModel, LatLon, id_field, child_parent_field, child_index_field, children_list_field

@CsvModel('shapes.txt')
class ShapePoint:
    shape_id: "Shape" = child_parent_field()
    shape_pt_sequence: int = child_index_field()
    shape_pt_latlon: LatLon = None
    shape_dist_traveled: float = None

@CsvModel(None)
class Shape:
    shape_id: str = id_field()
    shape_points: List[ShapePoint] = children_list_field()
