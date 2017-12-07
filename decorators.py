# -*- coding=UTF-8 -*-
"""Function decorators.  """

from __future__ import print_function, unicode_literals

import logging
import time
import inspect
import types
from functools import wraps
import threading
from multiprocessing.dummy import Queue

from wlf.Qt.QtCore import QObject, Signal, Slot
from wlf.Qt.QtWidgets import QApplication
from wlf.env import has_nuke

LOGGER = logging.getLogger('com.wlf.decorators')
assert isinstance(LOGGER, logging.Logger)

if has_nuke():
    import nuke

__version__ = '0.2.1'


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


def run_in_main_thread(func):
    """(Decorator)Run @func in nuke main_thread.   """

    if has_nuke():
        @wraps(func)
        def _func(*args, **kwargs):
            if nuke.GUI and threading.current_thread().name != 'MainThread':
                return nuke.executeInMainThreadWithResult(func, args, kwargs)
            else:
                return func(*args, **kwargs)
    else:
        @wraps(func)
        def _func(*args, **kwargs):
            runner = Runner()
            runner.moveToThread(QApplication.instance().thread())
            runner.execute.emit(func, args, kwargs)
            return runner.result.get()

    return _func


def run_with_memory_require(size=1, task=None):
    """Run func with a memory require. @size unit is GB.  """

    from wlf.notify import Progress, CancelledError
    import psutil

    assert task is None or isinstance(task, Progress)

    def _wrap(func):

        # LOGGER.debug(func.__name__)

        @wraps(func)
        def _func(*args, **kwargs):
            while psutil.virtual_memory().free < size * 1024 ** 3:
                time.sleep(1)
                if task:
                    task.set(message='等待{}G空闲内存……'.format(size))

            try:
                if task and task.is_cancelled():
                    raise CancelledError
                func(*args, **kwargs)
            except CancelledError:
                raise
            except:
                LOGGER.error(
                    'Unexpected exception during function: %s', func.__name__, exc_info=True)
                raise
            finally:
                if task:
                    task.step()

        return _func

    return _wrap
