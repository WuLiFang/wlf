# -*- coding=UTF-8 -*-
"""Upload files to server.  """
from __future__ import print_function, unicode_literals

import os
import sys
import webbrowser
import logging

import wlf.config
from wlf import cgtwq
from wlf.decorators import run_async
from wlf.files import copy, is_same, version_filter
from wlf.notify import HAS_NUKE, CancelledError, Progress
from wlf.path import get_server, get_unicode, remove_version, split_version
from wlf.Qt import QtCompat, QtCore, QtWidgets
from wlf.Qt.QtGui import QBrush, QColor
from wlf.Qt.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox
from wlf.mp_logging import set_basic_logger

__version__ = '0.8.3'

LOGGER = logging.getLogger('com.wlf.uploader')

if __name__ == '__main__':
    set_basic_logger()


class Config(wlf.config.Config):
    """A disk config can be manipulated like a dict."""

    default = {
        'DIR': 'E:/',
        'SERVER': 'Z:\\',
        'PROJECT': 'SNJYW',
        'FOLDER': 'Comp\\mov',
        'PIPELINE': '合成',
        'EPISODE': '',
        'SCENE': '',
        'MODE': 1,
        'IS_SUBMIT': 2,
        'IS_BURN_IN': 2
    }
    path = os.path.expanduser('~/.wlf.uploader.json')


CONFIG = Config()


