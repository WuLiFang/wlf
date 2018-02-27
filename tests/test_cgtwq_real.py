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


@skip_if_no_cgtw
class DataBaseTestCase(TestCase):
    def test_account(self):
        from wlf.cgtwq.database import PROJECT
        result = PROJECT.names()
        self.assertIsInstance(result, tuple)
        for i in result:
            self.assertIsInstance(i, unicode)

    def test_project(self):
        from wlf.cgtwq.database import ACCOUNT
        result = ACCOUNT.names()
        self.assertIsInstance(result, tuple)
        for i in result:
            self.assertIsInstance(i, unicode)

    def test_account_name(self):
        from wlf.cgtwq.database import account_name
        logging.debug(account_name())

    def test_get_filebox(self):
        from wlf.cgtwq.database import Database, Filter
        module = Database('proj_big')['shot_task']
        select = module.filter(Filter(
            'shot.shot', 'SNJYW_EP26_01_sc026') & Filter('pipeline', '合成'))
        result = select.get_filebox('submit')
        self.assertIsInstance(result, dict)
        self.assertNotIsInstance(result['path'], dict)


# mp_logging.basic_config(level=logging.DEBUG)
if __name__ == '__main__':
    main()
