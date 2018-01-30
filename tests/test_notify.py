# -*- coding=UTF-8 -*-
"""Notify module test.  """

from __future__ import absolute_import
from unittest import TestCase, main
import time


class ProgressTestCase(TestCase):

    def test_base_handler(self):
        from wlf.notify import progress, BaseProgressHandler

        for _ in progress(xrange(200), 'base测试', handler=BaseProgressHandler()):
            time.sleep(0.01)

    def test_cli_handler(self):
        from wlf.notify import progress, CLIProgressHandler

        for _ in progress(xrange(200), 'cli测试', handler=CLIProgressHandler()):
            time.sleep(0.01)

    def test_qt_handler(self):
        from wlf.notify import progress, QtProgressHandler

        for _ in progress(xrange(200), 'qt测试', handler=QtProgressHandler()):
            time.sleep(0.01)


if __name__ == '__main__':
    main()
