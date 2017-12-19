# -*- coding=UTF-8 -*-
"""Manipulate video with FFMPEG."""
from __future__ import absolute_import, print_function, unicode_literals

import os
import time
from logging import getLogger
from subprocess import PIPE, Popen
from tempfile import mktemp

from .path import Path, get_encoded

LOGGER = getLogger('com.wlf.ffmpeg')


def generate_gif(filename, output=None, width=None, height=300):
    """Generate a gif with same name.  """

    path = Path(filename)
    _palette = mktemp('.png')
    _filters = 'fps=15,scale={}:{}:flags=lanczos'.format(
        -1 if width is None else width,
        -1 if height is None else height)
    ret = Path(output or path).with_suffix('.gif')

    # Skip generated.
    if ret.exists() and abs(path.stat().st_mtime - ret.stat().st_mtime) < 1e-06:
        # LOGGER.info('跳过已有GIF生成: %s', ret)
        return ret

    # Generate palette
    cmd = ('ffmpeg -i "{0[filename]}" '
           '-vf "{0[_filters]}, palettegen" '
           '-y "{0[_palette]}"').format(locals())
    # LOGGER.debug(cmd)
    proc = Popen(get_encoded(cmd),
                 cwd=str(ret.parent),
                 stdout=PIPE, stderr=PIPE,
                 env=os.environ)
    stderr = proc.communicate()[1]
    if proc.wait():
        raise RuntimeError(
            'Error during generate gif palette:\n\t %s\n\t%s' % (cmd, stderr))
    # Generate gif
    cmd = (u'ffmpeg -i "{0[filename]}" -i "{0[_palette]}" '
           '-lavfi "{0[_filters]} [x]; [x][1:v] paletteuse" '
           '-y "{0[ret]}"').format(locals())
    # LOGGER.debug(cmd)
    proc = Popen(get_encoded(cmd),
                 cwd=str(ret.parent),
                 stdout=PIPE, stderr=PIPE,
                 env=os.environ)
    stderr = proc.communicate()[1]
    if proc.wait():
        raise RuntimeError(
            'Error during generate gif:\n\t %s\n\t%s' % (cmd, stderr))

    # Copy mtime for skip generated.
    os.utime(get_encoded(ret), (time.time(), path.stat().st_mtime))

    LOGGER.info('生成GIF: %s', ret)
    return ret
