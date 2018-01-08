# -*- coding=UTF-8 -*-
"""Run as web app.  """

from __future__ import unicode_literals, print_function, absolute_import

from functools import update_wrapper

from flask import (Flask, render_template, request, send_file,
                   abort, make_response)

from ..cgtwq import Project, Shots
from .html import HTMLImage
from . import __version__

APP = Flask(__name__, static_folder='../static')
APP.secret_key = ('}w\xb7\xa3]\xfaI\x94Z\x14\xa9\xa5}\x16\xb3'
                  '\xf7\xd6\xb2R\xb0\xf5\xc6*.\xb3I\xb7\x066V\xd6\x8d')
APP.config['version'] = __version__
PROJECT = Project()
SHOTS_CACHE = {}


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
        database = PROJECT.get_info(project, 'database')
        code = PROJECT.get_info(project, 'code')
        shots = get_shots(database, prefix=prefix, pipeline=pipeline)
        title = '{}色板'.format('_'.join(
            i for i in [project, prefix.strip(code).strip('_'), pipeline] if i))
        images = shots.shots
        images = [get_html_image(database, pipeline, prefix, i)
                  for i in images]
        count = len(images)

        resp = make_response(
            render_template('csheet.html', database=database, pipeline=pipeline,
                            prefix=prefix, title=title, images=images, count=count))
        cookie_life = 60 * 60 * 24 * 90
        resp.set_cookie('project', project, max_age=cookie_life)
        resp.set_cookie('pipeline', pipeline, max_age=cookie_life)
        resp.set_cookie('prefix', prefix, max_age=cookie_life)

        return resp

    return render_template('index.html', projects=PROJECT.names())


def get_shots(database, pipeline, prefix):
    key = (database, pipeline, prefix)
    if not SHOTS_CACHE.has_key(key):
        SHOTS_CACHE[key] = Shots(database, prefix=prefix, pipeline=pipeline)
    return SHOTS_CACHE[key]


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
