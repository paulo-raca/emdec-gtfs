from google.appengine.ext import ndb
from protorpc import messages
from google.appengine.ext.ndb import msgprop
from csvmodel import CsvModel

class StopTime(CsvModel):
    class PickupDropoffType(messages.Enum):
        AVAILABLE = 0
        UNAVAILABLE = 1
        SCHEDULE_WITH_AGENCY = 2
        SCHEDULE_WITH_DRIVER = 3

    class TimePoint(messages.Enum):
        APPROXIMATE = 0
        EXACT = 1

    _csv_file = 'stop_times.txt'
    _csv_parent_id = 'trip_id'
    _csv_list_index = 'stop_sequence'
    arrival_time = ndb.StringProperty()
    departure_time = ndb.StringProperty()
    stop_id = ndb.KeyProperty(kind='Stop', required=True)
    stop_headsign = ndb.StringProperty()
    pickup_type = msgprop.EnumProperty(PickupDropoffType)
    drop_off_type = msgprop.EnumProperty(PickupDropoffType)
    shape_dist_traveled = ndb.FloatProperty()
    timepoint = msgprop.EnumProperty(TimePoint)

class TripFrequency(CsvModel):
    class ExactTime(messages.Enum):
        APPROXIMATE = 0
        EXACT = 1

    _csv_file = 'frequencies.txt'
    _csv_parent_id = 'trip_id'
    start_time = ndb.StringProperty(required=True)
    end_time = ndb.StringProperty(required=True)
    headway_secs = ndb.IntegerProperty(required=True)
    exact_times = msgprop.EnumProperty(ExactTime)


class Trip(CsvModel):
    class Direction(messages.Enum):
        A = 0
        B = 1

    class WheelchairAcessible(messages.Enum):
        UNKNOWN = 0
        ACESSIBLE = 1
        INACESSIBLE = 2

    class BikesAllowed(messages.Enum):
        UNKNOWN = 0
        ALLOWED = 1
        NOT_ALLOWED = 2

    _csv_file = 'trips.txt'
    _csv_id = 'trip_id'
    route_id = ndb.KeyProperty(kind='Route', required=True)
    service_id = ndb.KeyProperty(kind='Calendar', required=True)
    trip_headsign = ndb.StringProperty()
    trip_short_name = ndb.StringProperty()
    direction_id = msgprop.EnumProperty(Direction)
    block_id = ndb.KeyProperty(kind='Block')
    shape_id = ndb.KeyProperty(kind='Shape')
    stop_times = ndb.StructuredProperty(StopTime, repeated=True)
    frequencies = ndb.StructuredProperty(TripFrequency, repeated=True)
    wheelchair_accessible = msgprop.EnumProperty(WheelchairAcessible)
    bikes_allowed = msgprop.EnumProperty(BikesAllowed)
