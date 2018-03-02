# -*- coding=UTF-8 -*-
"""Create connection with cgtw server.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import errno
import hashlib
import io
import json
import logging
import os
import tempfile
from collections import namedtuple
from contextlib import contextmanager

import requests
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


def _hash(path):
    hash_ = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(2048), b''):
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
    json_ = resp.json()
    result = json_.get('data', json_)
    if (isinstance(json_, dict)
            and (json_.get('code'), json_.get('type')) == ('0', 'msg')):
        raise ValueError(result)

    return result


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

    LOGGER.debug('GET: kwargs: %s', kwargs)
    resp = requests.get('http://{}/{}'.format(ip_, pathname.lstrip('\\/')),
                        cookies=cookies,
                        **kwargs)
    try:
        result = json.loads(resp.content)
    except ValueError:
        result = None
    if (isinstance(result, dict)
            and (result.get('code'), result.get('type')) == ('0', 'msg')):
        raise ValueError(result.get('data', result))
    LOGGER.debug('GET: %s', result)
    return resp


def upload(path, pathname, is_backup=True, is_continue=True, is_replace=False):
    """Upload file to server.

    Args:
        path (unicode): Local file path.
        pathname (unicode): Server pathname.
        is_backup (bool, optional): Defaults to True.
            Tell server backup to history or not.
        is_continue (bool, optional): Defaults to True.
            If `is_continue` is True, will continue previous upload(if exists).
        is_replace (bool, optional): Defaults to False.
            If `is_replace` is Ture, will replace exsited server file.

    Raises:
        ValueError: When server file exists and `is_replace` is False.
        ValueError: When local file is empty.
    """

    chunk_size = 2*2**20  # 2MB
    hash_ = _hash(path)
    result = post('/file.php', {'file_md5': hash_,
                                'upload_des_path': pathname,
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
                'upload_des_path': pathname,
                'is_backup_to_history': 'Y' if is_backup else 'N',
                'no_continue_upload': 'N' if is_continue else 'Y'}
        for chunk in iter(lambda: f.read(chunk_size), ''):
            data['read_pos'] = file_pos
            post('/upload_file', data, files={'files': chunk})
            file_pos += chunk_size


def download(pathname, dest):
    """Download file from server.

    Args:
        pathname (unicode): Server host pathname. (e.g. `/upload/somefile.txt`)
        dest (unicode): Local destination path.
            if `dest` ends with `\\` or `/`, will treat dest as directory.

    Raises:
        ValueError: When server file not exists.
        ValueError: Local file already exists.
        RuntimeError: Dowanload fail.

    Returns:
        unicode: Path of downloaded file.
    """

    info = stat(pathname)
    if not info.file_md5:
        raise ValueError('Server file not exists.', pathname)

    # Convert diraname as dest.
    if unicode(dest).endswith(('\\', '/')):
        dest = os.path.abspath(
            os.path.join(
                dest, os.path.basename(info.server_path)
            )
        )

    # Skip if already downloaded.
    if os.path.exists(dest):
        if os.path.isfile(dest) and _hash(dest) == info.file_md5:
            return dest
        else:
            raise ValueError('Local file already exists.', dest)

    # Create dest_dir.
    dest_dir = os.path.dirname(dest)
    try:
        os.makedirs(dest_dir)
    except OSError as ex:
        if ex.errno not in (errno.EEXIST, errno.EACCES):
            raise

    # Download to tempfile.
    headers = {'Range': 'byte={}-'.format(info.file_size)}
    resp = get(info.server_path, stream=True, verify=False, headers=headers)
    fd, filename = tempfile.mkstemp('.cgtwqdownload', dir=dest_dir)
    with io.open(fd, 'wb') as f:
        for chunk in resp.iter_content():
            f.write(chunk)

    # Check hash of downloaded file.
    if _hash(filename) != info.file_md5:
        os.remove(filename)
        raise RuntimeError('Downloaded content not match server md5.')

    os.rename(filename, dest)
    return dest


def file_operation(action, **kwargs):
    """Do file operation on server.

    Args:
        action (unicode): Server defined action name.

    Returns:
        Server execution result.
    """

    LOGGER.debug('%s: %s', action, kwargs)
    kwargs['action'] = action
    result = post('/file.php', kwargs)
    LOGGER.debug('%s: result: %s', action, result)
    return result


def delete(pathname):
    """Delete file on server.

    Args:
        pathname (unicode): Server pathname.

    Returns:
        bool: Is deletion successed.
    """

    return file_operation('delete', server_path=pathname)


def rename(src, dst):
    """Rename(move) file on server.

    Args:
        src (unicode): Source server pathname.
        dst (unicode): Destnation server pathname.

    Returns:
        bool: Is deletion successed.
    """

    return file_operation('rename', old_path=src, new_path=dst)


def mkdir(pathname):
    """Make directory on server.

    Args:
        pathname (unicode): Server pathname.

    Returns:
        bool: Is directory created.
    """

    return file_operation('create_dir', server_path=pathname)


DirInfo = namedtuple('DirInfo', ('dir', 'file'))


def listdir(pathname):
    """List directory contents on server.

    Args:
        pathname (unicode): Server pathname

    Returns:
        DirInfo: namedtuple of directory info.
    """

    result = file_operation('list_dir', server_path=pathname)
    return DirInfo(**result)


def isdir(pathname):
    """Check if pathname is directory.

    Args:
        pathname (unicode): Server pathname.

    Returns:
        bool: True if `pathname` is directory.
    """

    return file_operation('is_dir', server_path=pathname)


def exists(pathname):
    """Check if pathname exists on server.

    Args:
        pathname (unicode): Server pathname.

    Returns:
        bool: True if `pathname` exists on server.
    """

    return file_operation('file_exists', server_path=pathname)


FileInfo = namedtuple('FileInfo', ('file_md5', 'file_size', 'server_path'))


def stat(pathname):
    """Get server file status.

    Args:
        pathname (unicode): Server pathname.

    Returns:
        FileInfo: Server file information.
    """

    result = file_operation('file_info', server_path=pathname)
    assert isinstance(result, dict), type(result)
    return FileInfo(**result)
