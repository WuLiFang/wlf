# -*- coding=UTF-8 -*-
"""Contactsheet test.  """
from __future__ import absolute_import, print_function, unicode_literals

from tempfile import mkstemp, mktemp
from unittest import TestCase, main
import pickle


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

    def test_pickle_image(self):
        from wlf.csheet.base import Image

        image_b = Image('temp')
        data = pickle.dumps(image_b, pickle.HIGHEST_PROTOCOL)
        image_a = pickle.loads(data)
        self.assertIsInstance(image_a, Image)
        self.assertEqual(image_a, image_b)

    def test_pickle_htmlimage(self):
        from wlf.csheet.html import HTMLImage

        image_b = HTMLImage('temp')
        image_b.related_video = 'hahaha'
        data = pickle.dumps(image_b, pickle.HIGHEST_PROTOCOL)
        image_a = pickle.loads(data)
        self.assertIsInstance(image_a, HTMLImage)
        self.assertEqual(image_a, image_b)


class WSGICsheetTestCase(TestCase):
    def setUp(self):
        from wlf.csheet.views import APP
        import wlf.cgtwq
        self.dummy_projects = ['test1', '测试项目2', '测试项目 3']
        for _ in xrange(20):
            self.dummy_projects.append(mktemp(dir=''))

        wlf.cgtwq.Project.names = lambda *args: self.dummy_projects
        APP.testing = True
        self.app = APP.test_client()

    def test_index(self):
        import wlf.csheet.views
        wlf.csheet.views.MODULE_ENABLE = False
        recieve = self.app.get('/')
        self.assertEqual(recieve.status_code, 503)
        wlf.csheet.views.MODULE_ENABLE = True
        recieve = self.app.get('/')
        self.assertEqual(recieve.status_code, 200)
        for i in self.dummy_projects:
            self.assertIn(i, recieve.data)

    def tearDown(self):
        pass


if __name__ == '__main__':
    main()
