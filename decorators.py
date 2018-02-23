# -*- coding=UTF-8 -*-
"""Function decorators.  """

from __future__ import absolute_import, print_function, unicode_literals

import inspect
import logging
import time
from functools import wraps
from multiprocessing.dummy import Queue
from threading import Thread, current_thread

from .env import HAS_QT, has_nuke

try:
    from gevent.lock import Semaphore
except ImportError:
    from threading import Semaphore


LOGGER = logging.getLogger('com.wlf.decorators')
assert isinstance(LOGGER, logging.Logger)


def run_async(func):
    """Run func in thread.  """

    @wraps(func)
    def _func(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
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

    if has_nuke():
        import nuke  # pylint: disable=import-error

        @wraps(func)
        def _func(*args, **kwargs):
            if nuke.GUI and current_thread().name != 'MainThread':
                return nuke.executeInMainThreadWithResult(func, args, kwargs)

            return func(*args, **kwargs)

    elif HAS_QT:
        from Qt.QtCore import QObject, QEvent, QCoreApplication

        class Event(QEvent):

            def __init__(self, func, args, kwargs):
                super(Event, self).__init__(QEvent.Type.User)
                self.func = func
                self.args = args
                self.kwargs = kwargs

        class Runner(QObject):
            """Runner for run in main thread.  """

            result = Queue(1)

            def event(self, event):
                if event.type() == QEvent.Type.User:
                    try:
                        self.result.put(event.func(
                            *event.args, **event.kwargs))
                        return True
                    except AttributeError:
                        return False
                return super(Runner, self).event(event)

        @wraps(func)
        def _func(*args, **kwargs):
            app = QCoreApplication.instance()
            if app is None:
                return func(*args, **kwargs)

            runner = Runner()
            try:
                runner.moveToThread(app.thread())
                app.notify(runner, Event(func, args, kwargs))
                return runner.result.get()
            finally:
                runner.deleteLater()

    else:
        _func = func

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


def run_with_semaphore(value):
    """Run with a semaphore lock.

    Args:
        value (int): Semaphore value.

    Returns:
        function: function warpper.
    """

    def _wrap(func):
        _lock = Semaphore(value)

        @wraps(func)
        def _func(*args, **kwargs):
            with _lock:
                return func(*args, **kwargs)

        _func.lock = _lock

        return _func

    return _wrap