class Dialog(QDialog):
    """Main GUI dialog.  """

    def __init__(self, parent=None):
        def _icon():
            _stdicon = self.style().standardIcon

            _icon = _stdicon(QtWidgets.QStyle.SP_DirOpenIcon)
            self.toolButtonOpenDir.setIcon(_icon)
            self.toolButtonOpenServer.setIcon(_icon)

            _icon = _stdicon(QtWidgets.QStyle.SP_DialogOpenButton)
            self.dirButton.setIcon(_icon)
            self.serverButton.setIcon(_icon)

            _icon = _stdicon(QtWidgets.QStyle.SP_FileDialogToParent)
            self.syncButton.setIcon(_icon)
            self.setWindowIcon(_icon)

        def _actions():
            self.actionDir.triggered.connect(self.ask_dir)
            self.actionSync.triggered.connect(self.upload)
            self.actionServer.triggered.connect(self.ask_server)
            self.actionOpenDir.triggered.connect(
                lambda: webbrowser.open(CONFIG['DIR']))
            self.actionOpenServer.triggered.connect(
                lambda: webbrowser.open(CONFIG['SERVER']))

        def _edits():
            def _set_config(k, v):
                CONFIG[k] = v

            for edit, key in self.edits_key.items():
                if isinstance(edit, QtWidgets.QLineEdit):
                    edit.editingFinished.connect(
                        lambda e=edit, k=key: _set_config(k, e.text())
                    )
                    edit.editingFinished.connect(self.update_ui)
                elif isinstance(edit, QtWidgets.QCheckBox):
                    edit.stateChanged.connect(
                        lambda state, k=key: _set_config(k, state)
                    )
                    edit.stateChanged.connect(self.update_ui)
                elif isinstance(edit, QtWidgets.QComboBox):
                    edit.currentIndexChanged.connect(
                        lambda index, ex=edit, k=key: _set_config(
                            k,
                            ex.itemText(index)
                        )
                    )
                elif isinstance(edit, QtWidgets.QToolBox):
                    edit.currentChanged.connect(
                        lambda index, ex=edit, k=key: _set_config(
                            k,
                            index
                        )
                    )
                    edit.currentChanged.connect(self.update_ui)
                else:
                    print(u'待处理的控件: {} {}'.format(type(edit), edit))

        def _recover():
            for qt_edit, k in self.edits_key.items():
                try:
                    if isinstance(qt_edit, QtWidgets.QLineEdit):
                        qt_edit.setText(CONFIG[k])
                    elif isinstance(qt_edit, QtWidgets.QCheckBox):
                        qt_edit.setCheckState(
                            QtCore.Qt.CheckState(CONFIG[k])
                        )
                    elif isinstance(qt_edit, QtWidgets.QComboBox):
                        qt_edit.setCurrentIndex(
                            qt_edit.findText(CONFIG[k]))
                    elif isinstance(qt_edit, QtWidgets.QToolBox):
                        qt_edit.setCurrentIndex(CONFIG[k])
                except KeyError as ex:
                    print('wlf.uploader: not found key {} in config'.format(ex))
            if HAS_NUKE:
                mov_path = __import__('node').Last.mov_path
                if mov_path:
                    self.directory = get_unicode(os.path.dirname(mov_path))

        QDialog.__init__(self, parent)
        QtCompat.loadUi(os.path.abspath(
            os.path.join(__file__, '../uploader.ui')), self)

        self.edits_key = {
            self.serverEdit: 'SERVER',
            self.folderEdit: 'FOLDER',
            self.dirEdit: 'DIR',
            self.projectEdit: 'PROJECT',
            self.epEdit: 'EPISODE',
            self.scEdit: 'SCENE',
            self.toolBox: 'MODE',
            self.checkBoxSubmit: 'IS_SUBMIT',
            self.checkBoxBurnIn: 'IS_BURN_IN',
            self.comboBoxPipeline: 'PIPELINE',
        }
        self.cgtw_dests = {}

        self.file_list_widget = FileListWidget(self.listWidget)
        self.version_label.setText('v{}'.format(__version__))

        self.update_timer = QtCore.QTimer()
        self.update_timer.setInterval(100)
        self.update_timer.timeout.connect(self.update_ui)

        _icon()
        _recover()
        _edits()
        _actions()

    def closeEvent(self, event):
        event.accept()
        self.hideEvent(event)

    def showEvent(self, event):
        LOGGER.debug('Uploader show event triggered.')
        event.accept()
        self.update_timer.start()
        self.file_list_widget.showEvent(event)

    def hideEvent(self, event):
        LOGGER.debug('Uploader hide event triggered.')
        event.accept()
        self.update_timer.stop()
        self.file_list_widget.hideEvent(event)

    def update_ui(self):
        """Update dialog UI content.  """

        mode = self.mode()
        sync_button_enable = any(self.file_list_widget.checked_files)
        sync_button_text = u'上传至CGTeamWork'
        if mode == 0:
            sync_button_enable &= os.path.exists(get_server(self.server))\
                and os.path.isdir(os.path.dirname(self.dest_folder))
            sync_button_text = u'上传至: {}'.format(self.dest_folder)

        self.syncButton.setText(sync_button_text)
        self.syncButton.setEnabled(sync_button_enable)

    @run_async
    def upload(self):
        """Upload videos to server.  """

        try:
            files = list(self.checked_files)
            task = Progress(total=len(files))
            for i in files:
                src = os.path.join(self.directory, i)
                dst = self.get_dest(i)
                shot_name = split_version(os.path.basename(dst))[0]
                if isinstance(dst, Exception):
                    self.error(u'{}\n-> {}'.format(i, dst))
                    continue
                copy(src, dst)
                if src.lower().endswith(('.jpg', '.png', '.jpeg')):
                    shot = cgtwq.Shot(shot_name, pipeline=self.pipeline)
                    shot.shot_image = dst
                if self.is_submit and self.mode() == 1:
                    cgtwq.Shot(shot_name, pipeline=self.pipeline).submit(
                        [dst], note='自上传工具提交')
                task.step(i)

        except CancelledError:
            pass

        self.activateWindow()

    @property
    def dest_folder(self):
        """File upload folder destination.  """

        ret = os.path.join(
            self.server,
            self.project,
            self.folderEdit.text(),
            self.epEdit.text(),
            self.scEdit.text()
        )
        ret = os.path.normpath(ret)
        return ret

    @property
    def pipeline(self):
        """Current working pipeline.  """

        return self.comboBoxPipeline.currentText()

    def get_dest(self, filename, refresh=False):
        """Get destination for @filename. """

        mode = self.mode()
        if mode == 0:
            return os.path.join(self.dest_folder, remove_version(filename))
        elif mode == 1:
            ret = self.cgtw_dests.get(filename)
            if not ret or (isinstance(ret, Exception) and refresh):
                try:
                    shot = cgtwq.Shot(split_version(filename)[0],
                                      pipeline=self.pipeline)
                    shot.check_account()
                    ret = shot.submit_dest
                    if not ret:
                        raise(ValueError('Cound not get dest.  '))
                    ret = os.path.join(ret, remove_version(filename))
                except ValueError as ex:
                    self.error(u'找不到上传路径, 请联系管理员设置文件夹submit_dest标识')
                    ret = ex
                except cgtwq.LoginError as ex:
                    self.error(u'需要登录CGTeamWork')
                    ret = ex
                except cgtwq.IDError as ex:
                    self.error(u'{}: CGTW上未找到对应镜头'.format(filename))
                    ret = ex
                except cgtwq.AccountError as ex:
                    self.error(u'#{}\n已被分配给: {}\n当前用户: {}'.format(
                        filename, ex.owner or u'<未分配>', ex.current))
                    ret = ex
                self.cgtw_dests[filename] = ret
                LOGGER.debug('Found dest: %s', ret)
            return ret
        else:
            raise ValueError('No such mode. {}'.format(mode))

    def error(self, message):
        """Show error.  """

        self.textBrowser.append(message)

    def mode(self):
        """Upload mode. """
        return self.toolBox.currentIndex()

    @property
    def directory(self):
        """Current working dir.  """
        return self.dirEdit.text()

    @directory.setter
    def directory(self, value):
        value = os.path.normpath(value)
        if value != self.directory:
            self.dirEdit.setText(value)

    @property
    def server(self):
        """Current server path.  """
        return self.serverEdit.text()

    @property
    def project(self):
        """Current working dir.  """
        return self.projectEdit.text()

    def ask_dir(self):
        """Show a dialog ask user CONFIG['DIR'].  """

        file_dialog = QFileDialog()
        _dir = file_dialog.getExistingDirectory(
            dir=os.path.dirname(CONFIG['DIR'])
        )
        if _dir:
            self.directory = _dir
            CONFIG['DIR'] = _dir

    @property
    def is_submit(self):
        """Submit when upload or not.  """
        return self.checkBoxSubmit.checkState()

    @property
    def checked_files(self):
        """Return files checked in listwidget.  """
        return self.file_list_widget.checked_files

    def ask_server(self):
        """Show a dialog ask user config['SERVER'].  """

        file_dialog = QFileDialog()
        dir_ = file_dialog.getExistingDirectory(
            dir_=os.path.dirname(CONFIG['SERVER'])
        )
        if dir_:
            self.serverEdit.setText(dir_)


