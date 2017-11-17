# -*- coding=UTF-8 -*-
"""GUI for csheet creation.  """
from __future__ import print_function, unicode_literals

import os
import webbrowser
import logging

from wlf import cgtwq, csheet
import wlf.config
from wlf.notify import Progress, CancelledError
from wlf.files import copy
from wlf.Qt import QtWidgets, QtCore
from wlf.Qt.QtWidgets import QMessageBox
from wlf.uitools import DialogWithDir, main_show_dialog

LOGGER = logging.getLogger('com.wlf.csheet')


__version__ = '0.4.4'


class Config(wlf.config.Config):
    """Comp config.  """

    default = {
        'PROJECT': '少年锦衣卫',
        'PIPELINE': '合成',
        'DATABASE': 'proj_big',
        'PREFIX': 'SNJYW_EP19_',
        'OUTDIR': 'E:/',
        'PACK': 0,
        'ALLOW_HTTP': 2,
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
            'checkBoxAllowHTTP': 'ALLOW_HTTP',
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

    def auto_set_prefix(self):
        """Set prefix according current project. """

        edit = self.lineEditPrefix
        project_name = self.comboBoxProject.currentText()
        text = self.projects_code[project_name]
        text = '{}_EP01_'.format(text)

        edit.setText(text)
        edit.setFocus(QtCore.Qt.ShortcutFocusReason)
        edit.setSelection(len(text) - 3, 2)

    def accept(self):
        """Override QDialog.accept .  """

        try:
            project_name = self.comboBoxProject.currentText()
            database = self.projects_databse.get(
                project_name, CONFIG.default['DATABASE'])
            code = self.projects_code.get(project_name, '')
            pipeline = self.comboBoxPipeline.currentText()
            prefix = self.lineEditPrefix.text()
            outdir = self.directory
            is_pack = self.checkBoxPack.checkState()
            is_allow_http = self.checkBoxAllowHTTP.checkState()
            chseet_name = '{}色板'.format('_'.join(
                i for i in [project_name, prefix.strip(code).strip('_'), pipeline] if i))

            try:
                task = Progress('访问数据库', parent=self)
                task.step(database)
                shots = cgtwq.Shots(
                    database, pipeline=pipeline, prefix=prefix)
                task.total = len(shots.shots) + 1
                rename_dict = {}
                for shot in shots.shots:
                    task.step(shot)
                    image = shots.get_shot_image(
                        shot, is_allow_http=is_allow_http)
                    if image:
                        ext = os.path.splitext(image)[1]
                        rename_dict[image] = ''.join([shot, ext])
                images = sorted(rename_dict.keys(), key=rename_dict.get)
            except cgtwq.IDError as ex:
                QMessageBox.critical(self, '找不到对应条目', str(ex))
                return
            except cgtwq.PrefixError as ex:
                QMessageBox.critical(
                    self, '无匹配镜头', '''
项目: {} <br>
流程: {} <br>
前缀: <span style="color:red;font-weight: bold">{}</span>
'''.format(project_name, pipeline, ex.prefix)
                )
                return

            if is_pack:
                outdir = os.path.join(outdir, chseet_name)
                task = Progress('下载图像到本地', total=len(images), parent=self)
                image_dir = os.path.join(outdir, 'images')
                for f in images:
                    task.step(f)
                    dst = os.path.join(image_dir, rename_dict.get(f, ''))
                    copy(f, dst)
                created_file = csheet.create_html_from_dir(
                    image_dir, rename_dict=rename_dict)
            else:
                save_path = os.path.join(outdir, '{}.html'.format(chseet_name))
                created_file = csheet.create_html(
                    images,
                    save_path,
                    title=u'色板 {}@{}'.format(prefix, database),
                    rename_dict=rename_dict)
            if created_file:
                webbrowser.open(outdir)
                webbrowser.open(created_file)

        except CancelledError:
            LOGGER.debug(u'用户取消创建色板')
        except:
            LOGGER.error('Unexcepted error', exc_info=True)
            raise

        super(Dialog, self).accept()


def main():
    main_show_dialog(Dialog)


if __name__ == '__main__':
    main()
