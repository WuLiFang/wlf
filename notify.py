# -*- coding=UTF-8 -*-
"""Show notify to user.  """
from __future__ import absolute_import, print_function, unicode_literals

import logging
import multiprocessing
import os
import sys
import threading
import time
from datetime import timedelta

from six import text_type, PY2

from . import util
from .decorators import deprecated, run_in_main_thread
from .env import HAS_QT, has_gui, has_nuke
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

        @run_in_main_thread
        def __init__(self, parent=None):
            if parent is None:
                parent = self.default_parent
            self._cancelled = False

            super(QtProgressBar, self).__init__(parent)
            QtCompat.loadUi(os.path.abspath(
                os.path.join(__file__, '../progress.ui')), self)
            if parent:
                geo = self.geometry()
                geo.moveCenter(parent.geometry().center())
                self.setGeometry(geo)

            self.setAttribute(Qt.WA_QuitOnClose)
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

        def closeEvent(self, event):
            """Override QWidget.closeEvent()"""

            event.ignore()

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
            self.progress_bar.hide()
            self.progress_bar.deleteLater()


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

    try:
        handler.on_started()
        if start_message is not None:
            handler.set_message(start_message)
        for i in iterable:
            handler.step(i)
            yield i
        handler.on_finished()
    finally:
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


def traytip(title, text, seconds=3, icon='Information', **kwargs):
    """Show a traytip.

    @icon enum:
        NoIcon,
        Information,
        Warning,
        Critical
    """

    from .tray import Tray

    if kwargs:
        LOGGER.warning('Unused kwargs: %s', kwargs)
    icon = getattr(QtWidgets.QSystemTrayIcon, icon)

    tray = Tray()
    tray.show()

    tray.showMessage(title, text, icon=icon, msecs=seconds * 1000)


# TODO: deprecated api, remove at next major version.

if HAS_QT:
    from Qt import QtCompat, QtWidgets
    from Qt.QtCore import Signal

    class ProgressBar(QtWidgets.QDialog):
        """Qt progressbar dialog."""

        progress_changed = Signal(int)
        message_changed = Signal(str)

        @run_in_main_thread
        def __init__(self, name, parent=None):
            self._cancelled = False
            self.name = name

            app = QtWidgets.QApplication.instance()
            if not app:
                app = QtWidgets.QApplication(sys.argv)
            super(ProgressBar, self).__init__(parent)
            QtCompat.loadUi(os.path.join(__file__, '../progress.ui'), self)
            if parent:
                geo = self.geometry()
                geo.moveCenter(parent.geometry().center())
                self.setGeometry(geo)
            self.show()

            self.progress_changed.connect(self.set_progress)
            self.message_changed.connect(self.set_message)

            setattr(self, 'setProgress', self.progress_changed.emit)
            setattr(self, 'setMessage', self.message_changed.emit)

        def set_progress(self, value):
            """Set progress value.  """

            self.progressBar.setValue(value)
            QtWidgets.QApplication.processEvents()

        def set_message(self, message):
            """Set progress message.  """

            self.setWindowTitle(
                u':'.join(i for i in [self.name, message] if i))
            QtWidgets.QApplication.processEvents()

        def isCancelled(self):
            """Return if cancel button been pressed.  """
            return self._cancelled

        def reject(self):
            """Override QDiloag.reject()"""
            self._cancelled = True

        def closeEvent(self, event):
            """Override QWidget.closeEvent()"""
            dummy = self
            event.ignore()

else:
    def do_nothing(*args, **kwargs):
        pass

    class ProgressBar(object):
        setProgress = setMessage = do_nothing


@deprecated('Progress')
class _Progress(object):
    """A progressbar compatible with or without nuke imported."""

    count = -1
    total = 100

    def __init__(self, name='', total=None, parent=None):
        super(_Progress, self).__init__()

        self.total = total or self.total

        if HAS_NUKE:
            self._task = __import__('nuke').ProgressTask(
                get_encoded(name, 'utf-8'))
        else:
            self._task = ProgressBar(name, parent)

    def __del__(self):
        if not HAS_NUKE:
            self._task.hide()
        del self._task

    @property
    def progress(self):
        """Progress caculated by count and total.  """

        return self.count * 100 // self.total

    def set(self, progress=None, message=None):
        """Set progress number and message"""

        if self.is_cancelled():
            raise CancelledError

        if progress is not None:
            self.set_progress(progress)
        if message is not None:
            self.set_message(message)

    def set_progress(self, value):
        """Set progress value.  """

        if self.progress != value:
            self.count = self.total * value // 100
        self._task.setProgress(value)
        QtWidgets.QApplication.processEvents()

    def set_message(self, message):
        """Set progress message.  """

        if HAS_NUKE:
            message = get_encoded(message, 'utf-8')
        self._task.setMessage(message)
        QtWidgets.QApplication.processEvents()

    def step(self, message=None):
        """Signal wrapper.  """

        self.on_step(message)
        QtWidgets.QApplication.processEvents()

    def on_step(self, message=None):
        """One step forward.  """

        self.count += 1
        message = message or '剩余{}项'.format(int(self.total - self.count))
        self.set(self.progress, message)

    def is_cancelled(self):
        """Return if task has been cancelled.  """

        return self._task.isCancelled()

    def check_cancelled(self):
        """Raise a `CancelledError` if task has been cancelled.  """

        if self.is_cancelled():
            raise CancelledError
