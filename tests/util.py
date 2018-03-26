# -*- coding=UTF-8 -*-
"""Test utilities.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
from unittest import skipIf

from wlf.env import HAS_QT

skip_if_no_qt = skipIf(  # pylint: disable=invalid-name
    not HAS_QT, 'Qt not installed')

ROOT = os.path.abspath(os.path.dirname(__file__))


def path(*other):
    """Get resource path.

    Returns:
        six.text_type: Joined absolute path.
    """

    return os.path.abspath(os.path.join(ROOT, *other))
