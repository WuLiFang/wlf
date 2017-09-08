# -*- coding=UTF-8 -*-
"""Show message to user.  """

import warnings
from .notify import *

with warnings.catch_warnings():
    warnings.simplefilter('always')
    warnings.warn(
        'wlf.message deprecated, use wlf.notify Instead.', DeprecationWarning)
