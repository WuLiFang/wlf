# -*- coding=UTF-8 -*-
"""Test package `uitools`.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

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
    uitools.Tray.information('test', 'b')
    uitools.Tray.warning('test', 'c')
    uitools.Tray.critical('test', 'd')
