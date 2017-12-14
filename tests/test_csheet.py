# -*- coding=UTF-8 -*-
"""Contactsheet test.  """
from __future__ import absolute_import, print_function, unicode_literals

from tempfile import mkstemp, mktemp
from unittest import TestCase, main


class CSheetTestCase(TestCase):
    @classmethod
    def _sheet(cls):
        from wlf.csheet.html import HTMLContactSheet, HTMLImage
        images = ([HTMLImage(mktemp()) for _ in xrange(20)]
                  + [HTMLImage(i)for i in
                     ('e:/test/EP_test_sc999_abc.png', 'e:/test2/EP_test_sc999_abc.png',
                      'e:/中文路径', 'e:/测试/中文路径')])
        sheet = HTMLContactSheet(images)
        return sheet

    def test_html(self):
        self._sheet().generate(mkstemp('.html')[1], is_pack=False)

    def test_packed_html(self):
        self._sheet().generate(mkstemp('.html')[1], is_pack=True)


if __name__ == '__main__':
    main()
