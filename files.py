# -*- coding=UTF-8 -*-
"""Files operation. """
from __future__ import absolute_import, print_function, unicode_literals

import errno
import logging
import multiprocessing.dummy
import os
import shutil
import sys
import urllib
import warnings
from subprocess import Popen, call

from . import path
from .decorators import deprecated
from .notify import traytip as _traytip
from .notify import Progress
from .path import get_encoded as e
from .path import Path, PurePath

LOGGER = logging.getLogger('com.wlf.files')


def copy(src, dst, threading=False):
    """Copy src to dst."""

    from .path import get_encoded, get_unicode

    def _mkdirs():
        dst_dir = os.path.dirname(dst_e)
        if not os.path.exists(dst_dir):
            LOGGER.debug('创建目录: %s', dst_dir)
            os.makedirs(dst_dir)
        elif os.path.isfile(dst_dir):
            raise ValueError(
                'Can not use file as directory: {}'.format(dst_dir))

    src_e, dst_e = get_encoded(src), get_encoded(dst)
    src_u, dst_u = get_unicode(src), get_unicode(dst)
    # Handle exceptions.
    if src_e == dst_e:
        LOGGER.warning('不能原地复制: %s', src_e)
        return
    elif not os.path.exists(src_e):
        LOGGER.warning('尝试复制不存在的文件: %s', src_u)
        return

    if threading:
        thread = multiprocessing.dummy.Process(
            target=copy, args=(src_e, dst_e), kwargs={'threading': False})
        thread.start()
        return thread

    if src_u.startswith('http:'):
        LOGGER.info('下载:\n\t\t%s\n\t->\t%s', src_u, dst_u)
        _mkdirs()
        try:
            src_fd = urllib.urlopen(src_e)
            with open(dst_e, 'wb') as dst_fd:
                dst_fd.write(src_fd.read())
        finally:
            src_fd.close()
    else:
        LOGGER.info('复制:\n\t\t%s\n\t->\t%s', src_u, dst_u)
        _mkdirs()
        try:
            shutil.copy2(src_e, dst_e)
        except OSError:
            if sys.platform == 'win32':
                call(get_encoded(
                    'XCOPY /V /Y "{}" "{}"'.format(src_e, dst_e)))
            else:
                raise

    if os.path.isdir(get_encoded(dst_e)):
        ret = os.path.join(dst_e, os.path.basename(src_e))
    else:
        ret = dst_e

    ret = get_unicode(ret)
    return ret


def version_filter(iterable):
    """Keep only newest version for each shot, try compare mtime when version is same.

    >>> version_filter(('sc_001_v1', 'sc_001_v2', 'sc002_v3', 'thumbs.db'))
    [u'sc002_v3', u'sc_001_v2', u'thumbs.db']
    """
    shots = {}
    iterable = sorted(
        iterable, key=lambda x: PurePath(x).version, reverse=True)
    for i in iterable:
        path = PurePath(i)
        shot = path.shot.lower()
        version = path.version
        shots.setdefault(shot, {})
        shots[shot].setdefault('path_list', [])
        if version > shots[shot].get('version'):
            shots[shot]['path_list'] = [i]
            shots[shot]['version'] = version
        elif version == shots[shot].get(version):
            shots[shot]['path_list'].append(i)

    for shot in shots:
        shots[shot] = sorted(
            shots[shot]['path_list'],
            key=lambda shot:
            Path(shot).stat().st_mtime if Path(shot).exists() else None,
            reverse=True)[0]
    return sorted(shots.values())


def map_drivers():
    """Map unc path. """

    LOGGER.info(u'映射网络驱动器')
    if sys.platform == 'win32':
        cmd = r'(IF NOT EXIST X: NET USE X: \\192.168.1.4\h) &'\
            r'(IF NOT EXIST Y: NET USE Y: \\192.168.1.7\y) &'\
            r'(IF NOT EXIST Z: NET USE Z: \\192.168.1.7\z) &'\
            r'(IF NOT EXIST G: NET USE G: \\192.168.1.4\snjyw)'
        call(cmd, shell=True)
    else:
        LOGGER.warning('Map drivers not implemented on this platform.')


def checked_exists(checking_list):
    """Return file existed item in @checking_list.  """
    from .path import get_encoded

    checking_list = list(checking_list)
    task = Progress('验证文件', total=len(checking_list))

    def _check(i):
        task.step(i)
        if os.path.exists(get_encoded(i)):
            return i
    pool = multiprocessing.dummy.Pool()
    ret = pool.map(_check, checking_list)
    pool.close()
    pool.join()
    return [i for i in ret if i]


def is_same(src, dst):
    """Check if @src has same modifield time with @dst. """
    if not src or not dst:
        return False

    try:
        if abs(os.path.getmtime(e(src)) - os.path.getmtime(e(dst))) < 1e-4:
            return True
    except OSError as ex:
        if ex.errno not in (errno.ENOENT,):
            LOGGER.warning('Can not check if same: %s',
                           os.strerror(ex.errno), exc_info=True)

    return False

# Deprecated functions.


@deprecated('url_open')
def _url_open(url, isfile=False):
    """Open url.  """
    import webbrowser

    dummy = isfile
    LOGGER.warning('url_open decrypted, use webbrowser.open instead.')
    LOGGER.debug('Open url:\n%s', url)
    webbrowser.open(url)


@deprecated('unicode_popen')
def _unicode_popen(args, **kwargs):
    """Return Popen object use encoded args.  """

    from .path import get_encoded

    with warnings.catch_warnings():
        warnings.simplefilter('always')
        warnings.warn(
            'Use Popen(wlf.path.get_encoded(arg) Instead.', DeprecationWarning)
    if isinstance(args, unicode):
        args = get_encoded(args)
    return Popen(args, **kwargs)


for i in ('get_encoded', 'get_unicode', 'split_version', 'expand_frame',
          'get_footage_name', 'get_layer', 'get_server',
          'get_tag', 'remove_version', 'is_ascii', 'escape_batch'):
    deprecated(i, reason='moved to wlf.path')(getattr(path, i))

deprecated('traytip', reason='use wlf.notify instead')(_traytip)
