#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python import

# GAE import
from google.appengine.ext import ndb

# local import


class GcmAppModel(ndb.Model):
    '''
    All entities have the same parent ndb.Key(GcmAppModel, 'GcmApp')
    Entity's key = ndb.Key(GcmAppModel, apk_package_name)
    '''
    display_name = ndb.StringProperty()
    #package_name = ndb.StringProperty()
    sender_id = ndb.StringProperty(indexed=False)
    google_api_key = ndb.StringProperty(indexed=False)
    timestamp = ndb.DateTimeProperty(auto_now=True)
