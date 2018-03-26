# -*- coding=UTF-8 -*-
"""pathname manipulations. """

from __future__ import print_function, unicode_literals

import io
import json
import locale
import logging
import os
import re
import string
import sys
from functools import wraps

from six import binary_type, python_2_unicode_compatible, text_type

import pathlib2

from .decorators import deprecated

with pathlib2.Path(os.path.abspath(
        os.path.join(__file__, '../files.tags.json'))).open(encoding='utf-8') as _f:
    _TAGS = json.load(_f)
    REGULAR_TAGS = _TAGS['regular_tags']
    TAG_CONVERT_DICT = _TAGS['tag_convert_dict']
    DEFAULT_TAG = _TAGS['default']
    TAG_PATTERN = _TAGS['pattern']
del _TAGS, _f

LOGGER = logging.getLogger('com.wlf.path')


def get_unicode(input_str, codecs=('UTF-8', 'GBK')):
    """Return unicode by try decode @string with @codecs.  """

    try:
        return text_type(input_str)
    except UnicodeDecodeError:
        input_str = binary_type(input_str)
        for i in tuple(codecs) + (sys.getfilesystemencoding(), locale.getdefaultlocale()[1]):
            try:
                return text_type(input_str, i)
            except UnicodeDecodeError:
                continue
    raise UnicodeDecodeError(input_str)


def get_encoded(input_str, encoding=None):
    """Return unicode by try decode @string with @encodeing.  """

    return get_unicode(input_str).encode(encoding or sys.getfilesystemencoding())


def is_ascii(text):
    """Return true if @text can be convert to ascii.

    >>> is_ascii('a')
    True
    >>> is_ascii('测试')
    False

    """
    try:
        get_unicode(text).encode('ASCII')
        return True
    except UnicodeEncodeError:
        return False


@deprecated
def get_server(path):
    r"""Return only path head for unc path.

    >>> get_server('\\\\192.168.1.7\\z\\b')
    u'\\\\192.168.1.7'
    >>> get_server('C:/steam')
    u'C:/steam'
    """
    if path.startswith('\\\\'):
        match = re.match(r'(\\\\[^\\]+)\\?', text_type(path))
        if match:
            return match.group(1)

    return path


def escape_batch(text):
    r"""Return escaped text for windows shell.

    >>> escape_batch('test_text "^%~1"')
    u'test_text \\"^^%~1\\"'
    >>> print(escape_batch(u'中文 "^%1"'))
    中文 \"^^%1\"
    """

    return text.replace(u'^', u'^^').replace(u'"', u'\\"').replace(u'|', u'^|')


def _py2_encode(parts):
    return [get_encoded(part) for part in parts]


setattr(pathlib2, '_py2_fsencode', _py2_encode)


def path_accessor():
    """Path pathlib2._normal_accessor to accept encoded path.  """

    def _e(func):
        @wraps(func)
        def _func(path):
            return func(get_encoded(path))
        return _func

    pathlib2._normal_accessor.stat = _e(pathlib2._normal_accessor.stat)


path_accessor()


