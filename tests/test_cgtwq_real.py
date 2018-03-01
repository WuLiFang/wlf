# -*- coding=UTF-8 -*-
"""Cgtw test.
Only work when connected to server.
"""
from __future__ import absolute_import, print_function, unicode_literals

import logging
from unittest import TestCase, main, skipIf

from wlf import mp_logging
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
        self.cgtw.all_pipeline
        self.cgtw.get_pipeline('合成')

    def test_get_filebox(self):
        self.cgtw.get_filebox('合成')


@skip_if_no_cgtw
class CGTeamWorkClientTestCase(TestCase):
    def test_status(self):
        from wlf.cgtwq import CGTeamWorkClient
        CGTeamWorkClient().status

    def test_refresh(self):
        from wlf.cgtwq import CGTeamWorkClient
        CGTeamWorkClient.refresh('proj_big', 'shot_task')

    def test_refresh_selected(self):
        from wlf.cgtwq import CGTeamWorkClient
        CGTeamWorkClient.refresh_select('proj_big', 'shot_task')


@skip_if_no_cgtw
class ServerTestCase(TestCase):
    def test_account(self):
        from wlf.cgtwq import server
        account = server.account()
        account_id = server.account_id()
        print('# account: <id: {}: {}>'.format(account_id, account))


# mp_logging.basic_config(level=logging.DEBUG)
if __name__ == '__main__':
    main()
