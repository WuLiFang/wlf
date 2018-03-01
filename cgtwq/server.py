# -*- coding=UTF-8 -*-
"""Create connection with cgtw server.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import json
import logging
from collections import namedtuple
from contextlib import contextmanager

import websocket

from .client import CGTeamWorkClient
from .exceptions import LoginError

LOGGER = logging.getLogger('wlf.cgtwq.server')


@contextmanager
def connection(ip=None, port=8888):
    """Create connection to server.

    Decorators:
        contextmanager

    Args:
        ip (unicode, optional): Defaults to None. Server ip,
            if `ip` is None, will try use ip from running client.
        port (int, optional): Defaults to 8888. Server port.

    Returns:
        websocket.WebSocket: Connected soket.
    """
    # pylint: disable=invalid-name

    ip = ip or CGTeamWorkClient.server_ip()
    url = 'ws://{}:{}'.format(ip, port)
    conn = websocket.create_connection(url)
    assert isinstance(conn, websocket.WebSocket)
    try:
        yield conn
    finally:
        conn.close()


Response = namedtuple('Response', ['data', 'code', 'type'])


def parse_recv(payload):
    """Parse server response

    Args:
        payload (bytes): Server defined response.

    Returns:
        Response: Parsed payload.
    """

    resp = json.loads(payload)
    data = resp['data']
    code = int(resp['code'])
    type_ = resp['type']
    return Response(data, code, type_)


def call(controller, method, **kwargs):
    """Send command to server, then get response.

    Args:
        controller (str): Server defined controller.
        method (str): Server defined controller method.
        **kwargs : Server defined keyword arguments for method.

    Raises:
        LoginError: When not loged in .
        ValueError: When server call failed.

    Returns:
        Response: Server response.
    """
    payload = {'controller': controller,
               'method': method,
               'token': CGTeamWorkClient.token()}
    payload.update(kwargs)
    with connection() as conn:
        assert isinstance(conn, websocket.WebSocket)
        conn.send(json.dumps(payload))
        LOGGER.debug('SEND: %s', payload)
        recv = conn.recv()
        LOGGER.debug('RECV: %s', recv)
        resp = parse_recv(recv)
        if resp.data == 'please login!!!':
            raise LoginError(resp)
        if (resp.code, resp.type) == (0, 'msg'):
            raise ValueError(resp.data)
        return resp


def account():
    """Get current account.

    Returns:
        unicode: Account name.
    """
    return call("c_token", "get_account").data


def account_id():
    """Get current acccount id.

    Returns:
        unicode: account id.
    """
    return call("c_token", "get_account_id").data
