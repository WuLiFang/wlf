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
        self.database.get_fileboxes(filters=Filter('title', '检查MOV'))
        # id
        self.database.get_fileboxes(id_='271')

    def test_get_pipline(self):
        Filter = database.Filter
        result = self.database.get_piplines(Filter('name', '合成'))
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
        result = self.module.pipelines()
        for i in result:
            self.assertIsInstance(i, database.Pipeline)


@skip_if_not_logged_in
class SelectionTestCase(TestCase):
    def setUp(self):
        module = database.Database('proj_big')['shot_task']
        select = module.filter(database.Filter('pipeline', '合成') &
                               database.Filter('shot.shot', ['SNJYW_EP26_06_sc349', 'SNJYW_EP26_06_sc350']))
        assert isinstance(select, database.Selection)
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

    def test_get_fields(self):
        result = self.select.get_fields('id', 'shot.shot')
        for i in result:
            self.assertEqual(len(i), 2)

    def test_get_image(self):
        result = self.select.get_fields('image')
        print(result)

    def test_get_notes(self):
        result = self.select.get_notes()
        print(result)


class TaskTestCase(TestCase):
    def test_get_note(self):
        pass


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
