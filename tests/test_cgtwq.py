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


@skip_if_no_cgtw
class CGTeamWorkClientTestCase(TestCase):
    def test_status(self):
        from wlf.cgtwq import CGTeamWorkClient
        print(CGTeamWorkClient().status)

    def test_refresh(self):
        from wlf.cgtwq import CGTeamWorkClient
        CGTeamWorkClient.refresh('proj_big', 'shot_task')

    def test_refresh_selected(self):
        from wlf.cgtwq import CGTeamWorkClient
        CGTeamWorkClient.refresh_select('proj_big', 'shot_task')


class FiltersTestCase(TestCase):
    def test_operations(self):
        from wlf.cgtwq.module import Filter, FilterList
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
        print(server.account())


if __name__ == '__main__':
    main()
