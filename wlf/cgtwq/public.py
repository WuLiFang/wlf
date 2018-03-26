# -*- coding=UTF-8 -*-
"""Get information from CGTeamWork `public` database.  """

from __future__ import absolute_import, print_function, unicode_literals

import json
import os

from wlf.decorators import deprecated

from .base import CGTeamWork


@deprecated('Public')
class _Public(CGTeamWork):
    """Public database for project and account info.  """
    database = 'public'


@deprecated('Project')
class _Project(_Public):
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


@deprecated
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
