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
import json
import time
from logging import getLogger
from subprocess import PIPE, Popen
from tempfile import mktemp

from .path import Path, get_encoded as e, get_unicode as u

LOGGER = getLogger('com.wlf.ffmpeg')


def generate_gif(filename, output=None, **kwargs):
    """Generate a gif with same name.  """

    path = Path(filename)
    width = kwargs.get('width')
    height = kwargs.get('height')
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
    os.utime(e(ret), (time.time(), path.stat().st_mtime))

    LOGGER.info('生成GIF: %s', ret)
    return ret


def generate_mp4(filename, output=None, **kwargs):
    """Convert a video file to mp4 format.

    Args:
        filename (path): File to convert.
        output (path, optional): Defaults to None. Output filepath.

    Returns:
        wlf.Path: output path.
    """

    path = Path(filename)
    ret = Path(output or path).with_suffix('.mp4')
    width = kwargs.get('width')
    height = kwargs.get('height')
    duration = kwargs.get('duration')
    output_options = [
        '-movflags faststart',
        '-vcodec libx264',
        '-pix_fmt yuv420p',
        '-f mp4'
    ]
    if duration > 0:
        output_options.append('-t {}'.format(duration))
    output_options.append('-vf scale="{}:{}:flags=lanczos"'.format(
        '-2' if width is None else int(width) // 2 * 2,
        r'min(trunc(ih / 2) * 2\, 1080)' if height is None else int(height) // 2 * 2))

    # Skip generated.
    if ret.exists() and abs(path.stat().st_mtime - ret.stat().st_mtime) < 1e-06:
        return ret

    # Generate.
    cmd = ('ffmpeg -y -hide_banner -i "{}" {} "{}"').format(
        filename, ' '.join(output_options), ret)
    _try_run_cmd(cmd, 'Error during generate mp4', cwd=str(ret.parent))
    LOGGER.info('生成mp4: %s', ret)

    # Copy mtime for skip generated.
    os.utime(e(ret), (time.time(), path.stat().st_mtime))

    return ret


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
    ret = Path(output or path).with_suffix('.jpg')
    _filters = 'scale="{}:{}:flags=lanczos"'.format(
        '-1' if width is None else int(width),
        r'min(ih\, 1080)' if height is None else int(height))

    # Skip generated.
    if ret.exists() and abs(path.stat().st_mtime - ret.stat().st_mtime) < 1e-06:
        return ret

    try:
        seekstart = probe(path).duration() / 2
    except (ValueError, KeyError):
        seekstart = 0

    # Generate.
    cmd = ('ffmpeg -y -hide_banner '
           '-noaccurate_seek -i "{}" -vframes 1 -ss {} '
           '-vf {} "{}"').format(
        filename, seekstart, _filters, ret)
    _try_run_cmd(cmd, 'Error during generate jpg', cwd=str(ret.parent))
    LOGGER.info('生成jpg: %s', ret)

    # Copy mtime for skip generated.
    os.utime(e(ret), (time.time(), path.stat().st_mtime))

    return ret


class ProbeResult(dict):
    """Optimized dict for probe result.  """

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

        assert isinstance(exp, (unicode, str))
        return reduce(lambda a, b: float(a) / float(b), exp.split('/'))


def probe(filename):
    """Probe for media file info.

    Args:
        filename (pathLike object): file path. 

    Returns:
        ProbeResult: Optimized dict to save result.
    """

    cmd = ('ffprobe -show_entries format:streams '
           '-of json -hide_banner "{}"').format(u(filename))
    proc = Popen(e(cmd), stdout=PIPE, stderr=PIPE, env=os.environ)
    stdout, _ = proc.communicate()
    ret = json.loads(stdout)
    return ProbeResult(ret)


def _try_run_cmd(cmd, error_msg, **popen_kwargs):
    kwargs = {
        'stdout': PIPE,
        'stderr': PIPE,
        'env': os.environ
    }
    kwargs.update(popen_kwargs)

    proc = Popen(e(cmd), **kwargs)
    stderr = proc.communicate()[1]
    if proc.wait():
        raise GenerateError(
            '%s:\n\t %s\n\t%s' % (u(error_msg), u(cmd), u(stderr)))


class GenerateError(RuntimeError):
    """Exception during generate.  """
    pass
