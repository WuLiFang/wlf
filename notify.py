# -*- coding=UTF-8 -*-
"""Show notify to user.  """
import os
import sys
import multiprocessing
import threading
from subprocess import Popen

from wlf.Qt import QtCompat, QtWidgets
from wlf.path import get_encoded, escape_batch

HAS_NUKE = bool(sys.modules.get('nuke'))

if HAS_NUKE:
    import nuke

__version__ = '0.4.4'


class ProgressBar(QtWidgets.QDialog):
    """Qt progressbar dialog."""

    def __init__(self):
        self._cancelled = False

        app = QtWidgets.QApplication.instance()
        if not app:
            app = QtWidgets.QApplication(sys.argv)
        super(ProgressBar, self).__init__()
        QtCompat.loadUi(os.path.join(__file__, '../progress.ui'), self)
        self.show()

    def setProgress(self, value):
        """Set progress value.  """
        self.progressBar.setValue(value)

    def setMessage(self, message):
        """Set progress message.  """
        self.setWindowTitle(message)

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


class Progress(object):
    """A progressbar compatible with or without nuke imported."""
    count = 0
    total = 100

    def __init__(self, name='', total=None):
        self.total = total or self.total
        self.count = -1

        QtWidgets.QApplication.processEvents()
        if HAS_NUKE:
            self._task = nuke.ProgressTask(name)
        else:
            self._task = ProgressBar()
            self._task.setMessage(name)

    def __del__(self):
        if not HAS_NUKE:
            self._task.hide()
        del self._task

    def set(self, progress=None, message=None):
        """Set progress number and message"""
        if not HAS_NUKE:
            QtWidgets.QApplication.processEvents()

        if self._task.isCancelled():
            raise CancelledError

        if progress:
            self.count = int(self.total * (progress / 100.0))
            self._task.setProgress(progress)
        if message:
            self._task.setMessage(message)

    def step(self, message=None):
        """One step forward.  """
        self.count += 1
        self._task.setProgress(self.count * 100 // self.total)
        if message:
            self._task.setMessage(message)


class CancelledError(Exception):
    """Indicate user pressed CancelButton.  """

    def __str__(self):
        return 'Cancelled. '


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


def traytip(title, text, seconds=3, options=1):
    """Show a traytip(windows only).  """
    executable = os.path.abspath(
        os.path.join(__file__, '../traytip.exe'))
    if not os.path.exists(get_encoded(executable)):
        raise IOError('traytip.exe missing')
    cmd = u'"{}" "{}" "{}" "{}" "{}"'.format(
        executable, escape_batch(title), escape_batch(text), seconds, options)
    Popen(get_encoded(cmd))
