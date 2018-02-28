# -*- coding=UTF-8 -*-
"""Query info from cgteamwork.  """

from __future__ import absolute_import, print_function, unicode_literals

from ..env import has_cgtw
from .exceptions import (AccountError, CGTeamWorkException, IDError,
                         PrefixError, SignError, LoginError)
from .client import CGTeamWorkClient

MODULE_ENABLE = has_cgtw()

if MODULE_ENABLE:
    from . import patches
    from .base import CGTeamWork, Filebox, Pipeline
    from .public import Project, Public, proj_info
    from .database import ACCOUNT, PROJECT
    from .shottask import Shot, Shots, ShotTask
    from .database import Database
    from .filter import Filter, FilterList

    # Apply patch.
    patches.patch_tw_lib()
    # patches.patch_tw_local_con()
    patches.patch_tw_message()
