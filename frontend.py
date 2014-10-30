#!/usr/bin/env python

# python imports
import os

# GAE imports
import webapp2

# local imports
from admin import routes as admin_routes
from api import routes as api_routes


_debug = os.environ.get('SERVER_SOFTWARE').startswith('Dev')
_config = {}
_routes = []

APP = webapp2.WSGIApplication(debug=_debug, config=_config)

admin_routes.add_routes(APP)
api_routes.add_routes(APP)