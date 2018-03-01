# -*- coding=UTF-8 -*-
"""Test module `cgtwq.database`."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from unittest import TestCase, main

from util import skip_if_not_logged_in


@skip_if_not_logged_in
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
        print(account_name())

    def test_get_filebox(self):
        from wlf.cgtwq.database import Database, Filter
        module = Database('proj_big')['shot_task']
        select = module.filter(Filter(
            'shot.shot', 'SNJYW_EP26_01_sc026') & Filter('pipeline', '合成'))
        result = select.get_filebox('submit')
        self.assertIsInstance(result, dict)
        self.assertNotIsInstance(result['path'], dict)


if __name__ == '__main__':
    main()
