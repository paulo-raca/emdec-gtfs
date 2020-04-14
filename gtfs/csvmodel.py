from dataclasses import dataclass, field, fields
from functools import partial
from enum import Enum
from datetime import date

FIELD_METADATA_CSVMODEL_TYPE = "csvmodel_type"

def id_field(metadata={}, **kwargs):
    metadata[FIELD_METADATA_CSVMODEL_TYPE] = "id"
    return field(metadata=metadata, default=None, **kwargs)

def child_parent_field(metadata={}, **kwargs):
    metadata[FIELD_METADATA_CSVMODEL_TYPE] = "child_parent_node"
    return field(metadata=metadata, default=None, repr=False, **kwargs)

def child_index_field(metadata={}, **kwargs):
    metadata[FIELD_METADATA_CSVMODEL_TYPE] = "child_index"
    return field(metadata=metadata, default=None, **kwargs)

def children_list_field(metadata={}, **kwargs):
    metadata[FIELD_METADATA_CSVMODEL_TYPE] = "children_list"
    return field(default_factory=list, metadata=metadata, **kwargs)

def reference_field(metadata={}, **kwargs):
    metadata[FIELD_METADATA_CSVMODEL_TYPE] = "reference"
    return field(metadata=metadata, default=None, repr=False, **kwargs)


@dataclass
class LatLon:
    lat: float
    lon: float

def _path_getter(*path):
    def getter(obj):
        for prop in path:
            if obj is None:
                return None
            if isinstance(prop, str):
                obj = getattr(obj, prop)
            elif hasattr(prop, '__call__'):
                obj = prop(obj)
            else:
                raise ValueError(f"Expected property name or function, got {repr(prop)}")
        return obj
    return getter

def get_children(obj):
    for field in obj.__class__._csv_node_fields:
        value = getattr(obj, field.name)
        if value is not None:
            yield value
    for field in obj.__class__._csv_node_list_fields:
        values = getattr(obj, field.name)
        for index, value in enumerate(values):
            if value.__class__._csv_parent_field is not None:
                setattr(value, value.__class__._csv_parent_field.name, obj)
            if value.__class__._csv_index_field is not None:
                setattr(value, value.__class__._csv_index_field.name, index)
            yield value

def CsvModel(csv_file):
    def wrapper(cls):
        cls = dataclass(cls)
        cls._csv_file = csv_file

        cls._csv_id_field = None
        cls._csv_parent_field = None
        cls._csv_index_field = None
        cls._csv_node_list_fields = []
        cls._csv_node_fields = []
        cls._csv_fields = {}

        for field in fields(cls):
            csv_type = field.metadata.get(FIELD_METADATA_CSVMODEL_TYPE, None)
            if csv_type == 'id':
                assert cls._csv_id_field is None, "Already has an ID field"
                cls._csv_id_field = field
            elif csv_type == 'child_parent_node':
                assert cls._csv_parent_field is None, "Already has a parent ID field"
                cls._csv_parent_field = field
                cls._csv_node_fields.append(field)
            elif csv_type == 'child_index':
                assert cls._csv_index_field is None, "Already has a list index field"
                cls._csv_index_field = field
            elif csv_type == 'children_list':
                cls._csv_node_list_fields.append(field)
            elif csv_type == 'reference':
                cls._csv_node_fields.append(field)


            if csv_type != 'children_list':
                if csv_type in ['reference', 'child_parent_node']:
                    cls._csv_fields[field.name] = _path_getter(field.name, lambda obj: getattr(obj, type(obj)._csv_id_field.name))
                elif isinstance(field.type, type) and issubclass(field.type, Enum):
                    cls._csv_fields[field.name] = _path_getter(field.name, "value")
                elif field.type == date:
                    cls._csv_fields[field.name] = _path_getter(field.name, lambda date: date.strftime('%Y%m%d'))
                elif field.name.endswith("_latlon"):
                    cls._csv_fields[field.name.replace('_latlon', '_lat')] = _path_getter(field.name, "lat")
                    cls._csv_fields[field.name.replace('_latlon', '_lon')] = _path_getter(field.name, "lon")
                else:
                    cls._csv_fields[field.name] = _path_getter(field.name)
        return cls
    return wrapper
