# -*- coding=UTF-8 -*-
"""Run as web app.  """

from __future__ import absolute_import, print_function, unicode_literals

import json
from os import SEEK_END
from os.path import join
from tempfile import TemporaryFile, gettempdir
from zipfile import ZipFile

from diskcache import FanoutCache
from flask import (Flask, Response, abort, escape, make_response, redirect,
                   render_template, request, send_file)
from gevent import sleep, spawn
from gevent.queue import Empty, Queue

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
STATUS = {}
PROGRESS_EVENT_LISTENER = []
CACHE = FanoutCache(join(gettempdir(), 'csheet_server/cache'))


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
        return render_template('index.html', projects=cgtwq.PROJECT.names())

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
# @nocache
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
    folder = APP.config.get('storage')
    if folder:
        kwargs['output'] = join(folder, role, uuid)

    result = Queue(1)

    def _gen():
        try:
            ret = image.generate(role,
                                 is_strict=role not in ('thumb', 'full'),
                                 limit_size=APP.config['preview_limit_size'],
                                 **kwargs)
            result.put(ret)
        except Exception as ex:  # pylint: disable=broad-except
            result.put(ex)
    spawn(_gen)
    sleep()

    try:
        generated = result.get(block=False)
        if isinstance(generated, ValueError):
            raise Empty
        if isinstance(generated, Exception):
            u_abort(500, generated)

        if not Path(generated).exists():
            try:
                del image.genearated[role]
            except KeyError:
                pass
            return make_response('Generated file has been moved', 503, {'Retry-After': 10})

        resp = send_file(unicode(generated), conditional=True)
        resp.cache_control.max_age = 0
        resp.cache_control.no_cache = True
        if request.args:
            resp.cache_control.no_store = True
        return resp
    except Empty:
        return make_response('Image not ready.', 503, {'Retry-After': 10})


def get_images(database, pipeline, prefix):
    """Get all images relate @shots.  """

    related_pipeline = {'灯光':  '渲染'}.get(pipeline)
    database = cgtwq.Database(database)
    module = database['shot_task']
    select = module.filter(cgtwq.Filter('pipeline', pipeline))
    field_data = select.get_fields('id', 'shot.shot', 'image')
    ret = []

    fileboxes = database.get_filebox(
        cgtwq.Filter(
            '#pipeline_id',
            database.get_pipline(cgtwq.Filter('name', pipeline))[0].id) &
        cgtwq.Filter('title', ['单帧图', '检查单帧图']))
    if related_pipeline:
        related_shots = module.filter(
            cgtwq.Filter('pipeline', related_pipeline))
        previews = {i[0]: i[1]
                    for i in related_shots.get_fields('shot.shot', 'submit_file_path')}
    for i in field_data:
        id_, shot, image_data = i
        if shot and shot.startswith(prefix):
            _select = module.select(id_)

            try:
                path = json.loads(image_data)['image_path']
            except (TypeError, KeyError):
                path = '{}/{}.jpg'.format(
                    _select.get_filebox(id_=fileboxes[0].id).path, shot)

            img = HTMLImage(path)
            if related_pipeline:
                try:
                    data = previews.get(shot)
                    if data:
                        img.source['preview'] = json.loads(data)['path']
                except (TypeError, IndexError):
                    pass
            ret.append(img)
    return ret


def get_csheet_config(project, pipeline, prefix):
    """Provide infos a csheet needed.  """

    database = cgtwq.PROJECT.filter(
        cgtwq.Filter('full_name', project))['database'][0]
    config = {
        'project': project,
        'database': database,
        'pipeline': pipeline,
        'prefix': prefix,
        'images': get_images(database, pipeline=pipeline, prefix=prefix),
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


@APP.route('/project_code/<project>')
def get_project_code(project):
    """Get proejct code for @project.  """

    try:
        return cgtwq.PROJECT.filter(cgtwq.Filter('full_name', project))['code'][0]
    except IndexError:
        u_abort(404, 'No such project.')
