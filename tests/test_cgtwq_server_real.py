# -*- coding=UTF-8 -*-
"""Test module `cgtwq.database`."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from unittest import TestCase, main

from util import skip_if_not_logged_in
from wlf.cgtwq import server
from tempfile import mkstemp, mkdtemp
import uuid
import io

import os


@skip_if_not_logged_in
class ServerTestCase(TestCase):
    def test_account(self):
        account = server.account()
        account_id = server.account_id()
        print('# account: <id: {}: {}>'.format(account_id, account))

    def test_file_operation(self):
        # Prepare
        tempdir = mkdtemp()
        self.addCleanup(os.rmdir, tempdir)
        fd, tempfile = mkstemp(dir=tempdir)
        self.addCleanup(os.remove, tempfile)
        dummy_data = unicode(uuid.uuid4())
        with io.open(fd, 'w') as f:
            f.write(dummy_data)
        dir_pathname = '/_pytest_{}'.format(dummy_data)
        filename = '{}.pytemp'.format(dummy_data)

        # Do test.

        # `mkdir`, `exists`, 'isdir'.
        self.assertIs(server.exists(dir_pathname), False)
        server.mkdir(dir_pathname)
        self.assertIs(server.exists(dir_pathname), True)
        self.assertIs(server.isdir(dir_pathname), True)

        # `upload`, `exists`, 'isdir'.
        pathname = '{}/{}'.format(dir_pathname, filename)
        self.assertIs(server.exists(pathname), False)
        server.upload(tempfile, pathname)
        self.assertIs(server.exists(pathname), True)
        self.assertIs(server.isdir(pathname), False)

        # `rename`.
        temppathname = '{}.rename'.format(pathname)
        server.rename(pathname, temppathname)
        self.assertIs(server.exists(temppathname), True)
        self.assertIs(server.exists(filename), False)
        server.rename(temppathname, pathname)
        self.assertIs(server.exists(pathname), True)
        self.assertIs(server.exists(temppathname), False)

        # `download`.
        downloaded = server.download(pathname, tempdir + '/')
        self.assertIn(filename, server.listdir(dir_pathname).file)
        with open(downloaded) as f:
            self.assertEqual(f.read(), dummy_data)
        self.addCleanup(os.remove, downloaded)

        # `delete`, `exists`, 'isdir'.
        server.delete(pathname)
        self.assertNotIn(filename, server.listdir(dir_pathname).file)
        server.delete(dir_pathname)
        self.assertIs(server.exists(dir_pathname), False)


if __name__ == '__main__':
    main()
