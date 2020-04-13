#from google.cloud import ndb
from enum import Enum
from typing import List
from .csvmodel import CsvModel, id_field, child_parent_field, child_index_field, children_list_field, reference_field
from .calendar import Calendar
from .route import Route
from .stop import Stop
from .shape import Shape

@CsvModel('stop_times.txt')
class StopTime():
    class PickupDropoffType(Enum):
        Available = 0
        Unavailable = 1
        Schedule_with_agency = 2
        Schedule_with_driver = 3

    class TimePoint(Enum):
        Approximate = 0
        Exact = 1

    trip_id: "Trip" = child_parent_field()
    stop_sequence: int = child_index_field()
    arrival_time: str = None
    departure_time: str = None
    stop_id: Stop = reference_field()
    stop_headsign:str = None
    pickup_type: PickupDropoffType = None
    drop_off_type: PickupDropoffType = None
    shape_dist_traveled: float = None
    timepoint: TimePoint = None

@CsvModel('frequencies.txt')
class TripFrequency:
    class ExactTime(Enum):
        Approximate = 0
        Exact = 1

    trip_id: "Trip" = child_parent_field()
    start_time: str = None
    end_time: str = None
    headway_secs: int = None
    exact_times: ExactTime = None

@CsvModel(None)
class Block():
    block_id: str = id_field()

@CsvModel('trips.txt')
class Trip:
    class Direction(Enum):
        A = 0
        B = 1

    class WheelchairAcessible(Enum):
        Unknown = 0
        Acessible = 1
        Inacessible = 2

    class BikesAllowed(Enum):
        Unknown = 0
        Allowed = 1
        NotAllowed = 2

    trip_id: str = id_field()
    route_id: Route = reference_field()
    service_id: Calendar = reference_field()
    trip_headsign: str = None
    trip_short_name: str = None
    direction_id: Direction = None
    block_id: Block = reference_field()
    shape_id: Shape = reference_field()
    stop_times: List[StopTime] = children_list_field()
    frequencies: List[TripFrequency] = children_list_field()
    wheelchair_accessible: WheelchairAcessible = None
    bikes_allowed: BikesAllowed = None
