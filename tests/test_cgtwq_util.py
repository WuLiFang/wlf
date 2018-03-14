# -*- coding=UTF-8 -*-
"""Test module `cgtwq.filter`.   """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from unittest import TestCase, main

import os


class UtilTestCase(TestCase):
    def test_generate_thumb(self):
        from wlf.cgtwq.util import genreate_thumb
        result = genreate_thumb(r'E:\test\images\autoComper.0112.jpg')
        self.addCleanup(os.unlink, result)


if __name__ == '__main__':
    main()
