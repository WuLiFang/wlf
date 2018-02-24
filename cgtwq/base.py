# -*- coding=UTF-8 -*-
"""Get information from CGTeamWork Database.  """

from __future__ import absolute_import, print_function, unicode_literals

import datetime
import logging
import sys
from collections import namedtuple
from functools import wraps
from subprocess import PIPE, Popen

import cgtw

from ..path import get_unicode
from .client import CGTeamWorkClient
from .exceptions import IDError

LOGGER = logging.getLogger('com.wlf.cgtwq')

Filebox = namedtuple('Filebox', ['id', 'title'])
Pipeline = namedtuple('Pipeline', ['id', 'name'])


class CGTeamWork(object):
    """Base class for cgtw action."""

    is_logged_in = False
    __tw = None
    _task_module = None
    _sys_module = None
    _pipeline_module = None
    _history_module = None
    _filebox_module = None
    database = None
    module = None
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    SIGNS = {'shot': 'shot.shot',
             'pipeline': 'shot_task.pipeline'}

    @property
    def _tw(self):
        if CGTeamWork.__tw is None:
            CGTeamWork.__tw = cgtw.tw()
        return CGTeamWork.__tw

    def reset(self):
        """Reset connection.  """

        LOGGER.debug('Reset connection.')
        CGTeamWork.__tw = None
        self._task_module = None
        self._sys_module = None
        self._pipeline_module = None

    def try_reset(self, func):
        """(Decorator)Try reset connection once if @func fail. """

        @wraps(func)
        def _func(*args, **kwargs):
            ret = func(*args, **kwargs)
            if ret is False:
                LOGGER.warning('%s fail, reset connection', func)
                self.reset()
                ret = func(*args, **kwargs)
            if ret is False:
                raise IDError(args, kwargs)
            return ret
        return _func

    @property
    def task_module(self):
        """CGTeamWork task module for further use. """

        if not self._task_module:
            module = self._tw.task_module(self.database, self.module)
            for func in ('init_with_id', 'init_with_filter'):
                setattr(module,
                        func,
                        self.try_reset(getattr(module, func)))
            self._task_module = module
        return self._task_module

    @property
    def sys_module(self):
        """CGTeamWork sys module for further use. """
        if not self._sys_module:
            self._sys_module = self._tw.sys()
        return self._sys_module

    @property
    def pipeline_module(self):
        """CGTeamWork pipeline for further use. """

        if not self._pipeline_module:
            self._pipeline_module = self._tw.pipeline(self.database)
        return self._pipeline_module

    @property
    def history_module(self):
        """CGTeamWork pipeline for further use. """

        if not self._history_module:
            self._history_module = self._tw.history(self.database, self.module)
        return self._history_module

    @property
    def filebox_module(self):
        """CGTeamWork filebox for further use. """

        if not self._filebox_module:
            self._filebox_module = self._tw.filebox(self.database)
        return self._filebox_module

    def get_filebox(self, pipeline):
        """Get filebox list for @pipeline.  """

        pipeline = self.get_pipeline(pipeline)
        all_data = (self.filebox_module
                    .get_with_pipeline_id(pipeline.id, self.module))
        ret = []
        for data in all_data:
            filebox = Filebox(title=data['title'], id=data['id'])
            ret.append(filebox)
        return ret

    def get_pipeline(self, id_or_name):
        """Get pipeline id for @pipeline.  """

        for i in self.all_pipeline:
            assert isinstance(i, Pipeline)
            if id_or_name in i._asdict().values():
                return i

    @property
    def all_pipeline(self):
        """All pipeline name for this module. """

        return [Pipeline(id=i['id'], name=i['name'])
                for i in self.pipeline_module.get_with_module(self.module, ['name'])]

    @staticmethod
    def update_status():
        """Return and set if cls.is_logged_in."""

        ret = CGTeamWorkClient().is_logged_in()
        CGTeamWork.is_logged_in = ret
        return ret

    @property
    def signs(self):
        """Field sign dict depends on current module.  """

        ret = CGTeamWork.SIGNS
        if self.module == 'shot_task':
            signs = {
                'name': 'shot.shot',
                'artist': 'shot_task.artist',
                'submit_file_path': 'shot_task.submit_file_path',
            }
        else:
            signs = {
                'name': 'asset.cn_name',
                'artist': 'asset_task.artist',
                'submit_file_path': 'asset_task.submit_file_path',
            }
        ret.update(signs)
        return ret

    def current_account(self):
        """Return current account.  """
        return self._tw.sys().get_account()

    def current_account_id(self):
        """Return current account id.  """
        return self._tw.sys().get_account_id()

    def submit(self, file_list, folders=None, note='自nuke提交'):
        """Submit current initiated item to cgtw."""
        if not folders:
            folders = []
        LOGGER.info(u'提交: %s', file_list + folders)
        ret = self._task_module.submit(file_list, note, folders)
        if not ret:
            LOGGER.error(u'提交失败')
        return ret

    def add_note(self, note, distinct=False):
        """Add note for current initiated item on cgtw."""

        if distinct and self.is_note_existed(note):
            return False

        self._task_module.create_note(note)
        return True

    def is_note_existed(self, note):
        """Return if note already added.  """

        info = self.task_module.get_note_with_task_id(['text'])
        notes = [i['text'] for i in info]
        return note in notes

    def login(self, account, password):
        """Log in cgtw with nuke.  """

        ret = self._tw.sys().login(account, password)
        return ret

    def parse_datetime(self, text):
        """Parse teamwork time."""
        return datetime.datetime.strptime(text, self.DATETIME_FORMAT)

    # Code below is for backward campatibility.
    # TODO: delete at next major version.

    @property
    def _server_ip(self):
        """Current server ip.  """
        return self.sys_module.get_server_ip()

    @staticmethod
    def _is_running():
        """Return is CgTeamWork.exe is running.  """

        ret = True
        if sys.platform == 'win32':
            tasklist = Popen('TASKLIST', stdout=PIPE).communicate()[0]
            if '\nCgTeamWork.exe ' not in get_unicode(tasklist):
                ret = False
                LOGGER.debug('未运行 CGTeamWork.exe 。')

        return ret


# pylint: disable=protected-access
setattr(CGTeamWork, 'server_ip',
        CGTeamWork._server_ip)

setattr(CGTeamWork, 'is_running',
        CGTeamWork._is_running)
# pylint: enable=protected-access

# Code above is for backward compatibility.
