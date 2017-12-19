# -*- coding=UTF-8 -*-
"""wlf studio common lib.  """
from __future__ import absolute_import

import os
import sys
from site import addsitedir

from .path import PurePath

# Remap deprecated module.
# TODO: Remove at next major version.
from . import notify
progress = notify
message = notify
import Qt
sys.modules['{}.Qt'.format(__name__)] = Qt
for i in Qt.__all__:
    sys.modules['{}.Qt.{}'.format(__name__, i)] = getattr(Qt, i)
from .csheet import __main__ as csheet_tool
sys.modules['{}.csheet_tool'.format(__name__)] = csheet_tool

addsitedir('./site-packages')

__version__ = '0.2.0'
sys.path.append(str(PurePath(__file__).parent / '_dep'))

# Add scandir
if 'scandir' not in os.__all__:
    import scandir
    os.__all__.append('scandir')
    os.scandir = scandir.scandir
    os.walk = scandir.walk

# Add bin folder to path.
BIN_FOLDER = str(PurePath(__file__).parent / 'bin')
if BIN_FOLDER not in os.environ['path']:
    os.environ['path'] = BIN_FOLDER + os.pathsep + os.environ['path']