@python_2_unicode_compatible
class PurePath(pathlib2.PurePath):
    """Optimized pathlib.PurePath object for footages.  """

    tag_pattern = None
    version_pattern = r'(.+)v(\d+)'
    default_tag = DEFAULT_TAG
    with pathlib2.Path(os.path.abspath(
            os.path.join(__file__, '../precomp.redshift.json'))).open(encoding='utf-8') as f:
        layers = json.load(f).get('layers')
    _unicode = None

    def __new__(cls, *args):
        """Construct a PurePath from one or several strings and or existing
        PurePath objects.  The strings and path objects are combined so as
        to yield a canonicalized path, which is incorporated into the
        new PurePath object.
        """

        if cls is PurePath:
            cls = PureWindowsPath if os.name == 'nt' else PurePosixPath
        args_u = []
        for i in args:
            if isinstance(i, str):
                i = get_unicode(i)
            args_u.append(i)
        return cls._from_parts(args_u)

    def __str__(self):
        """Return the string representation of the path, suitable for
        passing to system calls."""

        if self._unicode is None:
            setattr(self, '_parts',
                    list(get_unicode(i) if isinstance(i, str) else i
                         for i in self._parts))
            setattr(self, '_drv', get_unicode(self._drv))
            setattr(self, '_root', get_unicode(self._root))
            self._unicode = self._format_parsed_parts(
                get_unicode(self._drv),
                get_unicode(self._root),
                self._parts) or '.'
        return self._unicode

    @property
    def name(self):
        return get_unicode(super(PurePath, self).name)

    @property
    def layer(self):
        """The footage layer name.

        >>> PurePath('Z:/MT/Render/image/MT_BG_co/MT_BG_co_PuzzleMatte1/PuzzleMatte1.001.exr').layer
        u'PuzzleMatte1'
        """

        layers = self.layers
        if not self:
            return

        for layer in layers:
            match = re.search(r'\b({}\d*)\b'.format(layer),
                              self.name)
            if match:
                return get_unicode(match.group(1))

    @property
    def tag(self):
        """Return footage tag.

        Use custom tag pattern:

        >>> path = PurePath('Z:/MT/Render/image/MT_BG_co/MT_BG_co_Z/Z.001.exr')
        >>> path.tag_partten = r'MT_(.+)_'
        >>> path.tag
        u'BG'
        >>> path = PurePath('MT_BG_co_Z')
        >>> path.tag_partten = r'MT_(.+)_'
        >>> path.tag
        u'BG'
        >>> path = PurePath('Z.001.exr')
        >>> path.tag_partten = r'MT_(.+)_'
        >>> path.tag
        u'Z'

        Use default tag pattern:

        >>> PurePath('Z:/QQFC2017/Render/SC_065/QQFC_sc065_CH2').tag
        u'CH2'
        >>> PurePath('Z:/EP13_09_sc151_CH_B/EP13_09_sc151_CH_B.0015.exr').tag
        u'CH_B'

        result of below cases has been auto converted
        by a dictionary defined in `__file__/../files.tag.json`.

        >>> # BG_CO -> BG:
        >>> PurePath('Z:/MT/Render/image/MT_BG_co/MT_BG_co_Z/Z.001.exr').tag
        u'BG'
        >>> # CH_B_ID -> ID_CH_B:
        >>> PurePath('Z:/QQFC2017/Render/SC_031a/sc_031a_CH_B_ID/sc_031a_CH_B_ID.####.exr').tag
        u'ID_CH_B'
        >>> # CH_B_OC -> OCC_CH_B
        >>> PurePath('Z:/EP16_05_sc135b_CH_B_OC/EP16_05_sc135b_CH_B_OC.####.exr').tag
        u'OCC_CH_B'
        """

        pat = self.tag_pattern or TAG_PATTERN
        ret = None
        path = self
        for testing_pat in (pat, TAG_PATTERN):
            tag_pat = re.compile(testing_pat, flags=re.I)
            for test_string in\
                    (path.parent.name, path.name):
                match = re.match(tag_pat, test_string)
                if match and match.group(1):
                    ret = match.group(1).strip('_').upper()
                    for tag in REGULAR_TAGS:
                        if ret.startswith(tag):
                            break
                    else:
                        LOGGER.warning('不规范标签: %s: %s', ret, self)
                    break
            if ret:
                break
        else:
            ret = self.default_tag

        if TAG_CONVERT_DICT.has_key(ret):
            ret = TAG_CONVERT_DICT[ret]
        else:
            ret = '_'.join(ret.split('_')[:2])
            ret = TAG_CONVERT_DICT.get(ret, ret)

        if ret.startswith(tuple(string.digits)):
            ret = '_{}'.format(ret)
        return get_unicode(ret)

    @property
    def shot(self):
        """The related shot for this footage.

        >>> PurePath('sc_001_v20.nk').shot
        u'sc_001'
        >>> PurePath('hello world').shot
        u'hello world'
        >>> PurePath('sc_001_v-1.nk').shot
        u'sc_001_v-1'
        >>> PurePath('sc001V1.jpg').shot
        u'sc001'
        >>> PurePath('sc001V1_no_bg.jpg').shot
        u'sc001'
        >>> PurePath('suv2005_v2_m.jpg').shot
        u'suv2005'
        """

        match = re.match(self.version_pattern, self.name, flags=re.I)
        if not match:
            return get_unicode(self.stem)
        shot = match.group(1)
        return shot.strip('_')

    @property
    def version(self):
        """The nuke style version number of this footage.

        >>> PurePath('sc_001_v20.nk').version
        20
        >>> PurePath('hello world').version
        >>> PurePath('sc_001_v-1.nk').version
        >>> PurePath('sc001V1.jpg').version
        1
        >>> PurePath('sc001V1_no_bg.jpg').version
        1
        >>> PurePath('suv2005_v2_m.jpg').version
        2
        """

        match = re.match(self.version_pattern, self.name, flags=re.I)
        if not match:
            return None
        return int(match.group(2))

    @property
    def footage_name(self):
        """Return filename without frame number.

        >>> get_footage_name('sc_001_BG.0034.exr')
        u'sc_001_BG'
        >>> get_footage_name('sc_001_BG.%04d.exr')
        u'sc_001_BG'
        >>> get_footage_name('sc_001_BG.###.exr')
        u'sc_001_BG'
        >>> get_footage_name('sc_001._BG.exr')
        u'sc_001._BG'
        """

        ret = self.name
        ret = re.sub(r'\.\d+\b', '', ret)
        ret = re.sub(r'\.#+(?=\.)', '', ret)
        ret = re.sub(r'\.%0?\d*d\b', '', ret)
        ret = PurePath(ret).stem
        return get_unicode(ret)

    def with_frame(self, frame):
        '''Return a frame mark expaned version of filename, with given frame.

        >>> text_type(PurePath('test_sequence_###.exr').with_frame(1))
        u'test_sequence_001.exr'
        >>> text_type(PurePath('test_sequence_369.exr').with_frame(1))
        u'test_sequence_369.exr'
        >>> text_type(PurePath('test_sequence_%03d.exr').with_frame(1234))
        u'test_sequence_1234.exr'
        >>> text_type(PurePath('test_sequence_%03d.###.exr').with_frame(1234))
        u'test_sequence_1234.1234.exr'
        '''

        def _format_repl(matchobj):
            return matchobj.group(0) % frame

        def _hash_repl(matchobj):
            return '%0{}d'.format(len(matchobj.group(0)))

        ret = get_unicode(self)
        ret = re.sub(r'(\#+)', _hash_repl, ret)
        ret = re.sub(r'(%0?\d*d)', _format_repl, ret)
        return PurePath(ret)

    def as_no_version(self):
        """Return filename without version number.

        >>> text_type(PurePath('sc_001_v233.jpg').as_no_version())
        u'sc_001.jpg'
        """

        return self.with_name(u'{}{}'.format(self.shot, self.suffix))

    def as_posix(self):
        """Return the string representation of the path with forward (/)
        slashes."""
        f = getattr(self, '_flavour')
        return text_type(self).replace(f.sep, '/')

    def relative_to(self, *other):
        return super(PurePath, self).relative_to(*(get_unicode(i) for i in other))


