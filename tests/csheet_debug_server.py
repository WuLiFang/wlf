# -*- coding=UTF-8 -*-
"""Contactsheet test.  """
from __future__ import absolute_import, print_function, unicode_literals

import logging

from gevent.wsgi import WSGIServer

from wlf import mp_logging
from wlf.csheet.views import APP


def main():
    mp_logging.basic_config(level=logging.DEBUG)

    port = 5001
    APP.debug = True
    server = WSGIServer(('localhost', port), APP)
    APP.logger.debug('Server ready')
    server.serve_forever()


if __name__ == '__main__':
    main()
