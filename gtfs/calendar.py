from google.appengine.ext import ndb
from protorpc import messages
from google.appengine.ext.ndb import msgprop
from csvmodel import CsvModel

class Calendar(CsvModel):
    class Available(messages.Enum):
        UNAVAILABLE = 0
        AVAILABLE = 1

    _csv_file = 'calendar.txt'
    _csv_id = 'service_id'
    monday = msgprop.EnumProperty(Available, required=True)
    tuesday = msgprop.EnumProperty(Available, required=True)
    wednesday = msgprop.EnumProperty(Available, required=True)
    thursday = msgprop.EnumProperty(Available, required=True)
    friday = msgprop.EnumProperty(Available, required=True)
    saturday = msgprop.EnumProperty(Available, required=True)
    sunday = msgprop.EnumProperty(Available, required=True)
    start_date = ndb.DateProperty(required=True)
    end_date = ndb.DateProperty(required=True)
