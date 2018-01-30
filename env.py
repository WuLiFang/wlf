# -*- coding=UTF-8 -*-
"""Enviornment determinate.   """

import sys

try:
    from Qt.QtWidgets import QApplication
    HAS_QT = True
except ImportError:
    HAS_QT = False


def has_gui():
    """Return if running in gui envrionment.  """

    return HAS_QT and isinstance(QApplication.instance(), QApplication)


def has_nuke():
    """Return if in nuke enviornment.  """

    return bool(sys.modules.get('nuke'))
