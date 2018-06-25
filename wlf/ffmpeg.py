# -*- coding=UTF-8 -*-
"""Manipulate video with FFMPEG."""
from __future__ import absolute_import, print_function, unicode_literals

import json
import mimetypes
import os
import time
from logging import getLogger
from subprocess import PIPE
from tempfile import mktemp

import six

from .codectools import get_encoded as e
from .codectools import get_unicode as u
from .decorators import run_with_semaphore
from .fileutil import is_same
from .path import Path

try:
    from gevent.subprocess import Popen
except ImportError:
    from subprocess import Popen  # pylint: disable=ungrouped-imports
if six.PY3:
    from functools import reduce  # pylint: disable=redefined-builtin

LOGGER = getLogger('com.wlf.ffmpeg')


@run_with_semaphore(2)
def generate_gif(filename, output=None, **kwargs):
    """Generate a gif with same name.  """

    path = Path(filename)
    width = kwargs.get('width')
    height = kwargs.get('height')
    _palette = mktemp('.png')
    _filters = 'fps=15,scale={}:{}:flags=lanczos'.format(
        -1 if width is None else width,
        -1 if height is None else height)
    ret = Path(Path(output or path).with_suffix('.gif'))

    # Skip generated.
    if is_same(path, ret):
        return ret

    # Generate palette
    cmd = ['ffmpeg', '-i', filename,
           '-vf', '{}, palettegen'.format(_filters),
           '-y', _palette]
    _try_run_cmd(cmd, 'Error during generate gif palette',
                 cwd=str(ret.parent))
    # Generate gif
    cmd = ['ffmpeg', '-i', filename,
           '-i', _palette, '-lavfi', '{} [x]; [x][1:v] paletteuse'.format(
               _filters),
           '-y', ret]
    start_time = time.clock()
    _try_run_cmd(cmd, 'Error during generate gif', cwd=str(ret.parent))

    # Copy mtime for skip generated.
    os.utime(e(ret), (time.time(), path.stat().st_mtime))

    LOGGER.info('生成GIF: %s, 耗时 %s 秒', ret, time.clock() - start_time)
    return ret


