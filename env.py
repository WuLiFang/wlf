# -*- coding=UTF-8 -*-
"""Enviornment determinate.   """

import sys
import logging

from Qt.QtWidgets import QApplication

__version__ = '0.2.0'

LOGGER = logging.getLogger('com.wlf.env')


def has_gui():
    """Return if running in gui envrionment.  """

    return isinstance(QApplication.instance(), QApplication)


def has_nuke():
    """Return if in nuke enviornment.  """

    return bool(sys.modules.get('nuke'))


def set_default_encoding(codec='UTF-8'):
    """Set python default encoding to @codec.  """

    if sys.getdefaultencoding != codec:
        reload(sys)
        LOGGER.debug('Set default codec: %s', codec)
        sys.setdefaultencoding(codec)
