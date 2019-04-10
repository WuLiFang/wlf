# -*- coding=UTF-8 -*-
"""Test package `progress`.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import time
from multiprocessing.dummy import Pool
from threading import Thread
from unittest import TestCase, main, skip

from six.moves import range

from util import qt_app, skip_ci, skip_if_no_qt
from wlf.env import HAS_QT
from wlf.progress import progress

pytestmark = [skip_if_no_qt, skip_ci]


def test_base_handler():
    from wlf.progress.handlers import BaseProgressHandler
    for _ in progress(range(200), 'base测试', handler=BaseProgressHandler()):
        time.sleep(0.01)


def test_cli_handler():
    from wlf.progress.handlers import CLIProgressHandler

    for _ in progress(range(200), 'cli测试', handler=CLIProgressHandler()):
        time.sleep(0.01)


def test_qt_handler():
    from wlf.progress.handlers import QtProgressHandler
    with qt_app():
        for _ in progress(range(200), 'qt测试', handler=QtProgressHandler()):
            time.sleep(0.01)


def test_async():
    threads = []
    threads.append(Thread(target=test_base_handler))
    threads.append(Thread(target=test_cli_handler))

    for i in threads:
        i.start()
    for i in threads:
        i.join()
