# -*- coding=UTF-8 -*-
"""Test module `cgtwq.database`. with a mocked environment.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from collections import namedtuple
from unittest import TestCase, main, skip

from mock import MagicMock, call, patch

from wlf import cgtwq


class DatabaseTestCase(TestCase):
    def test_getitem(self):
        database = cgtwq.Database('dummy_db')
        self.assertEqual(database.name, 'dummy_db')
        result = database['shot_task']
        self.assertIsInstance(result, cgtwq.database.Module)
        self.assertEqual(result.name, 'shot_task')


class ModuleTestCase(TestCase):
    def setUp(self):
        patcher = patch('wlf.cgtwq.server.call')
        self.addCleanup(patcher.stop)
        self.call_method = patcher.start()

        for i in (patch('wlf.cgtwq.CGTeamWorkClient.server_ip'),
                  patch('wlf.cgtwq.CGTeamWorkClient.token')):
            self.addCleanup(i.stop)
            i.start()

        self.module = cgtwq.Database('dummy_db')['shot_task']

    def test_select(self):
        module = self.module
        result = module.select('0')
        self.assertIsInstance(result, cgtwq.database.Selection)
        last = result
        result = module['0']
        self.assertIsInstance(result, cgtwq.database.Selection)
        self.assertEqual(result, last)

        self.call_method.assert_not_called()

    def test_filter(self):
        module = self.module
        method = self.call_method
        dummy_resp = cgtwq.server.Response(['0', '1'], 1, 'json')
        method.return_value = dummy_resp

        select = module.filter(cgtwq.Filter('key', 'value'))
        method.assert_called_with('c_orm', 'get_with_filter',
                                  db='dummy_db',
                                  module='shot_task',
                                  sign_array=['shot_task.id'],
                                  sign_filter_array=[['shot_task.key', '=', 'value']])
        self.assertIsInstance(select, cgtwq.database.Selection)

    @patch('wlf.cgtwq.database.Module.filter')
    @patch('wlf.cgtwq.database.Module.select')
    def test_getitem(self, select, filter_):
        assert isinstance(select, MagicMock)
        assert isinstance(filter_, MagicMock)
        module = self.module
        select.return_value = filter_.return_value = cgtwq.database.Selection([
        ], module)

        module['abc']
        select.assert_called_once_with('abc')
        filters = cgtwq.Filter('dce', 'fgh')
        module[filters]
        filter_.assert_called_once_with(filters)


class SelectionTestCase(TestCase):
    def setUp(self):
        patcher = patch('wlf.cgtwq.server.call',
                        return_value=cgtwq.server.Response('Testing', 1, 'json'))
        self.addCleanup(patcher.stop)

        self.call_method = patcher.start()
        self.select = cgtwq.database.Selection(
            ['1', '2'], cgtwq.Database('dummy_db')['shot_task'])

    def test_getter(self):
        select = self.select
        call_method = self.call_method
        call_method.return_value = cgtwq.server.Response(
            [{"id": "1", "shot_task.artist": "monkey", 'shot_task.task_name': 'banana'},
             {'id': "2", "shot_task.artist": "dog", 'shot_task.task_name': 'bone'}],
            1, 'json')

        # Test `get_fields`.
        result = select.get_fields('artist')
        self.assertIsInstance(result, cgtwq.database.FieldsData)
        self.assertEqual(result.field('artist'), ('dog', 'monkey'))
        call_method.assert_called_once_with(
            'c_orm', 'get_in_id',
            db='dummy_db', id_array=['1', '2'], module='shot_task',
            order_sign_array=['shot_task.artist'],
            sign_array=['shot_task.artist'])

        # Test `__getitem__`.
        call_method.reset_mock()
        result = select['task_name']
        self.assertEqual(result, ('banana', 'bone'))
        call_method.assert_called_once_with(
            'c_orm', 'get_in_id',
            db='dummy_db', id_array=['1', '2'], module='shot_task',
            order_sign_array=['shot_task.task_name'],
            sign_array=['shot_task.task_name'])

    def test_setter(self):
        select = self.select
        call_method = self.call_method

        # Test `set_fields`.
        select.set_fields(artist='Yuri')
        call_method.assert_called_once_with(
            'c_orm', 'set_in_id',
            db='dummy_db', id_array=['1', '2'], module='shot_task',
            sign_data_array={'shot_task.artist': 'Yuri'})

        # Test `__setitem__`.
        call_method.reset_mock()
        select['artist'] = 'Monika'
        call_method.assert_called_once_with(
            'c_orm', 'set_in_id',
            db='dummy_db', id_array=['1', '2'],
            module='shot_task',
            sign_data_array={'shot_task.artist': 'Monika'})

    def test_delete(self):
        select = self.select
        call_method = self.call_method

        select.delete()
        call_method.assert_called_once_with(
            'c_orm', 'del_in_id',
            db='dummy_db', id_array=['1', '2'],
            module='shot_task')

    def test_get_dir(self):
        select = self.select
        call_method = self.call_method

        call_method.return_value = cgtwq.server.Response(
            data={'path': 'E:/temp'}, code=1, type='json'
        )
        select.get_path('test')
        call_method.assert_called_once_with(
            'c_folder',
            'get_replace_path_in_sign',
            db='dummy_db', id_array=['1', '2'],
            module='shot_task', os=cgtwq.database._OS,
            sign_array=['test'],
            task_id_array=['1', '2'])

    def test_get_filebox(self):
        select = self.select
        call_method = self.call_method

        call_method.return_value = cgtwq.server.Response(
            data={'title': 'orange',
                  "path": "E:/test", "classify": "测试", "title": "测试box",
                  "sign": "test_fb", "color": "#005500",
                  "rule": [], "rule_view": [], "is_submit": "N",
                  "is_move_old_to_history": "",
                  "is_move_same_to_history": "Y",
                  "is_in_history_add_version": "Y",
                  "is_in_history_add_datetime": "",
                  "is_cover_disable": "",
                  "is_msg_to_first_qc": ""}, code=1, type='json'
        )
        select.get_filebox('test_fb')
        call_method.assert_called_once_with(
            'c_file',
            'filebox_get_one_with_sign',
            db='dummy_db',
            id_array=['1', '2'],
            module='shot_task',
            os=cgtwq.database._OS,
            sign='test_fb',
            task_id='1')


if __name__ == '__main__':
    main()
