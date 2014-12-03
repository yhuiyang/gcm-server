#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python import
import logging
import json

# GAE import
import webapp2

# local import
from lib import gcm_http
from lib import parameter_helper


class TaskQueueGcmSender(webapp2.RequestHandler):
    def post(self):
        """
        Task parameters:

         Required

         - try_count: indicates how many times we've tried. 0 means first time execution, not retry, and 1 is first
           retry, 2 is second retries, and so on...
         - api_key: the access token you generate in the Google Developers Console for this project.
         - registration_ids: list of registration id of devices which you want sending message to.

         Optional

         - collapse_key:
         - delay_while_idle:
         - data:
         - time_to_live:
         - restricted_package_name:
         - dry_run:
        """

        headers = self.request.headers
        logging.debug('[TaskQueue] Header: %s' % headers)

        if 'X-Appengine-Taskretrycount' in headers and int(headers['X-Appengine-Taskretrycount']) > 0:
            self.response.status_int = 200
            logging.error('We do not retry this way. Error happens at below code, need to fix it first...')
            return

        logging.debug('[TaskQueue] task parameters: %s' % self.request.POST)
        api_key = self.request.POST.get('api_key')
        try_count = parameter_helper.to_int(self.request.POST.get('try_count'), default=0)
        registration_ids = self.request.POST.getall('registration_ids')
        collapse_key = self.request.POST.get('collapse_key')
        data = json.loads(self.request.POST.get('data', default='{}'))
        delay_while_idle = parameter_helper.to_bool(self.request.POST.get('delay_while_idle'))
        time_to_live = parameter_helper.to_int(self.request.POST.get('time_to_live'))
        restricted_package_name = self.request.POST.get('restricted_package_name')
        dry_run = parameter_helper.to_bool(self.request.POST.get('dry_run'), default=False)

        gcm = gcm_http.GCM(api_key, try_count)
        gcm.send(registration_ids, collapse_key=collapse_key, data=data, delay_while_idle=delay_while_idle,
                 time_to_live=time_to_live, restricted_package_name=restricted_package_name, dry_run=dry_run)

