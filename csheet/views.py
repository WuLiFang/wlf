# -*- coding=UTF-8 -*-
"""Run as web app.  """

from __future__ import absolute_import, print_function, unicode_literals


from functools import update_wrapper
from os import SEEK_END
from os.path import join
from tempfile import TemporaryFile, gettempdir
from zipfile import ZipFile

from diskcache import FanoutCache
from flask import (Flask, Response, abort, make_response, render_template,
                   request, send_file, redirect, send_from_directory)
from gevent import sleep, spawn, monkey
from gevent.queue import Queue

from . import __version__
from .. import cgtwq
from .html import HTMLImage, updated_config, from_dir, get_images_from_dir
from ..path import Path


monkey.patch_all()
APP = Flask(__name__, static_folder='../static')
APP.config['PACK_FOLDER'] = 'D:/'
APP.secret_key = ('}w\xb7\xa3]\xfaI\x94Z\x14\xa9\xa5}\x16\xb3'
                  '\xf7\xd6\xb2R\xb0\xf5\xc6*.\xb3I\xb7\x066V\xd6\x8d')
APP.config['version'] = __version__
if cgtwq.MODULE_ENABLE:
    PROJECT = cgtwq.Project()
STATUS = {}
SHOTS_CACHE = {}
PROGRESS_EVENT_LISTENER = []
CACHE = FanoutCache(join(gettempdir(), 'csheet_server'))


def nocache(func):
    """(Decorator)Tell falsk make respon with no_cache.  """

    def _func(*args, **kwargs):
        resp = make_response(func(*args, **kwargs))
        resp.cache_control.no_cache = True
        return resp
    return update_wrapper(_func, func)


@APP.route('/', methods=('GET',))
def render_main():
    """main page.  """

    if APP.config.get('local_dir'):
        return redirect('/local')

    if not cgtwq.MODULE_ENABLE:
        return '服务器无法连接CGTeamWork', 503

    if request.query_string:
        args = request.args

        project = args['project']
        prefix = args.get('prefix')
        pipeline = args.get('pipeline')

        config = get_csheet_config(project, pipeline, prefix)

        if 'pack' in args:
            return packed_page(**config)

        config['is_web'] = True

        # Respon with cookies set.
        resp = make_response(render_template('csheet_web.html', **config))
        cookie_life = 60 * 60 * 24 * 90
        resp.set_cookie('project', project, max_age=cookie_life)
        resp.set_cookie('pipeline', pipeline, max_age=cookie_life)
        resp.set_cookie('prefix', prefix, max_age=cookie_life)

        return resp

    return render_template('index.html', projects=PROJECT.names())


@APP.route('/local')
def render_local_dir():
    """Render page for local dir.  """

    local_dir = APP.config['local_dir']
    if not Path(local_dir).exists():
        abort(404)

    if request.args.get('pack'):
        return packed_page(images=get_images_from_dir(local_dir))

    return from_dir(local_dir, is_local=True, relative_to=local_dir)


@APP.route('/local/<path:filename>')
@nocache
def get_local(filename):
    """get file in local_dir.  """

    return send_from_directory(APP.config['local_dir'], filename)


@APP.route('/images/<uuid>/preview')
@nocache
def image_preview(uuid):
    """Response preview video for uuid.

    Decorators:
        APP

    Args:
        uuid (str): Image uuid.

    Returns:
        flask.Response: Response for client.
    """

    try:
        image = HTMLImage.cache[uuid]
    except KeyError:
        abort(404)
    assert isinstance(image, HTMLImage)

    job = spawn(image.generate_preview)
    while not job.ready():
        sleep(0.1)
    preview = job.get()
    if preview is None:
        return image_full(uuid)
    APP.logger.error(preview)
    return send_file(unicode(image.preview))


@APP.route('/images/<uuid>/full')
@nocache
def image_full(uuid):
    """Response full image for uuid.

    Decorators:
        APP

    Args:
        uuid (str): Image uuid.

    Returns:
        flask.Response: Response for client.
    """

    try:
        image = HTMLImage.cache[uuid]
    except KeyError:
        abort(404)
    assert isinstance(image, HTMLImage)

    return send_file(unicode(image.path))


def get_images(shots):
    """Get all images relate @shots.  """

    assert isinstance(shots, cgtwq.Shots)
    images = shots.shots
    images = [get_html_image(shots.database, shots.pipeline, shots.prefix, i)
              for i in images]
    return images


def get_csheet_config(project, pipeline, prefix):
    """Provide infos a csheet needed.  """

    database = PROJECT.get_info(project, 'database')
    config = {
        'project': project,
        'database': database,
        'pipeline': pipeline,
        'prefix': prefix,
        'images': get_images(get_shots(database, pipeline=pipeline, prefix=prefix)),
        'title': '{}色板'.format('_'.join(
            i for i in
            (project, prefix.strip(get_project_code(project)).strip('_'), pipeline) if i)),
        'pack_progress': pack_progress()
    }
    return updated_config(config)


