# -*- coding=UTF-8 -*-
"""Function decorators.  """

from __future__ import absolute_import, print_function, unicode_literals

import inspect
import logging
import sys
import threading
import time
import types
from functools import wraps
from multiprocessing.dummy import Queue


from .env import has_nuke

LOGGER = logging.getLogger('com.wlf.decorators')
assert isinstance(LOGGER, logging.Logger)

if has_nuke():
    import nuke


def run_async(func):
    """Run func in thread.  """

    @wraps(func)
    def _func(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return _func


def run_with_clock(name=None):
    """Run func with a clock.  """

    assert isinstance(name, (str, unicode)),\
        'Expected str type, got {}'.format(type(name))

    def _wrap(func):
        callerframerecord = inspect.stack()[1]
        frame = callerframerecord[0]
        info = inspect.getframeinfo(frame)
        func_desc = '{0.filename}: {0.lineno}: {1}'.format(info, func.__name__)

        @wraps(func)
        def _func(*args, **kwargs):
            start_time = time.clock()
            try:
                return func(*args, **kwargs)
            finally:
                cost_time = time.clock() - start_time
                LOGGER.debug('%s: cost %.2f seconds',
                             func_desc, cost_time)
                if name is not None:
                    LOGGER.info('%s 耗时 %.2f 秒', name, cost_time)
        return _func
    return _wrap


def run_in_main_thread(func):
    """(Decorator)Run @func in nuke main_thread.   """

    from Qt.QtWidgets import QApplication
    from Qt.QtCore import QObject, Signal, Slot

    class Runner(QObject):
        """Runner for run in main thread.  """

        execute = Signal(types.FunctionType, tuple, dict)
        result = Queue(1)

        def __init__(self):

            super(Runner, self).__init__()
            self.execute.connect(self.run)

        @Slot(types.FunctionType, tuple, dict)
        def run(self, func, args, kwargs):
            """Run a function.  """

            self.result.put(func(*args, **kwargs))

    if has_nuke():
        @wraps(func)
        def _func(*args, **kwargs):
            if nuke.GUI and threading.current_thread().name != 'MainThread':
                return nuke.executeInMainThreadWithResult(func, args, kwargs)

            return func(*args, **kwargs)
    else:
        @wraps(func)
        def _func(*args, **kwargs):
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            runner = Runner()
            runner.moveToThread(app.thread())
            runner.execute.emit(func, args, kwargs)
            return runner.result.get()

    return _func


def run_with_memory_require(size=1):
    """Run func with a memory require. @size unit is GB.  """

    import psutil

    def _wrap(func):

        @wraps(func)
        def _func(*args, **kwargs):
            informed = False
            while psutil.virtual_memory().free < size * 1024 ** 3:
                if not informed:
                    LOGGER.info('等待%dG空闲内存……', size)
                    informed = True
                time.sleep(1)

            return func(*args, **kwargs)

        return _func

    return _wrap
