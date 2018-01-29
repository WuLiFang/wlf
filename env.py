# -*- coding=UTF-8 -*-
"""Enviornment determinate.   """

import sys


def has_gui():
    """Return if running in gui envrionment.  """

    try:
        from Qt.QtWidgets import QApplication
    except ImportError:
        return False

    return isinstance(QApplication.instance(), QApplication)


def has_nuke():
    """Return if in nuke enviornment.  """

    return bool(sys.modules.get('nuke'))
