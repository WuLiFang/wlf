# -*- coding=UTF-8 -*-
"""Test `fileutil` module.  """


from wlf import codectools


def test_get_unicode():
    assert codectools.get_unicode(1) == '1'
    assert codectools.get_unicode(b'aaaa') == 'aaaa'
    assert codectools.get_unicode(u'测试'.encode('utf-8')) == u'测试'
    assert codectools.get_unicode(u'测试'.encode('gbk')) == u'测试'
