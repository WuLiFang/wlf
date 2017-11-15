# -*- coding=UTF-8 -*-
"""For build UI faster.  """
from __future__ import print_function, unicode_literals

import sys
import os

from wlf.Qt import QtWidgets, QtCore, QtCompat
from wlf.Qt.QtWidgets import QDialog, QApplication, QFileDialog
from wlf.mp_logging import set_basic_logger
import wlf.config

__version__ = '0.1.1'


class DialogWithDir(QDialog):
    """Dialog with a lineEdit dir input, can restore from config.  """

    def __init__(self, uifile, config=None, parent=None, icons=None, edits_key=None, dir_edit=None):
        assert isinstance(config, wlf.config.Config)
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
        QtCompat.loadUi(os.path.abspath(
            os.path.join(__file__, uifile)), self)
        _icon()
        _recover()
        _edits()
        self.__dir_edit = getattr(self, dir_edit)

    @property
    def directory(self):
        """Current working dir.  """

        return self.__dir_edit.text()

    @directory.setter
    def directory(self, value):
        edit = self.__dir_edit
        value = os.path.normpath(value)
        if value != self.directory:
            edit.setText(value)
            edit.editingFinished.emit()

    def ask_dir(self):
        """Show a dialog ask user CONFIG['DIR'].  """

        file_dialog = QFileDialog()
        dir_ = file_dialog.getExistingDirectory(
            dir=os.path.dirname(self.directory)
        )
        if dir_:
            self.directory = dir_


def main_show_dialog(dialog):
    """Show dialog, standalone.  """

    if sys.getdefaultencoding() != 'UTF-8':
        reload(sys)
        sys.setdefaultencoding('UTF-8')

    set_basic_logger()
    QApplication(sys.argv)
    frame = dialog()
    sys.exit(frame.exec_())
