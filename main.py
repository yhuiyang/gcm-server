#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os

# GAE imports
import webapp2
from webapp2_extras.routes import RedirectRoute

# local imports
from lib.base_handler import BaseHandler


class HomeHandler(BaseHandler):
    def get(self):
        self.render_template('under_construction.html')


_debug = os.environ.get('SERVER_SOFTWARE').startswith('Dev')
_config = {}
_routes = [
    RedirectRoute(r'/', handler=HomeHandler, name='home', strict_slash=True),
    RedirectRoute(r'/admin/', name='this-will-route-to-admin-module', strict_slash=True),
]

APP = webapp2.WSGIApplication(debug=_debug, config=_config, routes=_routes)
