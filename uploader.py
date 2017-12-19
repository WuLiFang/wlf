# -*- coding=UTF-8 -*-
"""Upload files to server.  """

from __future__ import print_function, unicode_literals

import logging
import os
import webbrowser

from wlf.Qt.QtCore import QObject, Signal, Slot, QTimer, Qt
from wlf.Qt.QtGui import QBrush, QColor
from wlf.Qt.QtWidgets import QFileDialog, QStyle, QListWidgetItem

from . import cgtwq
from .config import Config as _Config
from .decorators import run_async
from .files import copy, is_same, version_filter
from .notify import HAS_NUKE, CancelledError, Progress
from .path import get_unicode, PurePath, Path
from .uitools import DialogWithDir, main_show_dialog

__version__ = '0.10.4'

LOGGER = logging.getLogger('com.wlf.uploader')


class Config(_Config):
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


class Dialog(DialogWithDir):
    """Main GUI dialog.  """

    default_note = '自上传工具提交'
    instance = None
    upload_finished = Signal()

    def __init__(self, parent=None):

        edits_key = {
            'serverEdit': 'SERVER',
            'folderEdit': 'FOLDER',
            'dirEdit': 'DIR',
            'projectEdit': 'PROJECT',
            'epEdit': 'EPISODE',
            'scEdit': 'SCENE',
            'tabWidget': 'MODE',
            'checkBoxSubmit': 'IS_SUBMIT',
            'checkBoxBurnIn': 'IS_BURN_IN',
            'comboBoxPipeline': 'PIPELINE',
        }
        icons = {
            'toolButtonOpenDir': QStyle.SP_DirOpenIcon,
            'toolButtonOpenServer': QStyle.SP_DirOpenIcon,
            'dirButton': QStyle.SP_DialogOpenButton,
            'serverButton': QStyle.SP_DialogOpenButton,
            'syncButton': QStyle.SP_FileDialogToParent,
            None: QStyle.SP_FileDialogToParent,
        }
        DialogWithDir.__init__(
            self,
            '../uploader.ui',
            config=CONFIG,
            icons=icons,
            parent=parent,
            edits_key=edits_key,
            dir_edit='dirEdit')
        self.version_label.setText('v{}'.format(__version__))
        self.lineEditNote.setPlaceholderText(self.default_note)
        self.file_list_widget = FileListWidget(self.listWidget)

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.setInterval(100)
        self.update_timer.timeout.connect(self.update_ui)

        # Signals
        self.actionDir.triggered.connect(self.ask_dir)
        self.actionSync.triggered.connect(self.upload)
        self.actionServer.triggered.connect(self.ask_server)
        self.actionOpenDir.triggered.connect(
            lambda: webbrowser.open(CONFIG['DIR']))
        self.actionOpenServer.triggered.connect(
            lambda: webbrowser.open(CONFIG['SERVER']))
        self.upload_finished.connect(self.activateWindow)

    def showEvent(self, event):
        LOGGER.debug('Uploader show event triggered.')
        event.accept()
        if HAS_NUKE:
            mov_path = __import__('node').Last.mov_path
            if mov_path:
                self.directory = get_unicode(os.path.dirname(mov_path))
        self.update_timer.start()
        self.file_list_widget.showEvent(event)

    def hideEvent(self, event):
        LOGGER.debug('Uploader hide event triggered.')
        event.accept()
        self.update_timer.stop()
        self.file_list_widget.hideEvent(event)

    def update_ui(self):
        """Update dialog UI content.  """

        mode = self.mode
        sync_button_enable = any(self.file_list_widget.checked_files)
        sync_button_text = u'上传至CGTeamWork'
        if mode == 0:
            sync_button_enable &= Path(self.dest_folder).parent.is_dir()
            sync_button_text = u'上传至: {}'.format(self.dest_folder)

        self.syncButton.setText(sync_button_text)
        self.syncButton.setEnabled(sync_button_enable)

    def upload(self):
        """Upload videos to server.  """

        files = list(self.checked_files)
        directory = self.file_list_widget.directory

        task = Progress(total=len(files), parent=self)

        @run_async
        def _run():
            try:
                for i in files:
                    task.step(i)
                    src = os.path.join(self.directory, i)
                    dst = directory.get_dest(i)
                    shot_name = PurePath(dst).shot
                    if isinstance(dst, Exception):
                        self.error(u'{}\n-> {}'.format(i, dst))
                        continue
                    copy(src, dst)
                    if self.mode == 1:
                        shot = cgtwq.Shot(shot_name, pipeline=self.pipeline)
                        if src.lower().endswith(('.jpg', '.png', '.jpeg')):
                            shot.shot_image = dst
                        if self.is_submit:
                            note = self.lineEditNote.text() or self.default_note
                            shot.submit([dst], note=note)
            except CancelledError:
                LOGGER.info('用户取消上传')
            self.upload_finished.emit()

        _run()

    def ask_server(self):
        """Show a dialog ask user config['SERVER'].  """

        file_dialog = QFileDialog()
        dir_ = file_dialog.getExistingDirectory(
            dir_=os.path.dirname(CONFIG['SERVER'])
        )
        if dir_:
            self.serverEdit.setText(dir_)

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

    @property
    def mode(self):
        """Upload mode. """

        return self.tabWidget.currentIndex()

    @property
    def server(self):
        """Current server path.  """

        return self.serverEdit.text()

    @property
    def project(self):
        """Current working dir.  """

        return self.projectEdit.text()

    @property
    def is_submit(self):
        """Submit when upload or not.  """

        return self.checkBoxSubmit.checkState()

    @property
    def checked_files(self):
        """Return files checked in listwidget.  """

        return self.file_list_widget.checked_files


