# -*- coding=UTF-8 -*-
"""Test module `cgtwq.client`. with a mocked client.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import socket
import uuid
from unittest import TestCase, main

from mock import patch

from wlf import cgtwq


class CGTeamWorkClientTestCase(TestCase):
    def setUp(self):
        patcher = patch('wlf.cgtwq.client.CGTeamWorkClient.call')
        self.addCleanup(patcher.stop)
        self.call_method = patcher.start()

    def test_is_running(self):
        method = self.call_method
        result = cgtwq.CGTeamWorkClient.is_running()
        self.assertIsInstance(result, bool)
        method.assert_called_once_with(
            'main_widget', 'get_token',
            database='main_widget',
            module='main_widget')

    def test_is_logged_in(self):
        method = self.call_method
        result = cgtwq.CGTeamWorkClient.is_logged_in()
        self.assertIsInstance(result, bool)
        method.assert_called_once_with(
            'main_widget', 'get_token',
            database='main_widget',
            module='main_widget')

    def test_executable(self):
        method = self.call_method
        result = cgtwq.CGTeamWorkClient.executable()
        self.assertIsInstance(result, unicode)
        method.assert_not_called()

    def test_start(self):
        method = self.call_method
        cgtwq.CGTeamWorkClient.start()
        method.assert_called_once_with(
            'main_widget', 'get_token',
            database='main_widget',
            module='main_widget')

    def test_refresh(self):
        method = self.call_method
        cgtwq.CGTeamWorkClient.refresh('proj_big', 'shot_task')
        method.assert_called_once_with(
            'view_control', 'refresh',
            database='proj_big',
            module='shot_task',
            type='send')

    def test_refresh_select(self):
        method = self.call_method
        cgtwq.CGTeamWorkClient.refresh_select('proj_big', 'shot_task')
        method.assert_called_once_with(
            'view_control', 'refresh_select',
            database='proj_big',
            module='shot_task',
            type='send')

    def test_token(self):
        method = self.call_method

        # Check call args.
        cgtwq.CGTeamWorkClient.token()
        method.assert_called_once_with(
            'main_widget', 'get_token',
            database='main_widget',
            module='main_widget')

        # Logged in.
        method.return_value = uuid.uuid4()
        result = cgtwq.CGTeamWorkClient.token()
        self.assertEqual(result, method.return_value)

        # Running but not logged in.
        method.return_value = True
        result = cgtwq.CGTeamWorkClient.token()
        self.assertIs(result, None)

        # Not running.
        method.side_effect = socket.timeout
        self.assertRaises(socket.timeout, cgtwq.CGTeamWorkClient.token)

    def test_server_ip(self):
        method = self.call_method
        cgtwq.CGTeamWorkClient.server_ip()
        method.assert_called_once_with(
            'main_widget', 'get_server_ip',
            database='main_widget',
            module='main_widget')

    def test_server_http(self):
        method = self.call_method
        cgtwq.CGTeamWorkClient.server_http()
        method.assert_called_once_with(
            'main_widget', 'get_server_http',
            database='main_widget',
            module='main_widget')

    def test_plugin_data(self):
        method = self.call_method
        uuid_ = uuid.uuid4()
        cgtwq.CGTeamWorkClient.get_plugin_data(uuid_)
        method.assert_called_once_with(
            'main_widget', 'get_plugin_data',
            database='main_widget',
            module='main_widget',
            plugin_uuid=uuid_)

    def test_send_plugin_result(self):
        method = self.call_method
        uuid_ = uuid.uuid4()
        cgtwq.CGTeamWorkClient.send_plugin_result(uuid_)
        method.assert_called_once_with(
            'main_widget', 'exec_plugin_result',
            database='main_widget',
            module='main_widget',
            uuid=uuid_,
            result=False,
            type='send')


class CGTeamWorkClientLoggedInTestCase(TestCase):
    def setUp(self):
        patcher = patch('wlf.cgtwq.client.CGTeamWorkClient.token')
        self.addCleanup(patcher.stop)
        self.token_method = patcher.start()

        self.uuid = uuid.uuid4()
        self.token_method.return_value = self.uuid

    def test_is_logged_in(self):
        method = self.token_method
        result = cgtwq.CGTeamWorkClient.is_logged_in()
        self.assertIs(result, True)
        method.assert_called_once_with()

    def test_is_running(self):
        method = self.token_method
        result = cgtwq.CGTeamWorkClient.is_running()
        self.assertIs(result, True)
        method.assert_called_once_with()


class CGTeamWorkClientNotLoggedInTestCase(TestCase):
    def setUp(self):
        patcher = patch('wlf.cgtwq.client.CGTeamWorkClient.token')
        self.addCleanup(patcher.stop)
        self.token_method = patcher.start()

        self.token_method.return_value = None

    def test_is_logged_in(self):
        method = self.token_method
        result = cgtwq.CGTeamWorkClient.is_logged_in()
        self.assertIs(result, False)
        method.assert_called_once_with()

    def test_is_running(self):
        method = self.token_method
        result = cgtwq.CGTeamWorkClient.is_running()
        self.assertIs(result, True)
        method.assert_called_once_with()


class CGTeamWorkClientNotRunningTestCase(TestCase):
    def setUp(self):
        patcher = patch('wlf.cgtwq.client.CGTeamWorkClient.token')
        self.addCleanup(patcher.stop)
        self.token_method = patcher.start()

        self.token_method.side_effect = socket.timeout

    def test_is_logged_in(self):
        method = self.token_method
        result = cgtwq.CGTeamWorkClient.is_logged_in()
        self.assertIs(result, False)
        method.assert_called_once_with()

    def test_is_running(self):
        method = self.token_method
        result = cgtwq.CGTeamWorkClient.is_running()
        self.assertIs(result, False)
        method.assert_called_once_with()


if __name__ == '__main__':
    main()
