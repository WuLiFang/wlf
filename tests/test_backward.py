# -*- coding=UTF-8 -*-
"""Module backward compatibility test.  """
from __future__ import absolute_import

from unittest import TestCase, main
from inspect import ismodule


class BackwardTestCase(TestCase):

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


if __name__ == '__main__':
    main()
