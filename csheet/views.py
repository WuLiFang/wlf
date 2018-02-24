# -*- coding=UTF-8 -*-
"""Run as web app.  """

from __future__ import absolute_import, print_function, unicode_literals

from functools import update_wrapper
from os import SEEK_END
from os.path import join
from tempfile import TemporaryFile, gettempdir
from zipfile import ZipFile

from diskcache import FanoutCache
from flask import (Flask, Response, abort, make_response, redirect,
                   render_template, request, send_file, escape)
from gevent import sleep, spawn, Timeout
from gevent.queue import Queue

from . import __version__
from .. import cgtwq
from ..path import Path
from .html import HTMLImage, from_dir, get_images_from_dir, updated_config

APP = Flask(__name__, static_folder='../static')
APP.config['PACK_FOLDER'] = 'D:/'
APP.secret_key = ('}w\xb7\xa3]\xfaI\x94Z\x14\xa9\xa5}\x16\xb3'
                  '\xf7\xd6\xb2R\xb0\xf5\xc6*.\xb3I\xb7\x066V\xd6\x8d')
APP.config['version'] = __version__
APP.config['preview_limit_size'] = 10 * 2 ** 20  # 10MB
# APP.config['generate_folder'] = join(gettempdir(), 'csheet_server/generated')
if cgtwq.MODULE_ENABLE:
    PROJECT = cgtwq.Project()
STATUS = {}
SHOTS_CACHE = {}
PROGRESS_EVENT_LISTENER = []
CACHE = FanoutCache(join(gettempdir(), 'csheet_server/cache'))


def nocache(func):
    """(Decorator)Tell falsk make respon with no_cache.  """

    def _func(*args, **kwargs):
        resp = make_response(func(*args, **kwargs))
        resp.cache_control.no_cache = True
        resp.cache_control.max_age = 10
        return resp
    return update_wrapper(_func, func)


def u_abort(status, msg):
    """Abort with unicode message.  """

    abort(make_response(escape(unicode(msg)), status, {
        'Content-Type': 'text/html; charset=utf-8'}))


@APP.route('/', methods=('GET',))
def render_main():
    """main page.  """

    if APP.config.get('local_dir'):
        return redirect('/local')

    if not cgtwq.CGTeamWorkClient.is_logged_in():
        u_abort(503, '服务器无法连接到CGTeamWork')

    args = request.args
    if not args:
        return render_template('index.html', projects=PROJECT.names())

    try:
        project = args['project']
        prefix = args.get('prefix')
        pipeline = args.get('pipeline')

        config = get_csheet_config(project, pipeline, prefix)

        if 'pack' in args:
            return packed_page(**config)

        config['is_client'] = True

        # Respon with cookies set.
        resp = make_response(render_template('csheet_app.html', **config))
        cookie_life = 60 * 60 * 24 * 90
        resp.set_cookie('project', project, max_age=cookie_life)
        resp.set_cookie('pipeline', pipeline, max_age=cookie_life)
        resp.set_cookie('prefix', prefix, max_age=cookie_life)

        return resp
    except Exception as ex:
        u_abort(500, ex)
        raise


@APP.route('/local')
def render_local_dir():
    """Render page for local dir.  """

    local_dir = APP.config['local_dir']
    if not Path(local_dir).exists():
        abort(404)

    if request.args.get('pack'):
        return packed_page(images=get_images_from_dir(local_dir))

    return from_dir(local_dir, is_client=True, relative_to=local_dir)


@APP.route('/images/<uuid>.<role>')
def response_image(uuid, role):
    """Response file for a image.

    Decorators:
        APP

    Args:
        uuid (str): Image uuid.
        role (str): Role of wanted file.

    Returns:
        flask.Response: Response for client.
    """

    try:
        image = HTMLImage.from_uuid(uuid)
        assert isinstance(image, HTMLImage)
    except (KeyError, ValueError):
        abort(404, 'No image match this uuid.')

    kwargs = {}
    folder = APP.config.get('generate_folder')
    if folder:
        kwargs['output'] = join(folder, role, uuid)
    job = spawn(image.generate, role,
                is_strict=role not in ('thumb', 'full'),
                limit_size=APP.config['preview_limit_size'],
                **kwargs)

    sleep()
    try:
        generated = job.get(block=False)
        if not Path(generated).exists():
            del image.genearated[role]
            return make_response('Generated file has been moved', 503, {'Retry-After': 10})

        return send_file(unicode(generated), conditional=True)
    except Timeout:
        return make_response('Image not ready.', 503, {'Retry-After': 10})
    except Exception as ex:
        u_abort(500, ex)
        raise


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

    return str(STATUS.get('PACK_PROGRESS', -1))


@APP.route('/pack_progress')
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

        # Pack images.
        images = config.get('images')
        if not images:
            abort(404)
        total = len(images)

        def _write_image(image):
            assert isinstance(image, HTMLImage)
            for role, dirname in image.folder_names.items():
                try:
                    generated = image.generate(role)
                    zipfile.write(unicode(generated),
                                  '{}/{}'.format(dirname, generated.name))
                except (OSError, KeyError):
                    pass

        for index, i in enumerate(images, 1):
            job = spawn(_write_image, i)
            while not job.ready():
                sleep(0.1)
            pack_progress(index * 100.0 / total)

        # Pack static files:
        for i in config.get('static', ()):
            zipfile.write(APP.static_folder + '/' + i, 'static/{}'.format(i))

        # Pack index.
        index_page = render_template('csheet.html', **config)
        zipfile.writestr('{}.html'.format(
            config.get('title', 'index')), index_page.encode('utf-8'))

    f.seek(0, SEEK_END)
    size = f.tell()
    f.seek(0)
    resp = send_file(f, as_attachment=True, attachment_filename=filename.encode('utf-8'),
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


# @CACHE.memoize(tag='htmlimage', expire=3600)
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
    preview_source = (video_shots or shots).get_shot_submit_path(name)
    if preview_source:
        image.source['preview'] = preview_source
    return image


@APP.route('/project_code/<project>')
def get_project_code(project):
    """Get proejct code for @project.  """

    return PROJECT.get_info(project, 'code')
