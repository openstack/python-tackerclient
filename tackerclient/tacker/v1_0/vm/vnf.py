#
# Copyright 2013 Intel
# Copyright 2013 Isaku Yamahata <isaku.yamahata at intel com>
#                               <isaku.yamahata at gmail com>
# All Rights Reserved.
#
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
# @author: Isaku Yamahata, Intel

import abc
import six

from tackerclient.common import exceptions
from tackerclient.openstack.common.gettextutils import _
from tackerclient.tacker import v1_0 as tackerV10


_DEVICE = 'device'


class ListVNF(tackerV10.ListCommand):
    """List device that belong to a given tenant."""

    resource = _DEVICE


class ShowVNF(tackerV10.ShowCommand):
    """show information of a given VNF."""

    resource = _DEVICE


class CreateVNF(tackerV10.CreateCommand):
    """create a VNF."""

    resource = _DEVICE

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--vnfd-id',
            required=True,
            help='vnfd id to instantiate vnf based on')
        parser.add_argument(
            '--config-file',
            action='append',
            help='specify config yaml file')
        parser.add_argument(
            '--config',
            metavar='<key>=<value>',
            action='append',
            dest='configs',
            default=[],
            help='vnf config')

    def args2body(self, parsed_args):
        body = {
            self.resource: {
                'template_id': parsed_args.vnfd_id,
            }
        }
        if parsed_args.config_file:
            with open(parsed_args.config_file[0]) as f:
                config_yaml = f.read()
            body[self.resource]['attributes'] = {'config': config_yaml}
        if parsed_args.configs:
            try:
                configs = dict(key_value.split('=', 1)
                               for key_value in parsed_args.configs)
            except ValueError:
                msg = (_('invalid argument for --config %s') %
                       parsed_args.configs)
                raise exceptions.TackerCLIError(msg)
            if configs:
                body[self.resource].setdefault(
                    'attributes', {}).update(configs)

        tackerV10.update_dict(parsed_args, body[self.resource], ['tenant_id'])
        return body


class UpdateVNF(tackerV10.UpdateCommand):
    """Update a given VNF."""

    resource = _DEVICE

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--attributes',
            metavar='<key>=<value>',
            action='append',
            dest='attributes',
            default=[],
            help='instance specific argument')

    def args2body(self, parsed_args):
        body = {self.resource: {}}
        if parsed_args.attributes:
            try:
                attributes = dict(key_value.split('=', 1)
                                  for key_value in parsed_args.attributes)
            except ValueError:
                msg = (_('invalid argument for --attributes %s') %
                       parsed_args.attributes)
                raise exceptions.TackerCLIError(msg)
            if attributes:
                body[self.resource]['attributes'] = attributes
        tackerV10.update_dict(parsed_args, body[self.resource], ['tenant_id'])
        return body


class DeleteVNF(tackerV10.DeleteCommand):
    """Delete a given VNF."""

    resource = _DEVICE


@six.add_metaclass(abc.ABCMeta)
class _XtachInterface(tackerV10.UpdateCommand):
    resource = _DEVICE

    @abc.abstractmethod
    def call_api(self, tacker_client, device_id, body):
        pass

    def args2body(self, parsed_args):
        body = {
            'port_id': parsed_args.port_id,
        }
        tackerV10.update_dict(parsed_args, body, [])
        return body

    def get_parser(self, prog_name):
        parser = super(AttachInterface, self).get_parser(prog_name)
        parser.add_argument('port_id', metavar='PORT',
                            help=_('port to attach/detach'))
        self.add_known_arguments(parser)
        return parser

    def run(self, parsed_args):
        tacker_client = self.get_client()
        tacker_client.format = parsed_args.request_format
        body = self.args2body(parsed_args)
        _id = tackerV10.find_resourceid_by_name_or_id(tacker_client,
                                                      self.resource,
                                                      parsed_args.id)
        self.call_api(tacker_client, _id, body)


class AttachInterface(_XtachInterface):
    def call_api(self, tacker_client, device_id, body):
        return tacker_client.attach_interface(device_id, body)


class DetachInterface(_XtachInterface):
    def call_api(self, tacker_client, device_id, body):
        return tacker_client.detach_interface(device_id, body)
