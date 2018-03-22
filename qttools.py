# -*- coding=UTF-8 -*-
"""Tools for Qt.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys
from contextlib import contextmanager

from Qt.QtWidgets import QApplication


@contextmanager
def application():
    """Yield a QApplication, create one if needed.  """
    app = QApplication.instance()

    if not app:
        app = QApplication(sys.argv)
        yield app
        app.exec_()
    else:
        yield app
