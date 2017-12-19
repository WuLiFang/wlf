# -*- coding=UTF-8 -*-
"""Docstring test.  """
from __future__ import absolute_import

from os.path import isabs
from unittest import TestCase, main


class SetupTestCase(TestCase):

    def test_init(self):
        import wlf
        self.assertTrue(isabs(wlf.BIN_FOLDER))


if __name__ == '__main__':
    main()
