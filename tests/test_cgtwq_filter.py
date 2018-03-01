# -*- coding=UTF-8 -*-
"""Test module `cgtwq.filter`.   """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from unittest import TestCase, main, skip

from mock import MagicMock, call, patch
from contextlib import contextmanager

from wlf import cgtwq


class FiltersTestCase(TestCase):
    def test_operations(self):
        Filter = cgtwq.Filter
        FilterList = cgtwq.FilterList
        result = Filter('title', 'text') | Filter(
            'data', 'test') & Filter('name', 'name')
        self.assertIsInstance(result, FilterList)
        self.assertListEqual(
            result,
            [['title', '=', 'text'],
             'or', ['data', '=', 'test'],
             'and', ['name', '=', 'name']]
        )
        result |= Filter('test2', '233')
        self.assertIsInstance(result, FilterList)
        self.assertListEqual(
            result,
            [['title', '=', 'text'],
             'or', ['data', '=', 'test'],
             'and', ['name', '=', 'name'],
             'or', ['test2', '=', '233']]
        )


if __name__ == '__main__':
    main()
