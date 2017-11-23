# -*- coding=UTF-8 -*-
"""Enviornment determinate.   """

import sys

from wlf.Qt.QtWidgets import QApplication

__version__ = '0.1.0'


def has_gui():
    """Return if running in gui envrionment.  """

    return isinstance(QApplication.instance(), QApplication)


def has_nuke():
    """Return if in nuke enviornment.  """

    return bool(sys.modules.get('nuke'))
