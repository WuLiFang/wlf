# -*- coding=UTF-8 -*-
"""Test utilities.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import time
from contextlib import contextmanager

import pytest

from wlf.env import HAS_QT

skip_if_no_qt = pytest.mark.skipif(  # pylint: disable=invalid-name
    not HAS_QT, reason='Qt not installed')

ROOT = os.path.abspath(os.path.dirname(__file__))
skip_ci = pytest.mark.skipif(  # pylint: disable=invalid-name
    os.getenv('CI') == 'true',  reason='skip ci')


def path(*other):
    """Get resource path.

    Returns:
        six.text_type: Joined absolute path.
    """

    return os.path.abspath(os.path.join(ROOT, *other))


@contextmanager
def qt_app(delay=0):
    if not HAS_QT:
        yield
        return

    from wlf import uitools
    app = uitools.application()
    yield app
    finished = time.time()
    while time.time() - finished < delay:
        app.processEvents()
    app.quit()
