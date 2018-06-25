# -*- coding=UTF-8 -*-
"""Tray icon and menu.  """
from __future__ import absolute_import, print_function, unicode_literals

import os

from Qt.QtGui import QCursor, QIcon
from Qt.QtWidgets import QSystemTrayIcon

from .env import has_gui
from .uitools import Menu

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
        pass

    def on_activated(self, reason):
        if reason == self.Trigger:
            self.contextMenu().popup(QCursor.pos())


if has_gui():
    Tray().show()
