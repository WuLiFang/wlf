# -*- coding=UTF-8 -*-
"""Test module `cgtwq.database`."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from unittest import TestCase, main

from util import skip_if_not_logged_in
from wlf.cgtwq import server


@skip_if_not_logged_in
class ServerTestCase(TestCase):
    def test_account(self):
        account = server.account()
        account_id = server.account_id()
        print('# account: <id: {}: {}>'.format(account_id, account))


if __name__ == '__main__':
    main()
