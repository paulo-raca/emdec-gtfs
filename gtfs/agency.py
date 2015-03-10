from google.appengine.ext import ndb
from csvmodel import CsvModel

class Agency(CsvModel):
    _csv_file = 'agency.txt'
    _csv_id = 'agency_id'
    agency_name = ndb.StringProperty(required=True)
    agency_url = ndb.TextProperty(required=True)
    agency_timezone = ndb.StringProperty(required=True)
    agency_lang = ndb.StringProperty()
    agency_phone = ndb.StringProperty()
    agency_fare_url = ndb.StringProperty()
