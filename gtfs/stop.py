from enum import Enum
from .zone import Zone
from .csvmodel import CsvModel, LatLon, id_field, reference_field

@CsvModel('stops.txt')
class Stop():
    class LocationType(Enum):
        Stop = 0
        Station = 1

    class WheelchairBoarding(Enum):
        Unknown = 0
        Possible = 1
        Impossible = 2

    stop_id: str = id_field()
    stop_code: str = None
    stop_name: str = None
    stop_desc: str = None
    stop_latlon: LatLon = None
    zone_id: Zone = reference_field()
    stop_url: str = None
    location_type: LocationType = LocationType.Stop
    parent_station: "Stop" = reference_field()
    stop_timezone: str = None
    wheelchair_boarding: WheelchairBoarding = WheelchairBoarding.Unknown
