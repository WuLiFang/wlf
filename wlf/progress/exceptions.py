# -*- coding=UTF-8 -*-
"""Progress exceptions.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import six


@six.python_2_unicode_compatible
class CancelledError(Exception):
    """Indicate user pressed CancelButton.  """

    def __str__(self):
        return 'Cancelled.'
