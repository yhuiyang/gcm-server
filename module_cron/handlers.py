#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python import
import logging
from datetime import date, timedelta

# GAE import
import webapp2
from google.appengine.ext import ndb

# local import
from models import gcm_app
from lib import shard


class CronDaily0001Handler(webapp2.RequestHandler):
    def get(self):
        today = date.today()
        yesterday = today + timedelta(-1)
        logging.info('Today is: ' + str(today))

        # Calculate device register count for every gcm app daily
        apps = gcm_app.GcmAppModel.query(ancestor=ndb.Key(gcm_app.GcmAppModel, 'GcmApp'))
        for app in apps:
            app_package = app.key.string_id()
            # today count = total count - count till yesterday
            yesterday_entity = gcm_app.GcmDeviceDailyCountModel.get_by_id(app_package + '_register_' + str(yesterday))
            count_till_yesterday = 0 if yesterday_entity is None else yesterday_entity.countTillYesterday
            total_count = shard.get_count(app_package + '_register')
            today_count = total_count - count_till_yesterday

            logging.info('package: %s, total: %d, till yesterday: %d, today: %d' %
                         (app_package, total_count, count_till_yesterday, today_count))

            today_entity = gcm_app.GcmDeviceDailyCountModel(id=app_package + '_register_' + str(today))
            today_entity.count = today_count
            today_entity.countTillYesterday = total_count
            today_entity.put()