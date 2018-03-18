# -*- coding=UTF-8 -*-
"""Module backward compatibility test.  """
from __future__ import absolute_import

from unittest import TestCase, main, skipIf
from inspect import ismodule
import six
# pylint: disable=no-member,no-name-in-module,unused-variable,import-error

@skipIf(six.PY3, 'No need backward support for python3.')
class BackwardTestCase(TestCase):
    def assert_all_in(self, namespace, names):
        for i in names:
            self.assertIn(i, namespace)

    def test_csheet(self):
        import wlf.csheet_tool
        self.assertTrue(ismodule(wlf.csheet_tool))

    def test_csheet_from(self):
        from wlf import csheet_tool
        self.assertTrue(ismodule(csheet_tool))

    def test_notify(self):
        import wlf.progress
        import wlf.message
        self.assertTrue(ismodule(wlf.progress))
        self.assertTrue(ismodule(wlf.message))

    def test_notify_from(self):
        from wlf import progress, message
        self.assertTrue(ismodule(progress))
        self.assertTrue(ismodule(message))

    def test_qt(self):
        import wlf.Qt
        self.assertTrue(ismodule(wlf.Qt))

    def test_qt_from(self):
        from wlf import Qt
        from wlf.Qt import QtCore, QtWidgets
        from wlf.Qt.QtCore import QObject
        from wlf.Qt.QtWidgets import QApplication
        self.assertTrue(ismodule(QtCore))
        self.assertTrue(ismodule(QtWidgets))

    def test_file(self):
        from wlf import files
        deprecated = (
            'url_open',
            'get_encoded', 'get_unicode', 'split_version', 'expand_frame',
            'get_footage_name', 'get_layer', 'get_server',
            'get_tag', 'remove_version', 'is_ascii', 'escape_batch',
            'traytip'
        )
        self.assert_all_in(dir(files), deprecated)

    def test_path(self):
        from wlf import path
        deprecated = (
            'expand_frame',
            'split_version', 'get_shot', 'get_tag', 'get_layer',
            'get_footage_name'
        )
        self.assert_all_in(dir(path), deprecated)

    def test_uitools(self):
        from wlf import uitools
        deprecated = (
            'has_gui',
        )
        self.assert_all_in(dir(uitools), deprecated)


if __name__ == '__main__':
    main()
