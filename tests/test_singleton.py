# -*- coding=UTF-8 -*-
"""TestCase for singleton.py  """
import unittest
import logging

from multiprocessing import Process
from wlf.singleton import SingleInstance

LOGGER = logging.getLogger()


class SingletonTestCase(unittest.TestCase):
    @classmethod
    def _f(cls, name):
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
