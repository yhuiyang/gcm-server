#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python import

# GAE import
from webapp2_extras.routes import RedirectRoute

# local import
from handlers import TaskQueueGcmSender

_routes = [
    RedirectRoute(r'/taskqueue/gcm_sender', handler=TaskQueueGcmSender, name='gcm-sender', strict_slash=True),
]


def get_routes():
    return _routes


def add_routes(app):
    for r in _routes:
        app.router.add(r)
