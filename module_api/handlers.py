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
import logging
import json
import hashlib
import random

# GAE import
import webapp2
from google.appengine.ext import ndb
from google.appengine.ext import db

# local import
from models import gcm_app
from lib import shard


class RegisterHandlerV1(webapp2.RequestHandler):

    def post(self):

        # check header 'Content-Type' and read necessary parameters
        if self.request.content_type == 'application/json':
            try:
                content = json.loads(self.request.body)
                uuid = content['uuid']
                timestamp = content['timestamp']
                registration_id = content['registration_id']
                package = content['package']
                version = content['version']
            except KeyError as ke:
                self.set_result('Fail', 'MissingKey', 'Necessary key missed: ' + str(ke))
                return
            except ValueError as ve:
                self.set_result('Fail', 'BadJsonFormat', 'Client send bad json format: ' + str(ve))
                return
        else:
            try:
                uuid = self.request.POST['uuid']
                timestamp = self.request.POST['timestamp']
                registration_id = self.request.POST['registration_id']
                package = self.request.POST['package']
                version = self.request.POST['version']
            except KeyError as ke:
                self.set_result('Fail', 'MissingKey', 'Necessary key missed: ' + str(ke))
                return

        # verify client information
        client_hash = self.request.headers.get('X-Hash')
        if client_hash is None:
            self.set_result('Fail', 'MissingHash', 'Client does not send hash string. User-Agent: ' + self.request.user_agent)
            return

        h1 = hashlib.md5()
        try:
            h1.update(timestamp)
        except TypeError:
            h1.update(str(timestamp))
        timestamp_hash = h1.digest()  # hash data size = 128bit, 16bytes
        h2 = hashlib.md5()
        h2.update(timestamp_hash)
        h2.update(self.request.body)
        calculated_hash = h2.hexdigest()  # represented in hex-decimal format

        if client_hash.lower() != calculated_hash.lower():
            reasons = ('HashInvalid',) * 30
            reasons += ('DataCorrupted',) * 17
            reasons += ('AskAuthor',) * 2
            reasons += ('AreYouHacker',)
            self.set_result('Fail', reasons[random.randint(0, len(reasons) - 1)],
                            'Hash calculation is not matched. Client:'+client_hash+', Calculated:'+calculated_hash)
            return

        # check gcm app exist
        if not gcm_app.GcmAppModel.check_exist(package):
            self.set_result('Fail', 'UnknownApp', 'Client register for unknown app.')
            return

        # check not register before
        test_entity = gcm_app.GcmDeviceModel.get_instance(registration_id)
        if test_entity is not None:
            if not test_entity.enabled:
                enable_only = True
                logging.debug('Device registered and unregistered before, re-enable it again.')
            else:
                self.set_result('Fail', 'AlreadyRegistered', 'Client had registered before, ignore current request.')
                logging.debug('Entity: uuid[%s], package[%s], version[%d]' %
                              (test_entity.uuid, test_entity.package, test_entity.version))
                logging.debug('Request: uuid[%s], package[%s], version[%d]' % (uuid, package, int(version)))
                return
        else:
            enable_only = False

        # save into data store
        try:
            self.register_device(registration_id, package, int(version), uuid, enable_only=enable_only)
        except db.TransactionFailedError:
            self.set_result('Fail', 'RetryLater', 'Cross group transaction db write failed.')
            return

        self.set_result('OK')

    @ndb.transactional(xg=True, retries=0)
    def register_device(self, registration_id, package, version, uuid, enable_only=False):
        # create a registered device entity
        entity = gcm_app.GcmDeviceModel(id=registration_id)
        if enable_only:
            entity.enabled = True
        else:
            entity.package = package
            entity.version = version
            entity.uuid = uuid
        entity.put()

        # increase registered device count for this app package
        shard.increment(package + '_register')

    def set_result(self, result, reason=None, log_message=None):
        response = dict()
        response['result'] = result
        if reason is not None:
            response['reason'] = reason
        if log_message is not None:
            logging.debug(log_message)
        self.response.status = '200 OK'
        self.response.write(json.dumps(response))
