# -*- coding=UTF-8 -*-
"""Function decorators.  """

from __future__ import print_function, unicode_literals

import logging
import time
import inspect

from functools import wraps
import threading

LOGGER = logging.getLogger('com.wlf.decorators')
assert isinstance(LOGGER, logging.Logger)

__version__ = '0.1.1'


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
