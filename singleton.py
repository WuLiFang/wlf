#! /usr/bin/env python
"""Let script only run once at a time.

SingleInstance modified from: https://pypi.python.org/pypi/tendo
"""
# TODO: active pid
# TODO: test on windows

import sys
import os
import tempfile
import unittest
import logging
from multiprocessing import Process

LOGGER = logging.getLogger("wlf.singleton")
LOGGER.addHandler(logging.StreamHandler())

__version__ = '0.1.0'


class SingleInstance(object):
    """instantiate this class to check singleinstance.  """

    def __init__(self, flavor_id=""):
        self.initialized = False
        basename = os.path.splitext(os.path.abspath(sys.argv[0]))[0].replace(
            "/", "-").replace(":", "").replace("\\", "-") + '-{}'.format(flavor_id) + '.lock'
        self.lockfile = os.path.normpath(
            tempfile.gettempdir() + '/' + basename)

        LOGGER.debug("SingleInstance lockfile: " + self.lockfile)

        self.check()
        self.initialized = True

    def __del__(self):
        if not self.initialized:
            return

        if sys.platform == 'win32':
            if hasattr(self, 'fd'):
                os.close(self.file_windows)
                os.unlink(self.lockfile)
        else:
            import fcntl
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
                    os.unlink(self.lockfile)
                self.file_windows = os.open(
                    self.lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            except OSError as ex:
                if ex.errno == 13:
                    LOGGER.error(
                        "Another instance is already running, quitting.")
                    self.exit()
                raise
        else:  # non Windows
            import fcntl
            self.file = open(self.lockfile, 'w')
            try:
                fcntl.lockf(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                LOGGER.warning(
                    "Another instance is already running, quitting.")
                self.exit()

    @staticmethod
    def exit():
        """Exit scrpit."""
        sys.exit(-1)


class _SingletonTestCase(unittest.TestCase):
    @staticmethod
    def _f(name):
        tmp = LOGGER.level
        LOGGER.setLevel(logging.CRITICAL)  # we do not want to see the warning
        dummy = SingleInstance(flavor_id=name)
        LOGGER.setLevel(tmp)

    @staticmethod
    def test_1():
        dummy = SingleInstance(flavor_id="test-1")
        del dummy  # now the lock should be removed
        assert True

    def test_2(self):
        proc = Process(target=self._f, args=("test-2",))
        proc.start()
        proc.join()
        # the called function should succeed
        assert proc.exitcode == 0, "%s != 0" % proc.exitcode

    def test_3(self):
        dummy = SingleInstance(flavor_id="test-3")
        proc = Process(target=self._f, args=("test-3",))
        proc.start()
        proc.join()
        # the called function should fail because we already have another
        # instance running
        assert proc.exitcode != 0, "%s != 0 (2nd execution)" % proc.exitcode
        # note, we return -1 but this translates to 255 meanwhile we'll
        # consider that anything different from 0 is good
        proc = Process(target=self._f, args=("test-3",))
        proc.start()
        proc.join()
        # the called function should fail because we already have another
        # instance running
        assert proc.exitcode != 0, "%s != 0 (3rd execution)" % proc.exitcode


if __name__ == "__main__":
    LOGGER.setLevel(logging.DEBUG)
    unittest.main()
