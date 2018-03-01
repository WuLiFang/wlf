# -*- coding=UTF-8 -*-
"""Test `cgtw.client` module on real server.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from unittest import TestCase, main, skip

from wlf.cgtwq import CGTeamWorkClient


# @skip_if_not_logged_in
@ skip('TODO')
class CGTeamWorkClientTestCase(TestCase):
    def test_plugin_data(self):
        result = CGTeamWorkClient.get_plugin_data()
        print(result)


if __name__ == '__main__':
    main()