class FileListWidget(object):
    """Folder viewer.  """

    burnin_folder = 'burn-in'
    pipeline_ext = {
        '灯光': ('.jpg', '.png', '.jpeg'),
        '渲染': ('.mov'),
        '合成': ('.mov'),
    }
    if HAS_NUKE:
        brushes = {'local': QBrush(QColor(200, 200, 200)),
                   'uploaded': QBrush(QColor(100, 100, 100)),
                   'error': QBrush(QtCore.Qt.red)}
    else:
        brushes = {'local': QBrush(QtCore.Qt.black),
                   'uploaded': QBrush(QtCore.Qt.gray),
                   'error': QBrush(QtCore.Qt.red)}
    updating = False

    def __init__(self, list_widget):
        self.widget = list_widget
        self.parent = self.widget.parent()
        self.uploaded_files = set()
        self.dest_dict = self.parent.cgtw_dests
        assert isinstance(self.parent, Dialog)

        self.widget.itemDoubleClicked.connect(self.open_file)
        self.parent.actionSelectAll.triggered.connect(self.select_all)
        self.parent.actionReverseSelection.triggered.connect(
            self.reverse_selection)
        self.parent.actionUpdateFiles.triggered.connect(
            self.update_files)
        self.parent.actionClearCache.triggered.connect(
            self.clear_cache)

        self.widget.showEvent = self.showEvent
        self.widget.hideEvent = self.hideEvent

        self.update_timer = QtCore.QTimer(self.parent)
        self.update_timer.setInterval(1000)
        self.update_timer.timeout.connect(self.update_widget)

    @property
    def directory(self):
        """Current working dir.  """
        return self.parent.directory

    def showEvent(self, event):
        event.accept()
        self.update_files()
        self.update_timer.start()

    def hideEvent(self, event):

        event.accept()
        self.update_timer.stop()

    def update_widget(self):
        """Update widget.  """

        if self.updating:
            return

        widget = self.widget
        parent = self.parent
        brushes = self.brushes
        local_files = self.files
        assert isinstance(parent, Dialog)

        # Remove.
        for item in self.items():
            text = item.text()
            if text not in local_files:
                widget.takeItem(widget.indexFromItem(item).row())

            elif item.checkState() \
                    and isinstance(parent.get_dest(text, refresh=True), Exception):
                item.setCheckState(QtCore.Qt.Unchecked)

        for i in local_files:
            # Add.
            try:
                item = widget.findItems(
                    i, QtCore.Qt.MatchExactly)[0]
            except IndexError:
                item = QtWidgets.QListWidgetItem(i, widget)
                item.setCheckState(QtCore.Qt.Unchecked)
            # Set style.
            self.update_file(i)
            if i in self.uploaded_files:
                item.setFlags(QtCore.Qt.ItemIsEnabled)
                item.setForeground(brushes['uploaded'])
                item.setCheckState(QtCore.Qt.Unchecked)
            elif i in self.unexpected_files:
                item.setFlags(QtCore.Qt.ItemIsUserCheckable |
                              QtCore.Qt.ItemIsEnabled)
                item.setForeground(brushes['error'])
            else:
                item.setFlags(QtCore.Qt.ItemIsUserCheckable |
                              QtCore.Qt.ItemIsEnabled)
                item.setForeground(brushes['local'])

        widget.sortItems()

        # Count
        parent.labelCount.setText(
            '{}/{}/{}'.format(
                len(list(self.checked_files)),
                len(local_files) - len(self.uploaded_files),
                len(local_files)))

    def clear_cache(self):
        """Clear destination cache."""

        self.uploaded_files.clear()
        self.parent.cgtw_dests.clear()
        self.update_files()

    def update_files(self):
        """Check if files is uploaded.  """

        if self.updating:
            return
        self.updating = True

        files = self.files
        task = Progress('获取文件状态', total=len(files))
        try:
            for i in files:
                task.step(i)
                self.update_file(i)
        except CancelledError:
            if QMessageBox.question(self.parent,
                                    '正在获取信息',
                                    '退出?',
                                    QMessageBox.Ok | QMessageBox.Cancel) == QMessageBox.Ok:
                QApplication.exit()

        self.updating = False
        self.update_widget()

    def update_file(self, filename):
        """Check file state.  """

        uploaded_files = self.uploaded_files
        src = os.path.join(self.directory, filename)
        dst = self.parent.get_dest(filename)
        if isinstance(dst, (str, unicode)) and is_same(src, dst):
            uploaded_files.add(filename)
        else:
            uploaded_files.difference_update([filename])

    @property
    def files(self):
        """Files in directory with matched extension.  """

        directory = self.directory
        ext = self.pipeline_ext[self.parent.pipeline]
        ret = []

        if os.path.isdir(directory):
            ret = version_filter(i for i in os.listdir(directory)
                                 if i.lower().endswith(ext))
        return ret

    @property
    def unexpected_files(self):
        """Files that can not get destination.  """

        return [k for k, v in self.dest_dict.items() if not v or isinstance(v, Exception)]

    @property
    def checked_files(self):
        """Return files checked in listwidget.  """
        return (i.text() for i in self.items() if i.checkState())

    @property
    def is_use_burnin(self):
        """Use burn-in version when preview.  """
        return self.parent.checkBoxBurnIn.checkState()

    @QtCore.Slot(QtWidgets.QListWidgetItem)
    def open_file(self, item):
        """Open mov file for preview.  """

        filename = item.text()
        path = os.path.join(self.directory, filename)
        burn_in_path = os.path.join(
            self.directory, self.burnin_folder, filename)

        webbrowser.open(burn_in_path
                        if self.is_use_burnin and os.path.exists(burn_in_path)
                        else path)

    def items(self):
        """Item in list widget -> list."""

        widget = self.widget
        return list(widget.item(i) for i in xrange(widget.count()))

    def select_all(self):
        """Select all item in list widget.  """

        files = [i for i in self.files if i not in self.uploaded_files.union(
            self.unexpected_files)]
        refresh = False
        if not files:
            files = [i for i in self.files if i not in self.uploaded_files]
            refresh = True

        if not files:
            return

        for item in self.items():
            if item.text() in files:
                item.setCheckState(QtCore.Qt.Checked)
        if refresh:
            self.clear_cache()

    def reverse_selection(self):
        """Select all item in list widget.  """
        for item in self.items():
            if item.text() not in self.uploaded_files:
                if item.checkState():
                    item.setCheckState(QtCore.Qt.Unchecked)
                else:
                    item.setCheckState(QtCore.Qt.Checked)


def main():
    """Run this script standalone.  """

    app = QApplication(sys.argv)
    frame = Dialog()
    frame.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
