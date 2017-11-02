"""Function decorators.  """

from __future__ import print_function, unicode_literals

import logging
import time
import inspect

from functools import wraps
import threading

LOGGER = logging.getLogger('com.wlf.decorators')
assert isinstance(LOGGER, logging.Logger)

__version__ = '0.1.0'


def run_async(func):
    """Run func in thread.  """

    @wraps(func)
    def _func(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return _func


def run_with_clock(func):
    """Run func with a clock.  """

    callerframerecord = inspect.stack()[1]
    frame = callerframerecord[0]
    info = inspect.getframeinfo(frame)
    func_desc = '{0.filename}:{0.lineno}:{1}'.format(info, func.__name__)

    @wraps(func)
    def _func(*args, **kwargs):
        start_time = time.clock()
        try:
            return func(*args, **kwargs)
        finally:
            LOGGER.info('%s:cost %.2f seconds',
                        func_desc, time.clock() - start_time)
    return _func
