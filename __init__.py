# -*- coding=UTF-8 -*-
"""wlf studio common lib.  """

from __future__ import absolute_import


import os
import sys

__version__ = '0.2.4'

BIN_FOLDER = 'bin'


def _setup():
    from os.path import dirname, abspath, join
    from site import addsitedir

    __folder__ = dirname(abspath(__file__))
    dirname = join(__folder__, 'site-packages')
    addsitedir(dirname)

    # Add bin folder to path.
    bin_folder = join(__folder__, BIN_FOLDER)
    if bin_folder not in os.environ['path']:
        os.environ['path'] = bin_folder + os.pathsep + os.environ['path']
    setattr(sys.modules[__name__], 'BIN_FOLDER', bin_folder)


def _init():
    import Qt
    import scandir

    from .path import PurePath

    def _set_attr(name, value):
        setattr(sys.modules[__name__], name, value)
        sys.modules['{}.{}'.format(__name__, name)] = value

    # Remap deprecated module.
    # TODO: Remove at next major version.
    try:
        from .csheet import __main__ as csheet_tool
        _set_attr('csheet_tool', csheet_tool)
    except ImportError:
        pass

    try:
        from . import notify
        _set_attr('progress', notify)
        _set_attr('message', notify)
    except ImportError:
        pass

    _set_attr('Qt', Qt)
    for i in Qt.__all__:
        sys.modules['{}.Qt.{}'.format(__name__, i)] = getattr(Qt, i)

    # Add scandir
    if 'scandir' not in os.__all__:
        os.__all__.append('scandir')
        os.scandir = scandir.scandir
        os.walk = scandir.walk


_setup()
_init()
