# -*- coding=UTF-8 -*-
"""Tray icon and menu.  """
from __future__ import absolute_import, print_function, unicode_literals

from Qt.QtGui import QCursor, QIcon
from Qt.QtWidgets import QSystemTrayIcon

from ..env import has_gui
from ..filetools import module_path
from .core import Menu


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
                QIcon(module_path('assets', 'tray_icon.png')))

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

    @classmethod
    def _message(cls, title, text, seconds, icon):
        """Show a traytip.  """

        tray = cls()
        tray.show()
        tray.showMessage(title, text, icon=icon, msecs=seconds * 1000)

    @classmethod
    def message(cls, title, text, seconds=3):
        """Show a traytip with no icon.  """

        cls._message(title, text, seconds, QSystemTrayIcon.NoIcon)

    @classmethod
    def information(cls, title, text, seconds=3):
        """Show a traytip with information icon.  """

        cls._message(title, text, seconds, QSystemTrayIcon.Information)

    @classmethod
    def warning(cls, title, text, seconds=3):
        """Show a traytip with warning icon.  """

        cls._message(title, text, seconds, QSystemTrayIcon.Warning)

    @classmethod
    def critical(cls, title, text, seconds=3):
        """Show a traytip with critical icon.  """

        cls._message(title, text, seconds, QSystemTrayIcon.Critical)


if has_gui():
    Tray().show()
