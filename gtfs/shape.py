from google.appengine.ext import ndb
from protorpc import messages
from google.appengine.ext.ndb import msgprop
from csvmodel import CsvModel

class ShapePoint(CsvModel):
    _csv_file = 'shapes.txt'
    _csv_parent_id = 'shape_id'
    _csv_list_index = 'shape_pt_sequence'
    shape_pt_latlon = ndb.GeoPtProperty(required=True)
    shape_dist_traveled = ndb.FloatProperty()

class Shape(CsvModel):
    shape_points = ndb.StructuredProperty(ShapePoint, repeated=True)
