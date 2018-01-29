# -*- coding=UTF-8 -*-
"""Show notify to user.  """
from __future__ import print_function, unicode_literals, absolute_import

import os
import sys
import multiprocessing
import threading
import logging


from .env import has_nuke, has_gui
from .decorators import run_in_main_thread
from .path import get_encoded

HAS_NUKE = has_nuke()
HAS_GUI = has_gui()
LOGGER = logging.getLogger('com.wlf.notify')

if HAS_NUKE:
    import nuke

if HAS_GUI:
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


class Progress(object):
    """A progressbar compatible with or without nuke imported."""

    count = -1
    total = 100
    # stepped = Signal()
    # stepped_with_message = Signal(str)
    # progress_changed = Signal(int)
    # message_changed = Signal(str)

    def __init__(self, name='', total=None, parent=None):
        super(Progress, self).__init__()

        self.total = total or self.total

        if HAS_NUKE:
            self._task = nuke.ProgressTask(get_encoded( name))
        else:
            self._task = ProgressBar(name, parent)

        # self.stepped.connect(self.on_step)
        # self.stepped_with_message.connect(self.on_step)
        # self.progress_changed.connect(self.set_progress)
        # self.message_changed.connect(self.set_message)

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
            # self.progress_changed.emit(progress)
            self.set_progress(progress)
        if message is not None:
            # self.message_changed.emit(message)
            self.set_message(message)

    # @Slot(int)
    def set_progress(self, value):
        """Set progress value.  """

        if self.progress != value:
            self.count = self.total * value // 100
        self._task.setProgress(value)
        QtWidgets.QApplication.processEvents()

    # @Slot(str)
    def set_message(self, message):
        """Set progress message.  """

        self._task.setMessage(message)
        QtWidgets.QApplication.processEvents()

    def step(self, message=None):
        """Signal wrapper.  """

        # if message is None:
        #     self.stepped.emit()
        # else:
        #     self.stepped_with_message.emit(message)
        self.on_step(message)
        QtWidgets.QApplication.processEvents()

    # @Slot()
    # @Slot(str)
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
