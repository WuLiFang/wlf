# -*- coding=UTF-8 -*-
"""wlf studio common lib.  """

import os
import sys
from wlf.path import PurePath

__version__ = '0.1.0'

# Add scandir
if 'scandir' not in os.__all__:
    import wlf.scandir
    os.__all__.append('scandir')
    os.scandir = wlf.scandir.scandir
    os.walk = wlf.scandir.walk

# Add bin folder to path.
BIN_FOLDER = str(PurePath(__file__).parent / PurePath('bin'))
if BIN_FOLDER not in os.environ['path']:
    os.environ['path'] = BIN_FOLDER + os.pathsep + os.environ['path']
