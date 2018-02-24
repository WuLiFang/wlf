# -*- coding=UTF-8 -*-
"""Get information from `shot_task` module.  """
from __future__ import absolute_import, print_function, unicode_literals

import json
import logging
import os
import re

from ..path import Path, PurePath
from .base import CGTeamWork
from .exceptions import AccountError, IDError, PrefixError, SignError
from .public import proj_info

LOGGER = logging.getLogger('com.wlf.cgtwq.shottask')


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
        elif len(id_list) > 1:
            LOGGER.warning('Multiple match %s', id_list)
            for i in list(id_list):
                self.task_module.init_with_id(i['id'])
                try:
                    if self.task_module.get(['shot_task.artist'])[0]['shot_task.artist']:
                        id_list = [i]
                        break
                except (TypeError,KeyError):
                    continue
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
