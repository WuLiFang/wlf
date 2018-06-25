# -*- coding=UTF-8 -*-
"""Test package `progress`.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import time
from threading import Thread
from unittest import TestCase, main

from six.moves import range

from util import skip_if_no_qt
from wlf.env import HAS_QT
from wlf.progress import progress


class ProgressTestCase(TestCase):

    def test_base_handler(self):
        from wlf.progress.handlers import BaseProgressHandler
        for _ in progress(range(200), 'base测试', handler=BaseProgressHandler()):
            time.sleep(0.01)

    def test_cli_handler(self):
        from wlf.progress.handlers import CLIProgressHandler

        for _ in progress(range(200), 'cli测试', handler=CLIProgressHandler()):
            time.sleep(0.01)

    @skip_if_no_qt
    def test_qt_handler(self):
        from wlf.progress.handlers import QtProgressHandler
        from wlf.uitools import application
        application()
        for _ in progress(range(200), 'qt测试', handler=QtProgressHandler()):
            time.sleep(0.01)

    def test_async(self):
        threads = []
        threads.append(Thread(target=self.test_base_handler))
        threads.append(Thread(target=self.test_cli_handler))
        threads.append(Thread(target=self.test_qt_handler))

        def _start():
            for i in threads:
                i.start()
            for i in threads:
                i.join()

        if HAS_QT:
            from wlf.uitools import application
            application()
            _start()
        else:
            _start()


if __name__ == '__main__':
    main()
