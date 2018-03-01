# -*- coding=UTF-8 -*-
"""Database in cgtw server.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
from functools import partial

from . import server
from .filter import Filter, FilterList
from collections import namedtuple

_OS = {'windows': 'win', 'linux': 'linux', 'darwin': 'mac'}.get(
    __import__('platform').system().lower())  # Server defined os string.
LOGGER = logging.getLogger('wlf.cgtwq.database')


class Database(object):
    """Database on server.    """

    def __init__(self, name):
        self.name = name

    def __getitem__(self, name):
        return Module(name=name, database=self)


class FieldsData(list):
    """List for field data.  """

    def __init__(self, data, module):
        if not all(isinstance(i, dict)for i in data):
            if all(isinstance(i, list) and len(i) == 1 for i in data):
                # Unpack data.
                data = [i[0] for i in data]
            else:
                raise TypeError('Got unknown data format.', data)
        super(FieldsData, self).__init__(data)
        assert isinstance(module, Module)
        self.module = module

    def field(self, field):
        """Get data for single field.

        Args:
            field (unicode): Field name.

        Returns:
            tuple: Add data matches this field.
        """

        field = self.module.field(field)
        return tuple(sorted(set(
            i[field] if isinstance(i, dict) else i
            for i in self)))


class Selection(list):
    """Selection on a database module.   """

    def __init__(self, id_list, module):
        """
        Args:
            id_list (list): Selected id.
            module (Module): Related module.
        """

        assert isinstance(id_list, list), type(id_list)
        assert all(isinstance(i, (int, unicode)) for i in id_list), id_list
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

    def get_fields(self, fields):
        """Get field information for the selection.

        Args:
            fields (list): List of server defined field sign.

        Returns:
            FieldData: Optimized list object contains field data.
        """

        if not isinstance(fields, list):
            fields = [fields]

        server_fields = [self.module.field(i) for i in fields]
        resp = self.call("c_orm", "get_in_id",
                         sign_array=server_fields,
                         order_sign_array=server_fields)
        return FieldsData(resp.data, self.module)

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

        self.call("c_orm", "del_in_id", id_array=self)

    def get_path(self, sign_list):
        if not isinstance(sign_list, list):
            sign_list = [sign_list]
        resp = self.call("c_folder", "get_replace_path_in_sign",
                         sign_array=sign_list)

    def get_filebox(self, sign):
        if not self:
            raise ValueError('Empty selection.')
        resp = self.call("c_file",  "filebox_get_one_with_sign",
                         task_id=self[0],
                         sign=sign,
                         os=_OS)
        return resp.data

    @classmethod
    def from_response(cls, response, module):
        """Create selection from selection.

        Args:
            response (server.Response): Server response.
            module (Module): Related module.

        Raises:
            TypeError: Can not parse response data.

        Returns:
            Selection: Selection from the response.
        """

        assert isinstance(response, server.Response), response
        assert response.type == 'json', response
        payload = response.data

        def _get_id(data):
            if isinstance(data, (unicode, int)):
                return data
            if isinstance(data, dict):
                return data['id']
            elif isinstance(data, list) and len(data) == 1:
                return data[0]
            raise TypeError(type(data))

        id_list = [_get_id(i) for i in payload]
        ret = cls(id_list, module)
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
        self.call = partial(server.call,
                            db=self.database.name,
                            module=self.name)

    def __getitem__(self, name):
        if isinstance(name, (Filter, FilterList)):
            return self.filter(name)
        return self.select(name)

    def select(self, id_list):
        """Create selection on this module.

        Args:
            id_list (list, unicode): Id list to select.

        Returns:
            Selection: Created selection.
        """

        if not isinstance(id_list, list):
            id_list = [id_list]
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

        return Selection.from_response(resp, self)

    def field(self, name):
        """Formatted field name for this module.

        Args:
            name (unicode): Short field name.

        Returns:
            unicode: Full field name, for server.
        """

        assert isinstance(name, (str, unicode))
        if '.' in name:
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