class PurePosixPath(PurePath):
    """Port from pathlib.PurePosixPath.  """

    _flavour = getattr(pathlib2, '_posix_flavour')
    __slots__ = ()


class PureWindowsPath(PurePath):
    """Port from pathlib.PureWindowsPath.  """

    _flavour = getattr(pathlib2, '_windows_flavour')
    __slots__ = ()


class Path(pathlib2.Path, PurePath):
    """Port from pathlib.Path.  """

    def __new__(cls, *args, **kwargs):
        if cls is Path:
            cls = WindowsPath if os.name == 'nt' else PosixPath
        self = cls._from_parts(args, init=False)
        if not getattr(self, '_flavour').is_supported:
            raise NotImplementedError("cannot instantiate %r on your system"
                                      % (cls.__name__,))
        getattr(self, '_init')()
        return self

    def open(self, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None):
        """
        Open the file pointed by this path and return a file object, as
        the built-in open() function does.
        """
        if self._closed:
            self._raise_closed()
        if sys.version_info >= (3, 3):
            return io.open(
                get_encoded(self), mode, buffering, encoding, errors, newline,
                opener=self._opener)
        return io.open(get_encoded(self), mode, buffering,
                       encoding, errors, newline)


class PosixPath(Path, PurePosixPath):
    """Port from pathlib.PosixPath.  """

    __slots__ = ()


class WindowsPath(Path, PureWindowsPath):
    """Port from pathlib.WindowsPath.  """

    __slots__ = ()

    def owner(self):
        raise NotImplementedError("Path.owner() is unsupported on this system")

    def group(self):
        raise NotImplementedError("Path.group() is unsupported on this system")


# Deprecated functions.

@deprecated('expand_frame')
def _expand_frame(filename, frame):
    return get_unicode(PurePath(filename).with_frame(frame))


@deprecated('split_version')
def _split_version(f):
    path = PurePath(f)
    return path.shot, path.version


@deprecated('remove_version')
def _remove_version(path):
    return get_unicode(PurePath(path).as_no_version())


@deprecated('get_shot')
def _get_shot(path):
    return PurePath(path).shot


@deprecated('get_tag')
def _get_tag(filename, pat=None, default=DEFAULT_TAG):
    path = PurePath(filename)
    path.tag_pattern = pat
    path.default_tag = default

    return path.tag


@deprecated('get_layer')
def _get_layer(filename, layers=None):
    path = PurePath(filename)
    path.layers = layers
    return path.layer


@deprecated('get_footage_name')
def _get_footage_name(path):
    return PurePath(path).footage_name