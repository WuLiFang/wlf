# -*- coding=UTF-8 -*-
"""Qt progress handler.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from Qt import QtCompat, QtWidgets
from Qt.QtCore import Qt, Signal

from .. import core
from ...codectools import get_unicode as u
from ...decorators import run_in_main_thread
from ...pathtools import module_path
from .base import BaseProgressHandler


class QtProgressBar(QtWidgets.QDialog):
    """Qt progressbar dialog."""

    value_changed = Signal(int)
    message_changed = Signal(str)
    default_parent = None

    def __init__(self, parent=None):
        if parent is None:
            parent = self.default_parent
        self._cancelled = False

        super(QtProgressBar, self).__init__(parent)
        QtCompat.loadUi(module_path('assets', 'progress.ui'), self)
        if parent:
            geo = self.geometry()
            geo.moveCenter(parent.geometry().center())
            self.setGeometry(geo)

        self.setAttribute(Qt.WA_QuitOnClose, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.value_changed.connect(self.on_value_changed)
        self.message_changed.connect(self.on_message_changed)

    def on_value_changed(self, value):
        self.progressBar.setValue(value)

    def on_message_changed(self, message):
        self.setWindowTitle(message)

    def isCancelled(self):
        """Return if cancel button been pressed.  """
        return self._cancelled

    def reject(self):
        """Override QDiloag.reject()"""

        self._cancelled = True


class QtProgressHandler(BaseProgressHandler):
    """Qt progress handler."""

    def __init__(self, **handler_kwargs):
        super(QtProgressHandler, self).__init__(**handler_kwargs)

        self.progress_bar = QtProgressBar(handler_kwargs.get('parent'))

    def is_busy(self):
        return False

    @run_in_main_thread
    def on_started(self):
        super(QtProgressHandler, self).on_started()
        self.progress_bar.show()

    def set_message(self, message):
        self.progress_bar.message_changed.emit(message)

    def set_value(self, value):
        self.progress_bar.value_changed.emit(value)

    def is_cancelled(self):
        return self.progress_bar.isCancelled()

    def step(self, item=None):
        super(QtProgressHandler, self).step(item)
        QtWidgets.QApplication.processEvents()

    def message_factory(self, item):

        ret = '[{}/{}]'.format(self.count, self.total)
        if item is not None:
            ret += u(item)

        if self.task_name:
            ret = self.task_name + ': ' + ret
        return ret

    @run_in_main_thread
    def on_finished(self):
        super(QtProgressHandler, self).on_finished()
        self.progress_bar.accept()
        self.progress_bar.close()
        self.progress_bar = None


core.DefaultHandler = QtProgressHandler
