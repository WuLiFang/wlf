# -*- coding=UTF-8 -*-
"""Cgtw test.
Only work when connected to server.
"""
from __future__ import absolute_import, print_function, unicode_literals

from unittest import TestCase, main


class CGTWTestCase(TestCase):
    def setUp(self):
        from wlf.cgtwq import CGTeamWork
        self.cgtw = CGTeamWork()

        self.cgtw.update_status()
        self.assert_(self.cgtw.is_logged_in)
        self.cgtw.database = 'proj_big'
        self.cgtw.module = 'shot_task'

    def test_pipeline_id(self):
        print(self.cgtw.all_pipeline)
        print(self.cgtw.get_pipeline('合成'))

    def test_get_filebox(self):
        print(self.cgtw.get_filebox('合成'))


if __name__ == '__main__':
    main()
