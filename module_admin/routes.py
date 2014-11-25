#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python import

# GAE import
from webapp2_extras.routes import RedirectRoute

# local import
from handlers import GcmDashboardHandler
from handlers import GcmDevicesCRUDHandler
from handlers import GcmSenderHandler

_routes = [
    RedirectRoute(r'/admin/', redirect_to_name='admin-dashboard', name='admin-base', strict_slash=True),
    RedirectRoute(r'/admin/dashboard', handler=GcmDashboardHandler, name='admin-dashboard', strict_slash=True),
    RedirectRoute(r'/admin/app/<urlsafe_key>', handler=GcmDevicesCRUDHandler, name='admin-devices-crud',
                  strict_slash=True),
    RedirectRoute(r'/taskqueue/gcm_sender', handler=GcmSenderHandler, name='gcm-sender', strict_slash=True),
]


def get_routes():
    return _routes


def add_routes(app):
    for r in _routes:
        app.router.add(r)
