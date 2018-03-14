# -*- coding=UTF-8 -*-
"""Main entry for uploader.  """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from ..uitools import main_show_dialog
from .window import Dialog


def main():
    main_show_dialog(Dialog)


if __name__ == '__main__':
    main()