# -*- coding=UTF-8 -*-
"""Contactsheet creation."""

__version__ = '1.8.1'

from logging import getLogger

LOGGER = getLogger('com.wlf.csheet')


def create_html_from_dir(image_folder, **kwargs):
    """Create a html page for a @image_folder.  """
    import os
    from ..path import get_encoded, get_unicode
    from ..files import version_filter
    image_folder = os.path.normpath(image_folder)
    if not os.path.isdir(get_encoded(image_folder)):
        LOGGER.warning('Not a dir, ignore: %s', image_folder)
        return
    folder_name = os.path.basename(image_folder)
    images = version_filter(os.path.join(get_unicode(folder_name), get_unicode(i))
                            for i in os.listdir(get_encoded(image_folder))
                            if os.path.isfile(get_encoded(os.path.join(image_folder, i)))
                            and i.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.mov')))
    save_path = os.path.abspath(os.path.join(
        image_folder, u'../{}_色板.html'.format(os.path.basename(image_folder))))

    kwargs.setdefault('title', image_folder)
    kwargs.setdefault('save_path', save_path)
    return create_html(images, **kwargs)


def create_html(images, save_path, title=None, rename_dict=None):
    """Crete html contactsheet with @images list, save to @save_path.  """

    from .html import HTMLImage, HTMLContactSheet

    images = [HTMLImage(i) for i in images]
    rename_dict = rename_dict or {}

    for i in images:
        if i.path in rename_dict:
            i.name = rename_dict[i.path]
    csheet = HTMLContactSheet(images)
    csheet.title = title

    return csheet.generate(save_path)


def _dialog_create_html():
    """A dialog for create_html.  """

    import nuke
    import webbrowser

    folder_input_name = '文件夹'
    panel = nuke.Panel('创建HTML色板')
    panel.addFilenameSearch(folder_input_name, '')
    confirm = panel.show()
    if confirm:
        csheet = create_html_from_dir(panel.value(folder_input_name))
        if csheet:
            webbrowser.open(csheet)


locals()['dialog_create_html'] = _dialog_create_html
