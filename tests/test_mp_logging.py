# -*- coding=UTF-8 -*-
"""Test `mp_logging` module.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from unittest import main, TestCase


class MPLoggingTestCase(TestCase):
    def test_basic_config(self):
        from wlf.mp_logging import basic_config
        import logging
        _handlers = logging.root.handlers
        logging.root.handlers = []
        basic_config()
        self.assertEqual(len(logging.root.handlers),1)
        basic_config()
        self.assertEqual(len(logging.root.handlers),1)
        logging.root.handlers = _handlers


if __name__ == '__main__':
    main()
