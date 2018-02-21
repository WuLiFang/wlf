# -*- coding=UTF-8 -*-
"""HTML csheet page.  """
from __future__ import absolute_import, print_function, unicode_literals

import logging
import uuid
from os import strerror
try:
    from gevent.lock import Semaphore
except ImportError:
    from threading import Semaphore

from jinja2 import Environment, PackageLoader

from ..ffmpeg import generate_mp4
from ..files import copy, version_filter
from ..path import Path, PurePath, get_encoded
from .base import Image

logging.basicConfig()
LOGGER = logging.getLogger('wlf.chseet.html')
RESOURCES_DIR = Path(Path(__file__).parent.parent / 'static')
RESOURCES_DIR.resolve()


def updated_config(config=None):
    """Return a default csheet config or updated default from given @config. """

    default = {'static': ('csheet.css',
                          'html5shiv.min.js',
                          'jquery-3.2.1.min.js',
                          'jquery.appear.js',
                          'csheet.js'),
               'static_folder': 'static'}

    if config:
        default.update(config)

    return default


class HTMLImage(Image):
    """A image in html contactsheet page.  """

    thumb = None
    _preview = None
    _cache = {}

    def __new__(cls, path):
        if isinstance(path, HTMLImage):
            return path
            
        uuid_ = unicode(uuid.uuid5(uuid.NAMESPACE_URL, get_encoded(path)).hex)
        try:
            return cls.from_uuid(uuid_)
        except KeyError:
            pass

        ret = super(HTMLImage, cls).__new__(cls, path)
        ret.uuid = uuid_
        ret._preview_lock = Semaphore()  # pylint: disable=protected-access
        ret.preview_source = path
        cls._cache[uuid_] = ret

        return ret

    @classmethod
    def from_uuid(cls, uuid_):
        """Get image from uuid.

        Args:
            uuid_ (str): uuid of image.

        Returns:
            HTMLImage: image with that uuid.
        """

        return cls._cache[uuid_]

    def get_drag(self, **config):
        """get path used on drag.  """

        if config.get('is_pack'):
            return 'images/{}'.format(self.path.name)

        return self.path.as_uri()

    def get_full(self, **config):
        """get full image path.  """

        if config.get('is_pack'):
            return 'images/{}'.format(self.path.name)

        return ('/images/{}/full'.format(self.uuid))

    def get_preview(self, **config):
        """get preview video path.  """

        if config.get('is_pack'):
            return 'previews/{}'.format(self.preview.name)

        return ('/images/{}/preview'.format(self.uuid))

    @property
    def preview_default(self):
        """Preview path default.  """

        filename = PurePath(self.path).with_suffix('.mp4').name
        for i in (self.path, self.preview_source):
            if i is None:
                continue
            path = PurePath(i)
            if path.is_absolute():
                return (path.with_name('previews') / filename)
        return Path.home() / '.wlf.csheet.preview' / filename

    @property
    def preview(self):
        """Dynamic .gif preview.  """

        return self._preview or self.preview_default

    @preview.setter
    def preview(self, value):
        self._preview = value

    def generate_preview(self, **kwargs):
        """Generate gif preview with @source.  """

        if unicode(self.preview_source).endswith('.mp4'):
            return Path(self.preview_source)

        with self._preview_lock:
            source = Path(self.preview_source)
            output = Path(get_encoded(self.preview))

            try:
                output.parent.mkdir(exist_ok=True)
                self._preview = generate_mp4(source, output, **kwargs)
                return self._preview
            except OSError as ex:
                LOGGER.error(strerror(ex.errno), exc_info=True)
            except:
                LOGGER.error('Error during generate preview.', exc_info=True)
                raise

    def download(self, dest):
        """Download this image to dest.  """

        path = PurePath(dest)
        for attr in ('path', 'thumb', 'preview'):
            src_value = getattr(self, attr)
            if not src_value:
                continue
            src_path = Path(src_value)

            dirpath = PurePath({'path': 'images',
                                'thumb': 'thumbs',
                                'preview': 'previews'}.get(attr, ''))
            if src_path.exists():
                dst_path = (path / dirpath /
                            self.name).with_suffix(src_path.suffix)
                copy(src_path, dst_path)


def from_dir(images_folder, **config):
    """Create a html page for a @images_folder.  """

    path = Path(images_folder)
    images = get_images_from_dir(images_folder)
    config.setdefault('title', path.name)

    return from_list(images, **updated_config(config))


def get_images_from_dir(images_folder):
    """Get HTMLImage for @images_folder.  """

    path = Path(images_folder)
    if not path.is_dir():
        raise ValueError('Not a dir : {}'.format(images_folder))
    images = version_filter(i for i in path.iterdir()
                            if i.is_file()
                            and i.suffix.lower() in ('.jpg', '.jpeg', '.png', '.gif', '.mov', '.mp4'))
    return [HTMLImage(i) for i in images]


def from_list(images_list, **config):
    """Create a html page for a @images_list.  """

    config.update({
        'images': [HTMLImage(i) for i in images_list],
    })

    env = Environment(
        loader=PackageLoader(__name__),
    )

    template = env.get_template('csheet.html')

    return template.render(**updated_config(config))
