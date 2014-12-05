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

# GAE import
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

# local import
from models import gcm_app


# Some exceptions defined by this module

# Possible different type of errors that might occur when trying to send message to a device.
# See http://developer.android.com/google/gcm/http.html#error_codes
class MissingRegistrationIdException(Exception):
    """
    Check that the request contains a registration ID (either in the registration_id parameter in a plain text
    message, or in the registration_ids field in JSON).

    Happens when error code is MissingRegistration.
    """
    pass


class InvalidRegistrationIdException(Exception):
    """
    Check the formatting of the registration ID that you pass to the server. Make sure it matches the registration ID
    the phone receives in the com.google.android.c2dm.intent.REGISTRATION intent and that you're not truncating it or
    adding additional characters.

    Happens when error code is InvalidRegistration.
    """
    pass


class MismatchedSenderException(Exception):
    """
    A registration ID is tied to a certain group of senders. When an application registers for GCM usage, it must
    specify which senders are allowed to send messages. Make sure you're using one of those when trying to send
    messages to the device. If you switch to a different sender, the existing registration IDs won't work.

    Happens when error code is MismatchSenderId.
    """
    pass


class UnregisteredDeviceException(Exception):
    """
    An existing registration ID may cease to be valid in a number of scenarios, including:

    - If the application manually unregisters by issuing a com.google.android.c2dm.intent.UNREGISTER intent.
    - If the application is automatically unregistered, which can happen (but is not guaranteed) if the user uninstalls
      the application.
    - If the registration ID expires. Google might decide to refresh registration IDs.
    - If the application is updated but the new version does not have a broadcast receiver configured to receive
      com.google.android.c2dm.intent.RECEIVE intents.

    For all these cases, you should remove this registration ID from the 3rd-party server and stop using it to send
    messages.

    Happens when error code is NotRegistered.
    """
    pass


class MessageTooBigException(Exception):
    """
    The total size of the payload data that is included in a message can't exceed 4096 bytes. Note that this includes
    both the size of the keys as well as the values.

    Happens when error code is MessageTooBig.
    """
    pass


class InvalidDataKeyException(Exception):
    """
    The payload data contains a key (such as from or any value prefixed by google.) that is used internally by GCM in
    the com.google.android.c2dm.intent.RECEIVE Intent and cannot be used. Note that some words (such as collapse_key)
    are also used by GCM but are allowed in the payload, in which case the payload value will be overridden by the GCM
    value.

    Happens when the error code is InvalidDataKey.
    """
    pass


class InvalidTimeToLifeException(Exception):
    """
    The value for the Time to Live field must be an integer representing a duration in seconds between 0 and 2,419,200
    (4 weeks).

    Happens when error code is InvalidTtl.
    """
    pass


class AuthenticationErrorException(Exception):
    """
    The sender account that you're trying to use to send a message couldn't be authenticated. Possible causes are:

    - Authorization header missing or with invalid syntax.
    - Invalid project number sent as key.
    - Key valid but with GCM service disabled.
    - Request originated from a server not whitelisted in the Server Key IPs.

    Check that the token you're sending inside the Authorization header is the correct API key associated with your
    project.

    Happens when the HTTP status code is 401.
    """
    pass


class TimeoutException(Exception):
    """
    The server couldn't process the request in time. You should retry the same request, but you MUST obey the
    following requirements:

    - Honor the Retry-After header if it's included in the response from the GCM server.
    - Implement exponential back-off in your retry mechanism. This means an exponentially increasing delay after
     each failed retry (e.g. if you waited one second before the first retry, wait at least two second before the
    next one, then 4 seconds and so on). If you're sending multiple messages, delay each one independently by an
    additional random amount to avoid issuing a new request for all messages at the same time.

    Senders that cause problems risk being blacklisted.

    Happens when the HTTP status code is between 501 and 599, or when the error field of a JSON object in the results
    array is Unavailable.
    """
    pass


class InternalServerErrorException(Exception):
    """
    The server encountered an error while trying to process the request. You could retry the same request (obeying
    the requirements listed in the Timeout section), but if the error persists, please report the problem in the
    android-gcm group.

    Happens when the HTTP status code is 500, or when the error field of a JSON object in the results array is
    InternalServerError.
    """
    pass


