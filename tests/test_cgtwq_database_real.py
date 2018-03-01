# -*- coding=UTF-8 -*-
"""Test module `cgtwq.database`."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import uuid
from unittest import TestCase, main

from util import skip_if_not_logged_in
from wlf.cgtwq import database


@skip_if_not_logged_in
class ModuleTestCase(TestCase):
    pass


@skip_if_not_logged_in
class SelectionTestCase(TestCase):
    def setUp(self):
        Filter = database.Filter
        module = database.Database('proj_big')['shot_task']
        select = module.filter(Filter('pipeline', '合成') &
                               Filter('shot.shot', 'SNJYW_EP26_01_sc032') |
                               Filter('pipeline', '合成') &
                               Filter('shot.shot', 'SNJYW_EP26_01_sc033'))
        if not select:
            raise ValueError('No selection to test.')
        self.assertEqual(len(select), 2)
        self.select = select

    def test_get_dir(self):
        select = self.select
        result = select.get_path('comp_image')
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 2)
        self.assertRaises(ValueError,
                          select.get_filebox,
                          unicode(uuid.uuid4()))

    def test_get_filebox(self):
        select = self.select
        result = select.get_filebox('submit')
        self.assertIsInstance(result, dict)
        path = result['path']
        self.assert_(os.path.exists(path))

        # Test wrong sign.
        self.assertRaises(ValueError,
                          select.get_filebox,
                          unicode(uuid.uuid4()))


class ProjectTestCase(TestCase):
    def test_names(self):
        result = database.PROJECT.names()
        self.assertIsInstance(result, tuple)
        for i in result:
            self.assertIsInstance(i, unicode)


class AccountTestCase(TestCase):
    def test_names(self):
        result = database.ACCOUNT.names()
        self.assertIsInstance(result, tuple)
        for i in result:
            self.assertIsInstance(i, unicode)


if __name__ == '__main__':
    main()
