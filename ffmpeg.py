# -*- coding=UTF-8 -*-
"""Manipulate video with FFMPEG."""
from __future__ import absolute_import, print_function, unicode_literals

# Use gevent
try:
    from gevent import monkey
    monkey.patch_subprocess()
except ImportError:
    pass


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
        return ret

    # Generate palette
    cmd = ('ffmpeg -i "{0[filename]}" '
           '-vf "{0[_filters]}, palettegen" '
           '-y "{0[_palette]}"').format(locals())
    _try_run_cmd(cmd, 'Error during generate gif palette', cwd=str(ret.parent))
    # Generate gif
    cmd = (u'ffmpeg -i "{0[filename]}" -i "{0[_palette]}" '
           '-lavfi "{0[_filters]} [x]; [x][1:v] paletteuse" '
           '-y "{0[ret]}"').format(locals())
    _try_run_cmd(cmd, 'Error during generate gif', cwd=str(ret.parent))

    # Copy mtime for skip generated.
    os.utime(get_encoded(ret), (time.time(), path.stat().st_mtime))

    LOGGER.info('生成GIF: %s', ret)
    return ret


def generate_mp4(filename, output=None, width=None, height=None):
    """Convert a video file to mp4 format.

    Args:
        filename (path): File to convert.
        output (path, optional): Defaults to None. Output filepath.

    Returns:
        wlf.Path: output path.
    """

    path = Path(filename)
    ret = Path(output or path).with_suffix('.mp4')
    _filters = 'scale="{}:{}:flags=lanczos"'.format(
        '-2' if width is None else int(width) // 2 * 2,
        r'min(ih\, 1080)' if height is None else int(height) // 2 * 2)

    # Skip generated.
    if ret.exists() and abs(path.stat().st_mtime - ret.stat().st_mtime) < 1e-06:
        return ret

    # Generate.
    cmd = 'ffmpeg -y -i "{}" -movflags faststart -vf {} -vcodec libx264 -pix_fmt yuv420p -f mp4 "{}"'.format(
        filename, _filters, ret)
    _try_run_cmd(cmd, 'Error during generate mp4', cwd=str(ret.parent))
    LOGGER.info('生成mp4: %s', ret)

    # Copy mtime for skip generated.
    os.utime(get_encoded(ret), (time.time(), path.stat().st_mtime))

    return ret


def _try_run_cmd(cmd, error_msg, **popen_kwargs):
    kwargs = {
        'stdout': PIPE,
        'stderr': PIPE,
        'env': os.environ
    }
    kwargs.update(popen_kwargs)

    proc = Popen(get_encoded(cmd), **kwargs)
    stderr = proc.communicate()[1]
    if proc.wait():
        raise GenerateError(
            '%s:\n\t %s\n\t%s' % (error_msg, cmd, stderr))


class GenerateError(RuntimeError):
    """Exception during generate.  """
    pass
