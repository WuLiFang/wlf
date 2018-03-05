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
class DataBaseTestCase(TestCase):
    def setUp(self):
        self.database = database.Database('proj_big')

    def test_get_filebox(self):
        Filter = database.Filter
        # filters.
        self.database.get_filebox(filters=Filter('title', '检查MOV'))
        # id
        self.database.get_filebox(id_='271')

    def test_get_pipline(self):
        Filter = database.Filter
        result = self.database.get_pipline(Filter('name', '合成'))
        self.assertIsInstance(result[0], database.Pipeline)

    def test_get_software(self):
        result = self.database.get_software('maya')
        self.assertIsInstance(result, unicode)

    def test_data(self):
        dummy_data = unicode(uuid.uuid4())
        key = '_test_temp'
        self.database.set_data(key, dummy_data)
        result = self.database.get_data(key)
        self.assertEqual(result, dummy_data)
        result = self.database.get_data(key, False)
        self.assertNotEqual(result, dummy_data)
        self.database.set_data(key, dummy_data, False)
        result = self.database.get_data(key, False)
        self.assertEqual(result, dummy_data)


@skip_if_not_logged_in
class ModuleTestCase(TestCase):
    def setUp(self):
        self.module = database.Database('proj_big')['shot_task']

    def test_pipeline(self):
        result = self.module.pipeline()
        for i in result:
            self.assertIsInstance(i, database.Pipeline)


@skip_if_not_logged_in
class SelectionTestCase(TestCase):
    def setUp(self):
        Filter = database.Filter
        module = database.Database('proj_big')['shot_task']
        select = module.filter(Filter('pipeline', '合成') &
                               Filter('shot.shot', ['SNJYW_EP26_01_sc032', 'SNJYW_EP26_01_sc033']))
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
        import wlf
        wlf.mp_logging.basic_config(level=10)
        select = self.select
        result = select.get_filebox('submit')
        self.assertIsInstance(result, database.FileBoxInfo)
        path = result.path
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
