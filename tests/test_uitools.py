# -*- coding=UTF-8 -*-
"""Test package `uitools`.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import time
from contextlib import contextmanager

import pytest

from util import qt_app, skip_ci, skip_if_no_qt

# FIXME: broken with travis


@skip_ci
@skip_if_no_qt
def test_tray():
    from wlf import uitools

    with qt_app():
        uitools.Tray.message('test', 'a')
        uitools.Tray.information('test', 'b')
        uitools.Tray.warning('test', 'c')
        uitools.Tray.critical('test', 'd')

        tray = uitools.Tray()
        tray.menu.add_command('aa', lambda: print(1))
        tray.show()
