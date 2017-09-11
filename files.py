# -*- coding=UTF-8 -*-
"""Non-nuke-invoked files operation. """

import os
import sys
import shutil
import warnings
from subprocess import call, Popen

from wlf.notify import Progress
import wlf.path

__version__ = '0.6.0'


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


_remap_deprecated()


def copy(src, dst):
    """Copy src to dst."""

    message = u'{} -> {}'.format(src, dst)
    print(message)
    if not os.path.exists(src):
        return
    dst_dir = os.path.dirname(dst)
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    try:
        shutil.copy2(src, dst)
    except WindowsError:
        call(wlf.path.get_encoded(u'XCOPY /V /Y "{}" "{}"'.format(src, dst)))
    if os.path.isdir(wlf.path.get_encoded(dst)):
        ret = os.path.join(dst, os.path.basename(src))
    else:
        ret = dst
    return ret


def version_filter(iterable):
    """Keep only newest version for each shot, try compare mtime when version is same.

    >>> version_filter(('sc_001_v1', 'sc_001_v2', 'sc002_v3', 'thumbs.db'))
    ['sc002_v3', 'sc_001_v2', 'thumbs.db']
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
    cmd = r'(IF NOT EXIST X: NET USE X: \\192.168.1.4\h) &'\
        r'(IF NOT EXIST Y: NET USE Y: \\192.168.1.7\y) &'\
        r'(IF NOT EXIST Z: NET USE Z: \\192.168.1.7\z)'
    call(cmd, shell=True)


def url_open(url, isfile=False):
    """Open url in explorer. """
    if isfile:
        url = u'file://{}'.format(url)
    _cmd = u"rundll32.exe url.dll,FileProtocolHandler {}".format(url)
    Popen(wlf.path.get_encoded(_cmd))


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
    task = Progress('验证文件')
    checking_list = list(checking_list)
    all_num = len(checking_list)

    def _check(index, i):
        task.set(index * 100 // all_num, i)
        return os.path.exists(wlf.path.get_encoded(i))
    return (i for index, i in enumerate(checking_list) if _check(index, i))


def traytip(*args, **kwargs):
    """Show a traytip(windows only).  """
    with warnings.catch_warnings():
        warnings.simplefilter('always')
        warnings.warn(
            'Use wlf.notify.traytip Instead.', DeprecationWarning)
    from .notify import traytip as _new
    _new(*args, **kwargs)


def is_same(src, dst):
    """Check if @src has same modifield time with @dst. """
    if not src or not dst:
        return False

    try:
        if abs(os.path.getmtime(src) - os.path.getmtime(dst)) < 1e-4:
            return True
    except WindowsError:
        pass

    return False
