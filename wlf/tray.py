# -*- coding=UTF-8 -*-
"""Tray icon and menu.  """
from __future__ import print_function, unicode_literals, absolute_import

import os

from Qt.QtWidgets import QSystemTrayIcon
from Qt.QtGui import QIcon, QCursor

from .uitools import Menu
from .env import has_gui

RESOURCE_DIR = os.path.dirname(__file__)


class Tray(QSystemTrayIcon):
    """Tray icon with menu.  """

    instance = None
    initiated = False

    def __new__(cls):
        if not cls.instance:
            cls.instance = super(Tray, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        if not self.initiated:
            super(Tray, self).__init__(
                QIcon(os.path.join(RESOURCE_DIR, 'tray_icon.png')))

            # Menu.
            self.menu = Menu()
            self.setup_menu()
            self.setContextMenu(self.menu)

            # Signals.
            self.activated.connect(self.on_activated)

        self.initiated = True

    def setup_menu(self):
        """Set menu context.  """

        def _csheet_tool():
            import wlf.csheet
            wlf.csheet.__main__.Dialog().exec_()

        def _uploader():
            import wlf.uploader
            wlf.uploader.Dialog().exec_()

        self.menu.add_command('创建色板', _csheet_tool)
        self.menu.add_command('上传工具', _uploader)

    def on_activated(self, reason):
        if reason == self.Trigger:
            self.contextMenu().popup(QCursor.pos())


if has_gui():
    Tray().show()
