#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python import
import logging

# GAE import

# local import
from common.base_handler import BaseHandler


class GcmAppsCRUDHandler(BaseHandler):
    def get(self):
        params = {
            'app_name': 'Android GCM server',
        }
        return self.render_template('simple-sidebar.html', **params)


class GcmDevicesCRUDHandler(BaseHandler):
    def get(self):
        pass
