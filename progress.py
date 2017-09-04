# -*- coding=UTF-8 -*-
"""Show progress to user.  """
import os
import sys

from .Qt import QtCompat, QtWidgets

HAS_NUKE = bool(sys.modules.get('nuke'))

if HAS_NUKE:
    import nuke

__version__ = '0.3.4'


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
