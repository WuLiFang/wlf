# -*- coding=UTF-8 -*-
"""Localizaiton pyblish built-in plugins.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import json
from functools import wraps

import pyblish.api  # pylint: disable=import-error
from pyblish.plugin import discover  # pylint: disable=import-error

from ..filetools import module_path
from ..path import Path


def translate_pyblish_plugin(plugins):
    """Translate plugin infos.

    Args:
        plugins (list): Pyblish plugin list.
    """

    with Path(module_path('data', 'pyblish_translate.json')).open(encoding='utf-8') as f:
        tr_dict = json.load(f)

    def _tr(obj, attr):
        value = getattr(obj, attr)
        if value:
            tr_value = tr_dict.get(value)
            if tr_value:
                setattr(obj, attr, tr_value)

    for i in plugins:
        _tr(i, 'label')
        _tr(i, '__doc__')


def patch_pyblish_discover():
    """Add translate after discover.   """

    @wraps(discover)
    def _func(*args, **kwargs):
        ret = discover(*args, **kwargs)
        translate_pyblish_plugin(ret)
        return ret

    pyblish.api.discover = _func
