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
from google.appengine.ext import ndb

# local import


class GcmAppModel(ndb.Model):
    """
    All entities have the same parent ndb.Key(GcmAppModel, 'GcmApp')
    Entity's key = ndb.Key(GcmAppModel, apk_package_name)
    """
    display_name = ndb.StringProperty()
    sender_id = ndb.StringProperty(indexed=False)
    google_api_key = ndb.StringProperty(indexed=False)
    timestamp = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def get_instance(cls, apk_package_name):
        return cls.get_by_id(id=apk_package_name, parent=ndb.Key(GcmAppModel, 'GcmApp'))

    @classmethod
    def check_exist(cls, apk_package_name):
        return True if GcmAppModel.get_instance(apk_package_name) else False


class GcmDeviceModel(ndb.Model):
    """
    Entity's key = ndb.Key(GcmDeviceModel, registration_id)
    Use GcmDeviceModel.get_by_id(id=<your_registration_id>) to get device entity for specific registration id
    """
    package = ndb.StringProperty()
    version = ndb.IntegerProperty()
    timestamp = ndb.DateTimeProperty(auto_now=True)
    enabled = ndb.BooleanProperty(default=True)

    # below are custom properties
    uuid = ndb.StringProperty(indexed=False)

    @classmethod
    def get_instance(cls, registration_id):
        return cls.get_by_id(id=registration_id)

    @classmethod
    def disable_device(cls, registration_id):
        entity = GcmDeviceModel.get_instance(registration_id)
        if entity:
            entity.enabled = False
            entity.put()

    @classmethod
    def enable_device(cls, registration_id):
        entity = GcmDeviceModel.get_instance(registration_id)
        if entity:
            entity.enabled = True
            entity.put()


class GcmDeviceDailyCountModel(ndb.Model):
    # Entity key = ndb.Key(GcmDeviceDailyCountModel, 'app.package.name_{register,unregister}_yyyy-mm-dd')
    count = ndb.IntegerProperty(default=0)  # count for this one day
    countTillYesterday = ndb.IntegerProperty(default=0)  # count from long time ago to yesterday
