#!/usr/bin/env python

##############################################################################
# Copyright 2014 YH Yang <yhuiyang@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################


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
