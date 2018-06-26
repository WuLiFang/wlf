# -*- coding=UTF-8 -*-
"""Nuke progress handler.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import time

import nuke  # pylint: disable=import-error

from .. import core
from ...codectools import get_encoded as e
from .base import BaseProgressHandler


class NukeProgressHandler(BaseProgressHandler):
    """Handle progress with nuke built-in func.  """

    progress_bar = None

    def is_busy(self):
        return (self.start_time != self.last_step_time
                and self.last_step_time is not None
                and time.time() - self.last_step_time < 0.1)

    def is_cancelled(self):
        return self.progress_bar.isCancelled()

    def on_started(self):
        super(NukeProgressHandler, self).on_started()
        self.progress_bar = nuke.ProgressTask(
            e(self.task_name, 'utf-8') if self.task_name else '')

    def set_message(self, message):
        self.progress_bar.setMessage(e(message, 'utf-8'))

    def set_value(self, value):
        self.progress_bar.setProgress(int(value))


core.DefaultHandler = NukeProgressHandler
