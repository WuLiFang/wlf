# -*- coding=UTF-8 -*-
"""Database in cgtw server.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
import uuid
from collections import namedtuple
from functools import partial
import json

from . import server
from .filter import Filter, FilterList

_OS = {'windows': 'win', 'linux': 'linux', 'darwin': 'mac'}.get(
    __import__('platform').system().lower())  # Server defined os string.
LOGGER = logging.getLogger('wlf.cgtwq.database')

FileBox = namedtuple('FileBox', ('id', 'pipeline_id', 'title'))
FileBoxInfo = namedtuple(
    'FileBoxInfo',
    ('path',
     'classify', 'title',
     'sign', 'color', 'rule', 'rule_view',
     'is_submit', 'is_move_old_to_history',
     'is_move_same_to_history', 'is_in_history_add_version',
     'is_in_history_add_datetime', 'is_cover_disable',
     'is_msg_to_first_qc')
)
Pipeline = namedtuple('Pipeline', ('id', 'name', 'module'))


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
                             field_array=['#id', '#pipeline_id', 'title'])
            ret = [resp.data]
        elif filters:
            resp = self.call("c_file", "get_with_filter",
                             filter_array=FilterList(filters),
                             field_array=['#id', '#pipeline_id', 'title'])
            ret = resp.data
        else:
            raise ValueError(
                'Need at least one of (id_, filters) to get filebox.')

        if not resp.data:
            raise ValueError('No matched filebox.')
        assert all(isinstance(i, list) for i in ret), resp
        return tuple(FileBox(*i) for i in ret)

    def get_piplines(self, filters):
        """Get piplines from database.

        Args:
            filters (FilterList): Filter to get pipeline.

        Returns:
            tuple[Pipeline]: namedtuple for ('id', 'name', 'module')
        """

        resp = self.call(
            "c_pipeline", "get_with_filter",
            field_array=('#id', 'name', 'module'),
            filter_array=FilterList(filters))
        return tuple(Pipeline(*i) for i in resp.data)

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


class FieldsData(list):
    """List for field data.  """

    def __init__(self, fields, data, module):
        assert isinstance(module, Module)
        self.module = module
        self.fields = fields
        if all(isinstance(i, dict)for i in data):
            data = [[i[j] for j in fields] for i in data]
        elif all(isinstance(i, list) and len(i) == len(fields) for i in data):
            pass
        else:
            raise TypeError('Got unknown data format.', data)
        super(FieldsData, self).__init__(data)

    def field(self, field):
        """Get data for single field.

        Args:
            field (unicode): Field name.

        Returns:
            tuple: Add data matches this field.
        """

        field = self.module.field(field)
        index = self.fields.index(field)
        return tuple(sorted(set(i[index] for i in self)))


ImageInfo = namedtuple('ImageInfo', ['max', 'min'])


class Selection(list):
    """Selection on a database module.   """

    def __init__(self, id_list, module):
        """
        Args:
            id_list (list): Selected id.
            module (Module): Related module.
        """

        assert all(isinstance(i, unicode) for i in id_list), id_list
        assert isinstance(module, Module)
        super(Selection, self).__init__(id_list)
        self.module = module
        self.call = partial(self.module.call, id_array=self)

    def __getitem__(self, name):
        if isinstance(name, int):
            return super(Selection, self).__getitem__(name)
        return self.get_fields(name).field(name)

    def __setitem__(self, name, value):
        assert isinstance(name, (unicode, str))
        self.set_fields(**{name: value})

    def get_fields(self, *fields):
        """Get field information for the selection.

        Args:
            fields (list): List of server defined field sign.

        Returns:
            FieldData: Optimized list object contains field data.
        """

        server_fields = [self.module.field(i) for i in fields]
        resp = self.call("c_orm", "get_in_id",
                         sign_array=server_fields,
                         order_sign_array=server_fields)
        return FieldsData(server_fields, resp.data, self.module)

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
        return FileBoxInfo(**resp.data)

    def set_image(self, field, path, http_server=None):
        # TODO: Generate thumb.
        pathname = "/upload/image/{}/{}".format(
            self.module.database.name,
            uuid.uuid4()
        )
        server.upload(path, pathname, ip=http_server)
        self.set_fields(**{field: {'max': pathname, 'min': pathname}})

    def get_image(self, field):
        ret = set()
        for i in self[field]:
            try:
                if ret:
                    data = json.loads(i)
                    ret.add(ImageInfo(max=data['max'], min=data['min']))
            except (TypeError, KeyError):
                continue
        return tuple(sorted(ret))

    def get_note(self, fields):
        if not self:
            raise ValueError('Empty selection.')

        fields = list(fields) + ['#id']
        resp = self.call("c_note", "get_with_task_id",
                         task_id=self[0],
                         field_array=fields)
        return resp

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

        return Selection(id_list, self)

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
        return Selection(id_list, self)

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

    def send_message(self, to, title, content, task_id, from_=None):
        """Send message to users.  """
        # pylint: disable=invalid-name

        from_ = server.account() if from_ is None else from_
        return self.call(
            'c_msg', 'send_task',
            task_id=task_id,
            account_id_array=to,
            title=title,
            content=content,
            from_account_id=from_
        )

    def pipelines(self):
        """All pipeline in this module.

        Returns:
            tuple[Pipeline]: namedtuple for ('id', 'name', 'module').
        """

        return self.database.get_pipline(Filter('module', self.name))

    def get_history(self, filters):
        fields = ['#task_id', '#account_id', 'file',
                  'step', 'text', 'module', 'time']
        resp = self.call(
            "c_pipeline", "get_with_filter",
            field_array=fields,
            filter_array=filters)
        return resp

    def count_history(self, filters):
        resp = self.call(
            "c_pipeline", "count_with_filter",
            filter_array=filters)
        return resp


class PublicModule(Module):
    """Module in special `public` database.    """

    def __init__(self):
        database = Database('public')
        super(PublicModule, self).__init__(self.name, database)


class Project(PublicModule):
    """Module to keep project information.   """

    name = 'project'

    def names(self):
        """All actived project names.

        Returns:
            tuple
        """

        return self.filter(Filter('status', 'Active'))['full_name']


class Account(PublicModule):
    """Module to keep account information.   """

    name = 'account'

    def names(self):
        """All user names.

        Returns:
            tuple
        """

        return self[Filter('status', 'Y')]['name']


ACCOUNT = Account()
PROJECT = Project()


def account_name():
    """Current user name.

    Returns:
        unicode
    """

    return ACCOUNT[server.account_id()]['name'][0]
