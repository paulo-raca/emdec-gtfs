from google.appengine.ext import ndb
from protorpc import messages
from google.appengine.ext.ndb import msgprop
from csvmodel import CsvModel

class FareRule(CsvModel):
    _csv_file = 'fare_rules.txt'
    _csv_parent_id = 'fare_id'
    route_id = ndb.KeyProperty(kind='Route')
    origin_id = ndb.KeyProperty(kind='Zone')
    destination_id = ndb.KeyProperty(kind='Zone')
    contains_id = ndb.KeyProperty(kind='Zone')

class Fare(CsvModel):
    class PaymentMethod(messages.Enum):
        ONBOARD = 0
        BEFORE_BOARDING = 1

    _csv_file = 'fare_attributes.txt'
    _csv_id = 'fare_id'
    price = ndb.FloatProperty(required=True)
    currency_type = ndb.StringProperty(required=True)
    payment_method = msgprop.EnumProperty(PaymentMethod)
    transfers=ndb.IntegerProperty()
    transfer_duration=ndb.IntegerProperty()
    rules = ndb.StructuredProperty(FareRule, repeated=True)
