# -*- coding=UTF-8 -*-
"""Show progress to user.  """

import warnings
from wlf.notify import *

with warnings.catch_warnings():
    warnings.simplefilter('always')
    warnings.warn(
        'wlf.progress deprecated, use wlf.notify Instead.', DeprecationWarning)
