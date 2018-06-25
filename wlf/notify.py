# -*- coding=UTF-8 -*-
"""Show notify to user.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
import multiprocessing
import os
import sys
import threading
import time
from datetime import timedelta

from six import PY2, text_type

from . import util
from .decorators import run_in_main_thread
from .env import HAS_QT, has_gui, has_nuke
from .pathtools import module_path
from .path import get_encoded, get_unicode

HAS_NUKE = has_nuke()
LOGGER = logging.getLogger('com.wlf.notify')


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
            raise CancelledError
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

        util.u_print(message)

    def message_factory(self, item):
        """Get message from item.  """

        return text_type(item)

    def on_finished(self):
        cost_time = time.time() - self.start_time
        msg = 'Cost {}'.format(timedelta(seconds=cost_time))
        if self.task_name:
            msg = self.task_name + ': ' + msg
        self.set_message(msg)


class CLIProgressHandler(BaseProgressHandler):
    """Command line progress bar.

    reference with: https://github.com/noamraph/tqdm
    """

    def __init__(self, **handler_kwargs):
        super(CLIProgressHandler, self).__init__(**handler_kwargs)
        self.file = handler_kwargs.get('file', sys.stdout)
        self.last_printed_len = 0

    def set_message(self, message):
        message = get_unicode(message)
        encoding = sys.getfilesystemencoding()
        try:
            encoding = self.file.encoding or encoding
        except AttributeError:
            pass
        msg_len = len(message.encode(encoding))
        msg = ('\r' + message
               + ' ' * max(self.last_printed_len - msg_len, 0))

        if PY2:
            msg = msg.encode(encoding, 'replace')
        self.file.write(msg)
        self.file.flush()
        self.last_printed_len = msg_len

    def message_factory(self, item):
        return '[{}/{}]{}%{}'.format(self.count, self.total, self.count * 100 / self.total, item)


if HAS_QT:
    from Qt import QtCompat, QtWidgets
    from Qt.QtCore import Signal, Qt

    class QtProgressBar(QtWidgets.QDialog):
        """Qt progressbar dialog."""

        value_changed = Signal(int)
        message_changed = Signal(str)
        default_parent = None

        # @run_in_main_thread
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
                ret += get_unicode(item)

            if self.task_name:
                ret = self.task_name + ': ' + ret
            return ret

        @run_in_main_thread
        def on_finished(self):
            super(QtProgressHandler, self).on_finished()
            self.progress_bar.accept()
            self.progress_bar.close()
            self.progress_bar = None


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
        self.progress_bar = __import__('nuke').ProgressTask(
            get_encoded(self.task_name, 'utf-8') if self.task_name else '')

    def set_message(self, message):
        self.progress_bar.setMessage(get_encoded(message, 'utf-8'))

    def set_value(self, value):
        self.progress_bar.setProgress(value)


def get_default_progress_handler(**handler_kwargs):
    """Get default progress handler depends on current environment.  """

    if has_nuke() and __import__('nuke').GUI:
        return NukeProgressHandler(**handler_kwargs)
    elif has_gui():
        return QtProgressHandler(**handler_kwargs)
    return CLIProgressHandler(**handler_kwargs)


def progress(iterable, name=None, handler=None,
             start_message=None, oncancel=None, **handler_kwargs):
    """Progress with iterator. """

    assert handler is None or isinstance(
        handler, BaseProgressHandler), 'Got wrong handler class: {}'.format(handler.__class__)

    if handler is None:
        handler = get_default_progress_handler(**handler_kwargs)
    else:
        if handler_kwargs:
            LOGGER.warning(
                '@handler already given, ignore @handler_kwargs: %s', handler_kwargs)
    if name is not None:
        handler.task_name = get_unicode(name)

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


class CancelledError(Exception):
    """Indicate user pressed CancelButton.  """

    def __str__(self):
        return 'Cancelled.'

    def __unicode__(self):
        return '用户取消.'


def _error_process(message, error_type=''):
    app = QtWidgets.QApplication(sys.argv)
    dummy_var = _error_message(message, error_type)
    sys.exit(app.exec_())


def _error_message(message, error_type=''):
    frame = QtWidgets.QErrorMessage()
    frame.showMessage(message, error_type)
    frame.show()
    return frame


def error(message, error_type=''):
    """Show error message. """

    def _run():
        proc = multiprocessing.Process(
            target=_error_process, args=(message, error_type))
        proc.start()
        proc.join()
    if not QtWidgets.QApplication.instance():
        threading.Thread(target=_run, name='ErrorDialog').start()
    else:
        _error_message(message, error_type)


def _message_process(message, detail):
    QtWidgets.QApplication(sys.argv)
    dummy_var = _message(message, detail)


def _message(message, detail):
    msgbox = QtWidgets.QMessageBox()
    msgbox.setText(message)
    if detail:
        msgbox.setDetailedText(detail)
    return msgbox.exec_()


def message_box(message, detail=None):
    """Show a message.  """
    def _run():
        proc = multiprocessing.Process(
            target=_message_process, args=(message, detail))
        proc.start()
        proc.join()
    if not QtWidgets.QApplication.instance():
        threading.Thread(target=_run, name='MessageBox').start()
    else:
        _message(message, detail)
