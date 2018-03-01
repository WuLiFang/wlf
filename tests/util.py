# -*- coding=UTF-8 -*-
"""Test utilities.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from unittest import TestCase, main, skipIf

from wlf.cgtwq import CGTeamWorkClient

skip_if_not_logged_in = skipIf(not CGTeamWorkClient.is_logged_in(),
                               'CGTeamWork is not logged in.')
