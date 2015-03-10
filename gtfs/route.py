from google.appengine.ext import ndb
from protorpc import messages
from google.appengine.ext.ndb import msgprop
from csvmodel import CsvModel

class Route(CsvModel):
    class Type(messages.Enum):
        LIGHT_RAIL = 0
        SUBWAY = 1
        RAIL = 2
        BUS = 3
        FERRY = 4
        CABLE_CAR = 5
        GONDOLA = 6
        FUNICULAR = 7

    _csv_file = 'routes.txt'
    _csv_id = 'route_id'
    agency_id = ndb.KeyProperty(kind='Agency')
    route_short_name = ndb.StringProperty(required=True)
    route_long_name = ndb.StringProperty(required=True)
    route_desc = ndb.TextProperty()
    route_type = msgprop.EnumProperty(Type, required=True)
    route_url = ndb.StringProperty()
    route_color = ndb.StringProperty()
    route_text_color = ndb.StringProperty()
