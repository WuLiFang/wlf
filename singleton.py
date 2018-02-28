#! /usr/bin/env python
# -*- coding=UTF-8 -*-
"""Let script only run once at a time.

SingleInstance modified from: https://pypi.python.org/pypi/tendo
"""
import sys
import os
import tempfile
import logging

try:
    if sys.platform != 'win32':
        import fcntl
except ImportError:
    raise

LOGGER = logging.getLogger("wlf.singleton")


class SingleInstance(object):
    """instantiate this class and hold it on a dummy constant to keep singleinstance.  """

    def __init__(self, flavor_id="", on_exit=None):
        self.initialized = False
        self.on_exit = on_exit
        basename = os.path.splitext(os.path.abspath(sys.argv[0]))[0].replace(
            "/", "-").replace(":", "").replace("\\", "-") + '-{}'.format(flavor_id) + '.lock'
        self.lockfile = os.path.normpath(
            tempfile.gettempdir() + '/' + basename)

        LOGGER.debug("SingleInstance lockfile: %s", self.lockfile)

        self.check()
        self.initialized = True

    def __del__(self):
        if not self.initialized:
            return

        if sys.platform == 'win32':
            if hasattr(self, 'fd'):
                self.file_windows.close()
                os.remove(self.lockfile)
        else:
            fcntl.lockf(self.file, fcntl.LOCK_UN)
            # os.close(self.fp)
            if os.path.isfile(self.lockfile):
                os.unlink(self.lockfile)

    def check(self):
        """Check if singleton.  """
        if sys.platform == 'win32':
            try:
                # file already exists, we try to remove (in case previous
                # execution was interrupted)
                if os.path.exists(self.lockfile):
                    os.remove(self.lockfile)
                self.file_windows = open(self.lockfile, 'w')
            except OSError as ex:
                if ex.errno == 13:
                    LOGGER.error(
                        "Another instance is already running, quitting.")
                    self.exit()
                raise
        else:  # non Windows
            self.file = open(self.lockfile, 'w')
            try:
                fcntl.lockf(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                LOGGER.warning(
                    "Another instance is already running, quitting.")
                self.exit()

    def exit(self):
        """Exit scrpit."""
        if self.on_exit:
            try:
                self.on_exit()
            except TypeError:
                LOGGER.debug('Execute %s faild', self.on_exit)
        sys.exit(-1)
