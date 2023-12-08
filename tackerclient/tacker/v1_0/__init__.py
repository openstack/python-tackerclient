# Copyright 2012 OpenStack Foundation.
# All Rights Reserved
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

import abc
import argparse
import logging
import re

from cliff.formatters import table
from cliff import lister
from cliff import show
from oslo_serialization import jsonutils

from tackerclient.common._i18n import _
from tackerclient.common import command
from tackerclient.common import exceptions
from tackerclient.common import utils

HEX_ELEM = '[0-9A-Fa-f]'
UUID_PATTERN = '-'.join([HEX_ELEM + '{8}', HEX_ELEM + '{4}',
                         HEX_ELEM + '{4}', HEX_ELEM + '{4}',
                         HEX_ELEM + '{12}'])


def _get_resource_plural(resource, client):
    plurals = getattr(client, 'EXTED_PLURALS', [])
    for k in plurals:
        if plurals[k] == resource:
            return k
    return resource + 's'


def find_resourceid_by_id(client, resource, resource_id):
    resource_plural = _get_resource_plural(resource, client)
    obj_lister = getattr(client, "list_%s" % resource_plural)
    if resource == 'event':
        match = resource_id.isdigit() and resource_id != 0
    else:
        match = re.match(UUID_PATTERN, resource_id)
    collection = resource_plural
    if match:
        data = obj_lister(id=resource_id, fields='id')
        if data and data[collection]:
            return data[collection][0]['id']
    not_found_message = (_("Unable to find %(resource)s with id "
                           "'%(id)s'") %
                         {'resource': resource, 'id': resource_id})
    # 404 is used to simulate server side behavior
    raise exceptions.TackerClientException(
        message=not_found_message, status_code=404)


def _find_resourceid_by_name(client, resource, name):
    resource_plural = _get_resource_plural(resource, client)
    obj_lister = getattr(client, "list_%s" % resource_plural)
    data = obj_lister(name=name, fields='id')
    collection = resource_plural
    info = data[collection]
    if len(info) > 1:
        raise exceptions.TackerClientNoUniqueMatch(resource=resource,
                                                   name=name)
    elif len(info) == 0:
        not_found_message = (_("Unable to find %(resource)s with name "
                               "'%(name)s'") %
                             {'resource': resource, 'name': name})
        # 404 is used to simulate server side behavior
        raise exceptions.TackerClientException(
            message=not_found_message, status_code=404)
    else:
        return info[0]['id']


def find_resourceid_by_name_or_id(client, resource, name_or_id):
    try:
        return find_resourceid_by_id(client, resource, name_or_id)
    except exceptions.TackerClientException:
        return _find_resourceid_by_name(client, resource, name_or_id)


def add_show_list_common_argument(parser):
    parser.add_argument(
        '-D', '--show-details',
        help=_('Show detailed info'),
        action='store_true',
        default=False,)
    parser.add_argument(
        '--show_details',
        action='store_true',
        help=argparse.SUPPRESS)
    parser.add_argument(
        '--fields',
        help=argparse.SUPPRESS,
        action='append',
        default=[])
    parser.add_argument(
        '-F', '--field',
        dest='fields', metavar='FIELD',
        help=_('Specify the field(s) to be returned by server. You can '
               'repeat this option.'),
        action='append',
        default=[])


def add_pagination_argument(parser):
    parser.add_argument(
        '-P', '--page-size',
        dest='page_size', metavar='SIZE', type=int,
        help=_("Specify retrieve unit of each request, then split one request "
               "to several requests"),
        default=None)


def add_sorting_argument(parser):
    parser.add_argument(
        '--sort-key',
        dest='sort_key', metavar='FIELD',
        action='append',
        help=_("Sorts the list by the specified fields in the specified "
               "directions. You can repeat this option, but you must "
               "specify an equal number of sort_dir and sort_key values. "
               "Extra sort_dir options are ignored. Missing sort_dir options "
               "use the default asc value."),
        default=[])
    parser.add_argument(
        '--sort-dir',
        dest='sort_dir', metavar='{asc,desc}',
        help=_("Sorts the list in the specified direction. You can repeat "
               "this option."),
        action='append',
        default=[],
        choices=['asc', 'desc'])


def is_number(s):
    try:
        float(s)  # for int, long and float
    except ValueError:
        try:
            complex(s)  # for complex
        except ValueError:
            return False

    return True


