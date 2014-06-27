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

from tackerclient.common import exceptions
from tackerclient.openstack.common.gettextutils import _
from tackerclient.tacker import v1_0 as tackerV10


_DEVICE = 'device'


class ListDevice(tackerV10.ListCommand):
    """List device that belong to a given tenant."""

    resource = _DEVICE


class ShowDevice(tackerV10.ShowCommand):
    """show information of a given Device."""

    resource = _DEVICE


class CreateDevice(tackerV10.CreateCommand):
    """create a Device."""

    resource = _DEVICE

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--device-template-id',
            required=True,
            help='device template id to create device based on')
        parser.add_argument(
            '--kwargs',
            metavar='<key>=<value>',
            action='append',
            dest='kwargs',
            default=[],
            help='instance specific argument')
        parser.add_argument(
            '--service-context',
            metavar='<network-id=network-uuid,subnet-id=subnet-uuid,'
            'port-id=port-uuid,router-id=router-uuid,'
            'role=role-string,index=int>',
            action='append',
            dest='service_context',
            default=[],
            help='service context to insert service')

    def args2body(self, parsed_args):
        body = {
            self.resource: {
                'template_id': parsed_args.device_template_id,
            }
        }
        if parsed_args.kwargs:
            try:
                kwargs = dict(key_value.split('=', 1)
                              for key_value in parsed_args.kwargs)
            except ValueError:
                msg = (_('invalid argument for --kwargs %s') %
                       parsed_args.kwargs)
                raise exceptions.TackerCLIError(msg)
            if kwargs:
                body[self.resource]['kwargs'] = kwargs
        if parsed_args.service_context:
            try:
                service_context = [dict(
                    (k.replace('-', '_'), v)
                    for k, v in (key_value.split('=', 1)
                                 for key_value in entry_string.split(',')))
                    for entry_string in parsed_args.service_context]
            except ValueError:
                msg = (_('invalid argument for --service-context %s') %
                       parsed_args.service_context)
                raise exceptions.TackerCLIError(msg)

            if service_context:
                body[self.resource]['service_context'] = service_context

        tackerV10.update_dict(parsed_args, body[self.resource], ['tenant_id'])
        return body


class UpdateDevice(tackerV10.UpdateCommand):
    """Update a given Device."""

    resource = _DEVICE

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--kwargs',
            metavar='<key>=<value>',
            action='append',
            dest='kwargs',
            default=[],
            help='instance specific argument')

    def args2body(self, parsed_args):
        body = {self.resource: {}}
        if parsed_args.kwargs:
            try:
                kwargs = dict(key_value.split('=', 1)
                              for key_value in parsed_args.kwargs)
            except ValueError:
                msg = (_('invalid argument for --kwargs %s') %
                       parsed_args.kwargs)
                raise exceptions.TackerCLIError(msg)
            if kwargs:
                body[self.resource]['kwargs'] = kwargs
        tackerV10.update_dict(parsed_args, body[self.resource], ['tenant_id'])
        return body


class DeleteDevice(tackerV10.DeleteCommand):
    """Delete a given Device."""

    resource = _DEVICE
