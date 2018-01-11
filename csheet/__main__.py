#! /usr/bin/env python2
# -*- coding=UTF-8 -*-
"""GUI for csheet creation.  """
from __future__ import print_function, unicode_literals

import logging
import os
import webbrowser
from multiprocessing.dummy import Pool, cpu_count

from Qt import QtCore, QtWidgets

from Qt.QtWidgets import QMessageBox

from . import __version__
from .. import cgtwq
from ..config import Config as BaseConfig
from ..decorators import run_with_memory_require
from ..ffmpeg import GenerateError
from ..notify import CancelledError, Progress
from ..path import PurePath, get_encoded, Path
from ..uitools import DialogWithDir, main_show_dialog
from .html import HTMLImage, from_list

LOGGER = logging.getLogger('com.wlf.csheet')


class Config(BaseConfig):
    """Comp config.  """

    default = {
        'PROJECT': '少年锦衣卫',
        'PIPELINE': '合成',
        'DATABASE': 'proj_big',
        'PREFIX': 'SNJYW_EP19_',
        'OUTDIR': 'E:/',
        'IS_GENERATE_PREVIEW': 2,
        'PACK': 0,
    }
    path = os.path.expanduser(u'~/.wlf.csheet.json')


CONFIG = Config()


class Dialog(DialogWithDir):
    """Main GUI dialog.  """

    default_note = '自上传工具提交'

    def __init__(self, parent=None):

        edits_key = {
            'comboBoxProject': 'PROJECT',
            'comboBoxPipeline': 'PIPELINE',
            'lineEditPrefix': 'PREFIX',
            'lineEditOutDir': 'OUTDIR',
            'checkBoxPack': 'PACK',
            'checkBoxPreview': 'IS_GENERATE_PREVIEW',
        }
        icons = {
            'toolButtonAskDir': QtWidgets.QStyle.SP_DialogOpenButton,
            None: QtWidgets.QStyle.SP_FileDialogListView,
        }
        super(Dialog, self).__init__(
            PurePath(__file__).parent / '__main__.ui',
            config=CONFIG,
            icons=icons,
            edits_key=edits_key,
            dir_edit='lineEditOutDir')

        self.labelVersion.setText('v{}'.format(__version__))

        # Project combo box
        project = cgtwq.Project()
        names = project.names()
        edit = self.comboBoxProject
        self.projects_databse = {
            i: project.get_info(i, 'database')for i in names}
        self.projects_code = {
            i: project.get_info(i, 'code')for i in names}
        proj_config = CONFIG['PROJECT']
        edit.insertItems(0, names)
        edit.setCurrentIndex(edit.findText(proj_config))

        # Signals
        self.actionDir.triggered.connect(self.ask_dir)
        self.comboBoxProject.currentIndexChanged.connect(self.auto_set_prefix)

        # TODO
        self.checkBoxThumb.setEnabled(False)

    @property
    def csheet_name(self):
        """Csheet filename.  """

        return '{}色板'.format('_'.join(
            i for i in [self.project_name,
                        self.prefix.strip(self.code).strip('_'),
                        self.pipeline] if i))

    @property
    def project_name(self):
        """Project name.  """

        return self.comboBoxProject.currentText()

    @property
    def code(self):
        """Project code.  """
        return self.projects_code.get(self.project_name, '')

    @property
    def pipeline(self):
        """Database pipeline.  """

        return self.comboBoxPipeline.currentText()

    @property
    def prefix(self):
        """Shots prefix limitation.  """

        return self.lineEditPrefix.text()

    @property
    def database(self):
        """Database name on cgtw.  """

        return self.projects_databse.get(
            self.project_name, CONFIG.default['DATABASE'])

    @property
    def is_pack(self):
        """If pack before create csheet.  """

        return self.checkBoxPack.checkState()

    @property
    def is_generate_thumb(self):
        """If generate thumbnails before create csheet.  """

        return self.checkBoxThumb.checkState()

    @property
    def is_generate_preview(self):
        """If generate thumbnails before create csheet.  """

        return self.checkBoxPreview.checkState()

    @property
    def save_dir(self):
        """Csheet save dir.  """

        if self.is_pack:
            return PurePath(self.directory) / self.csheet_name

        return PurePath(self.directory)

    def auto_set_prefix(self):
        """Set prefix according current project. """

        edit = self.lineEditPrefix
        project_name = self.comboBoxProject.currentText()
        text = self.projects_code[project_name]
        text = '{}_EP01_'.format(text)

        edit.setText(text)
        edit.setFocus(QtCore.Qt.ShortcutFocusReason)
        edit.setSelection(len(text) - 3, 2)

    def get_images(self):
        """Get images from database.  """

        related_pipeline = {'灯光':  '渲染'}
        try:
            task = Progress('访问数据库', parent=self)
            task.step(self.database)
            shots = cgtwq.Shots(
                self.database,
                pipeline=self.pipeline,
                prefix=self.prefix)
            task.total = len(shots.shots) + 1

            # For pipelines thas has a another video related pipeline.
            if self.pipeline in related_pipeline:
                _pipeline = related_pipeline[self.pipeline]
                LOGGER.debug('Using related pipeline: %s', _pipeline)
                video_shots = cgtwq.Shots(
                    self.database,
                    pipeline=_pipeline,
                    prefix=self.prefix)
            else:
                video_shots = None

            images = []
            for shot in shots.shots:
                task.step(shot)
                image = HTMLImage(shots.get_shot_image(shot))
                if image:
                    image.name = shot
                    _shots = video_shots if self.pipeline in related_pipeline else shots
                    image.related_video = _shots.get_shot_submit_path(shot)
                    images.append(image)
            images.sort(key=lambda x: x.name)
            return images
        except cgtwq.IDError as ex:
            QMessageBox.critical(self, '找不到对应条目', str(ex))
            raise
        except cgtwq.PrefixError as ex:
            QMessageBox.critical(
                self, '无匹配镜头', '''
项目: {} <br>
流程: {} <br>
前缀: <span style="color:red;font-weight: bold">{}</span>
'''.format(self.project_name, self.pipeline, ex.prefix))
            raise

    def contactsheet(self):
        """ Construct contactsheet.  """

        images = self.get_images()
        sheet = from_list(images, title=self.csheet_name)

        # Generate preview.
        if self.is_generate_preview:
            height = {
                '动画': 180,
                '灯光': 200,
                '合成': 300,
            }.get(self.pipeline, None)

            errors = set()

            @run_with_memory_require(1)
            def _run(image):
                try:
                    image.generate_preview(height=height)
                except GenerateError:
                    LOGGER.error(
                        '%s: Cannot generate preview.', image, exc_info=True)
                    errors.add(image)
                except:
                    LOGGER.error(
                        'Unexcept error during generate preview.', exc_info=True)
                    raise

            task = Progress('生成预览', total=len(images), parent=self)
            thread_count = cpu_count()
            pool = Pool(thread_count)
            task.set(message='正在使用 {} 线程进行……'.format(thread_count))
            for _ in pool.imap_unordered(_run, images):
                task.step()
            pool.close()
            pool.join()
            if errors:
                QMessageBox.warning(self, '以下预览生成失败', '\n'.join(
                    unicode(i) for i in sorted(errors)))

        # Download resouces to local.
        if self.is_pack:
            dest = PurePath(self.save_dir)
            sheet.pack(dest)
            task = Progress('下载图像到本地', total=len(images), parent=self)
            dest = PurePath(self.save_dir) / 'images'
            for i in images:
                task.step(i.name)
                i.download(dest)

        return sheet

    def accept(self):
        """Override QDialog.accept .  """

        outdir = self.directory
        save_path = self.save_dir / '{}.html'.format(self.csheet_name)
        try:
            sheet = self.contactsheet()
            with Path(save_path).open('w', encoding='UTF-8') as f:
                f.write(sheet)

            webbrowser.open(get_encoded(outdir))
            webbrowser.open(get_encoded(save_path))

            super(Dialog, self).accept()
        except cgtwq.CGTeamWorkException:
            return
        except CancelledError:
            LOGGER.debug(u'用户取消创建色板')
        except:
            LOGGER.error('Unexcepted error', exc_info=True)
            raise


def run_server(port=5000):
    """Run csheet server at @port.  """

    from gevent.wsgi import WSGIServer
    from .views import APP
    from socket import gethostname, gethostbyname
    server = WSGIServer(('0.0.0.0', port), APP)
    print('服务器运行于: https://{}:{}'.format(gethostbyname(gethostname()), port))
    server.serve_forever()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='吾立方色板工具 {}'.format(__version__))
    parser.add_argument('-d', '--dir', metavar='目录', required=False,
                        help='包含色板所需图像的目录')
    parser.add_argument('-p', '--port', metavar='端口', type=int, required=False,
                        help='服务器运行端口')
    try:
        args = parser.parse_args()

        if args.dir:
            from . import create_html_from_dir
            result = create_html_from_dir(args.dir)
            print('生成色板: {}'.format(result))
            webbrowser.open(str(result))
            return
        elif args.port:
            return run_server(args.port)
    except SystemExit:
        pass

    main_show_dialog(Dialog)


if __name__ == '__main__':
    main()
