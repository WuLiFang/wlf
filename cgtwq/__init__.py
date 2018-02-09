# -*- coding=UTF-8 -*-
"""Query info from cgteamwork.  """

from __future__ import absolute_import, print_function, unicode_literals

from ..env import has_cgtw
from .exceptions import (AccountError, CGTeamWorkException, IDError,
                         PrefixError, SignError)
from .client import CGTeamWorkClient

MODULE_ENABLE = has_cgtw()

if MODULE_ENABLE:
    from . import patches
    from .base import CGTeamWork, Filebox, Pipeline
    from .public import Account, Project, Public
    from .shottask import Shot, Shots, ShotTask

    # Apply patch.
    patches.patch_tw_lib()
    patches.patch_tw_local_con()
    patches.patch_tw_message()
