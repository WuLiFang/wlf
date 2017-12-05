# -*- coding=UTF-8 -*-
"""Create contact sheet from all shot images.

"""
# TODO: support GIF
from __future__ import print_function, unicode_literals
import json
import logging
import os
import re
import sys
import threading
import webbrowser
from tempfile import mktemp
from subprocess import Popen, PIPE
from cgi import escape
from itertools import count
from abc import abstractmethod
from collections import Iterable

import wlf.config
from wlf.files import version_filter, copy
from wlf.notify import HAS_NUKE, Progress
from wlf.path import get_encoded, get_unicode, PurePath, Path

if HAS_NUKE:
    import nuke

__version__ = '1.6.1'

LOGGER = logging.getLogger('com.wlf.csheet')


class Config(wlf.config.Config):
    """Comp config.  """
    default = {
        'csheet_database': 'proj_big',
        'csheet_prefix': 'SNJYW_EP14_',
        'csheet_outdir': 'E:/',
        'csheet_checked': False,
    }
    path = os.path.expanduser(u'~/.nuke/wlf.csheet.json')


class Image(object):
    """Image item for contactsheet.  """

    exsited_id = []
    path = None
    name = None
    relative_to = None
    _html_id = None
    # Static .png image thumbnail.
    thumb = None
    # Dynamic .gif preview.
    preview = None

    def __new__(cls, path):
        if isinstance(path, Image):
            return path

        return super(Image, cls).__new__(cls, path)

    def __init__(self, path):
        # Ignore initiated.
        if isinstance(path, Image):
            return

        # Initiate.
        path = PurePath(path)

        self.path = path
        self.name = path.shot

    def __nonzero__(self):
        return bool(self.path)

    @property
    def html_path(self):
        """Path for html.  """

        if self.path is None:
            return self.path

        path = PurePath(self.path)
        try:
            path = path.relative_to(self.relative_to)
        except ValueError:
            pass
        if not path.is_absolute() and not get_unicode(path).startswith('http:'):
            path = './{}'.format(path)
        return get_unicode(path)

    @property
    def html_name(self):
        """Figcaption for html.  """

        name = self.name
        highlight = self.get_highlight(name)
        if highlight != self.name:
            return escape(name).replace(
                escape(highlight),
                '<span class="highlight">{}</span>'.format(escape(highlight)))
        return get_unicode(name)

    @property
    def html_id(self):
        """Element id for html.  """

        if self._html_id is None:
            name = self.name
            id_ = escape(name)
            for i in count(start=1):
                if id_ in self.exsited_id:
                    id_ = '{}_{}'.format(name, i)
                else:
                    self.exsited_id.append(id_)
                    self._html_id = id_
                    break

        return get_unicode(self._html_id)

    @classmethod
    def get_highlight(cls, filename):
        """Get highlight part of @filename.  """

        match = re.match(r'.*(sc_?\d+[^\.]*)\b', filename, flags=re.I)
        if match:
            return match.group(1)

        return get_unicode(filename)

    def generate_preivew(self, source=None):
        """Generate gif preview with @source.  """

        source = Path(source or self.path)
        output = Path(self.preview)

        try:
            output.parent.mkdir(exist_ok=True)
            if self.path.match('*.mov'):
                self.preview = generate_gif(source, output)
            return self.preview
        except OSError as ex:
            LOGGER.errno(os.strerror(ex.errno), exc_info=True)
        except:
            LOGGER.error('Error during generate preview.', exc_info=True)
            raise

    def download(self, dest):
        """Download this image to dest.  """

        path = PurePath(dest)
        for attr in ('path', 'thumb', 'preview'):
            old_value = getattr(self, attr)
            dirpath = PurePath('images')
            if attr != 'path':
                dirpath /= attr
            if old_value:
                suffix = PurePath(old_value).suffix
                new_value = copy(old_value,
                                 (path / dirpath / self.html_id).with_suffix(suffix))
                setattr(self, attr, new_value)


