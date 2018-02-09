# -*- coding=UTF-8 -*-
"""Test config module.  """

from __future__ import absolute_import, print_function, unicode_literals

import os
from tempfile import mktemp
from unittest import TestCase, main


class ConfigTestCase(TestCase):
    def test_config(self):
        from wlf.config import Config

        config = Config()
        temp_path = mktemp('.json')
        config.path = temp_path
        config['test'] = 1
        self.addCleanup(os.remove, temp_path)
        self.assertEqual(config['test'], 1)
        config = Config()
        config.path = temp_path
        self.assertEqual(config['test'], 1)


if __name__ == '__main__':
    main()
