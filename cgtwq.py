# -*- coding=UTF-8 -*-
"""Query info from cgteamwork.  """

from __future__ import print_function, unicode_literals

import datetime
import socket
import json
import logging
import os
import re
import sys
import traceback
from collections import namedtuple
from functools import wraps
from subprocess import PIPE, Popen

from .path import Path, PurePath, get_unicode

LOGGER = logging.getLogger('com.wlf.cgtwq')
logging.basicConfig()

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
        field_info = self._infos[shot][field_sign]
        key = self.image_path_key

        # Try use field info first
        if field_info:
            field_info = json.loads(field_info)
            if key in field_info:
                return field_info[key]

        image = PurePath(shot).with_suffix('.jpg')

        # Get from filebox
        for filebox_sign in ('image', 'submit'):
            dir_ = _get_path(filebox_sign)
            if dir_:
                image = PurePath(dir_) / image
                break

        image = unicode(image)

        # Record result for accelerate next run.
        field_info = field_info or {}
        field_info[key] = image
        self.task_module.set({field_sign: json.dumps(field_info)})

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


CGTeamWorkClientStatus = namedtuple(
    'CGTeamWorkClientStatus',
    ['server_ip', 'server_http', 'token', 'executable'])


class CGTeamWorkClient(object):
    """Query from CGTeamWork gui clients.  """

    url = "ws://127.0.0.1:64999"
    time_out = 1

    def __init__(self):
        # Get client executable.
        if MODULE_ENABLE:
            executable = os.path.abspath(os.path.join(
                cgtw.__file__, '../../cgtw/CgTeamWork.exe'))
        else:
            # Try use default when sys.path not been set correctly.
            executable = "C:/cgteamwork/bin/cgtw/CgTeamWork.exe"

        if not os.path.exists(executable):
            executable = None

        # Start client if not running.
        if executable and not self.is_running():
            Popen(executable,
                  cwd=os.path.dirname(executable),
                  close_fds=True)

        self.status = CGTeamWorkClientStatus(
            server_ip=self.server_ip(),
            server_http=self.server_http(),
            token=self.token(),
            executable=executable
        )

    @classmethod
    def is_running(cls):
        """Check if client is running.

        Returns:
            bool: Ture if client is running.
        """

        try:
            cls.token()
            return True
        except socket.error:
            pass

        return False

    @classmethod
    def is_logged_in(cls):
        """Check if client is logged in.

        Returns:
            bool: True if client is logged in.
        """

        try:
            if cls.token():
                return True
        except socket.error:
            pass

        return False

    @classmethod
    def get_plugin_data(cls, uuid):
        """Get plugin data for uuid.

        Args:
            uuid (unicode): Plugin uuid.
        """

        return cls.send_main_widget(method_name="get_plugin_data", plugin_uuid=uuid)

    @classmethod
    def send_plugin_result(cls, uuid, result=False):
        """
        Tell client plugin execution result.
        if result is `False`, following operation will been abort.

        Args:
            uuid (unicode): Plugin uuid.
            result (bool, optional): Defaults to False. Plugin execution result.
        """

        cls.send_main_widget(method_name="exec_plugin_result",
                             uuid=uuid,
                             result=result,
                             type='send')

    @classmethod
    def refresh(cls, database, module):
        """
        Refresh specified view in client
        if matched view is opened.

        Args:
            database (unicode): Database of view.
            module (unicode): Module of view.
        """

        cls.send(
            module=module,
            database=database,
            class_name='view_control',
            method_name='refresh',
            type='send',
        )

    @classmethod
    def refresh_select(cls, database, module):
        """
        Refresh selected part of specified view in client
        if matched view is opened.

        Args:
            database (unicode): Database of view.
            module (unicode): Module of view.
        """

        cls.send(
            module=module,
            database=database,
            class_name='view_control',
            method_name='refresh_select',
            type='send',
        )

    @classmethod
    def token(cls):
        """Client token.  """

        ret = cls.send_main_widget(method_name="get_token")
        if ret is True:
            return
        return ret

    @classmethod
    def server_ip(cls):
        """Server ip current using by client.  """

        ret = cls.send_main_widget(method_name="get_server_ip")
        if ret is True:
            return
        return ret

    @classmethod
    def server_http(cls):
        """Server http current using by client.  """

        ret = cls.send_main_widget(method_name="get_server_http")
        if ret is True:
            return
        return ret

    @classmethod
    def send_main_widget(cls, **data):
        """Send data to main widget.

        Args:
            **data (dict): Data to send.

        Returns:
            dict or unicode: Recived data.
        """

        return cls.send(
            module="main_widget",
            database="main_widget",
            class_name="main_widget",
            **data)

    @classmethod
    def send(cls, **data):
        """Send data to gui progress.

        Args:
            **data (dict): Data to send.

        Returns:
            dict or unicode: Recived data.
        """

        from websocket import create_connection

        default = {
            'type': 'get'
        }
        default.update(data)
        data = default

        conn = create_connection(cls.url, cls.time_out)

        try:
            conn.send(json.dumps(data))
            recv = conn.recv()
            ret = json.loads(recv)
            ret = ret['data']
            try:
                ret = json.loads(ret)
            except (TypeError, ValueError):
                pass
            return ret
        finally:
            conn.close()


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

# Patch for cgtw module.


def patch_tw_message():
    """Change tw message format.  """

    func = cgtw.tw.sys.message_error

    @wraps(func)
    def _func(self, msg, title='Error'):  # pylint: disable=unused-argument
        stack = b'\n'.join(traceback.format_stack()[:-1])
        stack = get_unicode(stack)
        LOGGER.error('[%s]%s\n%s', title, msg, stack)

    cgtw.tw.sys.message_error = _func


def patch_tw_lib():
    """Raise LoginError if not loged in.  """

    func = cgtw.tw.lib.format_data

    @wraps(func)
    def _func(data, sign):
        if data == 'please login!!!':
            raise LoginError(data, sign)
        return func(data, sign)

    cgtw.tw.lib.format_data = staticmethod(_func)


def patch_tw_local_con():
    """Reimplement websocket send.  """

    # pylint: disable=protected-access
    @staticmethod
    def _send(T_module, T_database, T_class_name, T_method_name, T_data, T_type="get"):
        """Wrapped function for cgtw path.  """
        # pylint: disable=invalid-name, too-many-arguments, bare-except
        try:
            return CGTeamWorkClient.send(
                module=T_module,
                database=T_database,
                class_name=T_class_name,
                method_name=T_method_name,
                type=T_type,
                **T_data
            )
        except:
            return False

    cgtw.tw.local_con._send = _send


if MODULE_ENABLE:
    patch_tw_message()
    patch_tw_lib()
    patch_tw_local_con()
