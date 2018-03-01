# -*- coding=UTF-8 -*-
"""Test module `cgtwq.database`."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from unittest import TestCase, main

from util import skip_if_not_logged_in
from wlf.cgtwq import server
from tempfile import mkstemp
import uuid
import io

import os


@skip_if_not_logged_in
class ServerTestCase(TestCase):
    def test_account(self):
        account = server.account()
        account_id = server.account_id()
        print('# account: <id: {}: {}>'.format(account_id, account))

    def test_upload(self):
        import wlf
        wlf.mp_logging.basic_config()
        fd, filename = mkstemp()
        self.addCleanup(os.remove, filename)
        with io.open(fd, 'w') as f:
            f.write(unicode(uuid.uuid4()))
        server.upload(
            filename, '/upload/test_python_upload_180301.txt')


if __name__ == '__main__':
    main()
