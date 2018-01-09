# -*- coding=UTF-8 -*-
"""HTML csheet page.  """
from __future__ import absolute_import, print_function, unicode_literals

import re
from itertools import count
from logging import getLogger
from os import strerror

from bs4 import BeautifulSoup

from ..ffmpeg import generate_gif
from ..files import copy
from ..path import Path, PurePath, get_encoded, get_unicode
from .base import ContactSheet, Image

LOGGER = getLogger('wlf.chseet.html')
RESOURCES_DIR = Path(Path(__file__).parent.parent / 'static')
RESOURCES_DIR.resolve()


class HTMLImage(Image):
    """A image in html contactsheet page.  """

    thumb = None
    _preview = None
    related_video = None

    def get_drag_path(self, for_pack=False):
        if for_pack:
            return './images/{}'.format(self.path.name)
        return self.path

    @property
    def preview_default(self):
        """Preview path default.  """

        filename = PurePath(self.path).with_suffix('.gif')
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


class HTMLContactSheet(ContactSheet):
    """Contactsheet in html page form.  """
    resources = ('csheet.css',
                 'html5shiv.min.js',
                 'jquery-3.2.1.min.js',
                 'jquery.appear.js',
                 'csheet.js')
    highlight_regex = re.compile(r'.*(sc_?\d+[^\.]*)\b', flags=re.I)

    def __init__(self, *args, **kwargs):
        super(HTMLContactSheet, self).__init__(*args, **kwargs)
        self.ids = set()
        for i in self:
            self.assign_id(i)

    def get_highlight(self, filename):
        """Get highlight part of @filename.  """

        match = re.match(self.highlight_regex, filename)
        if match:
            return match.group(1)

        return None

    def assign_id(self, image):
        """Get a unique id for @name.  """

        assert isinstance(image, HTMLImage), image
        assert image.html_id is None, 'This image already used in another contactsheet.'

        name = image.name
        id_ = name
        ids = self.ids
        for i in count(start=2):
            if id_ in ids:
                id_ = '{}_{}'.format(name, i)
            else:
                ids.add(id_)
                break
        image.html_id = id_
        return get_unicode(id_)

    def to_html(self, relative_to=None):
        """Convert to html form text.  """

        def _head():
            head = soup.new_tag('head')
            head.append(soup.new_tag('meta', charset='UTF-8'))
            title = soup.new_tag('title')
            title.append(self.title or '色板')
            head.append(title)
            for i in self.resources:
                path = PurePath(RESOURCES_DIR, i)
                rel_path = path.html_relative_to(relative_to)
                if path.match('*.css'):
                    tag = soup.new_tag('link',
                                       rel='stylesheet',
                                       type='text/css',
                                       href=rel_path)
                    head.append(tag)
                elif path.match('*.js'):
                    tag = soup.new_tag('script',
                                       type='text/javascript',
                                       src=rel_path)
                    head.append(tag)
                else:
                    LOGGER.warning('Ignore resource: %s', path)
            head.append(BeautifulSoup('''\
 <!--[if IE]>
  <script type="text/javascript">
   alert('请使用现代浏览器浏览本页面');
   window.open("http://outdatedbrowser.com/zh-cn", "_self");
  </script>
 <![endif]-->\
''', 'html.parser'))
            return head

        def _body():
            total = len(self)
            body = soup.new_tag('body')

            header = soup.new_tag('header')
            span = soup.new_tag('div', **{'class': 'count'})
            span.append(str(total))
            header.append(span)
            noscript = soup.new_tag('noscript')
            noscript.append('需要浏览器启用javascript')
            span = soup.new_tag('div', **{'class': 'noscript'})
            span.append(noscript)
            header.append(span)
            body.append(header)

            div = soup.new_tag('ul', **{'class': 'images'})
            for index, image in enumerate(self):
                assert isinstance(image, HTMLImage)
                div.append(_get_lightbox(index))
            body.append(div)

            return body

        def _get_figcaption(image):
            assert isinstance(image, HTMLImage)
            tag = soup.new_tag('figcaption')
            highlight = self.get_highlight(image.name)
            if highlight:
                parts = list(image.name.partition(highlight))
                span = soup.new_tag('span', **{'class': 'highlight'})
                span.append(highlight)
                parts[1] = span
                _ = [tag.append(i) for i in parts if i]
            else:
                tag.append(image.name)

            return tag

        def _get_lightbox(index):
            image = self[index]
            assert isinstance(image, HTMLImage)
            data_src = image.path.html_relative_to(relative_to)
            try:
                data_thumb = PurePath(
                    image.thumb).html_relative_to(relative_to)
            except TypeError:
                data_thumb = 'null'
            try:
                data_preview = PurePath(
                    image.preview).html_relative_to(relative_to)
            except TypeError:
                data_preview = 'null'
            lightbox = soup.new_tag('li', id=image.html_id,
                                    **{'class': 'lightbox',
                                       'data-thumb': data_thumb,
                                       'data-preview': data_preview,
                                       'data-full': data_src})
            figcatption = _get_figcaption(image)

            # Small image.
            small = soup.new_tag('figure', **{'class': 'small'})
            img = soup.new_tag('img', alt='no image',
                               src=data_thumb if data_thumb != 'null' else data_src)
            small.append(img)
            small.append(figcatption.__copy__())
            # Anchor to open viewer.
            anchor = soup.new_tag('a', href='#{}'.format(image.html_id))
            anchor.append(small)
            lightbox.append(anchor)

            # Full image with a viewer.
            viewer = soup.new_tag('div', **{'class': 'viewer'})
            # Close button.
            anchor = soup.new_tag('a', href='#void', **{'class': 'close'})
            viewer.append(anchor)
            # Figure
            full = soup.new_tag(
                'figure', **{'class': 'full'})
            anchor = soup.new_tag('a', href=data_src, target='_blank')
            img = soup.new_tag('img', src=data_src, alt='no image')
            anchor.append(img)
            full.append(anchor)
            full.append(figcatption.__copy__())
            viewer.append(full)
            # Prev botton.
            image = self[index - 1]
            anchor = soup.new_tag('a', href='#{}'.format(
                image.html_id), **{'class': 'prev'})
            viewer.append(anchor)
            # Next botton.
            try:
                image = self[index + 1]
            except IndexError:
                image = self[0]
            anchor = soup.new_tag('a', href='#{}'.format(
                image.html_id), **{'class': 'next'})
            viewer.append(anchor)

            lightbox.append(viewer)
            return lightbox

        soup = BeautifulSoup(
            '<!DOCTYPE html><html lang="zh"></html>', "html.parser")
        soup.html.append(_head())
        soup.html.append(_body())

        return soup.prettify()

    def generate(self, path, **kwargs):
        path = Path(path)
        if kwargs.get('is_pack'):
            self.pack(path.parent)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', encoding='UTF-8') as f:
            f.write(self.to_html(relative_to=path.parent))
        LOGGER.info(u'生成: %s', path)
        return path

    def pack(self, path):
        """Pack web page resouces to @path.  """

        # Download page resources.
        dest = PurePath(path) / 'resources'
        self.resources = tuple(copy(RESOURCES_DIR / i, dest / i)
                               or i for i in list(self.resources))