class InvalidPackageNameException(Exception):
    """
    A message was addressed to a registration ID whose package name did not match the value passed in the request.

    Happens when error code is InvalidPackageName.
    """
    pass


class DeviceMessageRateExceededException(Exception):
    """
    The rate of messages to a particular device is too high. You should reduce the number of messages sent to this
    device and should not retry sending to this device immediately.

    Happens when error code is DeviceMessageRateExceeded.
    """
    pass


class GCM:

    URL = 'https://android.googleapis.com/gcm/send'
    TASK_QUEUE_NAME = 'gcm-sender'
    RETRY_INTERVAL_INITIAL = 10  # unit in second
    RETRY_INTERVAL_MAX = 300
    RETRY_MAX = 5

    def __init__(self, api_key, try_count):
        self.api_key = api_key
        self.try_count = try_count

    def send(self, registration_ids, collapse_key=None, data=None, delay_while_idle=None, time_to_live=None,
             restricted_package_name=None, dry_run=False):
        """
        Use urlfetch service on appengine to send json format request to Google GCM http connection server.

        :param registration_ids: a list or tuple containing the registration IDs of devices receiving the message. It
         must contain at least 1 and at most 1000 registration IDs. (Required)
        :param collapse_key: an arbitrary string (such as "Updates Available") that is used to collapse a group of
         like messages when the device is offline, so that only the last message gets sent to the client. This is
         intended to avoid sending too many messages to the phone when it comes back online. Note that since there is
         no guarantee of the order in which messages get sent, the "last" message may not actually be the last message
         sent by the application server. (Optional)
        :param data: a dict containing key-value pairs of the user message. There is no limit on the number of key/value
         pairs, though there is a limit on the total size of the message (4kb). It is recommended to use string for both
         keys and values, since the values will be converted to strings in the GCM server anyway. (Optional)
        :param delay_while_idle: indicates that the message should not be sent immediately if the device is idle. The
         server will wait for the device to become active, and then only the last message for each collapse_key value
         will be sent. (Optional)
        :param time_to_live: how long (in seconds) the message should be kept on GCM storage if the device is offline.
         (Optional)
        :param restricted_package_name: a string containing the package name of your application. When set, messages
         are only sent to registration IDs that match the package name. (Optional)
        :param dry_run: allows developers to test a request without actually sending a message. (Optional)
        :return: nothing
        """

        # ###########################################################################################################
        # verify parameters
        # ###########################################################################################################
        # registration_ids needs to be list or tuple, and size between 1 and 1000.
        if registration_ids is None or (not isinstance(registration_ids, list) and not isinstance(registration_ids,
                                                                                                  tuple)):
            raise TypeError('registration_ids needs to be tuple or list.')
        elif not (1 <= len(registration_ids) <= 1000):
            raise ValueError('registration_ids can only contains 1 to 1000 registration id.')

        # collapse_key needs to be str or unicode if set
        if collapse_key is not None:
            if not isinstance(collapse_key, str) and not isinstance(collapse_key, unicode):
                raise TypeError('collapse_key needs to be ordinal or unicode string.')

        # data needs to be nonempty dict if set.
        if data is not None:
            if not isinstance(data, dict):
                raise TypeError('data field needs to be python dictionary, but get %s' % type(data))
            elif not len(data):  # empty dict
                data = None

        # delay_while_idle needs to be bool if set.
        if delay_while_idle is not None:
            if not isinstance(delay_while_idle, bool):
                raise TypeError('delay_while_idle needs to be bool value, but get %s' % type(delay_while_idle))

        # time_to_list needs to be int if set, and ranges from 0 to 2419200
        if time_to_live is not None:
            if not isinstance(time_to_live, int):
                raise TypeError('time_to_life needs to be int, but get type %s' % type(time_to_live))
            elif time_to_live > 2419200 or time_to_live < 0:
                raise ValueError('time_to_life ranges from 0 to 2419200. (unit: second)')

        # restricted_package_name needs to be str or unicode if set.
        if restricted_package_name is not None:
            if not isinstance(restricted_package_name, str) and not isinstance(restricted_package_name, unicode):
                raise TypeError('restricted_package_name needs to be ordinal or unicode string.')

        # dry_run needs to be bool.
        if not isinstance(dry_run, bool):
            raise TypeError('dry_run needs to be bool value, but get %s' % type(dry_run))

        # ###########################################################################################################
        # construct request (header + body)
        # ###########################################################################################################
        gcm_headers = {
            'Content-Type': 'application/json',
            'Authorization': 'key=' + self.api_key,
        }

        gcm_body = {
            'registration_ids': registration_ids
        }
        if collapse_key:
            gcm_body['collapse_key'] = collapse_key
        if data:
            gcm_body['data'] = data
        if delay_while_idle is not None:
            gcm_body['delay_while_idle'] = delay_while_idle
        if time_to_live is not None:
            gcm_body['time_to_live'] = time_to_live
        if restricted_package_name is not None:
            gcm_body['restricted_package_name'] = restricted_package_name
        if dry_run:
            gcm_body['dry_run'] = True

        logging.debug('Headers: %s' % gcm_headers)
        logging.debug('Body: %s' % gcm_body)

        # ###########################################################################################################
        # Send request and handle response
        # ###########################################################################################################
        try:
            response = urlfetch.fetch(GCM.URL, payload=json.dumps(gcm_body), method=urlfetch.POST, headers=gcm_headers,
                                      deadline=30, follow_redirects=False, validate_certificate=True)
            if response.status_code == 200:
                # See how to interpret a success response (http://developer.android.com/google/gcm/http.html#success)
                response_dict = json.loads(response.content)
                logging.debug('response: %s' % response_dict)
                failure_count = response_dict['failure']
                canonical_ids_count = response_dict['canonical_ids']
                if failure_count or canonical_ids_count:  # do nothing if both failure and canonical_ids are 0.
                    defer_failed_registration_ids = list()
                    defer_replaced_registration_ids = list()
                    defer_disabled_registration_ids = list()
                    results_mapping_list = zip(response_dict['results'], registration_ids)
                    for results_mapping in results_mapping_list:
                        # results_mapping should look likes below tuple:
                        # ({'message_id': 'fake_message_id', 'error': 'whats wrong', 'registration_id': 'canonical_id'},
                        #  registration_id)
                        # results_mapping[0] is results dictionary
                        # results_mapping[1] is registration_id unicode string
                        # Note: all db update operations () defer out of this loop
                        if 'message_id' in results_mapping[0]:
                            if 'registration_id' in results_mapping[0]:
                                # create new device entity and make old device entity disabled.
                                defer_replaced_registration_ids.append((results_mapping[1],
                                                                        results_mapping[0]['registration_id']))
                        elif 'error' in results_mapping[0]:
                            error = results_mapping[0]['error']
                            if error == 'Unavailable':
                                defer_failed_registration_ids.append(results_mapping[1])
                            elif error == 'NotRegistered':
                                # mark this old device entity disabled.
                                defer_disabled_registration_ids.append(results_mapping[1])
                            # The following errors may be non-recoverable. See how to interpret an error response.
                            # http://developer.android.com/google/gcm/http.html#error_codes
                            elif error == 'MissingRegistration':
                                raise MissingRegistrationIdException('Miss registration id in the request.')
                            elif error == 'InvalidRegistration':
                                raise InvalidRegistrationIdException('Invalid registration id in the request.')
                            elif error == 'MismatchSenderId':
                                raise MismatchedSenderException('Sender is mismatched.')
                            elif error == 'MessageTooBig':
                                raise MessageTooBigException('Message is too big.')
                            elif error == 'InvalidDataKey':
                                raise InvalidDataKeyException('Data key is invalid. (Probably use reserved keywords)')
                            elif error == 'InvalidTtl':
                                raise InvalidTimeToLifeException('time_to_life is out of range, [0, 2419200].')
                            elif error == 'InternalServerError':
                                raise InternalServerErrorException('Internal server error.')
                                # retry
                            elif error == 'InvalidPackageName':
                                raise InvalidPackageNameException('Invalid package name.')
                            elif error == 'DeviceMessageRateExceeded':
                                raise DeviceMessageRateExceededException('Device message rate exceeded.')
                            else:
                                # TODO: probably a non-recoverable error happened,
                                logging.error('Google GCM server sends back error that we do not handle: ' + error)

                    # Run the deferred actions
                    # 1. data store operations
                    entities = list()
                    for old_registration_id, new_canonical_id in defer_replaced_registration_ids:
                        old_entity = gcm_app.GcmDeviceModel.get_instance(old_registration_id)
                        old_entity.enabled = False
                        new_entity = gcm_app.GcmDeviceModel(id=new_canonical_id)
                        new_entity.package = old_entity.package
                        new_entity.version = old_entity.version
                        new_entity.uuid = old_entity.uuid
                        entities.append(old_entity)
                        entities.append(new_entity)
                    for disable_registration_id in defer_disabled_registration_ids:
                        disabled_entity = gcm_app.GcmDeviceModel.get_instance(disable_registration_id)
                        disabled_entity.enabled = False
                        entities.append(disabled_entity)
                    ndb.put_multi(entities)

                    # 2. retry failed device
                    if len(defer_failed_registration_ids):
                        if 'Retry-After' in response.headers:
                            suggested_try_after = int(response.headers.get('Retry-After'))
                        else:
                            suggested_try_after = None
                        self.push_to_task_queue(self.api_key, defer_failed_registration_ids, self.try_count + 1,
                                                suggested_try_after=suggested_try_after, data=data,
                                                collapse_key=collapse_key, delay_while_idle=delay_while_idle,
                                                time_to_live=time_to_live,
                                                restricted_package_name=restricted_package_name, dry_run=dry_run)

            elif response.status_code == 400:
                # This indicates that the request could not be parsed as JSON, or it contained invalid fields
                # (for instance, passing a string where a number was expected). The exact failure reason is described
                # in the response content and the problem should be addressed before the request can be retried.
                logging.error(response.content)
            elif response.status_code == 401:
                raise AuthenticationErrorException('If you sure your api key is valid and sender server is whitelisted,'
                                                   ' then maybe GCM service is disable.')
            elif 500 <= response.status_code <= 599:
                # Similar to handle for 'Unavailable'.
                logging.error('Google http connection server responses status code: %d' % response.status_code)
            else:
                logging.warning('unexpected status code: %d' % response.status_code)
        except urlfetch.InvalidURLError:
            logging.error('Invalid url! This should not happen.')
        except urlfetch.ResponseTooLargeError:
            logging.error('Response is too large. Try reducing size of registration_ids.')
        except urlfetch.DeadlineExceededError:
            logging.error('Deadline exceeded! What is different with Download Error?')
        except urlfetch.DownloadError:
            logging.error('Google http connection server did not response in time.')
            # TODO retry?
        except urlfetch.SSLCertificateError:
            logging.error('SSL certificate error? change validate_certificate to False?')

    @staticmethod
    def push_to_task_queue(api_key, registration_ids, try_count, suggested_try_after=None, data=None, collapse_key=None,
                           delay_while_idle=None, time_to_live=None, restricted_package_name=None, dry_run=False):

        if not isinstance(registration_ids, tuple) and not isinstance(registration_ids, list):
            logging.error('registration_ids is expected as list or tuple type, abort to push to task queue.')
            return
        elif len(registration_ids) == 0:
            logging.error('registration_ids is emptied, abort to push to task queue.')
            return
        elif try_count > GCM.RETRY_MAX:
            logging.error('Exceeded max retries count, abort to push to task queue.')
            return
        elif suggested_try_after is not None:
            # honor suggested try after
            try_after = suggested_try_after
        else:
            try_after = 0 if try_count is 0 else GCM.RETRY_INTERVAL_INITIAL * (2 ** (try_count - 1))
            if try_after > GCM.RETRY_INTERVAL_MAX:
                try_after = GCM.RETRY_INTERVAL_MAX

        task_parameters = {
            'try_count': try_count,
            'api_key': api_key,
            'registration_ids': registration_ids
        }
        if data is not None:
            task_parameters['data'] = data
        if collapse_key is not None:
            task_parameters['collapse_key'] = collapse_key
        if delay_while_idle is not None:
            task_parameters['delay_while_idle'] = delay_while_idle
        if time_to_live is not None:
            task_parameters['time_to_live'] = time_to_live
        if restricted_package_name is not None:
            task_parameters['restricted_package_name'] = restricted_package_name
        if dry_run:
            task_parameters['dry_run'] = dry_run

        taskqueue.add(queue_name=GCM.TASK_QUEUE_NAME, url='/taskqueue/gcm_sender', params=task_parameters,
                      countdown=try_after)
