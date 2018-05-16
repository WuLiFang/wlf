# -*- coding=UTF-8 -*-
"""Test `path` module.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys

from wlf import path


def _test_func(func, test_case):
    for k, v in test_case.items():
        result = func(k)
        assert result == v


def test_get_unicode():
    test_case = {
        b'a': 'a',
        '测试'.encode('gbk'): '测试',
        '测试2': '测试2'
    }
    _test_func(path.get_unicode, test_case)


def test_get_encoded():
    encoding = sys.getfilesystemencoding()
    test_case = {
        'a': b'a',
        '测试'.encode('gbk'): '测试'.encode(encoding),
        '测试2': '测试2'.encode(encoding)
    }
    _test_func(path.get_encoded, test_case)
