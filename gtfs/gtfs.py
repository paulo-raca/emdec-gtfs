from io import BytesIO
from zipfile import ZipFile
import unicodecsv
from .csvmodel import get_children

class GTFS:
    def __init__(self):
        self.types = {}

    def write(self, obj):
        clazz = obj.__class__
        if clazz not in self.types:
            csvFile = BytesIO()
            csvWriter = unicodecsv.writer(csvFile, encoding='utf-8')
            csvWriter.writerow(clazz._csv_fields.keys())
            self.types[clazz] = {
                "file": csvFile,
                "csv": csvWriter,
                'keys_written': set()
            }
        clazzdata = self.types[clazz]

        obj_id = None
        if clazz._csv_id_field is not None:
            obj_id = getattr(obj, clazz._csv_id_field.name)
        if obj_id is None:
            obj_id = f"{clazz.__name__}@{id(obj)}"
            if clazz._csv_id_field is not None:
                setattr(obj, clazz._csv_id_field.name, obj_id)
            #print(f"Assigned ID to {obj_id}")

        if obj_id in clazzdata['keys_written']:
            #print(f"Skipping repeated obj: {obj_id}")
            return
        else:
            clazzdata['keys_written'].add(obj_id)

        clazzdata["csv"].writerow([
            field_getter(obj) for field_getter in clazz._csv_fields.values()
        ])

        for child in get_children(obj):
            self.write(child)

    def getvalue(self):
        return {
            clazz._csv_file: clazzdata["file"].getvalue()
            for clazz, clazzdata in self.types.items()
            if clazz._csv_file
        }

    def writezip(self, zipfile):
        files = self.getvalue()
        with ZipFile(zipfile, mode='w') as zf:
            for k, v in self.getvalue().items():
                zf.writestr(k, v)

    def getzip(self):
        zipfile = BytesIO()
        self.writezip(zipfile)
        return zipfile

