# -*- coding=UTF-8 -*-
"""Enviornment determinate.   """

import sys


def has_gui():
    """Return if running in gui envrionment.  """

    if not has_qt():
        return False
    from Qt.QtWidgets import QApplication
    return isinstance(QApplication.instance(), QApplication)


def has_qt():
    """Return if qt availiable.  """

    try:
        from Qt.QtWidgets import QApplication
    except ImportError:
        return False
    return True


def has_nuke():
    """Return if in nuke enviornment.  """

    return bool(sys.modules.get('nuke'))
