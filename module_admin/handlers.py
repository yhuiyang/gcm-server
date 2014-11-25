#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python import
import logging
import json
from datetime import date, timedelta

# GAE import
import webapp2
from google.appengine.ext import ndb
from google.net.proto.ProtocolBuffer import ProtocolBufferDecodeError
from google.appengine.api import taskqueue
from google.appengine.api import urlfetch

# local import
#from ..lib import base_handler
from lib.base_handler import BaseHandler
from models import gcm_app
from lib import gviz_api
from lib import shard


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
        #
        # Need to convert the json string to unicode.
        # If we don't do this and there is Chinese character within the json string, there will be exception raised
        # when Jinja rendering its value...
        #
        params['chart_json'] = schema.ToJSon(columns_order=chart_column_order).decode('utf-8')

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


class GcmDevicesCRUDHandler(BaseHandler):
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

        # device count for registered and unregistered
        params['device_count'] = dict()
        params['device_count']['registered'] = shard.get_count(given_key.string_id() + '_register')
        params['device_count']['unregistered'] = shard.get_count(given_key.string_id() + '_unregister')

        self.render_template('gcm_devices.html', **params)

    def post(self, urlsafe_key):

        """
        Parameters:
         - message: app defined message.
                    It should be a unicode string which contains valid json object format or just an empty string.
        """

        # check user input message, if exist, it should be valid json object format
        user_message_unicode = self.request.POST.get('message')
        message_is_valid = True
        try:
            json.loads(user_message_unicode)
        except TypeError:  # typical means user_message_unicode is None, eg. client doesn't send this parameter
            logging.debug('Probably no user message exist ')
        except ValueError as e:
            if len(user_message_unicode.strip()):
                logging.debug('User provides invalid message: %s' % str(e))
                message_is_valid = False
                alert_type = 'danger'
                alert_message = u'Message 格式錯誤，請確認為正確的 JSON Object 格式: %s' % str(e)
            else:
                logging.debug('User probably leaves message empty.')
        logging.debug('User message(valid:%s): "%s"' % (message_is_valid, user_message_unicode))
        user_message = user_message_unicode.strip() if user_message_unicode is not None else None

        if message_is_valid:
            # retrieve app configuration from given key, and check if it is a valid gcm app
            try:
                app_key = ndb.Key(urlsafe=urlsafe_key)
                app_entity = app_key.get()
            except ProtocolBufferDecodeError:
                app_entity = None

            if app_entity is not None:
                api_key = app_entity.google_api_key
                q = gcm_app.GcmDeviceModel.query(gcm_app.GcmDeviceModel.package == app_entity.key.string_id())
                q = q.order(-gcm_app.GcmDeviceModel.timestamp)
                devices, cursor, more = q.fetch_page(20)
                device_count = len(devices)
                d = list()
                for device in devices:
                    d.append(device.key.string_id())
                self.send_to_google_gcm_server(api_key, devices=d, payload=user_message)

                while more:
                    devices, cursor, more = q.fetch_page(20, start_cursor=cursor)
                    device_count += len(devices)
                    d = list()
                    for device in devices:
                        d.append(device.key.string_id())
                    self.send_to_google_gcm_server(api_key, devices=d, payload=user_message)

                alert_type = 'success'
                alert_message = u'即將透過 Google GCM Server 傳送訊息至 ' + str(device_count) + u' 個 GCM 客戶端'
            else:
                alert_type = 'danger'
                alert_message = u'錯誤的gcm app(網址錯誤?)'

        if alert_type is not None and alert_message is not None:
            self.set_bootstrap_alert_message(alert_message, alert_type=alert_type)
        self.redirect_to('admin-devices-crud', urlsafe_key=urlsafe_key)

    def set_bootstrap_alert_message(self, message, alert_type='success', max_age=30):
        if alert_type not in ('success', 'info', 'warning', 'danger'):
            return
        self.response.set_cookie('alert-' + alert_type, message, max_age=max_age)

    @staticmethod
    def send_to_google_gcm_server(api_key, devices=list(), payload=None):
        """
        payload should be an unicode string which contains valid json object format data or None
        """
        # send to task queue, and then task queue send to google gcm server
        params = dict()
        params['api_key'] = api_key
        params['devices'] = devices
        if payload is not None and len(payload):
            params['payload'] = payload
        logging.debug('Parameters send to task queue: %s' % params)
        taskqueue.add(queue_name='gcm-sender', url='/taskqueue/gcm_sender', params=params)


class GcmSenderHandler(webapp2.RequestHandler):
    def post(self):

        """
        This is a handler for task queue which will send message to google gcm http connection server in json format.
        Required parameters:
         - api_key: the access token you generate in the Google Developers Console for this project.
         - devices: allow multiple values, and each value is device registration id.
         - payload: an optional parameter, if exists, it should be able to parse as JSON object format.
                    And these key/value pairs will be send to Google GCM server unmodified.
        """

        logging.debug('POST params: %s' % self.request.POST)
        # get() from UnicodeMultiDict will get None instead of raising KeyError if key doesn't exist
        api_key = self.request.POST.get('api_key')
        devices = self.request.POST.getall('devices')
        payload_unicode = self.request.POST.get('payload')

        try:
            payload = json.loads(payload_unicode)
        except TypeError:
            logging.debug('payload is not string or buffer which contains json format data')
            payload = None
        except ValueError:
            logging.debug('payload contains invalid json format')
            payload = None

        logging.debug('api key: %s' % api_key)
        logging.debug('devices: %s' % devices)
        logging.debug('payload: %s' % payload)

        gcm_url = 'https://android.googleapis.com/gcm/send'
        gcm_headers = {
            'Content-Type': 'application/json',
            'Authorization': 'key=' + api_key,
        }
        gcm_payload = {
            'registration_ids': devices
        }
        if payload is not None:
            gcm_payload['data'] = payload

        logging.debug('Sending to Google GCM Server. header: %s, payload: %s' % (gcm_headers, gcm_payload))
        response = urlfetch.fetch(gcm_url, method=urlfetch.POST, headers=gcm_headers, payload=json.dumps(gcm_payload),
                                  deadline=30)
        if response.status_code == 200:
            logging.debug('GCM Server result OK')
        else:
            logging.debug('GCM Server result: %d' % response.status_code)
        logging.debug('Content: %s' % response.content)
        logging.debug('headers: %s' % response.headers)
