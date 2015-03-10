from StringIO import StringIO
from zipfile import ZipFile
import unicodecsv
import codecs

class GTFS:
    def __init__(self):
        self.types = {}

    def write(self, obj, parent=None, index=None):
        clazz = obj.__class__
        if clazz not in self.types:
            filename = clazz._csv_file
            fields, children_getter = clazz.csv_fields()
            csvFile = StringIO()
            csvWriter = unicodecsv.writer(csvFile, encoding='utf-8')
            csvWriter.writerow(fields.keys())
            self.types[clazz] = {
                "fields": fields,
                "children": children_getter,
                "filename": filename,
                "file": csvFile,
                "csv": csvWriter,
                'keys_written': set()
            }
        if obj.key is not None:
            if obj.key in self.types[clazz]['keys_written']:
                #print('Skip repeated key %s' % obj.key)
                return
            else:
                self.types[clazz]['keys_written'].add(obj.key)

        row = [
            x(obj, parent, index) for x in self.types[clazz]["fields"].itervalues()
        ]
        self.types[clazz]["csv"].writerow(row)

        for children_getter in self.types[clazz]["children"]:
            children = children_getter(obj)
            for i in range(len(children)):
                self.write(children[i], parent=obj, index=i)

    def getvalue(self):
        return {
            x["filename"]: x["file"].getvalue()
            for x in self.types.itervalues()
            if x["filename"]
        }

    def getzip(self):
        files = self.getvalue()
        zipfile = StringIO()
        with ZipFile(zipfile, mode='w') as zf:
            for k, v in self.getvalue().iteritems():
                zf.writestr(k, v)

        return zipfile.getvalue()

