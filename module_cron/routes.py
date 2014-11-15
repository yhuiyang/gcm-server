#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python import

# GAE import
from webapp2_extras.routes import RedirectRoute

# local import
import handlers

_routes = [
    RedirectRoute('/cron/daily_0001', handler=handlers.CronDaily0001Handler, name='cron-daily-0001', strict_slash=True),
]


def get_routes():
    return _routes


def add_routes(app):
    for r in _routes:
        app.router.add(r)