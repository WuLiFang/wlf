# -*- coding=UTF-8 -*-
"""Test `mimetools` module.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from wlf import mimetools


def test_same_mimetype():
    result = mimetools.same_mimetype('.jpg', '.png')
    assert not result
    result = mimetools.same_mimetype('.jpg', '.jpeg')
    assert result
    result = mimetools.same_mimetype('.JPG', '.jpg')
    assert result
    result = mimetools.same_mimetype('.aaaaaaaaa', '.aaaaaaaaa')
    assert result
    result = mimetools.same_mimetype('.aaaAAAAAa', '.aaaaaaaaa')
    assert result


def test_is_mimetype():
    result = mimetools.is_mimetype('test.jpg', 'image')
    assert result
    result = mimetools.is_mimetype('test.JPG', 'image')
    assert result
    result = mimetools.is_mimetype('test.mp3', 'image')
    assert not result
    result = mimetools.is_mimetype('test.mp3', 'audio')
    assert result
    result = mimetools.is_mimetype('test.mov', 'video')
    assert result
    result = mimetools.is_mimetype('test.MOV', 'video')
    assert result
    result = mimetools.is_mimetype('test.txt', ('video', 'text'))
    assert result
    result = mimetools.is_mimetype('test', 'text')
    assert not result
