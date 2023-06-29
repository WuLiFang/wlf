# -*- coding=UTF-8 -*-
"""UI template.  """
from __future__ import absolute_import, division, print_function, unicode_literals

from abc import abstractmethod

from Qt import QtCompat, QtCore, QtWidgets
from Qt.QtWidgets import QDialog, QFileDialog

from ...path import Path
from ... import codectools


class DialogWithDir(QDialog):
    """Dialog with a lineEdit dir input, can restore from config."""

    uifile = None
    icons = None

    def __init__(self, config=None, parent=None):
        self.config = config or dict()
        super(DialogWithDir, self).__init__(parent)
        QtCompat.loadUi(
            codectools.get_unicode(Path(codectools.get_unicode(__file__), self.uifile)),
            self,
        )
        self._setup_icons()
        self._load_edits_state()
        self._setup_edits()
        self.dir_edit.textChanged.connect(self._validate_dir)

    @abstractmethod
    def _edits_key(self):
        return {}

    @property
    @abstractmethod
    def dir_edit(self):
        """Line edit for dir input."""

        return self.lineEditDir

    def _setup_icons(self):
        icons = self.icons
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

    def _setup_edits(self):
        config = self.config
        edits_key = self._edits_key()

        def _set_config(k, v):
            config[k] = v

        for edit, key in edits_key.items():
            edit = getattr(self, edit)
            if isinstance(edit, QtWidgets.QLineEdit):
                edit.editingFinished.connect(
                    lambda e=edit, k=key: _set_config(k, e.text())
                )
            elif isinstance(edit, QtWidgets.QCheckBox):
                edit.stateChanged.connect(lambda state, k=key: _set_config(k, state))
            elif isinstance(edit, QtWidgets.QComboBox):
                edit.currentIndexChanged.connect(
                    lambda index, ex=edit, k=key: _set_config(k, ex.itemText(index))
                )
            elif isinstance(edit, (QtWidgets.QToolBox, QtWidgets.QTabWidget)):
                edit.currentChanged.connect(
                    lambda index, ex=edit, k=key: _set_config(k, index)
                )
            else:
                print("待处理的控件: {} {}".format(type(edit), edit))

    def _load_edits_state(self):
        config = self.config
        edits_key = self._edits_key()
        for edit, k in edits_key.items():
            edit = getattr(self, edit)
            try:
                if isinstance(edit, QtWidgets.QLineEdit):
                    edit.setText(config[k])
                elif isinstance(edit, QtWidgets.QCheckBox):
                    edit.setCheckState(QtCore.Qt.CheckState(config[k]))
                elif isinstance(edit, QtWidgets.QComboBox):
                    edit.setCurrentIndex(edit.findText(config[k]))
                elif isinstance(edit, (QtWidgets.QToolBox, QtWidgets.QTabWidget)):
                    edit.setCurrentIndex(config[k])
            except KeyError as ex:
                print("wlf.uploader: not found key {} in config".format(ex))

    @property
    def directory(self):
        """Current working dir."""

        return self.dir_edit.text()

    @directory.setter
    def directory(self, value):
        edit = self.dir_edit
        path = Path(value)
        if not path.exists():
            return
        path.resolve()
        value = codectools.get_unicode(path)
        if value != self.directory:
            edit.setText(value)
            edit.editingFinished.emit()

    def ask_dir(self):
        """Show a dialog ask user CONFIG['DIR']."""

        file_dialog = QFileDialog()
        dir_ = file_dialog.getExistingDirectory(
            dir=codectools.get_unicode(Path(self.directory).parent)
        )
        if dir_:
            self.directory = dir_

    def _validate_dir(self):
        """Check if dir exists."""

        edit = self.dir_edit
        path = Path(edit.text())
        existed = path.exists()
        if existed:
            edit.setStyleSheet("")
        else:
            edit.setStyleSheet("background:rgb(100%,50%,50%)")

        return existed
