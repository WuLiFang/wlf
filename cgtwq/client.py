# -*- coding=UTF-8 -*-
"""Get information from CGTeamWork GUI client.  """

from __future__ import absolute_import, print_function, unicode_literals

import json
import os
import socket
from collections import namedtuple
from subprocess import Popen

from websocket import create_connection

from wlf.env import has_cgtw

CGTeamWorkClientStatus = namedtuple(
    'CGTeamWorkClientStatus',
    ['server_ip', 'server_http', 'token', 'executable'])


class CGTeamWorkClient(object):
    """Query from CGTeamWork GUI clients.  """

    url = "ws://127.0.0.1:64999"
    time_out = 1

    def __init__(self):
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

        # Start client if not running.
        if executable and not self.is_running():
            Popen(executable,
                  cwd=os.path.dirname(executable),
                  close_fds=True)

        self.status = CGTeamWorkClientStatus(
            server_ip=self.server_ip(),
            server_http=self.server_http(),
            token=self.token(),
            executable=executable
        )

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
    def get_plugin_data(cls, uuid):
        """Get plugin data for uuid.

        Args:
            uuid (unicode): Plugin uuid.
        """

        return cls.send_main_widget(method_name="get_plugin_data", plugin_uuid=uuid)

    @classmethod
    def send_plugin_result(cls, uuid, result=False):
        """
        Tell client plugin execution result.
        if result is `False`, following operation will been abort.

        Args:
            uuid (unicode): Plugin uuid.
            result (bool, optional): Defaults to False. Plugin execution result.
        """

        cls.send_main_widget(method_name="exec_plugin_result",
                             uuid=uuid,
                             result=result,
                             type='send')

    @classmethod
    def refresh(cls, database, module):
        """
        Refresh specified view in client
        if matched view is opened.

        Args:
            database (unicode): Database of view.
            module (unicode): Module of view.
        """

        cls.send(
            module=module,
            database=database,
            class_name='view_control',
            method_name='refresh',
            type='send',
        )

    @classmethod
    def refresh_select(cls, database, module):
        """
        Refresh selected part of specified view in client
        if matched view is opened.

        Args:
            database (unicode): Database of view.
            module (unicode): Module of view.
        """

        cls.send(
            module=module,
            database=database,
            class_name='view_control',
            method_name='refresh_select',
            type='send',
        )

    @classmethod
    def token(cls):
        """Client token.  """

        ret = cls.send_main_widget(method_name="get_token")
        if ret is True:
            return None
        return ret

    @classmethod
    def server_ip(cls):
        """Server ip current using by client.  """

        ret = cls.send_main_widget(method_name="get_server_ip")
        if ret is True:
            return None
        return ret

    @classmethod
    def server_http(cls):
        """Server http current using by client.  """

        ret = cls.send_main_widget(method_name="get_server_http")
        if ret is True:
            return None
        return ret

    @classmethod
    def send_main_widget(cls, **data):
        """Send data to main widget.

        Args:
            **data (dict): Data to send.

        Returns:
            dict or unicode: Recived data.
        """

        return cls.send(
            module="main_widget",
            database="main_widget",
            class_name="main_widget",
            **data)

    @classmethod
    def send(cls, **data):
        """Send data to gui progress.

        Args:
            **data (dict): Data to send.

        Returns:
            dict or unicode: Recived data.
        """

        default = {
            'type': 'get'
        }
        default.update(data)
        data = default

        conn = create_connection(cls.url, cls.time_out)

        try:
            conn.send(json.dumps(data))
            recv = conn.recv()
            ret = json.loads(recv)
            ret = ret['data']
            try:
                ret = json.loads(ret)
            except (TypeError, ValueError):
                pass
            return ret
        finally:
            conn.close()