def pack_progress(value=None):
    """Return server pack progress status.  """

    if value is not None:
        old_value = STATUS.get('PACK_PROGRESS')
        STATUS['PACK_PROGRESS'] = value
        if old_value != value:
            for queue in PROGRESS_EVENT_LISTENER:
                queue.put(value)
        return
    return str(STATUS.get('PACK_PROGRESS', -1))


@APP.route('/pack_progress')
@nocache
def pack_event():
    def _sse(data):
        return 'data: {}\n\n'.format(data)

    if request.headers.get('accept') == 'text/event-stream':
        def events():
            queue = Queue()
            PROGRESS_EVENT_LISTENER.append(queue)
            try:
                while True:
                    yield _sse(queue.get())
            except GeneratorExit:
                PROGRESS_EVENT_LISTENER.remove(queue)

        return Response(events(), content_type='text/event-stream')
    return pack_progress()


def packed_page(**config):
    """Return zip packed local version.  """

    if float(pack_progress()) != -1:
        abort(429)
    config = updated_config(config)
    pack_progress(0)

    f = TemporaryFile(suffix='.zip',
                      prefix=config.get('title', 'packing_csheet_'),
                      dir=APP.config.get('PACK_FOLDER'))
    filename = '{}.zip'.format(config.get('title', 'temp'))
    APP.logger.info('Start archive page.')
    config['is_pack'] = True

    with ZipFile(f, 'w', allowZip64=True) as zipfile:
        # Pack index.
        index_page = render_template('csheet.html', **config)
        zipfile.writestr('{}.html'.format(
            config.get('title', 'index')), bytes(index_page))

        # Pack images.
        images = config.get('images')
        if not images:
            abort(404)
        total = len(images)

        def _write_image(image):
            assert isinstance(image, HTMLImage)
            try:
                zipfile.write(unicode(image.path),
                              'images/{}'.format(image.path.name))
            except OSError:
                pass
            try:
                zipfile.write(unicode(image.generate_preview()),
                              'previews/{}'.format(image.preview.name))
            except OSError:
                pass

        for index, i in enumerate(images, 1):
            job = spawn(_write_image, i)
            while not job.ready():
                sleep(0.1)
            pack_progress(index * 100.0 / total)

        # Pack static files:
        for i in config.get('static', ()):
            zipfile.write(APP.static_folder + '/' + i, 'static/{}'.format(i))

    f.seek(0, SEEK_END)
    size = f.tell()
    f.seek(0)
    resp = send_file(f, as_attachment=True, attachment_filename=filename,
                     add_etags=False)
    resp.headers.extend({
        'Content-Length': size,
        'Cache-Control': 'no-cache'
    })
    pack_progress(-1)
    return resp


def get_shots(database, pipeline, prefix):
    """Get shots, try from cache.  """

    key = (database, pipeline, prefix)
    if not SHOTS_CACHE.has_key(key):
        SHOTS_CACHE[key] = cgtwq.Shots(
            database, prefix=prefix, pipeline=pipeline)
    return SHOTS_CACHE[key]


@CACHE.memoize(tag='htmlimage', expire=3600)
def get_html_image(database, pipeline, prefix, name):
    """Get HTMLImage object.  """

    related_pipeline = {'灯光':  '渲染'}

    shots = get_shots(database, pipeline=pipeline, prefix=prefix)
    if pipeline in related_pipeline:
        _pipeline = related_pipeline[pipeline]
        video_shots = get_shots(database, pipeline=_pipeline, prefix=prefix)
    else:
        video_shots = None

    path = shots.get_shot_image(name)
    if path is None:
        raise ValueError
    image = HTMLImage(path)
    image.preview_source = (video_shots or shots).get_shot_submit_path(name)
    return image


# @APP.route('/images/<database>/<pipeline>/<prefix>/<name>')
# @nocache
# def get_image(database, pipeline, prefix, name):
#     """Respon image request.  """
#     name = name.split('.')[0]
#     try:
#         image = get_html_image(database, pipeline, prefix, name)
#         return send_file(unicode(image.path))
#     except (IOError, ValueError) as ex:
#         APP.logger.error(ex)
#         abort(404)


# @APP.route('/previews/<database>/<pipeline>/<prefix>/<name>')
# @nocache
# def get_preview(database, pipeline, prefix, name):
#     """Respon preview request.  """

#     name = name.split('.')[0]
#     height = {
#         '动画': 180,
#         '灯光': 200,
#         '合成': 300,
#     }.get(pipeline, None)

#     try:
#         image = get_html_image(database, pipeline, prefix, name)
#         job = spawn(image.generate_preview, height=height)
#         while not job.ready():
#             sleep(0.1)
#         preview = job.get()
#         if preview is None:
#             return get_image(database, pipeline, prefix, name)
#         APP.logger.debug(u'获取动图: %s', preview)
#     except ValueError:
#         APP.logger.error(image)
#         abort(404)

#     return send_file(unicode(preview))


@APP.route('/project_code/<project>')
def get_project_code(project):
    """Get proejct code for @project.  """

    return PROJECT.get_info(project, 'code')
