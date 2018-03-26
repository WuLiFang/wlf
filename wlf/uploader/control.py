# -*- coding=UTF-8 -*-
"""Uploader control.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os

from Qt.QtCore import QObject, QTimer, Signal

from .. import __version__, cgtwq
from ..decorators import run_async
from ..files import is_same, version_filter
from ..notify import CancelledError, progress
from ..path import PurePath
from .util import LOGGER


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

            try:
                cgtw_shots = cgtwq.Shots(database, pipeline=self.pipeline)
            except cgtwq.CGTeamWorkException:
                self.dest = cgtwq.LoginError()
                return
            for shot in progress(shots, '获取镜头信息', parent=self.parent):
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
            for database in progress(all_database, '连接数据库', parent=self.parent):
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