def _process_previous_argument(current_arg, _value_number, current_type_str,
                               _list_flag, _values_specs, _clear_flag,
                               values_specs):
    if current_arg is not None:
        if _value_number == 0 and (current_type_str or _list_flag):
            # This kind of argument should have value
            raise exceptions.CommandError(
                message=_("Invalid values_specs %s") % ' '.join(values_specs))
        if _value_number > 1 or _list_flag or current_type_str == 'list':
            current_arg.update({'nargs': '+'})
        elif _value_number == 0:
            if _clear_flag:
                # if we have action=clear, we use argument's default
                # value None for argument
                _values_specs.pop()
            else:
                # We assume non value argument as bool one
                current_arg.update({'action': 'store_true'})


def parse_args_to_dict(values_specs):
    '''It is used to analyze the extra command options to command.

    Besides known options and arguments, our commands also support user to
    put more options to the end of command line. For example,
    list_nets -- --tag x y --key1 value1, where '-- --tag x y --key1 value1'
    is extra options to our list_nets. This feature can support V1.0 API's
    fields selection and filters. For example, to list networks which has name
    'test4', we can have list_nets -- --name=test4.

    value spec is: --key type=int|bool|... value. Type is one of Python
    built-in types. By default, type is string. The key without value is
    a bool option. Key with two values will be a list option.

    '''

    # values_specs for example: '-- --tag x y --key1 type=int value1'
    # -- is a pseudo argument
    values_specs_copy = values_specs[:]
    if values_specs_copy and values_specs_copy[0] == '--':
        del values_specs_copy[0]
    # converted ArgumentParser arguments for each of the options
    _options = {}
    # the argument part for current option in _options
    current_arg = None
    # the string after remove meta info in values_specs
    # for example, '--tag x y --key1 value1'
    _values_specs = []
    # record the count of values for an option
    # for example: for '--tag x y', it is 2, while for '--key1 value1', it is 1
    _value_number = 0
    # list=true
    _list_flag = False
    # action=clear
    _clear_flag = False
    # the current item in values_specs
    current_item = None
    # the str after 'type='
    current_type_str = None
    for _item in values_specs_copy:
        if _item.startswith('--'):
            # Deal with previous argument if any
            _process_previous_argument(
                current_arg, _value_number, current_type_str,
                _list_flag, _values_specs, _clear_flag, values_specs)

            # Init variables for current argument
            current_item = _item
            _list_flag = False
            _clear_flag = False
            current_type_str = None
            if "=" in _item:
                _value_number = 1
                _item = _item.split('=')[0]
            else:
                _value_number = 0
            if _item in _options:
                raise exceptions.CommandError(
                    message=_("Duplicated "
                              "options %s") % ' '.join(values_specs))
            else:
                _options.update({_item: {}})
            current_arg = _options[_item]
            _item = current_item
        elif _item.startswith('type='):
            if current_arg is None:
                raise exceptions.CommandError(
                    message=_("Invalid "
                              "values_specs %s") % ' '.join(values_specs))
            if 'type' not in current_arg:
                current_type_str = _item.split('=', 2)[1]
                current_arg.update({'type': eval(current_type_str)})
                if current_type_str == 'bool':
                    current_arg.update({'type': utils.str2bool})
                elif current_type_str == 'dict':
                    current_arg.update({'type': utils.str2dict})
                continue
        elif _item == 'list=true':
            _list_flag = True
            continue
        elif _item == 'action=clear':
            _clear_flag = True
            continue

        if not _item.startswith('--'):
            # All others are value items
            # Make sure '--' occurs first and allow minus value
            if (not current_item or '=' in current_item or
               _item.startswith('-') and not is_number(_item)):
                raise exceptions.CommandError(
                    message=_("Invalid "
                              "values_specs %s") % ' '.join(values_specs))
            _value_number += 1

        _values_specs.append(_item)

    # Deal with last one argument
    _process_previous_argument(
        current_arg, _value_number, current_type_str,
        _list_flag, _values_specs, _clear_flag, values_specs)

    # populate the parser with arguments
    _parser = argparse.ArgumentParser(add_help=False)
    for opt, optspec in _options.items():
        _parser.add_argument(opt, **optspec)
    _args = _parser.parse_args(_values_specs)

    result_dict = {}
    for opt in _options.keys():
        _opt = opt.split('--', 2)[1]
        _opt = _opt.replace('-', '_')
        _value = getattr(_args, _opt)
        result_dict.update({_opt: _value})
    return result_dict


