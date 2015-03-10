from google.appengine.ext import ndb
from protorpc import messages
from google.appengine.ext.ndb import msgprop
from csvmodel import CsvModel

class FeedInfo(CsvModel):
    _csv_file = 'feed_info.txt'
    feed_publisher_name = ndb.StringProperty(required=True)
    feed_publisher_url = ndb.StringProperty(required=True)
    feed_lang = ndb.StringProperty(required=True)
    feed_start_date = ndb.DateProperty()
    feed_end_date = ndb.DateProperty()
    feed_version = ndb.StringProperty()
