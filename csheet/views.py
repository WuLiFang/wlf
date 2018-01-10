# -*- coding=UTF-8 -*-
"""Run as web app.  """

from __future__ import absolute_import, print_function, unicode_literals

from functools import update_wrapper
from os import SEEK_END
from os.path import join
from tempfile import TemporaryFile, gettempdir
from zipfile import ZipFile

from diskcache import FanoutCache
from flask import (Flask, abort, make_response, render_template, request,
                   send_file)

from . import __version__
from ..cgtwq import Project, Shots
from .html import HTMLImage

APP = Flask(__name__, static_folder='../static')
APP.config['PACK_FOLDER'] = 'D:/'
APP.secret_key = ('}w\xb7\xa3]\xfaI\x94Z\x14\xa9\xa5}\x16\xb3'
                  '\xf7\xd6\xb2R\xb0\xf5\xc6*.\xb3I\xb7\x066V\xd6\x8d')
APP.config['version'] = __version__
PROJECT = Project()
SHOTS_CACHE = {}
CACHE = FanoutCache(join(gettempdir(), 'csheet_server'))


def nocache(func):
    """(Decorator)Tell falsk make respon with no_cache.  """

    def _func(*args, **kwargs):
        resp = make_response(func(*args, **kwargs))
        resp.cache_control.no_cache = True
        return resp
    return update_wrapper(_func, func)


@APP.route('/', methods=('GET',))
def index():
    """main page.  """

    if request.query_string:
        args = request.args

        project = args['project']
        prefix = args.get('prefix')
        pipeline = args.get('pipeline')

        config = get_csheet_config(project, pipeline, prefix)

        if 'pack' in args:
            return packed_page(**config)

        # Respon with cookies set.
        resp = make_response(render_template('csheet_web.html', **config))
        cookie_life = 60 * 60 * 24 * 90
        resp.set_cookie('project', project, max_age=cookie_life)
        resp.set_cookie('pipeline', pipeline, max_age=cookie_life)
        resp.set_cookie('prefix', prefix, max_age=cookie_life)

        return resp

    return render_template('index.html', projects=PROJECT.names())


def get_images(shots):
    assert isinstance(shots, Shots)
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
        'static': ('csheet.css', 'html5shiv.min.js',
                   'jquery-3.2.1.min.js', 'jquery.appear.js', 'csheet.js')
    }
    return config


def packed_page(**config):
    """Return zip packed local version.  """

    f = TemporaryFile(suffix='.zip', prefix=config.get(
        'title'), dir=APP.config.get('PACK_FOLDER'))
    filename = '{}.zip'.format(config.get('title', 'temp'))
    APP.logger.debug('Start archive page.')

    with ZipFile(f, 'w', allowZip64=True) as zipfile:
        index_page = render_template('csheet_pack.html', **config)

        # Pack index.
        zipfile.writestr('{}.html'.format(
            config.get('title', 'index')), bytes(index_page))

        # Pack static files:
        for i in config.get('static', ()):
            zipfile.write(APP.static_folder + '/' + i, 'static/{}'.format(i))

        # Pack images.
        for i in config.get('images', ()):
            assert isinstance(i, HTMLImage)
            try:
                zipfile.write(unicode(i.path), 'images/{}.jpg'.format(i.name))
            except OSError:
                pass
            try:
                zipfile.write(unicode(i.generate_preview()),
                              'previews/{}.gif'.format(i.name))
            except OSError:
                pass

    f.seek(0, SEEK_END)
    size = f.tell()
    f.seek(0)
    resp = send_file(f, as_attachment=True, attachment_filename=filename,
                     add_etags=False)
    resp.headers.extend({
        'Content-Length': size,
        'Cache-Control': 'no-cache'
    })
    return resp


def get_shots(database, pipeline, prefix):
    """Get shots, try from cache.  """

    key = (database, pipeline, prefix)
    if not SHOTS_CACHE.has_key(key):
        SHOTS_CACHE[key] = Shots(database, prefix=prefix, pipeline=pipeline)
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
    image.related_video = (video_shots or shots).get_shot_submit_path(name)
    return image


@APP.route('/test')
def test():
    return 'test text'


@APP.route('/images/<database>/<pipeline>/<prefix>/<name>')
@nocache
def get_image(database, pipeline, prefix, name):
    """Respon image request.  """
    name = name.split('.')[0]
    try:
        image = get_html_image(database, pipeline, prefix, name)
        return send_file(unicode(image.path))
    except (IOError, ValueError) as ex:
        APP.logger.error(ex)
        abort(404)


@APP.route('/previews/<database>/<pipeline>/<prefix>/<name>')
@nocache
def get_preview(database, pipeline, prefix, name):
    """Respon preview request.  """

    name = name.split('.')[0]
    height = {
        '动画': 180,
        '灯光': 200,
        '合成': 300,
    }.get(pipeline, None)

    try:
        image = get_html_image(database, pipeline, prefix, name)
        preview = image.generate_preview(height=height)
        if preview is None:
            return get_image(database, pipeline, prefix, name)
        APP.logger.debug(u'获取动图: %s', preview)
    except ValueError:
        APP.logger.error(image)
        abort(404)

    return send_file(unicode(preview))


@APP.route('/project_code/<project>')
def get_project_code(project):
    """Get proejct code for @project.  """

    return PROJECT.get_info(project, 'code')
