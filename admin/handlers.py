#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python import
import logging

# GAE import
from google.appengine.ext import ndb
from google.net.proto.ProtocolBuffer import ProtocolBufferDecodeError

# local import
from common.base_handler import BaseHandler
from models import gcm_app


class GcmDashboardHandler(BaseHandler):
    def get(self):

        params = {
            'is_dashboard': True,
            'messages': [],
            'gcm_app_list': [],
        }

        # check if alert messages exist (only one most recently for each alert type)
        for alert in ('danger', 'warning', 'info', 'success'):
            message = self.request.cookies.get('alert-' + alert)
            if message is not None:
                params['messages'].append((message, alert))

        # query gcm app list
        parent_key = ndb.Key(gcm_app.GcmAppModel, 'GcmApp')
        apps = gcm_app.GcmAppModel.query(ancestor=parent_key)
        for app in apps:
            d = dict()
            d['active'] = False
            d['name'] = app.display_name
            d['url'] = app.key.urlsafe()
            params['gcm_app_list'].append(d)

        self.render_template('gcm_dashboard.html', **params)

    def post(self):

        name = self.request.get('name')
        package = self.request.get('package')
        sender = self.request.get('sender')
        key = self.request.get('key')
        #logging.debug('name: %s, package: %s, sender: %s, key: %s' % (name, package, sender, key))

        parent_key = ndb.Key(gcm_app.GcmAppModel, 'GcmApp')

        # check if already exist
        test_key = ndb.Key(gcm_app.GcmAppModel, package, parent=parent_key)
        if test_key.get() is not None:
            self.response.set_cookie('alert-danger', u'要創建的apk套件名稱(' + package + u')已使用過，請修改套件名稱後重新創建', max_age=90)
        else:
            entity = gcm_app.GcmAppModel(id=package, parent=parent_key)
            entity.populate(display_name=name, sender_id=sender, google_api_key=key)
            entity.put()
            self.response.set_cookie('alert-success', u'成功創建GCM app: ' + name, max_age=30)

        self.redirect_to('admin-dashboard')


class GcmAppsCRUDHandler(BaseHandler):
    def get(self, urlsafe_key):

        # check if key built from urlsafe_key exists or not?
        # try:
        #     test_key = ndb.Key(urlsafe=urlsafe_key)
        #     test_entity = test_key.get()
        # except ProtocolBufferDecodeError:
        #     test_entity = None
        # if test_entity is None:
        #     self.response.status = '404 Not Found'
        #     return

        params = {
            'is_dashboard': False,
            'messages': [],
            'gcm_app_list': [],
        }

        # retrieve app configuration from given key
        try:
            given_key = ndb.Key(urlsafe=urlsafe_key)
            given_entity = given_key.get()
        except ProtocolBufferDecodeError:
            given_entity = None
        if given_entity is not None:
            params['package_name'] = given_key.id()
            params['sender_id'] = given_entity.sender_id
            params['api_key'] = given_entity.google_api_key

        # check if alert messages exist (only one most recently for each alert type)
        for alert in ('danger', 'warning', 'info', 'success'):
            message = self.request.cookies.get('alert-' + alert)
            if message is not None:
                params['messages'].append((message, alert))

        # query gcm app list
        parent_key = ndb.Key(gcm_app.GcmAppModel, 'GcmApp')
        apps = gcm_app.GcmAppModel.query(ancestor=parent_key)
        for app in apps:
            d = dict()
            d['name'] = app.display_name
            d['url'] = app.key.urlsafe()
            d['active'] = True if d['url'] == urlsafe_key else False

            params['gcm_app_list'].append(d)

        self.render_template('gcm_devices.html', **params)
