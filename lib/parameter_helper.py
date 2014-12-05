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


def to_bool(unicode_string, default=None):
    if unicode_string in [u'True', u'T', u'true', u't', u'Yes', u'Y', u'yes', u'y', 1]:
        return True
    elif unicode_string in [u'False', u'F', u'false', u'f', u'No', u'N', u'no', u'n', 0]:
        return False
    else:
        return default


def to_int(unicode_string, default=None):
    if isinstance(unicode_string, str) or isinstance(unicode_string, unicode):
        return int(unicode_string)
    else:
        return default
