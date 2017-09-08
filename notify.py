# -*- coding=UTF-8 -*-
"""Show notify to user.  """
import os
import sys
import multiprocessing
import threading
from subprocess import Popen

from wlf.Qt import QtCompat, QtWidgets


HAS_NUKE = bool(sys.modules.get('nuke'))

if HAS_NUKE:
    import nuke

__version__ = '0.4.0'


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
        event.ignore()


class Progress(object):

    """A Nuke progressbar compatible without nuke imported."""

    def __init__(self, name=''):
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
            self._task.setProgress(progress)
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


def traytip(title, text, seconds=3, options=1):
    """Show a traytip(windows only).  """
    from wlf.files import get_encoded, escape_batch
    executable = os.path.abspath(
        os.path.join(__file__, '../traytip.exe'))
    if not os.path.exists(get_encoded(executable)):
        raise IOError('traytip.exe missing')
    cmd = u'"{}" "{}" "{}" "{}" "{}"'.format(
        executable, escape_batch(title), escape_batch(text), seconds, options)
    Popen(get_encoded(cmd))