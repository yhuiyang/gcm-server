#!/usr/bin/env python

# python imports
import os

# GAE imports
import webapp2

# local imports
import routes


_debug = os.environ.get('SERVER_SOFTWARE').startswith('Dev')
_config = {}
_routes = []

APP = webapp2.WSGIApplication(debug=_debug, config=_config)

routes.add_routes(APP)
