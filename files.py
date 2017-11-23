# -*- coding=UTF-8 -*-
"""Files operation. """
from __future__ import unicode_literals, print_function

import os
import sys
import shutil
import logging
import warnings
import urllib
import errno
from subprocess import call, Popen
import multiprocessing.dummy

from wlf.notify import Progress
import wlf.path

__version__ = '0.7.0'

LOGGER = logging.getLogger('com.wlf.files')


def _remap_deprecated():
    def _get_func(name):
        def _func(*args, **kwargs):
            with warnings.catch_warnings():
                warnings.simplefilter('once')
                msg = 'Use wlf.path.{} Instead.'.format(i)
                warnings.warn(msg, DeprecationWarning)
            return getattr(wlf.path, name)(*args, **kwargs)
        return _func
    i = None
    for i in ['get_encoded', 'get_unicode', 'split_version', 'expand_frame',
              'get_footage_name', 'get_layer', 'get_server',
              'get_tag', 'remove_version', 'is_ascii', 'escape_batch']:
        setattr(sys.modules[__name__], i, _get_func(i))

    def traytip(*args, **kwargs):
        """Show a traytip(windows only).  """
        with warnings.catch_warnings():
            warnings.simplefilter('once')
            warnings.warn(
                'Use wlf.notify.traytip Instead.', DeprecationWarning)
        from .notify import traytip as _new
        _new(*args, **kwargs)

    setattr(sys.modules[__name__], 'traytip', traytip)


_remap_deprecated()


def copy(src, dst, threading=False):
    """Copy src to dst."""

    def _mkdirs():
        dst_dir = os.path.dirname(dst)
        if not os.path.exists(dst_dir):
            LOGGER.debug('创建目录: %s', dst_dir)
            os.makedirs(dst_dir)

    assert isinstance(src, (str, unicode))
    assert isinstance(dst, (str, unicode))

    if threading:
        thread = multiprocessing.dummy.Process(
            target=copy, args=(src, dst), kwargs={'threading': False})
        thread.start()
        return thread

    if src.startswith('http:'):
        LOGGER.info('下载:\n\t\t%s\n\t->\t%s', src, dst)
        _mkdirs()
        try:
            src_fd = urllib.urlopen(src)
            with open(dst, 'wb') as dst_fd:
                dst_fd.write(src_fd.read())
        finally:
            src_fd.close()
    elif not os.path.exists(src):
        LOGGER.warning('尝试复制不存在的文件: %s', src)
        return
    else:
        LOGGER.info('复制:\n\t\t%s\n\t->\t%s', src, dst)
        _mkdirs()
        try:
            shutil.copy2(src, dst)
        except OSError:
            if sys.platform == 'win32':
                call(wlf.path.get_encoded('XCOPY /V /Y "{}" "{}"'.format(src, dst)))
            else:
                raise

    if os.path.isdir(wlf.path.get_encoded(dst)):
        ret = os.path.join(dst, os.path.basename(src))
    else:
        ret = dst
    return ret


def version_filter(iterable):
    """Keep only newest version for each shot, try compare mtime when version is same.

    >>> version_filter(('sc_001_v1', 'sc_001_v2', 'sc002_v3', 'thumbs.db'))
    [u'sc002_v3', u'sc_001_v2', u'thumbs.db']
    """
    shots = {}
    iterable = sorted(
        iterable, key=lambda x: wlf.path.split_version(x)[1], reverse=True)
    for i in iterable:
        shot, version = wlf.path.split_version(i)
        shot = shot.lower()
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
            os.path.getmtime(shot) if os.path.exists(shot) else None,
            reverse=True)[0]
    return sorted(shots.values())


def map_drivers():
    """Map unc path. """
    if sys.platform == 'win32':
        cmd = r'(IF NOT EXIST X: NET USE X: \\192.168.1.4\h) &'\
            r'(IF NOT EXIST Y: NET USE Y: \\192.168.1.7\y) &'\
            r'(IF NOT EXIST Z: NET USE Z: \\192.168.1.7\z)'
        call(cmd, shell=True)
    else:
        LOGGER.warning('Map drivers not implemented on this platform.')


def _url_open(url, isfile=False):
    """(Decrypted)Open url.  """
    import webbrowser

    dummy = isfile
    LOGGER.warning('url_open decrypted, use webbrowser.open instead.')
    LOGGER.debug('Open url:\n%s', url)
    webbrowser.open(url)


setattr(sys.modules[__name__], 'url_open', _url_open)


def unicode_popen(args, **kwargs):
    """Return Popen object use encoded args.  """
    with warnings.catch_warnings():
        warnings.simplefilter('always')
        warnings.warn(
            'Use Popen(wlf.path.get_encoded(arg) Instead.', DeprecationWarning)
    if isinstance(args, unicode):
        args = wlf.path.get_encoded(args)
    return Popen(args, **kwargs)


def checked_exists(checking_list):
    """Return file existed item in @checking_list.  """
    checking_list = list(checking_list)
    task = Progress('验证文件', total=len(checking_list))

    def _check(i):
        task.step(i)
        if os.path.exists(wlf.path.get_encoded(i)):
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
        if abs(os.path.getmtime(src) - os.path.getmtime(dst)) < 1e-4:
            return True
    except OSError as ex:
        if ex.errno not in (errno.ENOENT,):
            LOGGER.warning('Can not check if same: %s',
                           os.strerror(ex.errno), exc_info=True)

    return False
