# -*- coding=UTF-8 -*-
"""Get information from CGTeamWork GUI client.  """

from __future__ import absolute_import, print_function, unicode_literals

import json
import logging
import os
import socket
from collections import namedtuple
from subprocess import Popen
from functools import partial

from websocket import create_connection

from ..decorators import deprecated
from ..env import has_cgtw

CGTeamWorkClientStatus = namedtuple(
    'CGTeamWorkClientStatus',
    ['server_ip', 'server_http', 'token'])

LOGGER = logging.getLogger('wlf.cgtwq.client')

class CGTeamWorkClient(object):
    """Query from CGTeamWork GUI clients.  """

    url = "ws://127.0.0.1:64999"
    time_out = 1

    def __init__(self):
        self.start()
        self.status = CGTeamWorkClientStatus(
            server_ip=self.server_ip(),
            server_http=self.server_http(),
            token=self.token(),
        )

    @staticmethod
    def executable():
        """Get a cgteawmwork client executable.

        Returns:
            unicode: Executable path.
        """

        # Get client executable.
        if has_cgtw():
            import cgtw
            executable = os.path.abspath(os.path.join(
                cgtw.__file__, '../../cgtw/CgTeamWork.exe'))
        else:
            # Try use default when sys.path not been set correctly.
            executable = "C:/cgteamwork/bin/cgtw/CgTeamWork.exe"

        if not os.path.exists(executable):
            executable = None
        return executable

    @classmethod
    def start(cls):
        """Start client if not running.  """

        executable = cls.executable()
        if executable and not cls.is_running():
            Popen(executable,
                  cwd=os.path.dirname(executable),
                  close_fds=True)

    @classmethod
    def is_running(cls):
        """Check if client is running.

        Returns:
            bool: Ture if client is running.
        """

        try:
            cls.token()
            return True
        except (socket.error, socket.timeout):
            pass

        return False

    @classmethod
    def is_logged_in(cls):
        """Check if client is logged in.

        Returns:
            bool: True if client is logged in.
        """

        try:
            if cls.token():
                return True
        except (socket.error, socket.timeout):
            pass

        return False

    @classmethod
    def refresh(cls, database, module):
        """
        Refresh specified view in client
        if matched view is opened.

        Args:
            database (unicode): Database of view.
            module (unicode): Module of view.
        """

        cls.call('view_control', 'refresh',
                 module=module,
                 database=database,
                 type='send')

    @classmethod
    def refresh_select(cls, database, module):
        """
        Refresh selected part of specified view in client
        if matched view is opened.

        Args:
            database (unicode): Database of view.
            module (unicode): Module of view.
        """

        cls.call(
            'view_control', 'refresh_select',
            module=module,
            database=database,
            type='send',
        )

    @classmethod
    def token(cls):
        """Client token.  """

        ret = cls.call_main_widget("get_token")
        if ret is True:
            return None
        return ret

    @classmethod
    def server_ip(cls):
        """Server ip current using by client.  """

        ret = cls.call_main_widget("get_server_ip")
        if ret is True:
            return None
        return ret

    @classmethod
    def server_http(cls):
        """Server http current using by client.  """

        ret = cls.call_main_widget("get_server_http")
        if ret is True:
            return None
        return ret

    @classmethod
    def get_plugin_data(cls, uuid):
        """Get plugin data for uuid.

        Args:
            uuid (unicode): Plugin uuid.
        """

        return cls.call_main_widget("get_plugin_data", plugin_uuid=uuid)

    @classmethod
    def send_plugin_result(cls, uuid, result=False):
        """
        Tell client plugin execution result.
        if result is `False`, following operation will been abort.

        Args:
            uuid (unicode): Plugin uuid.
            result (bool, optional): Defaults to False. Plugin execution result.
        """

        cls.call_main_widget("exec_plugin_result",
                             uuid=uuid,
                             result=result,
                             type='send')

    @classmethod
    def call_main_widget(cls, *args, **kwargs):
        """Send data to main widget.

        Args:
            **data (dict): Data to send.

        Returns:
            dict or unicode: Recived data.
        """

        method = partial(
            cls.call, "main_widget",
            module="main_widget",
            database="main_widget")

        return method(*args, **kwargs)

    @classmethod
    def call(cls, controller, method, **kwargs):
        """Call method on the cgteawork client.

        Args:
            controller: Client defined controller name.
            method (str, unicode): Client defined method name on the controller.
            **kwargs: Client defined method keyword arguments.

        Returns:
            dict or unicode: Recived data.
        """

        _kwargs = {
            'type': 'get'
        }
        _kwargs.update(kwargs)
        _kwargs['class_name'] = controller
        _kwargs['method_name'] = method

        payload = json.dumps(_kwargs, indent=4, sort_keys=True)
        conn = create_connection(cls.url, cls.time_out)

        try:
            conn.send(payload)
            LOGGER.debug('SEND: %s', payload)
            recv = conn.recv()
            LOGGER.debug('RECV: %s', recv)
            ret = json.loads(recv)
            ret = ret['data']
            try:
                ret = json.loads(ret)
            except (TypeError, ValueError):
                pass
            return ret
        finally:
            conn.close()

    @classmethod
    @deprecated('Use `call_main_widget` instead.')
    def send_main_widget(cls, *args, **kwargs):
        """Depreacted. Use `call_main_widget` instead.  """

        return cls.call_main_widget(*args, **kwargs)

    @classmethod
    @deprecated('Use `call` instead.')
    def send(cls, *args, **kwargs):
        """Depreacted. Use `call` instead.  """

        return cls.call(*args, **kwargs)
