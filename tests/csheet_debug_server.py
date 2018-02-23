# -*- coding=UTF-8 -*-
"""Contactsheet test.  """
from __future__ import absolute_import, print_function, unicode_literals

from gevent.wsgi import WSGIServer

from wlf.csheet.views import APP


def main():
    import logging
    logging.basicConfig(level=logging.DEBUG)

    port = 5001
    APP.debug = True
    server = WSGIServer(('localhost', port), APP)
    APP.logger.debug('Server ready')
    server.serve_forever()


if __name__ == '__main__':
    main()
