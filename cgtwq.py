# -*- coding=UTF-8 -*-
"""Query info from cgteamwork.

should compatible by any cgteamwork bounded python executable.
"""
from __future__ import print_function, unicode_literals

import datetime
import json
import logging
import os
import re
import sys
from functools import wraps
from subprocess import PIPE, Popen

from .path import Path, PurePath, get_unicode

LOGGER = logging.getLogger('com.wlf.cgtwq')
CGTW_EXECUTABLE = r"C:\cgteamwork\bin\cgtw\CgTeamWork.exe"


# Test if module should be enabled
MODULE_ENABLE = True
try:
    import cgtw
except ImportError:
    LOGGER.warning('CGTeamWork not found, related module disabled.')
    MODULE_ENABLE = False


def proj_info(shot_name=None, database=None):
    """Return current project info by @shot_name or by @database.  """

    with open(os.path.join(__file__, '../cgtwq.project_info.json')) as f:
        all_info = json.load(f)

    ret = all_info['default']
    all_proj = all_info.keys()
    prefixs = dict({all_info[proj]['prefix']: all_info[proj]
                    for proj in all_info if all_info[proj].get('prefix')})
    if database:
        for proj in all_proj:
            if all_info[proj].get('database') == database:
                ret.update(all_info[proj])
                break
    if shot_name:
        for prefix, info in prefixs.items():
            if shot_name.upper().startswith(prefix.upper()):
                ret.update(info)
                break
    return ret