def _merge_args(qCmd, parsed_args, _extra_values, value_specs):
    """Merge arguments from _extra_values into parsed_args.

    If an argument value are provided in both and it is a list,
    the values in _extra_values will be merged into parsed_args.

    @param parsed_args: the parsed args from known options
    @param _extra_values: the other parsed arguments in unknown parts
    @param values_specs: the unparsed unknown parts
    """
    temp_values = _extra_values.copy()
    for key, value in temp_values.items():
        if hasattr(parsed_args, key):
            arg_value = getattr(parsed_args, key)
            if arg_value is not None and value is not None:
                if isinstance(arg_value, list):
                    if value and isinstance(value, list):
                        if (not arg_value or
                                isinstance(arg_value[0], type(value[0]))):
                            arg_value.extend(value)
                            _extra_values.pop(key)


def update_dict(obj, dict, attributes):
    """Update dict with fields from obj.attributes

    :param obj: the object updated into dict
    :param dict: the result dictionary
    :param attributes: a list of attributes belonging to obj
    """
    for attribute in attributes:
        if hasattr(obj, attribute) and getattr(obj, attribute) is not None:
            dict[attribute] = getattr(obj, attribute)


class TableFormater(table.TableFormatter):
    """This class is used to keep consistency with prettytable 0.6.

    https://bugs.launchpad.net/python-tackerclient/+bug/1165962
    """

    def emit_list(self, column_names, data, stdout, parsed_args):
        if column_names:
            super(TableFormater, self).emit_list(column_names, data, stdout,
                                                 parsed_args)
        else:
            stdout.write('\n')


# command.OpenStackCommand is abstract class so that metaclass of
# subclass must be subclass of metaclass of all its base.
# otherwise metaclass conflict exception is raised.
class TackerCommandMeta(abc.ABCMeta):
    def __new__(cls, name, bases, cls_dict):
        if 'log' not in cls_dict:
            cls_dict['log'] = logging.getLogger(
                cls_dict['__module__'] + '.' + name)
        return super(TackerCommandMeta, cls).__new__(cls,
                                                     name, bases, cls_dict)


class TackerCommand(command.OpenStackCommand, metaclass=TackerCommandMeta):

    api = 'nfv-orchestration'
    values_specs = []
    json_indent = None

    def __init__(self, app, app_args):
        super(TackerCommand, self).__init__(app, app_args)
        # NOTE(markmcclain): This is no longer supported in cliff version 1.5.2
        # see https://bugs.launchpad.net/python-tackerclient/+bug/1265926

        # if hasattr(self, 'formatters'):
        # self.formatters['table'] = TableFormater()

    def get_client(self):
        return self.app.client_manager.tacker

    def get_parser(self, prog_name):
        parser = super(TackerCommand, self).get_parser(prog_name)
        parser.add_argument(
            '--request-format',
            help=_('The json request format'),
            default='json',
            choices=['json', ], )
        parser.add_argument(
            '--request_format',
            choices=['json', ],
            help=argparse.SUPPRESS)

        return parser

    def format_output_data(self, data):
        # Modify data to make it more readable
        if self.resource in data:
            for k, v in data[self.resource].items():
                if isinstance(v, list):
                    value = '\n'.join(jsonutils.dumps(
                        i, indent=self.json_indent) if isinstance(i, dict)
                        else str(i) for i in v)
                    data[self.resource][k] = value
                elif isinstance(v, dict):
                    value = jsonutils.dumps(v, indent=self.json_indent)
                    data[self.resource][k] = value
                elif v is None:
                    data[self.resource][k] = ''

    def add_known_arguments(self, parser):
        pass

    def args2body(self, parsed_args):
        return {}


class CreateCommand(TackerCommand, show.ShowOne):
    """Create a resource for a given tenant

    """

    api = 'nfv-orchestration'
    resource = None
    log = None
    remove_output_fields = []

    def get_parser(self, prog_name):
        parser = super(CreateCommand, self).get_parser(prog_name)
        parser.add_argument(
            '--tenant-id', metavar='TENANT_ID',
            help=_('The owner tenant ID'), )
        parser.add_argument(
            '--tenant_id',
            help=argparse.SUPPRESS)
        self.add_known_arguments(parser)
        return parser

    def get_data(self, parsed_args):
        self.log.debug('get_data(%s)', parsed_args)
        tacker_client = self.get_client()
        tacker_client.format = parsed_args.request_format
        _extra_values = parse_args_to_dict(self.values_specs)
        _merge_args(self, parsed_args, _extra_values,
                    self.values_specs)
        body = self.args2body(parsed_args)
        body[self.resource].update(_extra_values)
        obj_creator = getattr(tacker_client,
                              "create_%s" % self.resource)
        data = obj_creator(body)
        self.format_output_data(data)
        # {u'network': {u'id': u'e9424a76-6db4-4c93-97b6-ec311cd51f19'}}
        info = self.resource in data and data[self.resource] or None
        if info:
            print(_('Created a new %s:') % self.resource,
                  file=self.app.stdout)
            for f in self.remove_output_fields:
                if f in info:
                    info.pop(f)
        else:
            info = {'': ''}
        return zip(*sorted(info.items()))


