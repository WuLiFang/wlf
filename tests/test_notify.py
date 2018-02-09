# -*- coding=UTF-8 -*-
"""Notify module test.  """

from __future__ import absolute_import

import time
from threading import Thread
from unittest import TestCase, main, skip


class ProgressTestCase(TestCase):
    @classmethod
    def async_test(cls, func):
        """Run test async.  """

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

    @skip('TODO')
    def test_async(self):
        threads = []
        threads.append(Thread(target=self.test_base_handler))
        threads.append(Thread(target=self.test_cli_handler))
        threads.append(Thread(target=self.test_qt_handler))

        for i in threads:
            i.start()
        for i in threads:
            i.join()


if __name__ == '__main__':
    main()