class ContactSheet(list):
    """Contactsheet for images.  """

    title = None

    def __init__(self, images):
        assert isinstance(images, Iterable)

        list.__init__(self, (Image(i) for i in images))

    def __setitem__(self, index, value):
        return list.__setitem__(self, index, Image(value))

    @abstractmethod
    def generate(self, path):
        """Generate csheet to given @path.  """
        raise NotImplementedError


class HTMLContactSheet(ContactSheet):
    """Contactsheet in html page form.  """

    def to_html(self, relative_to=None):
        """Convert to html form text.  """

        body = ''
        total = len(self)
        task = Progress('生成页面', total)

        for index, image in enumerate(self):
            task.step(image.name)
            image.relative_to = relative_to
            try:
                next_image = self[index + 1]
            except IndexError:
                next_image = self[0]
            body += '''<figure class='lightbox'>
        <figure class="preview" id="{this.html_id}">
            <a href="#{this.html_id}" class="image">
                <img alt="no image" class="thumb"
                    onerror="hide(this.parentNode.parentNode.parentNode)"
                    onmouseover="use_preview(this)"
                    onmouseout="use_thumb(this)"
                    src="{this.html_path}"
                    data-thumb="{this.thumb}"
                    data-preivew="{this.preview}"/>
            </a>
            <figcaption><a href="#{this.html_id}">{this.html_name}</a></figcaption>
        </figure>
        <figure class="full">
            <figcaption>{this.html_name}</figcaption>
            <a href="{this.html_path}" target="_blank" class="viewer">
                <img src="{this.html_path}" alt="no image"/>
            </a>
            <a class="close" href="#void"></a>
            <a class="prev" href="#{prev.html_id}">&lt;</a>
            <a class="next" href="#{next.html_id}">&gt;</a>
        </figure>
    </figure>
    '''.format(this=image,
               prev=self[index - 1],
               next=next_image)

        body = '''<body>
        <header>{}</header>
        <div class="shots">
        {}
        </div>
    </body>'''.format(total, body)

        title = self.title or u'色板'
        with open(os.path.join(__file__, '../csheet.head.html')) as f:
            head = f.read().replace('<title></title>', '<title>{}</title>'.format(title))
        html_page = head + body
        return html_page

    def generate(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', encoding='UTF-8') as f:
            f.write(self.to_html(relative_to=path.parent))
        LOGGER.info(u'生成: %s', path)
        return path


class JPGContactSheet(ContactSheet):
    """Create contactsheet in new script."""

    shot_width, shot_height = 1920, 1080
    contactsheet_shot_width, contactsheet_shot_height = 1920, 1160

    class Thread(threading.Thread):
        """Thread that create contact sheet."""

        lock = threading.Lock()

        def __init__(self, new_process=False):
            threading.Thread.__init__(self)
            self._new_process = new_process

        def run(self):
            config_json = JPGContactSheet.json_path()
            if not os.path.isfile(config_json):
                return
            self.lock.acquire()
            task = Progress('生成色板')
            task.set(50)
            cmd = u'"{NUKE}" -t "{script}" "{json}"'.format(
                NUKE=nuke.EXE_PATH,
                script=__file__.rstrip('cd'),
                json=config_json
            )
            if self._new_process:
                cmd = u'START "生成色板" {}'.format(cmd)
            Popen(get_encoded(cmd), shell=self._new_process)
            task.set(100)
            del task
            self.lock.release()

    def __init__(self):
        try:
            self.read_config()
        except IOError:
            print('没有.projectsettings.json, 不会生成色板')
        else:
            nuke.scriptClear()
            nuke.Root()['project_directory'].setValue(
                os.getcwd().replace('\\', '/'))
            nuke.knob('root.format', '1920 1080')
            self.create_nodes()
            self.output()

    def read_config(self):
        """Set instance config from disk."""

        with open(self.json_path()) as f:
            self._config = json.load(f)

    @staticmethod
    def json_path():
        """Return current json config path."""

        if __name__ == '__main__':
            result = sys.argv[1]
        else:
            result = os.path.join(os.path.dirname(
                nuke.value('root.name')), '.projectsettings.json')
        return result

    def create_nodes(self):
        """Create node tree for rendering contactsheet."""

        nuke.addFormat('{} {} contactsheet_shot'.format(
            self.contactsheet_shot_width, self.contactsheet_shot_height))
        _nodes = []
        for i in self.image_list():
            n = nuke.nodes.Read(file=i.replace('\\', '/').encode('UTF-8'))
            if n.hasError():
                nuke.delete(n)
                print(u'排除:\t\t\t{} (不能读取)'.format(i))
                continue
            n = nuke.nodes.Reformat(
                inputs=[n],
                format='contactsheet_shot',
                center=False,
                black_outside=True
            )
            n = nuke.nodes.Transform(
                inputs=[n],
                translate='0 {}'.format(
                    self.contactsheet_shot_height - self.shot_height)
            )
            n = nuke.nodes.Text2(
                inputs=[n],
                message=PurePath(i).shot,
                box='5 0 1000 75',
                color='0.145 0.15 0.14 1',
                global_font_scale=0.8,
                # font='{{Microsoft YaHei : Regular : msyh.ttf : 0}}'
            )
            _nodes.append(n)

        n = nuke.nodes.ContactSheet(
            inputs=_nodes,
            width='{rows*shot_format.w+gap*(rows+1)}',
            height='{columns*shot_format.h+gap*(columns+1)}',
            rows='{{ceil(pow([inputs this], 0.5))}}',
            columns='{rows}',
            gap=50,
            roworder='TopBottom')
        n.setName('_Csheet')
        k = nuke.WH_Knob('shot_format')
        k.setValue([self.contactsheet_shot_width,
                    self.contactsheet_shot_height])
        n.addKnob(k)
        _contactsheet_node = n

        print(u'使用背板:\t\t{}'.format(self._config['backdrop']))
        if os.path.isfile(self._config['backdrop']):
            n = nuke.nodes.Read()
            n['file'].fromUserText(self._config['backdrop'].encode('UTF-8'))
            if n.hasError():
                n = nuke.nodes.Constant()
                print(u'**警告**\t\t背板文件无法读取,将用纯黑代替')
        else:
            n = nuke.nodes.Constant()
            print(u'**提示**\t\t找不到背板文件,将用纯黑代替')
        n = nuke.nodes.Reformat(
            inputs=[n],
            type='scale',
            scale='{_Csheet.width/input.width*backdrop_scale}'
        )
        k = nuke.Double_Knob('backdrop_scale', '背板缩放')
        k.setValue(1.13365)
        n.addKnob(k)
        n.setName('_Reformat_Backdrop')
        print(u'底板 scale: {}, width: {}, height: {}'.format(
            n['scale'].value(), n.width(), n.height()))
        _reformat_node = n
        n = nuke.nodes.Transform(
            inputs=[_contactsheet_node],
            translate='{0.108*_Reformat_Backdrop.width} {0.018*_Reformat_Backdrop.height}',
        )
        print(u'联系表 translate: {}'.format(n['translate'].value(),))
        _transform_node = n
        n = nuke.nodes.Merge2(inputs=[_reformat_node, _transform_node])
        n = nuke.nodes.Write(
            inputs=[n],
            file=self._config['csheet'].encode('UTF-8').replace('\\', '/'),
            file_type='jpg',
            _jpeg_quality='1',
            _jpeg_sub_sampling='4:4:4'
        )
        self._write_node = n

    def output(self):
        """Write contactsheet to disk."""

        # nuke.scriptSave('E:\\temp.nk')
        print(u'输出色板:\t\t{}'.format(self._config['csheet']))
        nuke.render(self._write_node, 1, 1)

    def image_list(self, showinfo=True):
        """Return images to create contactsheet."""

        footage_dir = self._config['csheet_footagedir']

        images = list(os.path.join(footage_dir, i)
                      for i in os.listdir(footage_dir))
        ret = version_filter(images)

        if not ret:
            raise FootageError

        if showinfo:
            for image in images:
                if image not in ret:
                    print(u'排除:\t\t{} (较旧)'.format(image))
                else:
                    print(u'包含:\t\t{}\n'.format(image))
            print(u'共{}个文件 总计{}个镜头'.format(len(images), len(ret)))
        return ret

    def generate(self, path):
        # self.Thread().start()
        raise NotImplementedError


def create_html_from_dir(image_folder, **kwargs):
    """Create a html page for a @image_folder.  """

    image_folder = os.path.normpath(image_folder)
    if not os.path.isdir(get_encoded(image_folder)):
        LOGGER.warning('Not a dir, ignore: %s', image_folder)
        return
    folder_name = os.path.basename(image_folder)
    images = version_filter(os.path.join(get_unicode(folder_name), get_unicode(i))
                            for i in os.listdir(get_encoded(image_folder))
                            if os.path.isfile(get_encoded(os.path.join(image_folder, i)))
                            and i.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.mov')))
    save_path = os.path.abspath(os.path.join(
        image_folder, u'../{}_色板.html'.format(os.path.basename(image_folder))))

    kwargs.setdefault('title', image_folder)
    kwargs.setdefault('save_path', save_path)
    return create_html(images, **kwargs)


def create_html(images, save_path, title=None, rename_dict=None):
    """Crete html contactsheet with @images list, save to @save_path.  """

    images = [Image(i) for i in images]
    rename_dict = rename_dict or {}

    for i in images:
        if i.path in rename_dict:
            i.name = rename_dict[i.path]
    csheet = HTMLContactSheet(images)
    csheet.title = title

    return csheet.generate(save_path)


class FootageError(Exception):
    """Indicate no footage available."""

    def __unicode__(self):
        return '在文件夹中没有可用图像'


def generate_gif(filename, output=None):
    """Generate a gif with same name.  """

    path = PurePath(filename)
    _palette = mktemp('.png')
    _filters = 'fps=15,scale=640:-1:flags=lanczos'
    ret = PurePath(output or path.with_name('{0.stem}.gif'.format(path)))
    if PurePath(ret).suffix != '.gif':
        ret = PurePath('{}.gif'.format(ret))

    # Generate palette
    cmd = ('ffmpeg -i "{0[filename]}" '
           '-vf "{0[_filters]}, palettegen" '
           '-y "{0[_palette]}"').format(locals())
    proc = Popen(get_encoded(cmd), cwd=str(ret.parent),
                 stdout=PIPE, stderr=PIPE, env=os.environ)
    if proc.wait():
        raise RuntimeError('Error during generate gif palette:\n\t %s' % cmd)
    # Generate gif
    cmd = ('ffmpeg -i "{0[filename]}" -i "{0[_palette]}" '
           '-lavfi "{0[_filters]} [x]; [x][1:v] paletteuse" '
           '-y {0[ret]}').format(locals())
    proc = Popen(get_encoded(cmd), cwd=str(ret.parent),
                 stdout=PIPE, stderr=PIPE, env=os.environ)
    if proc.wait():
        raise RuntimeError('Error during generate gif:\n\t %s' % cmd)

    LOGGER.info('生成GIF: %s', ret)
    return ret

# Remap deprecated functions.


def _dialog_create_html():
    """A dialog for create_html.  """

    folder_input_name = '文件夹'
    panel = nuke.Panel('创建HTML色板')
    panel.addFilenameSearch(folder_input_name, '')
    confirm = panel.show()
    if confirm:
        csheet = create_html_from_dir(panel.value(folder_input_name))
        if csheet:
            webbrowser.open(csheet)


locals()['dialog_create_html'] = _dialog_create_html
