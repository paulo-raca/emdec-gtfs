from enum import Enum
from .csvmodel import CsvModel, id_field, reference_field
from .agency import Agency

@CsvModel('routes.txt')
class Route():
    class Type(Enum):
        LightRail = 0
        Subway = 1
        Rail = 2
        Bus = 3
        Ferry = 4
        Cable_car = 5
        Gondola = 6
        Funicular = 7

    route_id: str = id_field()
    agency_id: Agency = reference_field()
    route_short_name: str = None
    route_long_name: str = None
    route_desc: str = None
    route_type: Type = None
    route_url: str = None
    route_color: str = None
    route_text_color: str = None
