# -*- coding=UTF-8 -*-
"""For build UI faster.  """
from __future__ import absolute_import, print_function, unicode_literals

import sys

from Qt import QtCompat, QtCore, QtWidgets
from Qt.QtWidgets import QAction, QApplication, QDialog, QFileDialog, QMenu

from .config import Config
from .decorators import deprecated
from .env import has_gui as _has_gui
from . import mp_logging
from .path import Path


class DialogWithDir(QDialog):
    """Dialog with a lineEdit dir input, can restore from config.  """

    def __init__(self, uifile, config=None, parent=None, icons=None, edits_key=None, dir_edit=None):
        assert isinstance(config, Config)
        assert isinstance(icons, dict)
        assert isinstance(edits_key, dict)

        def _icon():
            if not icons:
                return

            _stdicon = self.style().standardIcon

            for k, v in icons.items():
                v = _stdicon(v)
                if k is None:
                    self.setWindowIcon(v)
                else:
                    k = getattr(self, k)
                    k.setIcon(v)

        def _edits():
            def _set_config(k, v):
                config[k] = v

            for edit, key in edits_key.items():
                edit = getattr(self, edit)
                if isinstance(edit, QtWidgets.QLineEdit):
                    edit.editingFinished.connect(
                        lambda e=edit, k=key: _set_config(k, e.text())
                    )
                elif isinstance(edit, QtWidgets.QCheckBox):
                    edit.stateChanged.connect(
                        lambda state, k=key: _set_config(k, state)
                    )
                elif isinstance(edit, QtWidgets.QComboBox):
                    edit.currentIndexChanged.connect(
                        lambda index, ex=edit, k=key: _set_config(
                            k,
                            ex.itemText(index)
                        )
                    )
                elif isinstance(edit, (QtWidgets.QToolBox, QtWidgets.QTabWidget)):
                    edit.currentChanged.connect(
                        lambda index, ex=edit, k=key: _set_config(
                            k,
                            index
                        )
                    )
                else:
                    print(u'待处理的控件: {} {}'.format(type(edit), edit))

        def _recover():
            for edit, k in edits_key.items():
                edit = getattr(self, edit)
                try:
                    if isinstance(edit, QtWidgets.QLineEdit):
                        edit.setText(config[k])
                    elif isinstance(edit, QtWidgets.QCheckBox):
                        edit.setCheckState(
                            QtCore.Qt.CheckState(config[k])
                        )
                    elif isinstance(edit, QtWidgets.QComboBox):
                        edit.setCurrentIndex(
                            edit.findText(config[k]))
                    elif isinstance(edit, (QtWidgets.QToolBox, QtWidgets.QTabWidget)):
                        edit.setCurrentIndex(config[k])
                except KeyError as ex:
                    print('wlf.uploader: not found key {} in config'.format(ex))

        super(DialogWithDir, self).__init__(parent)
        QtCompat.loadUi(unicode(Path(__file__, uifile)), self)
        _icon()
        _recover()
        _edits()
        self.__dir_edit = getattr(self, dir_edit)
        self.__dir_edit.textChanged.connect(self._check_dir)

    @property
    def directory(self):
        """Current working dir.  """

        return self.__dir_edit.text()

    @directory.setter
    def directory(self, value):
        edit = self.__dir_edit
        path = Path(value)
        if not path.exists():
            return
        path.resolve()
        value = unicode(path)
        if value != self.directory:
            edit.setText(value)
            edit.editingFinished.emit()

    def ask_dir(self):
        """Show a dialog ask user CONFIG['DIR'].  """

        file_dialog = QFileDialog()
        dir_ = file_dialog.getExistingDirectory(
            dir=unicode(Path(self.directory).parent)
        )
        if dir_:
            self.directory = dir_

    def _check_dir(self):
        """Check if dir exists.  """

        edit = self.__dir_edit
        path = Path(edit.text())
        existed = path.exists()
        if existed:
            edit.setStyleSheet('')
        else:
            edit.setStyleSheet('background:rgb(100%,50%,50%)')

        return existed


class Menu(QMenu):
    """Wrapped QMenu.  """

    def add_command(self, name, cmd):
        """Add command to tray menu.  """

        action = QAction(name, self, triggered=cmd)
        self.addAction(action)
        return action

    def add_menu(self, name):
        """Add submenu to tray menu.  """

        menu = Menu(name)
        self.addMenu(menu)
        return menu


def main_show_dialog(dialog):
    """Show dialog, standalone.  """

    from .notify import QtProgressBar

    mp_logging.basic_config()
    QApplication(sys.argv)
    frame = dialog()
    QtProgressBar.default_parent = frame
    sys.exit(frame.exec_())

# Deprecated functions.


deprecated('has_gui', reason='moved to wlf.env')(_has_gui)
