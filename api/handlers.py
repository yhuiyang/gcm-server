#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python import
import logging
import json
import hashlib
import random

# GAE import
import webapp2
from google.appengine.ext import ndb

# local import
from models import gcm_app


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
        app_entity = gcm_app.GcmAppModel.get_by_id(package, parent=ndb.Key(gcm_app.GcmAppModel, 'GcmApp'))
        if app_entity is None:
            self.set_result('Fail', 'UnknownApp', 'Client register for unknown app.')
            return

        # check not register before
        test_entity = gcm_app.GcmDeviceModel.get_by_id(registration_id)
        if test_entity is not None:
            self.set_result('Fail', 'AlreadyRegistered', 'Client had registered before, ignore current request.')
            logging.debug('Entity: uuid[%s], package[%s], version[%d]' %
                          (test_entity.uuid, test_entity.package, test_entity.version))
            logging.debug('Request: uuid[%s], package[%s], version[%d]' % (uuid, package, int(version)))
            return

        # save into data store
        entity = gcm_app.GcmDeviceModel(id=registration_id)
        entity.populate(uuid=uuid, package=package, version=int(version))
        entity.put()

        self.set_result('OK')

    def set_result(self, result, reason=None, log_message=None):
        response = dict()
        response['result'] = result
        if reason is not None:
            response['reason'] = reason
        if log_message is not None:
            logging.debug(log_message)
        self.response.status = '200 OK'
        self.response.write(json.dumps(response))
