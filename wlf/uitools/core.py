# -*- coding=UTF-8 -*-
"""For build UI faster.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys

from Qt.QtWidgets import QAction, QApplication, QMenu

from .. import mp_logging
from ..notify import QtProgressBar


class Menu(QMenu):
    """Wrapped QMenu.  """

    def add_command(self, name, cmd):
        """Add command to tray menu.  """

        action = QAction(name, self, triggered=cmd)
        self.addAction(action)
        return action

    def add_menu(self, name):
        """Add submenu to tray menu.  """

        menu = Menu(name)
        self.addMenu(menu)
        return menu


def main_show_dialog(dialog):
    """Show dialog, for run in `__main__`.  """

    mp_logging.basic_config()
    QApplication(sys.argv)
    frame = dialog()
    QtProgressBar.default_parent = frame
    sys.exit(frame.exec_())
