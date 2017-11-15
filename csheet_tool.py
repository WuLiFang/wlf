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
from wlf.Qt import QtWidgets
from wlf.Qt.QtWidgets import QMessageBox
from wlf.uitools import DialogWithDir, main_show_dialog

LOGGER = logging.getLogger('com.wlf.csheet')


__version__ = '0.2.0'


class Config(wlf.config.Config):
    """Comp config.  """

    default = {
        'PROJECT': '少年锦衣卫',
        'DATABASE': 'proj_big',
        'PREFIX': 'SNJYW_EP14_',
        'OUTDIR': 'E:/',
        'PACK': False,
    }
    path = os.path.expanduser(u'~/.wlf.csheet.json')


CONFIG = Config()


class Dialog(DialogWithDir):
    """Main GUI dialog.  """

    default_note = '自上传工具提交'

    def __init__(self, parent=None):

        edits_key = {
            'comboBoxProject': 'PROJECT',
            'lineEditPrefix': 'PREFIX',
            'lineEditOutDir': 'OUTDIR',
            'checkBoxPack': 'PACK',
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
        proj_config = CONFIG['PROJECT']
        edit.insertItems(0, names)
        edit.setCurrentIndex(edit.findText(proj_config))

        # Signals
        self.actionDir.triggered.connect(self.ask_dir)

    def accept(self):
        """Override QDialog.accept .  """

        try:
            task = Progress('创建色板')
            project_name = self.comboBoxProject.currentText()
            database = self.projects_databse.get(
                project_name, CONFIG.default['DATABASE'])
            prefix = self.lineEditPrefix.text()
            outdir = self.directory
            is_pack = self.checkBoxPack.checkState()
            chseet_name = '{}_{}_色板'.format(project_name, prefix.strip('_'))

            task.set(message='访问数据库文件')
            try:
                images = cgtwq.Shots(database, prefix=prefix).get_all_image()
            except cgtwq.IDError as ex:
                QMessageBox.critical(self, '找不到对应条目', str(ex))
                return
            except RuntimeError:
                return

            task.set(50, '生成文件')
            if is_pack:
                outdir = os.path.join(outdir, chseet_name)
                task = Progress('下载图像到本地', total=len(images))
                for f in images:
                    task.step(f)
                    image_dir = os.path.join(outdir, 'images/')
                    copy(f, image_dir)
                created_file = csheet.create_html_from_dir(image_dir)
            else:
                save_path = os.path.join(outdir, '{}.html'.format(chseet_name))
                created_file = csheet.create_html(images, save_path,
                                                  title=u'色板 {}@{}'.format(prefix, database))
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
