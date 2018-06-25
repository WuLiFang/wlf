# -*- coding=UTF-8 -*-
"""Progress util.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
import threading
import time

from . import core
from ..codectools import get_unicode as u

LOGGER = logging.getLogger(__name__)


def progress(iterable, name=None, handler=None,
             start_message=None, oncancel=None, **handler_kwargs):
    """Progress with iterator. """

    if handler is None:
        handler = core.DefaultHandler(**handler_kwargs)
    else:
        if handler_kwargs:
            LOGGER.warning(
                '@handler already given, ignore @handler_kwargs: %s', handler_kwargs)
    if name is not None:
        handler.task_name = u(name)

    if handler.total is None:
        try:
            handler.total = len(iterable)
        except TypeError:
            pass

    finished_event = threading.Event()

    if callable(oncancel):
        def _watch():
            while not finished_event.is_set():
                time.sleep(0.2)
                if handler.is_cancelled():
                    return oncancel()

        threading.Thread(target=_watch).start()

    handler.on_started()
    try:
        if start_message is not None:
            handler.set_message(start_message)
        for i in iterable:
            handler.step(i)
            yield i
    finally:
        handler.on_finished()
        finished_event.set()
