# -*- coding=UTF-8 -*-
"""Test module `cgtwq.server`. with a mocked environment.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from collections import namedtuple
from unittest import TestCase, main, skip

from mock import MagicMock, call, patch
import json
from wlf.cgtwq import server


class ServerTestCase(TestCase):
    def setUp(self):
        patcher = patch('requests.post')
        self.addCleanup(patcher.stop)
        self.post = patcher.start().return_value

        for i in (patch('wlf.cgtwq.CGTeamWorkClient.server_ip', return_value='127.0.0.1'),
                  patch('wlf.cgtwq.CGTeamWorkClient.token', return_value='test_token')):
            self.addCleanup(i.stop)
            i.start()

    def test_upload(self):
        self.post.content.return_value = {'file_pos': 0, 'is_exist': False}
        server.upload(
            'E:/test.txt', '/upload/image/test_asda180301sdasd.txt')
