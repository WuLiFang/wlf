# -*- coding=UTF-8 -*-
"""Create contact sheet from all shot images.

"""

import json
import logging
import os
import re
import sys
import threading
import errno
from subprocess import Popen
from cgi import escape
from itertools import count

import wlf.config
from wlf.files import url_open, version_filter
from wlf.notify import HAS_NUKE, Progress
from wlf.path import get_encoded, get_unicode, split_version

if HAS_NUKE:
    import nuke

__version__ = '1.5.0'

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


class ContactSheet(object):
    """Create contactsheet in new script."""

    shot_width, shot_height = 1920, 1080
    contactsheet_shot_width, contactsheet_shot_height = 1920, 1160

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
                message=split_version(get_shot(i))[0],
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


def get_shot(filename):
    """Get shot name from filename.  """

    match = re.match(r'.*(sc_?\d+[^\.]*)\b', filename, flags=re.I)
    if match:
        return match.group(1)

    return filename


class ContactSheetThread(threading.Thread):
    """Thread that create contact sheet."""

    lock = threading.Lock()

    def __init__(self, new_process=False):
        threading.Thread.__init__(self)
        self._new_process = new_process

    def run(self):
        config_json = ContactSheet.json_path()
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


def create_html_from_dir(image_folder, **kwargs):
    """Create a html page for a @image_folder.  """
    image_folder = os.path.normpath(image_folder)
    if not os.path.isdir(get_encoded(image_folder)):
        return
    folder_name = os.path.basename(image_folder)
    images = version_filter(os.path.join(get_unicode(folder_name), get_unicode(i))
                            for i in os.listdir(get_encoded(image_folder))
                            if os.path.isfile(get_encoded(os.path.join(image_folder, i)))
                            and i.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')))
    save_path = os.path.abspath(os.path.join(
        image_folder, u'../{}_色板.html'.format(os.path.basename(image_folder))))

    kwargs.setdefault('title', image_folder)
    kwargs.setdefault('save_path', save_path)
    return create_html(images, **kwargs)


def create_html(images, save_path, title=None, rename_dict=None):
    """Crete html contactsheet with @images list, save to @save_path.  """

    class Image(object):
        """Image item.  """
        exsited_id = []

        def __init__(self, path):
            if rename_dict:
                name = rename_dict.get(path, path)
            path = os.path.normpath(path)
            name = os.path.basename(name)
            name = split_version(name)[0]
            shot = get_shot(name)
            if not os.path.isabs(path) and not path.startswith('http:'):
                path = './{}'.format(path)

            _id = escape(name)
            for i in count(start=1):
                if _id in self.exsited_id:
                    _id = '{}_{}'.format(name, i)
                else:
                    self.html_id = _id
                    self.exsited_id.append(self.html_id)
                    break

            if shot != name:
                self.html_name = escape(name).replace(
                    escape(shot), '<span class="highlight">{}</span>'.format(escape(shot)))
            else:
                self.html_name = name

            self.name = name
            self.path = path
            self.shot = shot

    body = ''
    images = [Image(i) for i in images]
    total = len(images)
    task = Progress('生成页面', total)
    save_dir = os.path.dirname(save_path)

    for index, image in enumerate(images):
        task.step(image.name)
        try:
            next_image = images[index + 1]
        except IndexError:
            next_image = images[0]
        body += u'''<figure class='lightbox'>
    <figure class="preview" id="{this.html_id}">
        <a href="#{this.html_id}" class="image">
            <img src="{this.path}" alt="no image" onerror="hide(this.parentNode.parentNode.parentNode)" class="thumb" />
        </a>
        <figcaption><a href="#{this.html_id}">{this.html_name}</a></figcaption>
    </figure>
    <figure class="full">
        <figcaption>{this.html_name}</figcaption>
        <a href="{this.path}" target="_blank" class="viewer">
            <img src="{this.path}" alt="no image"/>
        </a>
        <a class="close" href="#void"></a>
        <a class="prev" href="#{prev.html_id}">&lt;</a>
        <a class="next" href="#{next.html_id}">&gt;</a>
    </figure>
</figure>
'''.format(this=image,
           prev=images[index - 1],
           next=next_image)

    body = '''<body>
    <header>{}</header>
    <div class="shots">
    {}
    </div>
</body>'''.format(total, body)

    title = title or u'色板'
    with open(os.path.join(__file__, '../csheet.head.html')) as f:
        head = f.read().replace('<title></title>', '<title>{}</title>'.format(title))
    html_page = head + body

    try:
        os.makedirs(save_dir)
        LOGGER.info('创建目录: %s', save_dir)
    except OSError as ex:
        if ex.errno in (errno.EEXIST, errno.EACCES):
            pass
        else:
            LOGGER.error('Unexcepted exception during makedirs. errno: %s',
                         ex.errno)
            raise
    with open(get_encoded(save_path), 'w') as f:
        f.write(html_page.encode('UTF-8'))
    LOGGER.info(u'生成: %s', save_path)

    return save_path


def dialog_create_html():
    """A dialog for create_html.  """
    folder_input_name = '文件夹'
    panel = nuke.Panel('创建HTML色板')
    panel.addFilenameSearch(folder_input_name, '')
    confirm = panel.show()
    if confirm:
        csheet = create_html_from_dir(panel.value(folder_input_name))
        if csheet:
            url_open(csheet, isfile=True)


class FootageError(Exception):
    """Indicate no footage available."""

    def __init__(self):
        super(FootageError, self).__init__()
        print(u'\n**错误** - 在images文件夹中没有可用图像\n')


def main():
    """Run this module as script."""

    ContactSheet()


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('UTF-8')
    main()
