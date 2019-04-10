# -*- coding=UTF-8 -*-
"""Test `ffmpeg` module.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import distutils

import pytest
import six

import util
from wlf import ffmpeg

TEST_FILES = [util.path('resource', 'gray.jpg'),
              util.path('resource', 'gray.png')]

pytestmark = [pytest.mark.skipif(not distutils.spawn.find_executable(
    'ffmpeg'), reason='ffmpeg not installed')]


def _test_method(method, tmpdir):
    for index, i in enumerate(TEST_FILES):
        path = tmpdir.join(six.text_type(index))
        result = method(i, path)
        print(result)
        assert result.exists()


def test_generate_jpg(tmpdir):
    _test_method(ffmpeg.generate_jpg, tmpdir)


def test_generate_gif(tmpdir):
    _test_method(ffmpeg.generate_gif, tmpdir)


def test_generate_mp4(tmpdir):
    _test_method(ffmpeg.generate_mp4, tmpdir)


def test_parse_div():
    method = ffmpeg.ProbeResult.parse_div

    test_case = {
        '1 / 2': 0.5,
        '1 / 3 / 2': 1 / 6
    }
    for k, v in test_case.items():
        assert method(k) == v


def test_probe():
    for i in TEST_FILES:
        ffmpeg.probe(i)
