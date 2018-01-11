# -*- coding=UTF-8 -*-
"""HTML csheet page.  """
from __future__ import absolute_import, print_function, unicode_literals

from logging import getLogger
from os import strerror

from jinja2 import Environment, PackageLoader

from ..ffmpeg import generate_gif
from ..files import copy, version_filter
from ..path import Path, PurePath, get_encoded, get_unicode
from .base import Image

LOGGER = getLogger('wlf.chseet.html')
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
    related_video = None

    def get_drag(self, **config):
        """get path used on drag.  """

        if config.get('is_pack'):
            return 'images/{}'.format(self.path.name)

        return self.path.html_relative_to(config.get('relative_to'))

    def get_full(self, **config):
        """get full image path.  """

        if config.get('is_pack'):
            return 'images/{}'.format(self.path.name)
        elif config.get('is_web'):
            return ('/images/{0[database]}/{0[pipeline]}/{0[prefix]}/{1}'
                    .format(config, self.path.name))
        return self.path.html_relative_to(config.get('relative_to'))

    def get_preview(self, **config):
        """get preview image path.  """

        if config.get('is_pack'):
            return 'previews/{}'.format(self.preview.name)
        elif config.get('is_web'):
            return ('/previews/{0[database]}/{0[pipeline]}/{0[prefix]}/{1}'
                    .format(config, self.preview.name))
        return self.preview.html_relative_to(config.get('relative_to'))

    @property
    def preview_default(self):
        """Preview path default.  """

        filename = PurePath(self.path).with_suffix('.gif').name
        for i in (self.path, self.related_video):
            if i is None:
                continue
            path = PurePath(i)
            if path.is_absolute():
                return (path.with_name('preview') / filename)
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

        if self.related_video is None:
            # LOGGER.info('没有关联视频: %s', self)
            return

        source = Path(self.related_video)
        output = Path(get_encoded(self.preview))

        try:
            output.parent.mkdir(exist_ok=True)
            if source.match('*.mov'):
                self._preview = generate_gif(source, output, **kwargs)
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
            old_value = getattr(self, attr)
            if not old_value:
                continue
            old_path = Path(old_value)

            dirpath = PurePath('')
            if attr != 'path':
                dirpath /= attr
            if old_path.exists():
                new_path = (path / dirpath /
                            self.name).with_suffix(old_path.suffix)
                new_value = copy(old_path, new_path)
                if new_value:
                    setattr(self, attr, new_value)


def from_dir(images_folder, **config):
    """Create a html page for a @images_folder.  """

    path = Path(images_folder)
    if not path.is_dir():
        raise ValueError('Not a dir : %s', images_folder)
    images = version_filter(i for i in path.iterdir()
                            if i.is_file()
                            and i.suffix.lower() in ('.jpg', '.jpeg', '.png', '.gif', '.mov'))

    config.setdefault('title', path.name)
    config['static_folder'] = RESOURCES_DIR

    return from_list(images, **updated_config(config))


def from_list(images_list, **config):
    """Create a html page for a @images_list.  """

    config.update({
        'images': [HTMLImage(i) for i in images_list],
    })

    env = Environment(
        loader=PackageLoader(__name__),
    )

    template = env.get_template('csheet.html')
    config['static_folder'] = RESOURCES_DIR

    return template.render(**updated_config(config))
