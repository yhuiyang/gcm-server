#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python import
import logging

# GAE import
from webapp2_extras.routes import RedirectRoute

# local import
import handlers

_routes = [
    RedirectRoute(r'/admin/', redirect_to_name='admin-apps-crud', name='admin-dashboard', strict_slash=True),
    RedirectRoute(r'/admin/apps', handler=handlers.GcmAppsCRUDHandler, name='admin-apps-crud', strict_slash=True),
    RedirectRoute(r'/admin/app/<pkg_name:[a-zA-Z.]*>', handler=handlers.GcmDevicesCRUDHandler, name='admin-devices-crud', strict_slash=True),
]


def get_routes():
    return _routes


def add_routes(app):
    for r in _routes:
        app.router.add(r)
