# -*- coding=UTF-8 -*-
"""Cgtw test.
Only work when connected to server.
"""
from __future__ import absolute_import, print_function, unicode_literals

import logging
import socket
from contextlib import contextmanager
from functools import wraps
from unittest import TestCase, main, skipIf

from mock import MagicMock, call

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


class FiltersTestCase(TestCase):
    def test_operations(self):
        from wlf.cgtwq import Filter, FilterList
        result = Filter('title', 'text') | Filter(
            'data', 'test') & Filter('name', 'name')
        self.assertIsInstance(result, FilterList)
        self.assertListEqual(
            result,
            [['title', '=', 'text'],
             'or', ['data', '=', 'test'],
             'and', ['name', '=', 'name']]
        )
        result |= Filter('test2', '233')
        self.assertIsInstance(result, FilterList)
        self.assertListEqual(
            result,
            [['title', '=', 'text'],
             'or', ['data', '=', 'test'],
             'and', ['name', '=', 'name'],
             'or', ['test2', '=', '233']]
        )


@skip_if_no_cgtw
class ServerTestCase(TestCase):
    def test_account(self):
        from wlf.cgtwq import server
        account = server.account()
        account_id = server.account_id()
        print('# account: <id: {}: {}>'.format(account_id, account))


@skip_if_no_cgtw
class DataBaseTestCase(TestCase):
    def test_mocked(self):
        from wlf.cgtwq.server import Response
        from wlf.cgtwq.database import Selection
        from wlf.cgtwq import Database, Filter

        module = Database('proj_big')['shot_task']
        method = MagicMock(module.call)
        module.call = method

        method.return_value = Response(
            [{"id": "1", "name": "name_value"}], 1, 'json')

        # Filter / select
        select = module.filter(Filter(' ', ' '))
        method.assert_called_once()
        module.select('1')
        module.select(['1', '2'])
        method.assert_called_once()
        self.assertIsInstance(select, Selection)

        # Getter.
        method = MagicMock(select.call)

        @contextmanager
        def _once_call():
            method.reset_mock()
            yield
            method.assert_called_once()
        select.call = method
        method.return_value = Response([{"id": "1", "shot_task.artist": "monkey"}, {
            'id': "2", "shot_task.artist": "dog"}], 1, 'json')
        with _once_call():
            result = select.get_field('artist')
        self.assertEqual(result, ('monkey', 'dog'))
        with _once_call():
            result = select['artist']
        self.assertEqual(result, ('monkey', 'dog'))

        # Setter.
        with _once_call():
            select.set_field('artist', 'Test')
        with _once_call():
            select['artist'] = 'Test'

        # Deleter
        with _once_call():
            select.delete_field('artist')
        with _once_call():
            del select['artist']

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


from wlf import mp_logging
mp_logging.basic_config(level=logging.DEBUG)
if __name__ == '__main__':
    main()
