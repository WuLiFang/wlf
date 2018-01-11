# -*- coding=UTF-8 -*-
"""Contactsheet test.  """
from __future__ import absolute_import, print_function, unicode_literals

from gevent.wsgi import WSGIServer

from wlf.csheet.views import APP


def main():
    port = 5001
    APP.debug = True
    server = WSGIServer(('localhost', port), APP)
    server.serve_forever()


if __name__ == '__main__':
    main()
