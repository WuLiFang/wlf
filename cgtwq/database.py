# -*- coding=UTF-8 -*-
"""Database in cgtw server.  """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
from functools import partial

from . import server
from .filter import Filter, FilterList

_OS = {'windows': 'wind', 'linux': 'linux', 'darwin': 'mac'}.get(
    __import__('platform').system().lower())  # Server defined os string.
LOGGER = logging.getLogger('wlf.cgtwq.database')


def formatted_fields(fields, name):
    if not name:
        return tuple()
    return tuple(i if '.' in i else '{}.{}'.format(name, i) for i in fields)


class Database(object):
    """Database on server.    """

    def __init__(self, name):
        self.name = name

    def __getitem__(self, name):
        return Module(name=name, database=self)


class Selection(list):
    """Selection on a database module.   """

    def __init__(self, id_list, module):
        """
        Args:
            id_list (list): Selected id.
            module (Module): Related module.
        """

        assert isinstance(id_list, list), type(id_list)
        assert isinstance(module, Module)
        super(Selection, self).__init__(id_list)
        self.module = module
        self.call = partial(self.module.call, id_array=self)

    def __getitem__(self, name):
        if isinstance(name, int):
            return super(Selection, self).__getitem__(name)
        return self.get_field(name)

    def __setitem__(self, name, value):
        assert isinstance(name, (unicode, str))
        self.set_field(name, value)

    def __delitem__(self, name):
        assert isinstance(name, (unicode, str))
        self.delete_field(name)

    def get_field(self, field):
        """Get field information for the selection.

        Args:
            field (unicode): Server defined field.

        Returns:
            tuple: Field data.
        """

        field = self.module.field(field)
        resp = self.call("c_orm", "get_in_id",
                         sign_array=[field],
                         order_sign_array=[field])
        return tuple(set(i[field] if isinstance(i, dict) else i
                         for i in resp.data))

    def set_field(self, field, value):
        """Set field data for the selection.

        Args:
            field (unicode): Server defined field name.
            value (any): Value to set.
        """

        field = self.module.field(field)
        resp = self.call("c_orm", "set_in_id",
                         sign_data_array={field: value})
        if resp.code == 0:
            raise ValueError(resp)

    def delete_field(self, field):
        """Delete field data for the selection.

        Args:
            field (unicode): Server defined field name.
        """

        field = self.module.field(field)
        resp = self.call("c_orm", "del_in_id")

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

        assert isinstance(response, server.Response)
        assert response.type == 'json', response
        payload = response.data
        try:
            id_list = [i['id'] if isinstance(i, dict) else i for i in payload]
        except TypeError:
            raise TypeError(payload)
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

    return ACCOUNT[Filter('id', server.account_id())]['name'][0]
