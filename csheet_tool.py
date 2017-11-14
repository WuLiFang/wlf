# -*- coding=UTF-8 -*-
"""GUI for csheet creation.  """

import os
import webbrowser
import logging

import wlf.config
from wlf.notify import HAS_NUKE, Progress, CancelledError
from wlf.files import copy
from wlf.Qt import QtWidgets
from wlf.uitools import DialogWithDir, main_show_dialog
import wlf.cgtwq as cgtwq
import wlf.csheet as csheet

if HAS_NUKE:
    import nuke

LOGGER = logging.getLogger('com.wlf.csheet')


__version__ = '0.1.0'


class Config(wlf.config.Config):
    """Comp config.  """

    default = {
        'DATABASE': 'proj_big',
        'PREFIX': 'SNJYW_EP14_',
        'OUTDIR': 'E:/',
        'PACK': False,
    }
    path = os.path.expanduser(u'~/.nuke/wlf.csheet.json')


CONFIG = Config()


class Dialog(DialogWithDir):
    """Main GUI dialog.  """

    default_note = '自上传工具提交'

    def __init__(self, parent=None):

        edits_key = {
            'lineEditDatabase': 'DATABASE',
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

        # Default database
        database = cgtwq.CGTeamWork().sys_module.get_sys_database()
        if database:
            self.lineEditDatabase.setPlaceholderText(database)
            if not HAS_NUKE:
                self.lineEditDatabase.setText(database)

        # Signals
        self.actionDir.triggered.connect(self.ask_dir)

    def accept(self):
        """Override QDialog.accept .  """

        try:
            task = Progress('创建色板')
            database = self.lineEditDatabase.text(
            ) or CONFIG.default['DATABASE']
            prefix = self.lineEditPrefix.text()
            outdir = self.directory
            is_pack = self.checkBoxPack.checkState()
            save_path = os.path.join(outdir,
                                     u'{}_{}_色板.html'.format(database, prefix.strip('_')))

            task.set(message='访问数据库文件')
            try:
                images = cgtwq.Shots(database, prefix=prefix).get_all_image()
            except cgtwq.IDError as ex:
                nuke.message('找不到对应条目\n{}'.format(ex))
                return
            except RuntimeError:
                return

            task.set(50, '生成文件')
            if is_pack:
                task = Progress('下载图像到本地', total=len(images))
                for f in images:
                    task.step(f)
                    image_dir = os.path.join(
                        outdir, '{}_images/'.format(database))
                    copy(f, image_dir)
                created_file = csheet.create_html_from_dir(image_dir)
            else:
                created_file = csheet.create_html(images, save_path,
                                                  title=u'色板 {}@{}'.format(prefix, database))
            if created_file:
                webbrowser.open(created_file)
        except CancelledError:
            LOGGER.debug(u'用户取消创建色板')
        except:
            LOGGER.error('Unexcepted error', exc_info=True)
            raise


def main():
    main_show_dialog(Dialog)


if __name__ == '__main__':
    main()
