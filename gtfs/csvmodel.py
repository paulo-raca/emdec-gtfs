from collections import OrderedDict
from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop
import csv
import ast
import inspect

class NodeTagger(ast.NodeVisitor):
    def __init__(self):
        self.class_attribute_names = {}

    def visit_Assign(self, node):
        for target in node.targets:
            self.class_attribute_names[target.id] = target.lineno

    # Don't visit Assign nodes inside Function Definitions.
    def visit_FunctionDef(self, unused_node):
        return None

class CsvModel(ndb.Model):
    _csv_file = None
    _csv_id = None
    _csv_parent_id = None
    _csv_list_index = None

    @staticmethod
    def _getattrs(obj, *property_names):
        for p in property_names:
            if obj:
                if isinstance(p, str):
                    obj = getattr(obj, p)
                    if hasattr(obj, '__call__'):
                        obj = obj()
                else:
                    obj = p(obj)
        return obj

    @staticmethod
    def _field_to_csv(fieldname, property):
        if isinstance(property, msgprop.EnumProperty):
            return {
                fieldname: lambda obj, parent, index: CsvModel._getattrs(obj, fieldname, 'number')
            }
        if isinstance(property, ndb.DateProperty):
            return {
                fieldname: lambda obj, parent, index: CsvModel._getattrs(obj, fieldname, lambda x:x.strftime('%Y%m%d'))
            }
        if isinstance(property, ndb.KeyProperty):
            return {
                fieldname: lambda obj, parent, index: CsvModel._getattrs(obj, fieldname, 'id')
            }
        elif fieldname.endswith('_latlon'):
            return {
                fieldname.replace('_latlon', '_lat'): lambda obj, parent, index: CsvModel._getattrs(obj, fieldname, 'lat'),
                fieldname.replace('_latlon', '_lon'): lambda obj, parent, index: CsvModel._getattrs(obj, fieldname, 'lon'),
            }
        else:
            return {
                fieldname: lambda obj, parent, index: CsvModel._getattrs(obj, fieldname)
            }

    @staticmethod
    def _field_to_children(fieldname, property):
        if property._repeated:
            return lambda obj: getattr(obj, fieldname)
        else:
            return lambda obj: [getattr(obj, fieldname)]

    @classmethod
    def csv_fields(cls):
        fields = OrderedDict()
        children_getters = []
        if cls._csv_id:
            fields[cls._csv_id] = lambda obj, parent, index: CsvModel._getattrs(obj, 'key', 'id')
        if cls._csv_parent_id:
            fields[cls._csv_parent_id] = lambda obj, parent, index: CsvModel._getattrs(parent, 'key', 'id')
        if cls._csv_list_index:
            fields[cls._csv_list_index] = lambda obj, parent, index: index

        for fieldname in cls.ordered_ndb_fields():
            property = cls._properties[fieldname]
            if isinstance(property, ndb.StructuredProperty):
                children_getters.append(CsvModel._field_to_children(fieldname, property))
            else:
                fields.update(CsvModel._field_to_csv(fieldname, property))

        return fields, children_getters

    @classmethod
    def ordered_ndb_fields(cls):
        properties = list(cls._properties.keys())
        source = inspect.getsource(cls)
        tree = ast.parse(source)
        visitor = NodeTagger()
        visitor.visit(tree)
        attributes = visitor.class_attribute_names
        properties.sort(key=lambda x:attributes[x])
        return properties
