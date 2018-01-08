# -*- coding=UTF-8 -*-
"""Contactsheet test.  """
from __future__ import absolute_import, print_function, unicode_literals

from wlf.csheet.views import APP


def main():
    port = 5000
    from wlf.mp_logging import set_basic_logger
    set_basic_logger()
    APP.run(host='0.0.0.0', port=port, debug=True)


if __name__ == '__main__':
    main()