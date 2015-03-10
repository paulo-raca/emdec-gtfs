from datetime import datetime, timedelta
from random import randint

try:
    from google.appengine.ext import ndb
    def NdbCached(namespace, expires=timedelta(days=1), splice=timedelta(days=1)):
        def NdbCached2(wrapped):
            class CacheEntry(ndb.Model):
                value = ndb.PickleProperty(compressed=True)
                expires_at = ndb.DateTimeProperty()

            def f(raw_key):
                key = ndb.Key(CacheEntry, '%s:-:%s' % (repr(namespace), repr(raw_key)))
                cache_entry = key.get()
                if cache_entry is None or cache_entry.expires_at < datetime.now():
                    cache_entry = CacheEntry(
                        key=key,
                        value=wrapped(raw_key),
                        expires_at=datetime.now() + expires + splice*randint(0,10000)/10000
                    )
                    cache_entry.put()
                return cache_entry.value
            return f
        return NdbCached2
except:
    from collections import namedtuple
    import shelve
    _CacheEntry = namedtuple('_CacheEntry', ['value', 'expires_at'])
    def NdbCached(namespace, expires=timedelta(days=1), splice=timedelta(days=1)):
        def NdbCached2(wrapped):
            store = shelve.open('%s.ndbcache' % (namespace))

            def f(raw_key):
                key = repr(raw_key)
                cache_entry = store.get(key, None)
                if cache_entry is None or cache_entry.expires_at < datetime.now():
                    cache_entry = _CacheEntry(
                        value=wrapped(raw_key),
                        expires_at=datetime.now() + expires + splice*randint(0,10000)/10000
                    )
                    store[key] = cache_entry
                return cache_entry.value
            return f
        return NdbCached2
