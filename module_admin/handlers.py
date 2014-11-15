#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python import
import logging
from datetime import date, timedelta

# GAE import
from google.appengine.ext import ndb
from google.net.proto.ProtocolBuffer import ProtocolBufferDecodeError

# local import
#from ..lib import base_handler
from lib.base_handler import BaseHandler
from models import gcm_app
from lib import gviz_api


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

        # init chart data
        chart_column = {'date': ('date', 'Register date')}
        chart_column_order = ('date',)  # final is ('date', 'app1', 'app2', ... 'appN')
        chart_data = list()  # final is [{'date': date1, 'app1': x, 'app2': y, ..., 'appN': K}{'date': date2, ...}]
        recently_day_list = range(-6, 1)
        for day in recently_day_list:
            d = dict()
            d['date'] = date.today() + timedelta(day)
            chart_data.append(d)

        # query gcm app list
        parent_key = ndb.Key(gcm_app.GcmAppModel, 'GcmApp')
        apps = gcm_app.GcmAppModel.query(ancestor=parent_key)
        for idx, app in enumerate(apps, start=1):
            # prepare data used by sidebar in template file
            d = dict()
            d['active'] = False
            d['name'] = app.display_name
            d['url'] = app.key.urlsafe()
            params['gcm_app_list'].append(d)

            # prepare data used by dashboard chart
            chart_column['app' + str(idx)] = ('number', app.display_name)
            chart_column_order += ('app' + str(idx),)
            for day_idx in range(len(recently_day_list)):
                this_day = chart_data[day_idx]['date']
                cnt_ent = gcm_app.GcmDeviceDailyCountModel.get_by_id(app.key.string_id() + '_register_' + str(this_day))
                chart_data[day_idx]['app' + str(idx)] = cnt_ent.count if cnt_ent is not None else 0

        schema = gviz_api.DataTable(chart_column)
        schema.LoadData(chart_data)
        params['chart_json'] = schema.ToJSon(columns_order=chart_column_order)

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
            'devices': [],
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

        # query gcm device list for this app
        devices = gcm_app.GcmDeviceModel.query(gcm_app.GcmDeviceModel.package == params['package_name'])
        devices = devices.order(-gcm_app.GcmDeviceModel.timestamp)
        devices = devices.fetch(100)
        l = list()
        for device in devices:
            d = dict()
            d['uuid'] = device.uuid
            d['package'] = device.package
            d['version'] = device.version
            d['timestamp'] = device.timestamp
            d['registration_id'] = device.key.id()
            l.append(d)
        params['devices'] = l

        self.render_template('gcm_devices.html', **params)