class UpdateCommand(TackerCommand):
    """Update resource's information."""

    api = 'nfv-orchestration'
    resource = None
    log = None
    allow_names = True

    def get_parser(self, prog_name):
        parser = super(UpdateCommand, self).get_parser(prog_name)
        parser.add_argument(
            'id', metavar=self.resource.upper(),
            help=_('ID or name of %s to update') % self.resource)
        self.add_known_arguments(parser)
        return parser

    def run(self, parsed_args):
        self.log.debug('run(%s)', parsed_args)
        tacker_client = self.get_client()
        tacker_client.format = parsed_args.request_format
        _extra_values = parse_args_to_dict(self.values_specs)
        _merge_args(self, parsed_args, _extra_values,
                    self.values_specs)
        body = self.args2body(parsed_args)
        if self.resource in body:
            body[self.resource].update(_extra_values)
        else:
            body[self.resource] = _extra_values
        if not body[self.resource]:
            raise exceptions.CommandError(
                message=_("Must specify new"
                          " values to update %s") % self.resource)
        if self.allow_names:
            _id = find_resourceid_by_name_or_id(
                tacker_client, self.resource, parsed_args.id)
        else:
            _id = find_resourceid_by_id(
                tacker_client, self.resource, parsed_args.id)
        obj_updator = getattr(tacker_client,
                              "update_%s" % self.resource)
        obj_updator(_id, body)
        print((_('Updated %(resource)s: %(id)s') %
               {'id': parsed_args.id, 'resource': self.resource}),
              file=self.app.stdout)
        return


class DeleteCommand(TackerCommand):
    """Delete given resource(s)

    """

    api = 'nfv-orchestration'
    resource = None
    log = None
    allow_names = True
    deleted_msg = {}

    def get_parser(self, prog_name):
        parser = super(DeleteCommand, self).get_parser(prog_name)
        if self.allow_names:
            help_str = _('IDs or names of %s to delete')
        else:
            help_str = _('IDs of %s to delete')
        parser.add_argument(
            'ids', nargs='+',
            metavar=self.resource.upper(),
            help=help_str % self.resource)
        self.add_known_arguments(parser)
        return parser

    def run(self, parsed_args):
        failure = False
        deleted_ids = []
        failed_items = {}
        tacker_client = self.get_client()
        tacker_client.format = parsed_args.request_format
        obj_deleter = getattr(tacker_client,
                              "delete_%s" % self.resource)
        body = self.args2body(parsed_args)

        for resource_id in parsed_args.ids:
            try:
                if self.allow_names:
                    _id = find_resourceid_by_name_or_id(
                        tacker_client, self.resource, resource_id)
                else:
                    _id = resource_id
                if body:
                    obj_deleter(_id, body)
                else:
                    obj_deleter(_id)
                deleted_ids.append(resource_id)
            except Exception as e:
                failure = True
                failed_items[resource_id] = e
        if failure:
            msg = ''
            if deleted_ids:
                status_msg = self.deleted_msg.get(self.resource, 'deleted')
                msg = (_('Successfully %(status_msg)s %(resource)s(s):'
                         ' %(deleted_list)s') % {'status_msg': status_msg,
                                                 'deleted_list':
                                                 ', '.join(deleted_ids),
                                                 'resource': self.resource})
            err_msg = _("\n\nUnable to delete the below"
                        " %s(s):") % self.resource
            for failed_id, error in failed_items.items():
                err_msg += (_('\n Cannot delete %(failed_id)s: %(error)s')
                            % {'failed_id': failed_id,
                               'error': error})
            msg += err_msg
            raise exceptions.CommandError(message=msg)
        else:
            print((_('All specified %(resource)s(s) %(msg)s successfully')
                   % {'msg': self.deleted_msg.get(self.resource, 'deleted'),
                      'resource': self.resource}))
        return


