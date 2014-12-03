#!/usr/bin/env python
# -*- coding: utf-8 -*-


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
