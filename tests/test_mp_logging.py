# -*- coding=UTF-8 -*-
"""Test `mp_logging` module.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
from unittest import TestCase, main

from wlf.mp_logging import basic_config

try:
    from unittest import mock
except ImportError:
    import mock


class BasicConfigTestCase(TestCase):
    def setUp(self):
        _handlers = logging.root.handlers

        def _restore():
            logging.root.handlers = _handlers
        logging.root.handlers = []
        self.addCleanup(_restore)
        pathcer = mock.patch('os.getenv')
        self.getenv = pathcer.start()
        self.addCleanup(pathcer.stop)

    def test_basic(self):
        self.assertEqual(len(logging.root.handlers), 0)
        basic_config()
        self.assertEqual(len(logging.root.handlers), 1)
        basic_config()
        self.assertEqual(len(logging.root.handlers), 1)

    def test_with_env(self):
        self.getenv.return_value = 'foo'
        basic_config()
        result = logging.root.getEffectiveLevel()
        assert result == logging.WARNING
        result = logging.getLogger("foo").getEffectiveLevel()
        assert result == logging.DEBUG


if __name__ == '__main__':
    main()