class CGTeamWork(object):
    """Base class for cgtw action."""

    initiated_class = None
    is_logged_in = False
    __tw = None
    _task_module = None
    _sys_module = None
    _pipeline_module = None
    _history_module = None
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
            self._pipeline_module = self._tw.pipeline(self.module)
        return self._pipeline_module

    @property
    def history_module(self):
        """CGTeamWork pipeline for further use. """

        if not self._history_module:
            self._history_module = self._tw.history(self.database, self.module)
        return self._history_module

    @property
    def server_ip(self):
        """Current server ip.  """
        return self.sys_module.get_server_ip()

    @property
    def all_pipeline(self):
        """All pipeline name for this module. """

        sign = 'name'
        return [i[sign] for i in self.pipeline_module.get_with_module(self.module, [sign])]

    @staticmethod
    def is_running():
        """Return is CgTeamWork.exe is running.  """

        ret = True
        if sys.platform == 'win32':
            tasklist = Popen('TASKLIST', stdout=PIPE).communicate()[0]
            if '\nCgTeamWork.exe ' not in get_unicode(tasklist):
                ret = False
                LOGGER.debug('未运行 CGTeamWork.exe 。')
        return ret

    @staticmethod
    def update_status():
        """Return and set if cls.is_logged_in."""

        LOGGER.debug('更新CGTeamWork状态')
        if not CGTeamWork.is_running() and os.path.exists(CGTW_EXECUTABLE):
            ret = False
            Popen(CGTW_EXECUTABLE, cwd=os.path.dirname(CGTW_EXECUTABLE))
        else:
            ret = cgtw.tw().sys().get_socket_status()
        CGTeamWork.is_logged_in = ret
        if ret:
            LOGGER.debug('CGTeamWork连接正常')
        else:
            LOGGER.warning('CGTeamWork未连接')
        return ret

    @property
    def signs(self):
        """Field sign dict depends on current module.  """

        ret = CGTeamWork.SIGNS
        if self.module == 'shot_task':
            signs = {
                'name': 'shot.shot',
                'artist': 'shot_task.artist',
            }
        else:
            signs = {
                'name': 'asset.cn_name',
                'artist': 'asset_task.artist',
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


class ShotTask(CGTeamWork):
    """Shot task base class.  """

    image_path_key = 'image_path'
    signs = {'shot': 'shot.shot',
             'eps': 'eps.eps_name',
             'project_code': 'eps.project_code',
             'artist': 'shot_task.artist',
             'account_id': 'shot_task.account_id',
             'image': 'shot_task.image',
             'submit_path': 'shot_task.submit_file_path'}


class Shots(ShotTask):
    """Deal multple shot at once.  """
    _epsodes = []

    def __init__(self, database, module=None, pipeline=None, prefix=None):
        super(Shots, self).__init__()

        self.database = database
        self._info = proj_info(database=database)
        self.module = module or self._info.get('module')
        self.pipeline = pipeline or self._info.get('pipeline')
        self.prefix = prefix

        filters = []
        if self.pipeline:
            filters.append(['shot_task.pipeline', '=', self.pipeline])

        initiated = self.task_module.init_with_filter(filters)
        if not initiated:
            raise IDError(self.database, filters)
        shots_info = self.task_module.get(self.signs.values())
        if shots_info is False:
            raise IDError(self.database, filters)
        self._infos = dict((i['shot.shot'], i) for i in shots_info
                           if i['shot.shot'])
        self._shots = sorted(
            i for i in self._infos if not prefix or i.startswith(prefix))
        if not self._shots:
            raise PrefixError(prefix)

    @property
    def shots(self):
        """Return shots names.   """

        return self._shots

    @property
    def episodes(self):
        """Episode shots contained.  """

        sign = self.signs['eps']
        if not self._epsodes:
            infos = self.task_module.get(sign)
            if infos:
                self._epsodes = set(i[sign] for i in infos)
        return self._epsodes

    @property
    def episode(self):
        """Single episode if shots only contain it, else return None.  """

        if len(self.episodes) == 1:
            return self.episodes.copy().pop()

    def get_shot_image(self, shot):
        """Get image dest for @shot.  """

        def _get_path(sign):
            try:
                return self.get_shot_filebox_path(shot, sign)
            except SignError:
                return

        field_sign = self.signs['image']
        filed_info = self._infos[shot][field_sign]
        key = self.image_path_key

        # Try use filed info first
        if filed_info:
            filed_info = json.loads(filed_info)
            if key in filed_info:
                return filed_info[key]

        image = PurePath(shot).with_suffix('.jpg')

        # Get from filebox
        for filebox_sign in ('image', 'submit'):
            dir_ = _get_path(filebox_sign)
            if dir_:
                image = PurePath(dir_) / image
                break

        image = unicode(image)

        # Record result for accelerate next run.
        filed_info = filed_info or {}
        filed_info[key] = image
        self.task_module.set({field_sign: json.dumps(filed_info)})

        return image

    def get_shot_submit(self, shot):
        """Get submit dest for @shot.  """

        return self.get_shot_filebox_path(shot, 'submit')

    def get_shot_final(self, shot):
        """Get final dest for @shot.  """

        if self.pipeline not in ('动画'):
            raise SignError
        return self.get_shot_filebox_path(shot, 'final')

    def get_shot_submit_path(self, shot):
        """Get submit file path for @shot. """

        infos = self._infos
        shot_info = infos[shot]
        context = shot_info[self.signs['submit_path']]
        if context is None:
            try:
                files = Path(self.get_shot_final(shot)).glob(
                    '{}.mov'.format(shot))
                for i in files:
                    return i
            except SignError:
                return
            return
        return json.loads(context).get('path')[0]

    def get_shot_filebox_path(self, shot, sign):
        """Get @shot filebox path with @sign.  """

        infos = self._infos
        shot_info = infos[shot]
        id_ = shot_info['id']

        self.task_module.init_with_id(id_)
        filebox = self.task_module.get_filebox_with_sign(sign)
        if isinstance(filebox, dict):
            return filebox['path']
        else:
            raise SignError

    def check_account(self, shot):
        """Return if @shot asigned to current account.  """

        info = self._infos[shot]
        id_list = info['shot_task.account_id']
        id_list = id_list and id_list.split(',')

        if not id_list or self.current_account_id() not in id_list:
            raise AccountError(owner=info.get('shot_task.artist'),
                               current=self.current_account())


class Shot(ShotTask):
    """Methods for single shot action."""

    def __init__(self, name, database=None, pipeline=None):
        super(Shot, self).__init__()

        self._name = name
        self._pipeline = pipeline
        if database:
            self._info = proj_info(database=database)
        else:
            self._info = proj_info(name)

        id_list = self.task_module.get_with_filter(
            [], [['shot.shot', '=', self.name], 'and', ['shot_task.pipeline', '=', self.pipeline]])
        if not id_list:
            raise IDError(self.database, self.module,
                          self.pipeline, self.name)
        elif len(id_list) != 1:
            if ''.join(i['id'] for i in id_list) == 'please login!!!':
                raise LoginError
            raise IDError('Multiple match', id_list)
        self._id = id_list[0]['id']

        self.task_module.init_with_id(self.shot_id)

        self.update_info()

    def update_info(self):
        """Update info from database"""

        infos = self.task_module.get(self.signs.values())[0]
        self._info.update(infos)

    @property
    def info(self):
        """The Shot info as a dictionary.  """
        return self._info

    @property
    def database(self):
        """The database current using.  """
        return self._info.get('database')

    @property
    def module(self):
        """The module current using(e.g. 'shot_task').  """
        return self._info.get('module')

    @property
    def pipeline(self):
        """The module current using(e.g. 'comp').  """

        return self._pipeline or self._info.get('pipeline')

    @property
    def name(self):
        """The name of current shot(e.g. 'ep01_sc001').  """
        return self._name

    @property
    def episode(self):
        """The episode name of current shot(e.g. 'EP14').  """
        return self._info.get('eps.eps_name')

    @property
    def shot_task_folder(self):
        """shot_task_folder on server.  """
        return self._info.get('shot_task_folder')

    @property
    def shot_id(self):
        """The id attribute of shot.  """
        return self._id

    @property
    def artist(self):
        """The aritist field on cgtw.  """
        return self._info.get('shot_task.artist')

    @property
    def artist_id(self):
        """The aritist_id field on cgtw.  """
        return self._info.get('shot_task.account_id')

    @property
    def artists_list(self):
        """The aritists as a list.  """

        return self.artist_id and self.artist_id.split(',')

    @property
    def shot_image(self):
        """The shot_task.image field on cgtw.  """
        return self._info.get('shot_task.image')

    @shot_image.setter
    def shot_image(self, value):
        LOGGER.debug('set_image:%s', value)
        self.task_module.set_image('shot_task.image', value)
        self.update_info()

        # Record for request path
        key = self.image_path_key
        sign = self.signs['image']

        image_info = self._info[sign]
        image_info = json.loads(image_info) if image_info else {}
        image_info[key] = value
        self.task_module.set({sign: image_info})

    @property
    def image_dest(self):
        """The .jpg file upload destination."""
        ret = self._info['image_dest_pat'].format(self._info)
        return ret

    @property
    def video_dest(self):
        """The .mov file upload destination."""
        ret = self._info['video_dest_pat'].format(self._info)
        return ret

    @property
    def workfile_dest(self):
        """The .mov file upload destination."""
        ret = self._info['workfile_dest_pat'].format(self._info)
        return ret

    @property
    def submit_dest(self):
        """Folder path for artist submit.  """

        sign = 'submit'
        info = self.task_module.get_filebox_with_sign(sign)
        if info:
            return info['path']
        else:
            raise SignError(sign)

    def upstream_videos(self):
        """Upstream videos for reference.  """

        upstream_signs = {
            'animation': 'animation_videos'
        }
        ret = {}
        pat = re.compile(r'{}\b'.format(self.name), re.I)
        for pipeline, sign in upstream_signs.items():
            info = self.task_module.get_filebox_with_sign(sign)
            if info:
                video_dir = info['path']
                videos = [i for i in os.listdir(
                    video_dir) if re.match(pat, i)]
                if len(videos) == 1:
                    ret[pipeline] = os.path.join(video_dir, videos[0])
                else:
                    LOGGER.warning('Can not specify video: %s@%s',
                                   self.name, pipeline)
        return ret

    def check_account(self):
        """Return if shot assined to current account.  """

        if not self.artists_list or self.current_account_id() not in self.artists_list:
            raise AccountError(owner=self.artist,
                               current=self.current_account())


class Public(CGTeamWork):
    """Public database for project and account info.  """
    database = 'public'


class Project(Public):
    """The project database.  """
    module = 'project'
    signs = {
        'code': 'project.code',
        'full_name': 'project.full_name',
        'id': 'project.id',
        'status': 'project.status',
        'is_template': 'project.is_template',
        'database': 'project.database',
        'color': 'project.color',
        'start_date': 'project.start_date',
        'end_date': 'project.end_date',
        'image': 'project.image',
        'description': 'project.description',
    }
    _infos = None

    @property
    def infos(self):
        """All avaliable info.  """

        if self._infos is None:
            filters = [('project.status', '=', 'Active')]
            self.task_module.init_with_filter(filters)
            self._infos = self.task_module.get(self.signs.values())
        return self._infos

    def names(self):
        """All project names.  """

        return [i[self.signs['full_name']] for i in self.infos]

    def get_info(self, value, key=None):
        """Get info first project has matched @value.  """

        key = self.signs.get(key, key)
        for i in self.infos:
            if value in i.values():
                if key in i:
                    return i[key]
                return i


class Account(Public):
    """The account database.  """
    module = 'project'


class CGTeamWorkException(Exception):
    """Base exception class for CGTeamWork.  """

    def __init__(self, *args):
        super(CGTeamWorkException, self).__init__()
        self.message = args


class IDError(CGTeamWorkException):
    """Indicate can't specify shot id on cgtw."""

    def __str__(self):
        return 'Can not found item with matched id:{}'.format(self.message)

    def __unicode__(self):
        return '找不到数据库对象: {}'.format(self.message)


class SignError(CGTeamWorkException):
    """Indicate can't found matched sign."""

    def __str__(self):
        return 'Can not found matched sign: {}'.format(self.message)

    def __unicode__(self):
        return '缺少数据库标志: {}'.format(self.message)


class FolderError(CGTeamWorkException):
    """Indicate can't found destination folder."""

    def __str__(self):
        return 'No such folder on server: {}'.format(self.message)

    def __unicode__(self):
        return '不存在服务器文件夹: {}'.format(self.message)


class LoginError(CGTeamWorkException):
    """Indicate can't found destination folder."""

    def __str__(self):
        return 'Not loged in.  \n{}'.format(self.message)

    def __unicode__(self):
        return '未登录或登录失效: {}'.format(self.message)


class PrefixError(CGTeamWorkException):
    """Indicate ."""

    def __init__(self, prefix):
        super(PrefixError, self).__init__(prefix)
        self.prefix = prefix

    def __str__(self):
        return 'Can not found any prefix matched shots: {}'.format(self.prefix)

    def __unicode__(self):
        return '无镜头匹配此前缀: {}'.format(self.message)


class AccountError(CGTeamWorkException):
    """Indicate can't found destination folder."""

    def __init__(self, owner='', current=''):
        CGTeamWorkException.__init__(self)
        self.owner = owner
        self.current = current

    def __str__(self):
        return 'Account not match.  \n{} ==> {}'.format(self.current, self.owner)

    def __unicode__(self):
        return '用户不匹配\n\t已分配给:\t{}\n\t当前用户:\t{}'.format(self.owner or '<未分配>', self.current)
