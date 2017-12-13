# -*- coding=UTF-8 -*-
"""wlf studio common lib.  """
from __future__ import absolute_import

import os
import sys
from .path import PurePath
from ._dep import Qt

# Remap deprecated module.
# TODO: Remove at next major version.
from . import notify as progress
from . import notify as message
sys.modules[__name__ + '.Qt'] = Qt

__version__ = '0.1.0'

# Add scandir
if 'scandir' not in os.__all__:
    from ._dep import scandir
    os.__all__.append('scandir')
    os.scandir = scandir.scandir
    os.walk = scandir.walk

# Add bin folder to path.
BIN_FOLDER = str(PurePath(__file__).parent / 'bin')
if BIN_FOLDER not in os.environ['path']:
    os.environ['path'] = BIN_FOLDER + os.pathsep + os.environ['path']
