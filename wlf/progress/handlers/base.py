# -*- coding=UTF-8 -*-
"""Base progress handler.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import time
from datetime import timedelta

import six

from .. import core
from ...codectools import u_print


class BaseProgressHandler(object):
    """Base class for progress handler."""

    task_name = None
    start_time = None
    last_step_time = None

    def __init__(self, **handler_kwargs):
        self.count = 0
        self.total = handler_kwargs.get('total')

    def is_busy(self):
        """Return if ok to progress.  """

        return self.last_step_time is not None and time.time() - self.last_step_time < 0.2

    def is_cancelled(self):
        """"Return if progress is cancelled.  """

        return False

    def on_started(self):
        self.start_time = self.last_step_time = time.time()

    def step(self, item=None):
        """Progress one step forward.  """

        if self.is_cancelled():
            raise core.CancelledError
        if not self.is_busy():
            self.set_value(self.count * 100 / self.total)
            self.set_message(self.message_factory(item))
            self.last_step_time = time.time()
        self.count += 1

    def set_value(self, value):
        """Set progress value.  """

        pass

    def set_message(self, message):
        """Set progress message.  """

        u_print(message)

    def message_factory(self, item):
        """Get message from item.  """

        return six.text_type(item)

    def on_finished(self):
        cost_time = time.time() - self.start_time
        msg = 'Cost {}'.format(timedelta(seconds=cost_time))
        if self.task_name:
            msg = self.task_name + ': ' + msg
        self.set_message(msg)
