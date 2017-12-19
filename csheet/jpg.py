# -*- coding=UTF-8 -*-
"""HTML csheet page.  """
from __future__ import absolute_import, print_function, unicode_literals

import json
import os
import sys
import threading
from subprocess import Popen

import nuke

from ..files import version_filter
from ..notify import Progress
from ..path import PurePath, get_encoded
from .base import ContactSheet, FootageError


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
            n['file'].fromUserText(
                self._config['backdrop'].encode('UTF-8'))
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
