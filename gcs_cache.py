import json
import cloudstorage as gcs
import logging
from google.appengine.api import app_identity
from collections import OrderedDict

_prefix = '/' + app_identity.get_default_gcs_bucket_name() + '/'
logging.info('GCS Prefix: %s' % _prefix)

def gcs_filename(filename):
    return _prefix + filename

def gcs_stat(filename, *args, **kwargs):
    return gcs.stat(gcs_filename(filename), *args, **kwargs)

def gcs_open(filename, *args, **kwargs):
    return gcs.open(gcs_filename(filename), *args, **kwargs)


def GCSCached(content_type='application/json', encode_contents=json.dumps, decode_contents=lambda x: json.loads(x, object_pairs_hook=OrderedDict)):
    if encode_contents is None:
        encode_contents = lambda x: x
    if decode_contents is None:
        decode_contents = lambda x: x

    def GCSCached(wrapped):
        def f(*args, **kwargs):
            filename, generator, cache_disabled = wrapped(*args, **kwargs)

            try:
                if cache_disabled or filename is None:
                    raise Exception('Cache disabled')
                file = gcs_open(filename)
                try:
                    data = file.read()
                    logging.info('READING "%s": %d bytes' % (filename, len(data)))
                    return decode_contents(data)
                finally:
                    file.close()
            except:
                ret = generator()
                try:
                    if filename is not None:
                        file = gcs_open(filename, 'w', content_type=content_type)
                        try:
                            data = encode_contents(ret)
                            logging.info('WRITING "%s": %d bytes' % (filename, len(data)))
                            file.write(data)
                        finally:
                            file.close()
                except:
                    pass
                return ret
            finally:
                pass
        return f
    return GCSCached
