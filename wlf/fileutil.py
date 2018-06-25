# -*- coding=UTF-8 -*-
"""File operation utility. """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import errno
import logging
import multiprocessing.dummy
import os
import shutil
import sys
from subprocess import call

from six.moves import urllib

from .notify import progress
from .path import Path, PurePath
from .path import get_encoded as e
from .path import get_unicode as u

LOGGER = logging.getLogger('com.wlf.fileutil')


def copy(src, dst, threading=False):
    """Copy src to dst."""

    def _mkdirs():
        dst_dir = os.path.dirname(dst_e)
        if not os.path.exists(dst_dir):
            LOGGER.debug('创建目录: %s', dst_dir)
            os.makedirs(dst_dir)
        elif os.path.isfile(dst_dir):
            raise ValueError(
                'Can not use file as directory: {}'.format(dst_dir))

    src_e, dst_e = e(src), e(dst)
    src_u, dst_u = u(src), u(dst)
    # Handle exceptions.
    if src_e == dst_e:
        LOGGER.warning('不能原地复制: %s', src_e)
        return dst_u
    elif not os.path.exists(src_e):
        LOGGER.warning('尝试复制不存在的文件: %s', src_u)
        return None

    if threading:
        thread = multiprocessing.dummy.Process(
            target=copy, args=(src_e, dst_e), kwargs={'threading': False})
        thread.start()
        return thread

    if src_u.startswith('http:'):
        LOGGER.info('下载:\n\t\t%s\n\t->\t%s', src_u, dst_u)
        _mkdirs()
        try:
            src_fd = urllib.request.urlopen(src_e)
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
                call(e(
                    'XCOPY /V /Y "{}" "{}"'.format(src_e, dst_e)))
            else:
                raise

    if os.path.isdir(e(dst_e)):
        ret = os.path.join(dst_e, os.path.basename(src_e))
    else:
        ret = dst_e

    ret = u(ret)
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

    checking_list = set(checking_list)

    def _check(i):
        if os.path.exists(e(i)):
            return i
        return None

    ret = set()
    pool = multiprocessing.dummy.Pool()
    for i in progress(pool.imap_unordered(_check, checking_list),
                      '验证文件', total=len(checking_list), start_message=''):
        if i:
            ret.add(i)
    ret = pool.map(_check, checking_list)
    pool.close()
    pool.join()
    return sorted(ret)


def is_same(src, dst):
    """Check if @src has same modifield time and size with @dst. """

    try:
        src_stat = os.stat(e(src))
        dst_stat = os.stat(e(dst))
    except OSError as ex:
        if ex.errno not in (errno.ENOENT,):
            LOGGER.warning('Can not check if same: %s',
                           os.strerror(ex.errno), exc_info=True)
        return False

    return (src_stat.st_size == dst_stat.st_size
            and abs(src_stat.st_mtime - dst_stat.st_mtime) < 1e-4)
