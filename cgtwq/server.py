# -*- coding=UTF-8 -*-
"""Create connection with cgtw server.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from contextlib import contextmanager
from .client import CGTeamWorkClient
from .exceptions import LoginError

import websocket
import json
import cgtw
from collections import namedtuple

CACHE = {}
PORT = 8888


@contextmanager
def connection():
    url = 'ws://{}:{}'.format(CGTeamWorkClient.server_ip(), PORT)
    conn = websocket.create_connection(url)
    assert isinstance(conn, websocket.WebSocket)
    try:
        yield conn
    finally:
        conn.close()


Response = namedtuple('Response', ['data', 'code', 'type'])


def parse_recv(payload):
    resp = json.loads(payload)
    data = resp['data']
    code = int(resp['code'])
    type_ = resp['type']
    return Response(data, code, type_)


def send(controller, method, payload):
    assert isinstance(payload, dict)
    assert 'controller' not in payload
    assert 'method' not in payload

    payload.update({'controller': controller,
                    'method': method, 'token': CGTeamWorkClient.token()})
    with connection() as conn:
        assert isinstance(conn, websocket.WebSocket)
        conn.send(json.dumps(payload.items()))
        recv = conn.recv()
        resp = parse_recv(recv)
        if resp.data == 'please login!!!':
            raise LoginError(resp)
        if not resp.code and resp.type == 'msg':
            raise RuntimeError(resp)
        return resp


def account():
    return send("c_token", "get_account", {"token": CGTeamWorkClient.token()}).data


def account_id():
    return send("c_token", "get_account_id", {"token": CGTeamWorkClient.token()}).data
