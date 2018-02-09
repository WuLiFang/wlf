# -*- coding=UTF-8 -*-
"""Patch the `cgtw` module.  """

from __future__ import absolute_import, print_function, unicode_literals

import logging
import traceback
from functools import wraps

import cgtw
from ..path import get_unicode as u
from .exceptions import LoginError
from .client import CGTeamWorkClient

LOGGER = logging.getLogger('com.wlf.cgtwq.patches')


def patch_tw_message():
    """Change tw message format.  """

    func = cgtw.tw.sys.message_error

    @wraps(func)
    def _func(self, msg, title='Error'):  # pylint: disable=unused-argument
        stack = b'\n'.join(traceback.format_stack()[:-1])
        stack = u(stack)
        LOGGER.error('[%s]%s\n%s', title, msg, stack)

    cgtw.tw.sys.message_error = _func


def patch_tw_lib():
    """Raise LoginError if not loged in.  """

    func = cgtw.tw.lib.format_data

    @wraps(func)
    def _func(data, sign):
        if data == 'please login!!!':
            raise LoginError(data, sign)
        return func(data, sign)

    cgtw.tw.lib.format_data = staticmethod(_func)


def patch_tw_local_con():
    """Reimplement websocket send.  """

    # pylint: disable=protected-access
    @staticmethod
    def _send(T_module, T_database, T_class_name, T_method_name, T_data, T_type="get"):
        """Wrapped function for cgtw path.  """
        # pylint: disable=invalid-name, too-many-arguments, bare-except
        try:
            return CGTeamWorkClient.send(
                module=T_module,
                database=T_database,
                class_name=T_class_name,
                method_name=T_method_name,
                type=T_type,
                **T_data
            )
        except:
            return False

    cgtw.tw.local_con._send = _send