class FileListWidget(object):
    """Folder viewer.  """

    if HAS_NUKE:
        brushes = {'local': QBrush(QColor(200, 200, 200)),
                   'uploaded': QBrush(QColor(100, 100, 100)),
                   'error': QBrush(Qt.red)}
    else:
        brushes = {'local': QBrush(Qt.black),
                   'uploaded': QBrush(Qt.gray),
                   'error': QBrush(Qt.red)}
    directory = None
    burnin_folder = 'burn-in'
    updating = False

    def __init__(self, list_widget):

        self.widget = list_widget
        parent = self.widget.parent()
        assert isinstance(parent, Dialog)
        self.parent = parent

        # Connect signal
        self.widget.itemDoubleClicked.connect(self.open_file)
        self.widget.itemChanged.connect(self.update_widget)
        self.parent.actionSelectAll.triggered.connect(self.select_all)
        self.parent.actionReverseSelection.triggered.connect(
            self.reverse_selection)
        self.parent.actionReset.triggered.connect(
            self.update_directory)

        # Event override
        self.widget.showEvent = self.showEvent
        self.widget.hideEvent = self.hideEvent

    def update_directory(self):
        """Update current working dir.  """

        if self.directory and self.directory.updating:
            return

        mode = self.parent.mode
        kwargs = {}
        if mode == 0:
            parent = self.parent
            assert isinstance(parent, Dialog)
            kwargs = {'dest': self.parent.dest_folder}

        directory = ShotsFileDirectory(
            self.parent.directory, self.parent.pipeline, parent=self.parent, **kwargs)
        directory.changed.connect(self.update_widget)
        directory.update_timer.start()

        if self.directory:
            self.directory.update_timer.stop()
            self.directory.deleteLater()
        self.directory = directory
        self.directory.changed.emit()

    def showEvent(self, event):
        event.accept()
        self.update_directory()

    def hideEvent(self, event):

        event.accept()
        if self.directory:
            self.directory.update_timer.stop()

    def update_widget(self):
        """Update widget.  """

        if self.updating:
            return

        self.updating = True

        widget = self.widget
        parent = self.parent
        brushes = self.brushes
        directory = self.directory
        assert isinstance(parent, Dialog)

        local_files = directory.files
        uploaded_files = directory.uploaded
        unexpected_files = directory.unexpected

        for item in self.items():
            text = item.text()
            # Remove.
            if text not in local_files:
                widget.takeItem(widget.indexFromItem(item).row())
            # Uncheck.
            elif item.checkState() \
                    and isinstance(self.directory.get_dest(text), Exception):
                item.setCheckState(Qt.Unchecked)

        for i in local_files:
            # Add.
            try:
                item = widget.findItems(
                    i, Qt.MatchExactly)[0]
            except IndexError:
                item = QListWidgetItem(i, widget)
                item.setCheckState(Qt.Unchecked)
            # Set style.
            dest = self.directory.get_dest(i)
            if i in uploaded_files:
                item.setFlags(Qt.ItemIsEnabled)
                item.setForeground(brushes['uploaded'])
                item.setCheckState(Qt.Unchecked)
                tooltip = '已上传至: {}'.format(dest)
            elif i in unexpected_files:
                item.setFlags(Qt.ItemIsUserCheckable |
                              Qt.ItemIsEnabled)
                item.setForeground(brushes['error'])
                tooltip = l10n(dest)
            else:
                item.setFlags(Qt.ItemIsUserCheckable |
                              Qt.ItemIsEnabled)
                item.setForeground(brushes['local'])
                tooltip = '将上传至: {}'.format(dest)
            item.setToolTip(tooltip)

        widget.sortItems()

        parent.labelCount.setText(
            '{}/{}/{}'.format(
                len(list(self.checked_files)),
                len(local_files) - len(self.directory.uploaded),
                len(local_files)))

        self.updating = False

    @property
    def checked_files(self):
        """Return files checked in listwidget.  """

        return (i.text() for i in self.items() if i.checkState())

    @property
    def is_use_burnin(self):
        """Use burn-in version when preview.  """

        return self.parent.checkBoxBurnIn.checkState()

    @Slot(QListWidgetItem)
    def open_file(self, item):
        """Open mov file for preview.  """

        filename = item.text()
        path = os.path.join(self.directory.path, filename)
        burn_in_path = os.path.join(
            self.directory.path, self.burnin_folder, filename)

        webbrowser.open(burn_in_path
                        if self.is_use_burnin and os.path.exists(burn_in_path)
                        else path)

    def items(self):
        """Item in list widget -> list."""

        widget = self.widget
        return list(widget.item(i) for i in xrange(widget.count()))

    def select_all(self):
        """Select all item in list widget.  """

        uploaded = self.directory.uploaded
        unexpected = self.directory.unexpected

        files = [i for i in self.directory.files if i not in uploaded.union(
            unexpected)]
        refresh = False
        if not files:
            files = [
                i for i in self.directory.files if i not in uploaded]
            refresh = True

        if not files:
            return

        for item in self.items():
            if item.text() in files:
                item.setCheckState(Qt.Checked)
        if refresh:
            self.update_directory()

    def reverse_selection(self):
        """Select all item in list widget.  """

        for item in self.items():
            if item.text() not in self.directory.uploaded:
                if item.checkState():
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)


