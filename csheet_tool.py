# -*- coding=UTF-8 -*-
"""GUI for csheet creation.  """
from __future__ import print_function, unicode_literals

import os
import webbrowser
import logging

from wlf import cgtwq
import wlf.config
from wlf.notify import Progress, CancelledError
from wlf.path import get_encoded, PurePath
from wlf.Qt import QtWidgets, QtCore
from wlf.Qt.QtWidgets import QMessageBox
from wlf.uitools import DialogWithDir, main_show_dialog
from wlf.csheet import HTMLContactSheet, Image

LOGGER = logging.getLogger('com.wlf.csheet')


__version__ = '0.6.1'


class Config(wlf.config.Config):
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
            '../csheet_tool.ui',
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

        try:
            task = Progress('访问数据库', parent=self)
            task.step(self.database)
            shots = cgtwq.Shots(
                self.database,
                pipeline=self.pipeline,
                prefix=self.prefix)
            task.total = len(shots.shots) + 1
            images = []
            for shot in shots.shots:
                task.step(shot)
                image = Image(shots.get_shot_image(shot))
                if image:
                    image.name = shot
                    image.related_video = shots.get_shot_submit_path(shot)
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

        if self.is_pack:
            task = Progress('下载图像到本地', total=len(images), parent=self)
            for i in images:
                task.step(i.name)
                i.download(PurePath(self.save_dir))
        if self.is_generate_preview:
            task = Progress('生成预览', total=len(images), parent=self)
            for i in images:
                task.step(i.name)
                i.generate_preivew()
        return HTMLContactSheet(images)

    def accept(self):
        """Override QDialog.accept .  """

        outdir = self.directory
        save_path = self.save_dir / '{}.html'.format(self.csheet_name)
        try:
            sheet = self.contactsheet()
            created_file = sheet.generate(save_path)
            if created_file:
                webbrowser.open(get_encoded(outdir))
                webbrowser.open(get_encoded(created_file))

            super(Dialog, self).accept()
        except cgtwq.CGTeamWorkException:
            return
        except CancelledError:
            LOGGER.debug(u'用户取消创建色板')
        except:
            LOGGER.error('Unexcepted error', exc_info=True)
            raise


def main():
    main_show_dialog(Dialog)


if __name__ == '__main__':
    main()
