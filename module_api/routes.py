#!/usr/bin/env python
# -*- coding: utf-8 -*-

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


# python import

# GAE import
from webapp2_extras.routes import RedirectRoute

# local import
import handlers

_routes = [
    RedirectRoute('/api/v1/register', handler=handlers.RegisterHandlerV1, name='api-register-v1', strict_slash=True),
]


def get_routes():
    return _routes


def add_routes(app):
    for r in _routes:
        app.router.add(r)