class ListCommand(TackerCommand, lister.Lister):
    """List resources that belong to a given tenant

    """

    api = 'nfv-orchestration'
    resource = None
    log = None
    _formatters = {}
    list_columns = []
    unknown_parts_flag = True
    pagination_support = False
    sorting_support = False

    def get_parser(self, prog_name):
        parser = super(ListCommand, self).get_parser(prog_name)
        add_show_list_common_argument(parser)
        if self.pagination_support:
            add_pagination_argument(parser)
        if self.sorting_support:
            add_sorting_argument(parser)
        return parser

    def args2search_opts(self, parsed_args):
        search_opts = {}
        fields = parsed_args.fields
        if parsed_args.fields:
            search_opts.update({'fields': fields})
        if parsed_args.show_details:
            search_opts.update({'verbose': 'True'})
        return search_opts

    def call_server(self, tacker_client, search_opts, parsed_args):
        resource_plural = _get_resource_plural(self.resource, tacker_client)
        obj_lister = getattr(tacker_client, "list_%s" % resource_plural)
        data = obj_lister(**search_opts)
        return data

    def retrieve_list(self, parsed_args):
        """Retrieve a list of resources from Tacker server"""
        tacker_client = self.get_client()
        tacker_client.format = parsed_args.request_format
        _extra_values = parse_args_to_dict(self.values_specs)
        _merge_args(self, parsed_args, _extra_values,
                    self.values_specs)
        search_opts = self.args2search_opts(parsed_args)
        search_opts.update(_extra_values)
        if self.pagination_support:
            page_size = parsed_args.page_size
            if page_size:
                search_opts.update({'limit': page_size})
        if self.sorting_support:
            keys = parsed_args.sort_key
            if keys:
                search_opts.update({'sort_key': keys})
            dirs = parsed_args.sort_dir
            len_diff = len(keys) - len(dirs)
            if len_diff > 0:
                dirs += ['asc'] * len_diff
            elif len_diff < 0:
                dirs = dirs[:len(keys)]
            if dirs:
                search_opts.update({'sort_dir': dirs})
        data = self.call_server(tacker_client, search_opts, parsed_args)
        collection = _get_resource_plural(self.resource, tacker_client)
        return data.get(collection, [])

    def extend_list(self, data, parsed_args):
        """Update a retrieved list.

        This method provides a way to modify a original list returned from
        the tacker server. For example, you can add subnet cidr information
        to a list network.
        """
        pass

    def setup_columns(self, info, parsed_args):
        _columns = len(info) > 0 and sorted(info[0].keys()) or []
        if not _columns:
            # clean the parsed_args.columns so that cliff will not break
            parsed_args.columns = []
        elif parsed_args.columns:
            _columns = [x for x in parsed_args.columns if x in _columns]
        elif self.list_columns:
            # if no -c(s) by user and list_columns, we use columns in
            # both list_columns and returned resource.
            # Also Keep their order the same as in list_columns
            _columns = [x for x in self.list_columns if x in _columns]
        return (_columns, (utils.get_item_properties(
            s, _columns, formatters=self._formatters, )
            for s in info), )

    def get_data(self, parsed_args):
        self.log.debug('get_data(%s)', parsed_args)
        data = self.retrieve_list(parsed_args)
        self.extend_list(data, parsed_args)
        return self.setup_columns(data, parsed_args)


class ShowCommand(TackerCommand, show.ShowOne):
    """Show information of a given resource

    """

    api = 'nfv-orchestration'
    resource = None
    log = None
    allow_names = True

    def get_id(self):
        if self.resource:
            return self.resource.upper()

    def get_parser(self, prog_name):
        parser = super(ShowCommand, self).get_parser(prog_name)
        add_show_list_common_argument(parser)
        if self.allow_names:
            help_str = _('ID or name of %s to look up')
        else:
            help_str = _('ID of %s to look up')
        parser.add_argument(
            'id', metavar=self.get_id(),
            help=help_str % self.resource)
        return parser

    def get_data(self, parsed_args):
        self.log.debug('get_data(%s)', parsed_args)
        tacker_client = self.get_client()
        tacker_client.format = parsed_args.request_format

        params = {}
        if parsed_args.show_details:
            params = {'verbose': 'True'}
        if parsed_args.fields:
            params = {'fields': parsed_args.fields}
        if self.allow_names:
            _id = find_resourceid_by_name_or_id(tacker_client, self.resource,
                                                parsed_args.id)
        else:
            _id = parsed_args.id

        obj_shower = getattr(tacker_client, "show_%s" % self.resource)
        data = obj_shower(_id, **params)
        self.format_output_data(data)
        resource = data[self.resource]
        if self.resource in data:
            return zip(*sorted(resource.items()))
        else:
            return None
