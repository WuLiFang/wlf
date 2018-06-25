# -*- coding=UTF-8 -*-
"""Tools for path operations.   """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os


def make_path_finder(filepath):
    """Create a path finder function
        for find path relative to file parent directory.

    Returns:
        str -- Absolute path under file parent direcotry.
    """

    root = os.path.abspath(os.path.dirname(filepath))

    def _path(*other):
        """Get absolutepath under given root.  """

        return os.path.abspath(os.path.join(root, *other))

    return _path


module_path = make_path_finder(__file__)  # pylint: disable = invalid-name
