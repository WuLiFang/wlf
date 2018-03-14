# -*- coding=UTF-8 -*-
"""Database in cgtw server.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import json
import logging
from collections import namedtuple
from functools import partial

from . import server
from .filter import Filter, FilterList
from .util import genreate_thumb, file_md5

_OS = {'windows': 'win', 'linux': 'linux', 'darwin': 'mac'}.get(
    __import__('platform').system().lower())  # Server defined os string.
LOGGER = logging.getLogger('wlf.cgtwq.database')

# Filebox
FIELDS_FILEBOX = ('#id', '#pipeline_id', 'title')
FileBoxInfo = namedtuple('FileBoxInfo', ('id', 'pipeline_id', 'title'))
FileBoxDetail = namedtuple(
    'FileBoxDetail',
    ('path',
     'classify', 'title',
     'sign', 'color', 'rule', 'rule_view',
     'is_submit', 'is_move_old_to_history',
     'is_move_same_to_history', 'is_in_history_add_version',
     'is_in_history_add_datetime', 'is_cover_disable',
     'is_msg_to_first_qc')
)

# Pipeline
FIELDS_PIPELINE = ('#id', 'name', 'module')
PipelineInfo = namedtuple('PipelineInfo', ('id', 'name', 'module'))

# Image
ImageInfo = namedtuple('ImageInfo', ('max', 'min', 'path'))

# Note
FIELDS_NOTE = ('#id', '#task_id', '#from_account_id',
               'text', 'time', 'create_by',
               'module')
NoteInfo = namedtuple('NoteInfo',
                      ('id', 'task_id', 'account_id',
                       'html', 'time', 'account_name',
                       'module'))
# History
FIELDS_HISTORY = ('#id', '#task_id', '#account_id',
                  'step', 'status', 'file',
                  'text', 'create_by', 'time')
HistoryInfo = namedtuple('HistoryInfo',
                         ('id', 'task_id', 'account_id',
                          'step', 'status', 'file',
                          'text', 'create_by', 'time'))


class Database(object):
    """Database on server.    """

    def __init__(self, name):
        self.name = name
        self.call = partial(server.call,
                            db=self.name)

    def __getitem__(self, name):
        return Module(name=name, database=self)

    def get_fileboxes(self, filters=None, id_=None):
        """Get fileboxes in this database.
            filters (FilterList, optional): Defaults to None. Filters to get filebox.
            id_ (unicode, optional): Defaults to None. Filebox id.

        Raises:
            ValueError: Not enough arguments.
            ValueError: No matched filebox.

        Returns:
            tuple[Filebox]: namedtuple for ('id', 'pipeline_id', 'title')
        """

        if id_:
            resp = self.call("c_file", "get_one_with_id",
                             id=id_,
                             field_array=FIELDS_FILEBOX)
            ret = [resp.data]
        elif filters:
            resp = self.call("c_file", "get_with_filter",
                             filter_array=FilterList(filters),
                             field_array=FIELDS_FILEBOX)
            ret = resp.data
        else:
            raise ValueError(
                'Need at least one of (id_, filters) to get filebox.')

        if not resp.data:
            raise ValueError('No matched filebox.')
        assert all(isinstance(i, list) for i in ret), resp
        return tuple(FileBoxInfo(*i) for i in ret)

    def get_piplines(self, filters):
        """Get piplines from database.

        Args:
            filters (FilterList): Filter to get pipeline.

        Returns:
            tuple[Pipeline]: namedtuple for ('id', 'name', 'module')
        """

        resp = self.call(
            "c_pipeline", "get_with_filter",
            field_array=FIELDS_PIPELINE,
            filter_array=FilterList(filters))
        return tuple(PipelineInfo(*i) for i in resp.data)

    def get_software(self, name):
        """Get software path for this database.

        Args:
            name (unicode): Software name.

        Returns:
            path: Path set in `设置` -> `软件`.
        """

        resp = self.call("c_software", "get_path", name=name)
        return resp.data

    def set_data(self, key, value, is_user=True):
        """Set addtional data in this database.

        Args:
            key (unicode): Data key.
            value (unicode): Data value
            is_user (bool, optional): Defaults to True.
                If `is_user` is True, this data will be user specific.
        """

        self.call("c_api_data",
                  'set_user' if is_user else 'set_common',
                  key=key, value=value)

    def get_data(self, key, is_user=True):
        """Get addional data set in this database.

        Args:
            key (unicode): Data key.
            is_user (bool, optional): Defaults to True.
                If `is_user` is True, this data will be user specific.

        Returns:
            Unicode: Data value.
        """

        resp = self.call("c_api_data",
                         'get_user' if is_user else 'get_common',
                         key=key)
        return resp.data


class Module(object):
    """Module(Database table) in database.    """

    def __init__(self, name, database):
        """
        Args:
            name (unicode): Server defined module name.
            database (Database): Parent database.
        """

        if name:
            self.name = name
        assert isinstance(database, Database)
        self.database = database
        self.call = partial(self.database.call,
                            module=self.name)

    def __getitem__(self, name):
        if isinstance(name, (Filter, FilterList)):
            return self.filter(name)
        return self.select(name)

    def select(self, *id_list):
        """Create selection on this module.

        Args:
            *id_list (unicode): Id list to select.

        Returns:
            Selection: Created selection.
        """

        return Selection(self, *id_list)

    def filter(self, filters):
        """Create selection with filter on this module.

        Args:
            filters (FilterList, Filter): Filters for server.

        Returns:
            Selection: Created selection.
        """

        _filters = self.format_filters(filters)
        resp = self.call('c_orm', 'get_with_filter',
                         sign_array=[self.field('id')],
                         sign_filter_array=_filters)
        if resp.data:
            id_list = [i[0] for i in resp.data]
        else:
            id_list = []
        return Selection(self, *id_list)

    def field(self, name):
        """Formatted field name for this module.

        Args:
            name (unicode): Short field name.

        Returns:
            unicode: Full field name, for server.
        """

        assert isinstance(name, (str, unicode))
        if ('.' in name
                or '#' in name):
            return name
        return '{}.{}'.format(self.name, name)

    def format_filters(self, filters):
        """Format field name in filters.

        Args:
            filters (FilterList, Filter): Format target.

        Returns:
            FilterList: Formatted filters.
        """

        assert isinstance(filters, (Filter, FilterList)), type(filters)
        ret = FilterList(filters)
        for i in ret:
            if isinstance(i, Filter):
                i[0] = self.field(i[0])
        return ret

    def pipelines(self):
        """All pipeline in this module.

        Returns:
            tuple[Pipeline]: namedtuple for ('id', 'name', 'module').
        """

        return self.database.get_piplines(Filter('module', self.name))

    def get_history(self, filters):
        """Get history record from the module.
            filters (Filter or FilterList): History filters.

        Returns:
            tuple[HistoryInfo]: History records.
        """

        resp = self.call(
            "c_history", "get_with_filter",
            field_array=FIELDS_HISTORY,
            filter_array=FilterList(filters))
        return tuple(HistoryInfo(*i) for i in resp.data)

    def count_history(self, filters):
        """Count history records in the module.

        Args:
            filters (Filter or FilterList):
                History filters.

        Returns:
            int: Records count.
        """

        resp = self.call(
            "c_history", "count_with_filter",
            filter_array=FilterList(filters))
        return int(resp.data)


class PublicModule(Module):
    """Module in special `public` database.    """

    def __init__(self):
        self.database = Database('public')
        super(PublicModule, self).__init__(self.name, self.database)


class Project(PublicModule):
    """Module to keep project information.   """

    name = 'project'

    def all(self):
        """All active project.

        Returns:
            Selection: Projects.
        """

        return self.filter(Filter('status', 'Active'))

    def names(self):
        """All actived project names.

        Returns:
            tuple
        """

        return self.all()['full_name']


PROJECT = Project()


class Account(PublicModule):
    """Module to keep account information.   """

    name = 'account'

    def all(self):
        """All active user  .

        Returns:
            Selection: Users.
        """

        return self.filter(Filter('status', 'Y'))

    def names(self):
        """All user names.

        Returns:
            tuple
        """

        return self.all()['name']


ACCOUNT = Account()


class Selection(tuple):
    """Selection on a database module.   """

    def __new__(cls, module, *id_list):
        assert all(isinstance(i, unicode) for i in id_list), id_list
        assert isinstance(module, Module)
        return super(Selection, cls).__new__(cls, id_list)

    def __init__(self, module, *id_list):
        """
        Args:
            module (Module): Related module.
            *id_list: Selected id.
        """

        super(Selection, self).__init__(id_list)
        self.module = module
        self.call = partial(self.module.call, id_array=self)

    def __getitem__(self, name):
        if isinstance(name, int):
            return super(Selection, self).__getitem__(name)
        return self.get_fields(name).column(name)

    def __setitem__(self, name, value):
        assert isinstance(name, (unicode, str))
        self.set_fields(**{name: value})

    def get_fields(self, *fields):
        """Get field information for the selection.

        Args:
            *fields: Server defined field sign.

        Returns:
            ResultSet: Optimized tuple object contains fields data.
        """

        server_fields = [self.module.field(i) for i in fields]
        resp = self.call("c_orm", "get_in_id",
                         sign_array=server_fields,
                         order_sign_array=server_fields)
        return ResultSet(server_fields, resp.data, self.module)

    def set_fields(self, **data):
        """Set field data for the selection.

        Args:
            **data: Field name as key, Value as value.
        """

        data = {
            self.module.field(k): v for k, v in data.items()
        }
        resp = self.call("c_orm", "set_in_id",
                         sign_data_array=data)
        if resp.code == 0:
            raise ValueError(resp)

    def delete(self):
        """Delete the selected item on database.  """

        self.call("c_orm", "del_in_id")

    def get_path(self, *sign_list):
        """Get signed folder path.

        Args:
            sign_list (unicode): Sign name defined in CGTeemWork:
                `设置` -> `目录文件` -> `标识`

        Returns:
            dict: Server returned path dictionary.
                id as key, path as value.
        """

        if not self:
            raise ValueError('Empty selection.')

        resp = self.call("c_folder", "get_replace_path_in_sign",
                         sign_array=sign_list,
                         task_id_array=self,
                         os=_OS)
        assert isinstance(resp.data, dict), type(resp.data)
        return dict(resp.data)

    def get_filebox(self, sign=None, id_=None):
        """Get one filebox with sign or id_.

        Args:
            sign (unicode): Server defined filebox sign.
            id_ (unicode): Server filebox id,
                if given, will ignore `sign` value.

        Raises:
            ValueError: When selection is empty.
            ValueError: When insufficient argument.
            ValueError: When got empty result.

        Returns:
            FileBoxInfo: Filebox information.
        """

        if not self:
            raise ValueError('Empty selection.')

        if id_:
            resp = self.call("c_file", "filebox_get_one_with_id",
                             task_id=self[0],
                             filebox_id=id_,
                             os=_OS)
        elif sign:
            resp = self.call("c_file", "filebox_get_one_with_sign",
                             task_id=self[0],
                             sign=sign,
                             os=_OS)
        else:
            raise ValueError(
                'Need at least one of (sign, id_) to get filebox.')

        if not resp.data:
            raise ValueError('No matched filebox.')
        assert isinstance(resp.data, dict), resp
        return FileBoxDetail(**resp.data)

    def send_message(self, title, content, *to, **kwargs):
        """Send message to users.

        Args:
            title (unicode): Message title.
            content (unicode): Message content, support html.
            *to: Users that will recives message, use account_id.
            **kwargs:
                from_: Unknown effect. used in `cgtw` module.
        """
        # pylint: disable=invalid-name

        from_ = kwargs.get('from_')

        return self.call(
            'c_msg', 'send_task',
            task_id=self[0],
            account_id_array=to,
            title=title,
            content=content,
            from_account_id=from_
        )

    def set_image(self, path, field='image', http_server=None):
        """Set image for the field.

        Args:
            field (unicode): Defaults to 'image', Server defined field name,
            path (unicode): File path.
            http_server (unicode, optional): Defaults to None. Http server address,
                if `http_server` is None, will use value from client.
        """

        pathname = "/upload/image/{}/".format(
            self.module.database.name
        )

        data = {'path': path}
        # Exactly same with CGTeamwork UI resolution.
        for key, width, height in (('min', 160, 120), ('max', 308, 186)):
            thumb = genreate_thumb(path, width, height)
            try:
                thumb_pathname = '{}{}.jpg'.format(pathname, file_md5(thumb))
                server.upload(thumb, thumb_pathname, ip=http_server)
            finally:
                os.remove(thumb)
            data[key] = thumb_pathname

        self.set_fields(**{field: data})

    def get_image(self, field='image'):
        """Get imageinfo used on the field.

        Args:
            field (unicode): Defaults to 'image', Server defined field name,

        Returns:
            set[ImageInfo]: Image information.
        """

        ret = set()
        for i in self[field]:
            try:
                data = json.loads(i)
                assert isinstance(data, dict)
                # TODO: Remove `image_path` support at next major version.
                info = ImageInfo(max=data['max'],
                                 min=data['min'],
                                 path=data.get('path', data.get('image_path')))
                ret.add(info)
            except (TypeError, KeyError):
                continue
        return tuple(sorted(ret))

    def get_notes(self):
        """Get notes on first item in the selection.

        Raises:
            ValueError: When no item selected.

        Returns:
            tuple[NoteInfo]: namedtuple about note information.
        """

        if not self:
            raise ValueError('Empty selection.')

        resp = self.call("c_note", "get_with_task_id",
                         task_id=self[0],
                         field_array=FIELDS_NOTE)
        return tuple(NoteInfo(*i) for i in resp.data)

    def get_history(self, filters=None):
        """Get selection related history.
            filters (Filter or FilterList, optional): Defaults to None.
                Addtional history filters.

        Returns:
            tuple[HistoryInfo]: History records.
        """

        _filters = Filter('#task_id', self)
        if filters:
            _filters &= filters
        return self.module.get_history(_filters)

    def count_history(self, filters=None):
        """Count selection related history records.

        Args:
            filters (Filter or FilterList):
                Addtional history filters.

        Returns:
            int: Records count.
        """

        _filters = Filter('#task_id', self)
        if filters:
            _filters &= filters
        return self.module.count_history(_filters)

    def submit(self, filelist, note="", pathlist=None):
        if not self:
            raise ValueError('Empty selection.')

        resp = self.call(
            "c_work_flow", "submit",
            task_id=self[0],
            account_id=server.account_id(),
            submit_file_path_array={
                'path': pathlist or [], 'file_path': filelist},
            text=note)
        return resp

    def get_filebox_submit(self):
        resp = self.call(
            'c_file', 'filebox_get_submit_data',
            task_id=self[0],
            os=_OS)
        return resp

    def link(self, *id_list):
        """Link the selection to other items. """

        self.call(
            "c_link", "set_link_id",
            id_array=self, link_id_array=id_list)

    def unlink(self, *id_list):
        """Unlink the selection with other items.  """

        for id_ in self:
            self.call(
                "c_link", "remove_link_id",
                id=id_, link_id_array=id_list)

    def get_linked(self):
        """Get linked items for the selections.

        Returns:
            set: All linked item id.
        """

        ret = set()
        for id_ in self:
            resp = self.call("c_link", "get_link_id", id=id_)
            ret.add(resp)
        return ret

    def to_entry(self):
        """Convert selection to one entry.

        Raises:
            ValueError: Not exactly one selected item.

        Returns:
            Entry: Entry.
        """

        if len(self) != 1:
            raise ValueError('Need exactly one selected item.')

        return Entry(self.module, self[0])

    def to_entries(self):
        """Convert selection to entries.

        Returns:
            tuple[Entry]: Entries.
        """

        return tuple(Entry(self.module, i) for i in self)


class Entry(Selection):
    """A selection that only has one item.  """

    def __init__(self, module, id_):
        assert isinstance(id_, unicode), type(id_)
        super(Entry, self).__init__(module, id_)

    def __getitem__(self, name):
        if isinstance(name, int):
            return super(Entry, self).__getitem__(name)
        return self.get_fields(name)[0]

    def get_fields(self, *fields):
        """Get multiple fields.

        Returns:
            tuple: Result fields with exactly same order with `fields`.
        """

        ret = super(Entry, self).get_fields(*fields)
        assert len(ret) == 1, ret
        ret = ret[0]
        assert isinstance(ret, list), ret
        return tuple(ret)

    def get_image(self, field='image'):
        """Get imageinfo used on the field.

        Args:
            field (unicode): Defaults to 'image', Server defined field name,

        Raises:
            ValueError: when no image in the field.

        Returns:
            ImageInfo: Image information.
        """

        try:
            return self._to_selection().get_image(field)[0]
        except IndexError:
            raise ValueError('No image in this field.', field)

    def _to_selection(self):
        return Selection(self.module, *self)


class ResultSet(list):
    """Database query result.  """

    def __init__(self, roles, data, module):
        assert isinstance(module, Module)
        assert all(isinstance(i, list) and len(i) == len(roles)
                   for i in data), data
        super(ResultSet, self).__init__(data)
        self.module = module
        self.roles = roles

    def column(self, field):
        """Get a column from field name.

        Args:
            field (unicode): Field name.

        Returns:
            tuple: Column data.
        """

        field = self.module.field(field)
        index = self.roles.index(field)
        return tuple(sorted(set(i[index] for i in self)))


def account_name():
    """Current user name.

    Returns:
        unicode
    """

    return ACCOUNT[server.account_id()]['name'][0]
