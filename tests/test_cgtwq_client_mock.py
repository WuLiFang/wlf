# -*- coding=UTF-8 -*-
"""Test module `cgtwq.client`. with a mocked client.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import json
import os
import socket
import uuid
from functools import partial
from unittest import TestCase, main, skip

import six

from wlf import cgtwq

if six.PY3:
    from unittest.mock import patch  # pylint: disable=import-error,no-name-in-module
else:
    from mock import patch


# Same argument with json.dumps used in `CGTeamWorkClient.call`.
dumps = partial(json.dumps, sort_keys=True, indent=4)


def server_dumps(code, data):
    """CGTeamwork server dumps json in this style.  """

    return dumps({'code': six.text_type(code), 'data': data})


class CGTeamWorkClientTestCase(TestCase):
    def setUp(self):
        patcher = patch('wlf.cgtwq.client.create_connection')
        self.addCleanup(patcher.stop)
        self.create_connection = patcher.start()
        self.conn = self.create_connection.return_value

    def test_is_running(self):
        conn = self.conn

        # Logged in.
        conn.recv.return_value = server_dumps(1, six.text_type(uuid.uuid4()))
        result = cgtwq.CGTeamWorkClient.is_running()
        self.assertIs(result, True)
        conn.send.assert_called_once_with(
            dumps({
                'class_name': 'main_widget',
                'method_name': 'get_token',
                'database': 'main_widget',
                'module': 'main_widget',
                'type': 'get'}
            )
        )

        # Running but not logged in.
        conn.recv.return_value = server_dumps(1, True)
        result = cgtwq.CGTeamWorkClient.is_running()
        self.assertIs(result, True)

        # Not running.
        conn.recv.side_effect = socket.timeout
        result = cgtwq.CGTeamWorkClient.is_running()
        self.assertIs(result, False)

    def test_is_logged_in(self):
        conn = self.conn

        # Logged in.
        conn.recv.return_value = server_dumps(
            1, six.text_type(uuid.uuid4()))
        result = cgtwq.CGTeamWorkClient.is_logged_in()
        self.assertIs(result, True)
        conn.send.assert_called_once_with(
            dumps({
                'class_name': 'main_widget',
                'method_name': 'get_token',
                'database': 'main_widget',
                'module': 'main_widget',
                'type': 'get'}
            )
        )

        # Running but not logged in.
        conn.recv.return_value = server_dumps(1, True)
        result = cgtwq.CGTeamWorkClient.is_logged_in()
        self.assertIs(result, False)

        # Not running.
        conn.recv.side_effect = socket.timeout
        result = cgtwq.CGTeamWorkClient.is_logged_in()
        self.assertIs(result, False)

    def test_executable(self):
        result = cgtwq.CGTeamWorkClient.executable()
        if result is not None:
            self.assertIsInstance(result, (six.text_type))
        self.conn.assert_not_called()

    def test_start(self):
        conn = self.conn
        conn.recv.return_value = server_dumps(1, True)
        cgtwq.CGTeamWorkClient.start()
        if cgtwq.CGTeamWorkClient.executable():
            self.conn.send.assert_called_once()

    def test_refresh(self):
        conn = self.conn
        conn.recv.return_value = server_dumps(1, True)
        cgtwq.CGTeamWorkClient.refresh('proj_big', 'shot_task')
        conn.send.assert_called_once_with(
            dumps({
                'class_name': 'view_control',
                'method_name': 'refresh',
                'database': 'proj_big',
                'module': 'shot_task',
                'type': 'send'}
            )
        )

    def test_refresh_select(self):
        conn = self.conn
        conn.recv.return_value = server_dumps(1, True)
        cgtwq.CGTeamWorkClient.refresh_select('proj_big', 'shot_task')
        conn.send.assert_called_once_with(
            dumps({
                'class_name': 'view_control',
                'method_name': 'refresh_select',
                'database': 'proj_big',
                'module': 'shot_task',
                'type': 'send'}
            )
        )

    def test_token(self):
        conn = self.conn
        uuid_ = six.text_type(uuid.uuid4())
        conn.recv.return_value = server_dumps(1, uuid_)

        # pylint: disable=protected-access
        # Logged in.
        cgtwq.CGTeamWorkClient._token()
        conn.send.assert_called_once_with(
            dumps({
                'class_name': 'main_widget',
                'method_name': 'get_token',
                'database': 'main_widget',
                'module': 'main_widget',
                'type': 'get'})
        )

        result = cgtwq.CGTeamWorkClient._token()
        self.assertEqual(result, uuid_)

        # Running but not logged in.
        conn.recv.return_value = server_dumps(1, True)
        result = cgtwq.CGTeamWorkClient._token()
        self.assertEqual(result, '')

        # Not running.
        self.create_connection.side_effect = socket.timeout
        self.assertRaises(socket.timeout, cgtwq.CGTeamWorkClient._token)

    def test_server_ip(self):
        # pylint: disable=protected-access
        dummy_ip = '192.168.55.55'
        conn = self.conn
        conn.recv.return_value = server_dumps(1, dummy_ip)
        result = cgtwq.CGTeamWorkClient._server_ip()
        conn.send.assert_called_once_with(
            dumps(
                {
                    'class_name': 'main_widget',
                    'method_name': 'get_server_ip',
                    'database': 'main_widget',
                    'module': 'main_widget',
                    'type': 'get'
                }
            )
        )
        self.assertEqual(result, dummy_ip)

    def test_server_http(self):
        dummy_http = '192.168.55.55'
        conn = self.conn
        conn.recv.return_value = server_dumps(1, dummy_http)
        result = cgtwq.CGTeamWorkClient.server_http()
        conn.send.assert_called_once_with(
            dumps(
                {
                    'class_name': 'main_widget',
                    'method_name': 'get_server_http',
                    'database': 'main_widget',
                    'module': 'main_widget',
                    'type': 'get'
                }
            )
        )
        self.assertEqual(result, dummy_http)

    def test_plugin_data(self):
        dummy_data = {'id_list': ['1', '2']}
        uuid_ = six.text_type(uuid.uuid4())
        conn = self.conn
        json.loads
        conn.recv.return_value = server_dumps(1, dummy_data)
        result = cgtwq.CGTeamWorkClient.get_plugin_data(uuid_)
        self.assertEqual(result,
                         cgtwq.client.PluginData(
                             plugin_id=None, filebox_id=None, database=None,
                             module=None, id_list=['1', '2'], folder=None,
                             file_path_list=None, argv=None))
        conn.send.assert_called_once_with(
            dumps(
                {
                    'class_name': 'main_widget',
                    'method_name': 'get_plugin_data',
                    'database': 'main_widget',
                    'module': 'main_widget',
                    'type': 'get',
                    'plugin_uuid': uuid_,
                }
            )
        )

    def test_send_plugin_result(self):
        uuid_ = six.text_type(uuid.uuid4())
        conn = self.conn

        conn.recv.return_value = server_dumps(1, True)
        cgtwq.CGTeamWorkClient.send_plugin_result(uuid_)
        conn.send.assert_called_once_with(
            dumps(
                {
                    "method_name": "exec_plugin_result",
                    "result": False,
                    "database": "main_widget",
                    "class_name": "main_widget",
                    "type": "send",
                    "module": "main_widget",
                    "uuid": uuid_
                }
            )
        )


if __name__ == '__main__':
    main()
