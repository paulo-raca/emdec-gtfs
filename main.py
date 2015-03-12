# -*- coding: utf-8 -*-
import sys
import os
import logging
from webapp2 import WSGIApplication, Route, RedirectHandler


IS_DEV = os.environ.get('SERVER_SOFTWARE','').startswith('Development')

# inject './lib' dir in the path so that we can simply do "import ndb"
# or whatever there's in the app lib dir.
if 'lib' not in sys.path:
    sys.path[0:0] = ['lib']

# webapp2 config
app_config = {
    'webapp2_extras.sessions': {
        'cookie_name': 'session_cookie',
        'secret_key': '566tSAsRIfbYuzgYfbGjV0cmStbQVPWKnSegfwVwsldjgn'
    },
    'webapp2_extras.auth': {
        'user_attributes': []
    }
}

# Map URLs to handlers
routes = [
    Route('/', handler=RedirectHandler, defaults={'_uri': 'https://github.com/paulo-raca/Emdec-GTransit'}),
    Route('/files/<filename>', handler='emdec2gtfs.RouteHandler:fetch_file'),
    Route('/async/refresh', handler='emdec2gtfs.RouteHandler:async_refresh'),
    Route('/async/<what:.*>', handler='emdec2gtfs.RouteHandler:async'),
    Route('/route/list', handler='emdec2gtfs.RouteHandler:export_route_list'),
    Route('/route/<route_codes>/json', handler='emdec2gtfs.RouteHandler:export_route_info'),
    Route('/route/<route_codes>/gtfs', handler='emdec2gtfs.RouteHandler:export_gtfs'),
]


app = WSGIApplication(routes, config=app_config, debug=True)
