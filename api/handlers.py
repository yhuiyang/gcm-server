#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python import
import logging
import json
import hashlib

# GAE import
import webapp2
from google.appengine.ext import ndb

# local import
from models import gcm_app


class RegisterHandlerV1(webapp2.RequestHandler):

    def post(self):

        # check header 'Content-Type'
        if self.request.content_type != 'application/json':
            logging.debug('bad content-type header')
            self.response.status = '400 Bad Request'
            return

        # read client information
        try:
            content = json.loads(self.request.body)
        except ValueError:
            logging.debug('bad json format')
            self.response.status = '400 Bad Request'
            return

        try:
            uuid = content['uuid']
            timestamp = content['timestamp']
            registration_id = content['registration_id']
            package = content['package']
            version = content['version']
        except KeyError:
            logging.debug('bad json data')
            self.response.status = '400 Bad Request'
            return

        # verify client information
        client_hash = self.request.headers.get('X-Hash')
        logging.debug('Client hash: %s' % client_hash)
        if client_hash is None:
            logging.debug('client does not send hash')
            self.response.status = '400 Bad Request'
            return

        h1 = hashlib.md5()
        h1.update(timestamp)
        timestamp_hash = h1.hexdigest()
        h2 = hashlib.md5()
        h2.update(timestamp_hash)
        h2.update(self.request.body)
        calculated_hash = h2.hexdigest()
        logging.debug('calculated hash: %s' % calculated_hash)

        if client_hash != calculated_hash:
            logging.debug('hash does not match')
            self.response.status = '404 Not Found'
            return

        # check gcm app exist
        app_entity = gcm_app.GcmAppModel.get_by_id(package, parent=ndb.Key(gcm_app.GcmAppModel, 'GcmApp'))
        if app_entity is None:
            logging.debug('Client register for unknown app')
            self.response.status = '404 Not Found'
            return

        # check not register before
        test_entity = gcm_app.GcmDeviceModel.get_by_id(registration_id)
        if test_entity is not None:
            logging.debug('client had registered before, ignored')
            self.response.status = '409 Conflict'
            return

        # save into data store
        entity = gcm_app.GcmDeviceModel(id=registration_id)
        entity.populate(uuid=uuid, package=package, version=version)
        entity.put()

        self.response.status = '200 OK'
