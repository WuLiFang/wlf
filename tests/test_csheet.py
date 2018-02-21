# -*- coding=UTF-8 -*-
"""Contactsheet test.  """
from __future__ import absolute_import, print_function, unicode_literals

from tempfile import mktemp
from unittest import TestCase, main, skipUnless
import pickle

from wlf.csheet.html import HTMLImage
from wlf.path import PurePath
from wlf.cgtwq import CGTeamWorkClient


class CSheetTestCase(TestCase):
    def setUp(self):
        self.dummy_list = (['e:/test/EP_test_sc999_abc.png', 'e:/test2/EP_test_sc999_abc.png',
                            'e:/中文路径', 'e:/测试/中文路径']
                           + [mktemp() for _ in xrange(20)])

    def test_from_list(self):
        from wlf.csheet.html import from_list
        from_list(self.dummy_list)

    def test_preview_default(self):
        image = HTMLImage('c:/test/case1.jpg')
        self.assertEqual(image.preview, PurePath('c:/test/previews/case1.mp4'))

    def test_pickle_image(self):
        from wlf.csheet.base import Image

        image_b = Image('temp')
        data = pickle.dumps(image_b, pickle.HIGHEST_PROTOCOL)
        image_a = pickle.loads(data)
        self.assertIsInstance(image_a, Image)
        self.assertEqual(image_a, image_b)

    def test_pickle_htmlimage(self):

        image_b = HTMLImage('temp')
        image_b.preview_source = 'hahaha'
        data = pickle.dumps(image_b, pickle.HIGHEST_PROTOCOL)
        image_a = pickle.loads(data)
        self.assertIsInstance(image_a, HTMLImage)
        self.assertEqual(image_a, image_b)

# TODO: Remove cgtw require.


@skipUnless(CGTeamWorkClient.is_logged_in(), 'CGTeamWork not logged in.')
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
            self.assertIn(i, recieve.data.decode('utf8'))

    def tearDown(self):
        pass


if __name__ == '__main__':
    main()
