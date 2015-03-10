from google.appengine.ext import ndb
from protorpc import messages
from google.appengine.ext.ndb import msgprop
from csvmodel import CsvModel

class Stop(CsvModel):
    class LocationType(messages.Enum):
        STOP = 0
        STATION = 1

    class WheelchairBoarding(messages.Enum):
        UNKNOWN = 0
        POSSIBLE = 1
        IMPOSSIBLE = 2

    _csv_file = 'stops.txt'
    _csv_id = 'stop_id'
    stop_code = ndb.StringProperty()
    stop_name = ndb.StringProperty(required=True)
    stop_desc = ndb.TextProperty()
    stop_latlon = ndb.GeoPtProperty(required=True)
    zone_id = ndb.KeyProperty(kind='Zone')
    stop_url = ndb.StringProperty()
    location_type = msgprop.EnumProperty(LocationType)
    parent_station = ndb.KeyProperty(kind='Stop')
    stop_timezone = ndb.StringProperty()
    wheelchair_boarding = msgprop.EnumProperty(WheelchairBoarding)
