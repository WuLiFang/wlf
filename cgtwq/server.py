# -*- coding=UTF-8 -*-
"""Create connection with cgtw server.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import json
import logging
import hashlib
import os
from collections import namedtuple
from contextlib import contextmanager

import websocket
import requests

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


def _get_md5(path):
    hash_ = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(2048), ''):
            hash_.update(chunk)
    return hash_.hexdigest()


def post(pathname, data, ip_=None, **kwargs):
    """Post data to CGTeamWork server.
        pathname (str unicode): Pathname for http host.
        ip_ (str unicode, optional): Defaults to None. If `ip_` is None,
            will use ip from CGTeamWorkClient.
        data: Data to post.
        **kwargs: kwargs for `requests.post`

    Returns:
        Server execution result. 
    """

    assert 'cookies' not in kwargs
    assert 'data' not in kwargs
    token = data.get('token', CGTeamWorkClient.token())
    data['token'] = token
    ip_ = ip_ or CGTeamWorkClient.server_ip()
    cookies = {'token': token}

    resp = requests.post('http://{}/{}'.format(ip_, pathname.lstrip('\\/')),
                         data={'data': json.dumps(data)},
                         cookies=cookies,
                         **kwargs)
    result = json.loads(resp.content)

    if result['code'] == '1':
        return result['data']

    raise ValueError(result)


def get(pathname, token=None, ip_=None, **kwargs):
    """Get request to CGTeamWork server.
        token (str unicode, optional): Defaults to None. If `token` is None,
            will use token from CGTeamWorkClient.
        ip_ (str unicode, optional): Defaults to None. If `ip_` is None,
            will use ip from CGTeamWorkClient.
        **kwargs: kwargs for `requests.get`

    Returns:
        [type]: [description]
    """

    assert 'cookies' not in kwargs
    token = token or CGTeamWorkClient.token()
    ip_ = ip_ or CGTeamWorkClient.server_ip()
    cookies = {'token': token}

    resp = requests.post('http://{}/{}'.format(ip_, pathname.lstrip('\\/')),
                         cookies=cookies,
                         **kwargs)
    return resp


def upload(path,
           server_path,
           is_backup=True,
           is_continue=True,
           is_replace=True,
           chunk_size=2*2**20):
    hash_ = _get_md5(path)
    LOGGER.debug(hash_)
    result = post('/file.php', {'file_md5': hash_,
                                'upload_des_path': server_path,
                                'action': 'pre_upload'})
    LOGGER.debug('POST: result: %s', result)
    assert isinstance(result, dict)
    if result['is_exist'] and not is_replace:
        raise ValueError('File already exists.')

    file_size = os.path.getsize(path)
    if not file_size:
        raise ValueError('File is empty.')

    file_pos = result['file_pos']
    with open(path, 'rb') as f:
        if file_pos:
            f.seek(file_pos)
        data = {'file_md5': hash_,
                'file_size': file_size,
                'upload_des_path': server_path,
                'is_backup_to_history': 'Y' if is_backup else 'N',
                'no_continue_upload': 'N' if is_continue else 'Y'}
        for chunk in iter(lambda: f.read(chunk_size), ''):
            data['read_pos'] = file_pos
            post('/upload_file', data, files={'files': chunk})
            file_pos += chunk_size


def download(pathname, dest):
    info = stat(pathname)
    T_server_path = T_result['server_path']
    if not info.file_md5:
        raise ValueError('File not exists.', pathname)
    if os.path.isfile(dest) and _get_md5(dest) == info.file_md5:
        return dest

    # T_cookies = {'token': G_tw_token}
    # T_headers = {'Range': 'byte=' + str(T_file_size) + '-'}
    # requests.get('http://' + G_tw_server_ip + '/' + T_server_path,
    #              stream=True, verify=False, headers=T_headers, cookies=T_cookies)
    # if not os.path.exists(os.path.dirname(T_save_tmp_path)):
    #     os.makedirs(os.path.dirname(T_save_tmp_path))
    # T_f = open(T_save_tmp_path, 'ab')
    # for T_chunk in T_r.iter_content(chunk_size=1048576):
    #     if T_chunk:
    #         T_f.write(T_chunk)
    #         T_file_size += len(T_chunk)
    #         T_f.flush()
    #         sys.stdout.write(
    #             '\x08' * 64 + str(T_file_size * 100 / int(T_result['file_size'])) + '%')
    #         sys.stdout.flush()

    # T_f.close()
    # if twfs.get_md5(T_save_tmp_path) == T_result['file_md5']:
    #     if os.path.isfile(T_local_path) == True and T_is_backup_to_history == True:
    #         if twfs.l_move_to_history(T_local_path) == False:
    #             print 'move file to history fail(' + T_local_path + ')'
    #             return False
    #     return twfs.l_move_file(T_save_tmp_path, T_local_path)
    # os.remove(T_save_tmp_path)
    # print 'check file fail\xef\xbc\x81\xef\xbc\x81--'.T_save_tmp_path
    # return False


def file_operation(action, **kwargs):
    kwargs['action'] = action
    result = post('/file.php', kwargs)
    if result is not True:
        raise ValueError(result)
    return result


def delete(pathname):
    return file_operation('delete', server_path=pathname)


def rename(src, dst):
    return file_operation('rename', old_path=src, new_path=dst)


def mkdir(pathname):
    return file_operation('create_dir', server_path=pathname)


def listdir(pathname):
    return file_operation('list_dir', server_path=pathname)


def isdir(pathname):
    return file_operation('is_dir', server_path=pathname)


def exists(pathname):
    return file_operation('file_exists', server_path=pathname)


FileInfo = namedtuple('FileInfo', ('file_md5', 'file_size', 'server_path'))


def stat(pathname):
    result = file_operation('file_info', server_path=pathname)
    assert isinstance(result, dict), type(result)
    return FileInfo(**result)
