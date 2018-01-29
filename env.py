# -*- coding=UTF-8 -*-
"""Enviornment determinate.   """

import sys
import logging


LOGGER = logging.getLogger('com.wlf.env')


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


def set_default_encoding(codec='UTF-8'):
    """Set python default encoding to @codec.  """

    if sys.getdefaultencoding != codec:
        reload(sys)
        LOGGER.debug('Set default codec: %s', codec)
        sys.setdefaultencoding(codec)
