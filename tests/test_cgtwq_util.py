# -*- coding=UTF-8 -*-
"""Test module `cgtwq.filter`.   """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from unittest import TestCase, main

import os
import util


class UtilTestCase(TestCase):
    def test_generate_thumb(self):
        from wlf.cgtwq.util import genreate_thumb
        result = genreate_thumb(util.path('resource', 'gray.jpg'), 100, 75)
        self.addCleanup(os.unlink, result)
        result = genreate_thumb(util.path('resource', 'gray.png'), 100, 75)
        self.addCleanup(os.unlink, result)


if __name__ == '__main__':
    main()
