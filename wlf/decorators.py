# -*- coding=UTF-8 -*-
"""Function decorators.  """

from __future__ import absolute_import, print_function, unicode_literals

import inspect
import logging
import time
import warnings
from functools import WRAPPER_ASSIGNMENTS, partial, wraps
from multiprocessing.dummy import Queue
from threading import Thread, current_thread

import six

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

    assert isinstance(name, (six.text_type, six.binary_type)),\
        'Expected str type, got {}'.format(type(name))

    def _wrap(func):
        callerframerecord = inspect.stack()[1]
        frame = callerframerecord[0]
        info = inspect.getframeinfo(frame)
        func_desc = '{0.filename}: {0.lineno}: {1}'.format(info, func.__name__)

        @wraps(func)
        def _func(*args, **kwargs):
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                cost_time = time.time() - start_time
                LOGGER.debug('%s: cost %.2f seconds',
                             func_desc, cost_time)
                if name is not None:
                    LOGGER.info('%s 耗时 %.2f 秒', name, cost_time)
        return _func
    return _wrap


if HAS_QT:
    from Qt.QtCore import QObject, QEvent, QCoreApplication
    import Qt

    class Event(QEvent):
        if Qt.IsPySide or Qt.IsPySide2:
            event_type = QEvent.Type.User
        else:
            event_type = QEvent.registerEventType()

        def __init__(self, func, args, kwargs):
            super(Event, self).__init__(self.event_type)
            self.func = func
            self.args = args
            self.kwargs = kwargs

    class Runner(QObject):
        """Runner for run in main thread.  """

        result = Queue(1)

        def event(self, event):
            if event.type() == Event.event_type:
                try:
                    self.result.put(event.func(
                        *event.args, **event.kwargs))
                    return True
                except AttributeError:
                    return False
            return super(Runner, self).event(event)


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


def renamed(old_name):
    """Return decorator for renamed callable.

    Args:
        old_name (str): This name will still accessible,
            but call it will result a warn.

    Returns:
        decorator: this will do the setting about `old_name`
            in the caller's module namespace.
    """

    def _wrap(obj):
        assert callable(obj)

        def _warn():
            warnings.warn('Renamed: {} -> {}'
                          .format(old_name, obj.__name__),
                          DeprecationWarning, stacklevel=3)

        def _wrap_with_warn(func, is_inspect):
            @wraps(func)
            def _func(*args, **kwargs):
                if is_inspect:
                    # XXX: If use another name to call,
                    # you will not get the warning.
                    frame = inspect.currentframe().f_back
                    code = inspect.getframeinfo(frame).code_context
                    if [line for line in code
                            if old_name in line]:
                        _warn()
                else:
                    _warn()
                return func(*args, **kwargs)
            return _func

        # Make old name available.
        frame = inspect.currentframe().f_back
        assert old_name not in frame.f_globals, (
            'Name already in use.', old_name)

        if inspect.isclass(obj):
            obj.__init__ = _wrap_with_warn(obj.__init__, True)
            placeholder = obj
        else:
            placeholder = _wrap_with_warn(obj, False)

        frame.f_globals[old_name] = placeholder

        return obj

    return _wrap


def deprecated(callable_or_name, reason=None):
    """Indicate this callable has been deprecated,
        when got a name, will place a placeholer with that name
        in the caller's global.

    Args:
        callable_or_name (callable, str): if got str, return a decorator,
            else return decoratored callable.
        reason (str): default to None, will be used in warning message.

    Returns:
        wrapped callable or decorator for wrap
    """

    def _wrap(callable_, name=None):
        assert callable(callable_)

        def _warn():
            msg = 'Deprecated'
            try:
                msg += ": '{}' {}".format(name or callable_.__name__,
                                          repr(callable_))
            except:  # pylint: disable=bare-except
                pass
            if reason:
                msg += ', {}'.format(reason)
            msg += '.'

            frame = inspect.currentframe()
            filename = inspect.getframeinfo(frame)[0]
            frame = frame.f_back
            stacklevel = 1

            while frame:
                stacklevel += 1
                _filename = frame.f_code.co_filename
                if _filename != filename:
                    warnings.warn(msg, DeprecationWarning,
                                  stacklevel=stacklevel)
                    break
                frame = frame.f_back

        def _wrap_with_warn(func):

            def _func(*args, **kwargs):
                _warn()
                return func(*args, **kwargs)

            # Only wrap attributes.
            assigned = (i for i in WRAPPER_ASSIGNMENTS if hasattr(func, i))
            _func = wraps(func, assigned=assigned)(_func)
            if not is_class and name:
                _func.__name__ = str(name)

            return _func

        is_class = inspect.isclass(callable_)
        if is_class:
            callable_.__init__ = _wrap_with_warn(callable_.__init__)
            ret = callable_
        else:
            ret = _wrap_with_warn(callable_)

        if name:
            frame = inspect.currentframe().f_back
            frame.f_globals[name] = ret

        return ret

    if callable(callable_or_name):
        callable_ = callable_or_name
        return _wrap(callable_)

    name = callable_or_name
    return partial(_wrap, name=name)
