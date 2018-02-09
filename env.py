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


def has_cgtw():
    """Return if module cgtw importable.  """

    try:
        import cgtw
        if 'tw' in dir(cgtw):
            return True
    except ImportError:
        pass

    return False
