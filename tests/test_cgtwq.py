# -*- coding=UTF-8 -*-
"""Cgtw test.
Only work when connected to server.
"""
from __future__ import absolute_import, print_function, unicode_literals

from unittest import TestCase, main, skipIf
import socket
from functools import wraps

from wlf.cgtwq import CGTeamWorkClient

skip_if_no_cgtw = skipIf(not CGTeamWorkClient.is_logged_in(),
                         'CGTeamWork is not logged in.')


@skip_if_no_cgtw
class CGTWTestCase(TestCase):

    def setUp(self):
        from wlf.cgtwq import CGTeamWork
        self.cgtw = CGTeamWork()
        self.cgtw.database = 'proj_big'
        self.cgtw.module = 'shot_task'

    def test_pipeline_id(self):
        print(self.cgtw.all_pipeline)
        print(self.cgtw.get_pipeline('合成'))

    def test_get_filebox(self):
        print(self.cgtw.get_filebox('合成'))


class CGTeamWorkClientTestCase(TestCase):
    def test_status(self):
        from wlf.cgtwq import CGTeamWorkClient
        print(CGTeamWorkClient().status)

    @skip_if_no_cgtw
    def test_refresh(self):
        from wlf.cgtwq import CGTeamWorkClient
        CGTeamWorkClient.refresh('proj_big', 'shot_task')

    @skip_if_no_cgtw
    def test_refresh_selected(self):
        from wlf.cgtwq import CGTeamWorkClient
        CGTeamWorkClient.refresh_select('proj_big', 'shot_task')


if __name__ == '__main__':
    main()
