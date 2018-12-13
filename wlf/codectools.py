# -*- coding=UTF-8 -*-
"""Common utilities.   """

from __future__ import print_function, unicode_literals

import locale
import os
import sys

import six
from six import text_type


def u_print(msg, **kwargs):
    """`print` with encoded unicode.

    `print` unicode may cause UnicodeEncodeError
    or non-readable result when `PYTHONIOENCODING` is not set.
    this will fix it.

    Arguments:
        msg (unicode): Message to print.
        **kwargs: Keyword argument for `print` function.
    """

    if isinstance(msg, text_type):
        encoding = None
        try:
            encoding = os.getenv('PYTHONIOENCODING', sys.stdout.encoding)
        except AttributeError:
            # `sys.stdout.encoding` may not exists.
            pass
        msg = msg.encode(encoding or 'utf-8', 'replace')
    print(msg, **kwargs)


def get_unicode(input_bytes, codecs=('UTF-8', 'GBK')):
    """Return unicode string by try decode @input_bytes with @codecs.  """

    if isinstance(input_bytes, (six.text_type, int)):
        return six.text_type(input_bytes)

    try:
        input_bytes = six.binary_type(input_bytes)
    except TypeError:
        return six.text_type(input_bytes)

    try:
        return input_bytes.decode()
    except UnicodeDecodeError as ex:
        for i in tuple(codecs) + (sys.getfilesystemencoding(), locale.getdefaultlocale()[1]):
            try:
                return six.text_type(input_bytes, i)
            except UnicodeDecodeError:
                continue
        raise ex


def get_encoded(input_str, encoding=None):
    """Return unicode by try decode @string with @encodeing.  """

    return get_unicode(input_str).encode(encoding or sys.getfilesystemencoding())


def is_ascii(text):
    """Return true if @text can be convert to ascii.

    >>> is_ascii('a')
    True
    >>> is_ascii('测试')
    False

    """
    try:
        get_unicode(text).encode('ASCII')
        return True
    except UnicodeEncodeError:
        return False
