# -*- coding: utf-8 -*-
import logging
import os
import time
import main
from datetime import datetime
import webapp2
import traceback
import json
from webapp2_extras import auth, sessions
from gcs_cache import gcs_stat, gcs_open

class BaseRequestHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    def serve_gcs(self, filename):
        stat = self.gcs_stat(filename)
        gcs_file = self.gcs_open(filename)
        try :
            self.response.headers['Content-Type'] = stat.content_type
            self.response.headers['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(stat.filename)
            self.response.write(gcs_file.read())
        finally:
            gcs_file.close()

    @webapp2.cached_property
    def now(self):
        return datetime.utcnow()

    @webapp2.cached_property
    def isDev(self):
        return main.IS_DEV

    @webapp2.cached_property
    def session(self):
        """Returns a session using the default cookie key"""
        return self.session_store.get_session()

def JsonHandler(sleep=0):
    def decorator(wrapped):
        def f(self, *args, **kwargs):
            try:
                if sleep:
                    time.sleep(sleep)
                if self.request.body:
                    args = [json.loads(self.request.body)] + list(args)

                response = wrapped(self, *args, **kwargs)

            except:
                logging.exception('Ajax Error:\n\tRequest=%s', self.request.body)
                self.response.status = 500
                response = {
                    'error': traceback.format_exc() if self.isDev else 'Internal Error',
                    'request': self.request.body
                }

            self.response.headers['Content-Type'] = "application/json; charset=UTF-8"
            self.response.headers['Access-Control-Allow-Origin'] = "*"

            self.response.out.write(json.dumps(
                response,
                indent=4 if self.isDev else None,
                separators=(', ', ': ') if self.isDev else (',', ':')))
        return f
    return decorator
