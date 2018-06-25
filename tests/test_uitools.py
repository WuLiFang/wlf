# -*- coding=UTF-8 -*-
"""Test package `uitools`.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import time

import pytest

from wlf import uitools


@pytest.fixture(name='app')
def _app():
    app = uitools.application()
    yield app
    app.processEvents()
    app.quit()


def test_tray(app):  # pylint: disable=unused-argument
    uitools.Tray.message('test', 'a')
    time.sleep(1)
    uitools.Tray.information('test', 'b')
    time.sleep(1)
    uitools.Tray.warning('test', 'c')
    time.sleep(1)
    uitools.Tray.critical('test', 'd')
    time.sleep(1)

    tray = uitools.Tray()
    tray.menu.add_command('aa', lambda: print(1))
    tray.show()
    start = time.clock()
    while time.clock() - start < 10:
        app.processEvents()
