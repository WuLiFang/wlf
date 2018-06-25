# -*- coding=UTF-8 -*-
"""wlf studio tool library.  """

from __future__ import absolute_import

import os
import sys

from .__about__ import __version__

BIN_FOLDER = 'bin'


def _setup():
    from os.path import dirname, abspath, join

    __folder__ = dirname(abspath(__file__))

    # Add bin folder to path.
    bin_folder = join(__folder__, BIN_FOLDER)
    _path = os.getenv('path', '')
    if bin_folder not in _path:
        os.environ['path'] = bin_folder + os.pathsep + _path
    setattr(sys.modules[__name__], 'BIN_FOLDER', bin_folder)


def _init():
    # Add scandir
    try:
        import scandir
        if 'scandir' not in os.__all__:
            os.__all__.append('scandir')
            os.scandir = scandir.scandir
            os.walk = scandir.walk
    except ImportError:
        pass


_setup()
_init()
