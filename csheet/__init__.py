# -*- coding=UTF-8 -*-
"""Contactsheet creation."""

__version__ = '1.11.0'

from logging import getLogger

LOGGER = getLogger('com.wlf.csheet')


def create_html_from_dir(image_folder, save_path=None, **config):
    """Create a html page for a @image_folder.  """

    from .html import from_dir
    from ..path import PurePath, Path

    images_folder_path = PurePath(image_folder)
    save_path = (Path(save_path) if save_path
                 else Path(image_folder)
                 .with_name('{}_色板.html'.format(images_folder_path.name)))
    config.setdefault('relative_to', images_folder_path.parent)
    with save_path.open('w', encoding='UTF-8') as f:
        f.write(from_dir(images_folder_path, **config))
    return save_path


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
