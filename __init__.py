# -*- coding=UTF-8 -*-
"""wlf studio common lib.  """

__version__ = '0.1.0'

# Add scandir
import os
if 'scandir' not in os.__all__:
    import wlf.scandir
    os.__all__.append('scandir')
    os.scandir = wlf.scandir.scandir
    os.walk = wlf.scandir.walk