def l10n(obj):
    """Localization.  """

    ret = obj
    if isinstance(ret, cgtwq.LoginError):
        ret = '需要登录CGTeamWork'
    elif isinstance(ret, cgtwq.AccountError):
        ret = '已被分配给: {}\n当前用户: {}'.format(
            ret.owner or u'<未分配>', ret.current)
    elif isinstance(ret, cgtwq.IDError):
        ret = 'CGTW上未找到对应镜头'

    return unicode(ret)


class ShotsFileDirectory(QObject):
    """Directory that store shots output files.  """

    pipeline_ext = {
        '灯光': ('.jpg', '.png', '.jpeg'),
        '渲染': ('.mov'),
        '合成': ('.mov'),
    }
    dest_dict = None
    changed = Signal()
    updating = False
    _uploaded = None

    def __init__(self, path, pipeline, dest=None, parent=None):
        assert os.path.exists(
            path), '{} is not existed.'.format(path)
        assert pipeline in self.pipeline_ext, '{} is not a pipeline'.format(
            pipeline)

        LOGGER.debug('Init directory.')
        super(ShotsFileDirectory, self).__init__()
        self.path = path
        self.pipeline = pipeline
        self.ext = self.pipeline_ext[pipeline]
        self.dest = dest
        self.files = []
        self.dest_dict = {}
        self.parent = parent

        # Direcotry update timer
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(1000)
        self.update_timer.timeout.connect(self.update)

    @run_async
    def update(self):
        """Update directory content.  """

        if self.updating:
            return

        self.updating = True

        if self.update_uploaded():
            self.changed.emit()
        try:
            path = self.path
            prev_files = self.files
            prev_shots = self.shots()
            self.files = version_filter(i for i in os.listdir(path)
                                        if i.lower().endswith(self.ext))
            if prev_files == self.files or self.shots() == prev_shots:
                return

            if not prev_files or set(self.files).difference(prev_files):
                try:
                    self.dest_dict = self.get_dest_dict()
                except CancelledError:
                    self.dest_dict = {}
                    LOGGER.info('用户取消获取信息')
            self.changed.emit()
        finally:
            self.updating = False

    def get_dest_dict(self):
        """Get upload destinations.  """

        def _get_database(filename):
            return cgtwq.proj_info(filename).get('database')

        all_shots = self.shots()
        dest = self.dest
        dest_dict = {}

        proj_info = cgtwq.proj_info(self.files[0] if self.files else None)
        database = proj_info.get('database')

        def _get_from_database(database):
            if self.dest:
                return

            shots = [i for i in all_shots if _get_database(i) == database]
            task = Progress('获取镜头信息',
                            total=len(shots) + 1,
                            parent=self.parent)

            task.step('连接数据库: {}'.format(database))
            try:
                cgtw_shots = cgtwq.Shots(database, pipeline=self.pipeline)
            except cgtwq.CGTeamWorkException:
                self.dest = cgtwq.LoginError()
                return
            for shot in shots:
                task.step(shot)
                try:
                    cgtw_shots.check_account(shot)
                    dest = cgtw_shots.get_shot_submit(shot)
                    dest_dict[shot] = dest
                except cgtwq.CGTeamWorkException as ex:
                    dest_dict[shot] = ex
                except KeyError as ex:
                    dest_dict[shot] = cgtwq.IDError(ex)

        if not dest:
            all_database = set(_get_database(i) for i in self.files)
            for database in all_database:
                _get_from_database(database)

        return dest_dict

    def shots(self):
        """Files related shots.  """

        return sorted(PurePath(i).shot for i in self.files)

    @property
    def unexpected(self):
        """Files that can not get destination.  """

        files = self.files
        ret = set()

        for filename in files:
            dest = self.get_dest(filename)
            if not dest or isinstance(dest, Exception):
                ret.add(filename)
        return ret

    @property
    def uploaded(self):
        """Files that does not need to upload agian.  """

        if self._uploaded is None:
            self.update_uploaded()
        return self._uploaded

    def update_uploaded(self):
        """Update uploaded files.  """

        old_value = self._uploaded
        files = self.files
        ret = set()

        for filename in files:
            src = os.path.join(self.path, filename)
            dst = self.get_dest(filename)

            if isinstance(dst, (str, unicode)) and is_same(src, dst):
                ret.add(filename)

        self._uploaded = ret

        return old_value != ret

    def get_dest(self, filename):
        """Get cgteamwork upload destination for @filename.  """

        ret = self.dest_dict.get(PurePath(filename).shot, self.dest)
        if isinstance(ret, (str, unicode)):
            ret = str(PurePath(ret) / PurePath(filename).as_no_version())
        return ret


def main():
    """Run this script standalone.  """

    main_show_dialog(Dialog)


if __name__ == '__main__':
    main()