@run_with_semaphore(1)
def generate_mp4(filename, output=None, **kwargs):
    """Convert a video file to mp4 format.

    Args:
        filename (path): File to convert.
        output (path, optional): Defaults to None. Output filepath.

    Returns:
        wlf.Path: output path.
    """

    path = Path(filename)
    ret = Path(Path(output or path).with_suffix('.mp4'))
    width = kwargs.get('width')
    height = kwargs.get('height')
    duration = kwargs.get('duration')
    limit_size = kwargs.get('limit_size')

    output_options = [
        '-movflags', 'faststart',
        '-vcodec', 'libx264',
        '-preset', 'veryslow',
        '-tune', 'fastdecode',
        '-crf', '18',
        '-pix_fmt', 'yuv420p',
        '-f', 'mp4'
    ]
    if duration and duration > 0:
        output_options.extend(['-t', duration])
    if limit_size:
        output_options.extend(['-fs', limit_size])

    output_options.extend(['-vf',
                           'scale={}:{}:flags=lanczos'.format(
                               '-2'
                               if width is None else int(width) // 2 * 2,
                               r'min(trunc(ih / 2) * 2\, 1080)'
                               if height is None else int(height) // 2 * 2)])

    # Skip generated.
    if is_same(path, ret):
        return ret

    # Generate.
    cmd = (['ffmpeg', '-y', '-hide_banner', '-i', filename]
           + output_options+[ret])
    start_time = time.clock()
    _try_run_cmd(cmd, 'Error during generate mp4', cwd=str(ret.parent))
    LOGGER.info('生成mp4: %s, 耗时 %s 秒', ret, time.clock() - start_time)

    # Copy mtime for skip generated.
    os.utime(e(ret), (time.time(), path.stat().st_mtime))

    return ret


@run_with_semaphore(8)
def generate_jpg(filename, output=None, **kwargs):
    """Convert given file to jpg format.

    Args:
        filename (path): File to convert.
        output (path, optional): Defaults to None. Output filepath.

    Returns:
        wlf.Path: output path.
    """

    path = Path(filename)
    width = kwargs.get('width')
    height = kwargs.get('height')
    ret = Path(Path(output or path).with_suffix('.jpg'))
    _filters = 'scale={}:{}:flags=lanczos'.format(
        '-1' if width is None else int(width),
        r'min(ih\, 1080)' if height is None else int(height))

    # Skip generated.
    if is_same(path, ret):
        return ret

    input_options = [
        '-noaccurate_seek'
    ]

    type_, _ = mimetypes.guess_type(six.text_type(path))
    if six.text_type(type_).startswith('video/'):
        try:
            mediainfo = probe(path)
            if mediainfo.frames() > 1:
                input_options.extend(['-ss', mediainfo.duration() / 2])
        except (ValueError, KeyError):
            pass

    # Generate.
    cmd = (['ffmpeg', '-y', '-hide_banner']
           + input_options
           + ['-i', filename, '-q:v', '1',
              '-vframes', '1', '-vf', _filters, ret])
    start_time = time.clock()
    _try_run_cmd(cmd, 'Error during generate jpg', cwd=str(ret.parent))
    LOGGER.info('生成jpg: %s, 耗时 %s 秒', ret, time.clock() - start_time)

    # Copy mtime for skip generated.
    os.utime(e(ret), (time.time(), path.stat().st_mtime))

    return ret


class ProbeResult(dict):
    """Optimized dict for probe result.  """

    error = None

    def fps(self):
        """FPS for the file.

        Raises:
            ValueError: FPS unknown.

        Returns:
            float: FPS value.
        """

        video_streams = [i for i in self['streams']
                         if i['codec_type'] == 'video']
        for i in video_streams:
            value = self.parse_div(i['r_frame_rate'])
            if value:
                return value

        raise ValueError('Can not determinate fps')

    def duration(self):
        """File duration in secondes.

        Returns:
            float: media duration.
        """

        return float(self['format']['duration'])

    def frames(self):
        """Frames in this file.

        Returns:
            int: frame count.
        """

        return int(round(self.duration() * self.fps()))

    @classmethod
    def parse_div(cls, exp):
        """Parse divsion expression to float.

        Args:
            exp (unicode): expression given by ffprobe

        Returns:
            float: caculate result.
        """

        assert isinstance(exp, (six.binary_type, six.text_type))
        return reduce(lambda a, b: float(a) / float(b), exp.split('/'))


@run_with_semaphore(2)
def probe(filename):
    """Probe for media file info.

    Args:
        filename (pathLike object): file path.

    Returns:
        ProbeResult: Optimized dict to save result.
    """

    cmd = ['ffprobe', '-show_entries', 'format:streams',
           '-of', 'json', '-hide_banner',
           '-loglevel', 'error', filename]
    proc = Popen([e(i) for i in cmd], stdout=PIPE, stderr=PIPE, env=os.environ)
    stdout, stderr = proc.communicate()
    ret = json.loads(stdout)
    ret = ProbeResult(ret)
    ret.error = stderr
    return ret


def _try_run_cmd(cmd, error_msg, **popen_kwargs):
    kwargs = {
        'stdout': PIPE,
        'stderr': PIPE,
        'env': os.environ
    }
    kwargs.update(popen_kwargs)

    cmd = [e(i) if six.PY2 else u(i) for i in cmd]

    proc = Popen(cmd, **kwargs)
    _, stderr = proc.communicate()
    if proc.wait():
        raise GenerateError(
            '%s:\n\t %s\n\t%s' % (u(error_msg), u(cmd), u(stderr)))


class GenerateError(RuntimeError):
    """Exception during generate.  """
    pass
