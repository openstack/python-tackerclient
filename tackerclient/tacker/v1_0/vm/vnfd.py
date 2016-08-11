#
# Copyright 2013 Intel Corporation
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

from oslo_serialization import jsonutils

from tackerclient.i18n import _
from tackerclient.tacker import v1_0 as tackerV10


_VNFD = "vnfd"


class ListVNFD(tackerV10.ListCommand):
    """List VNFD that belong to a given tenant."""

    resource = _VNFD
    list_columns = ['id', 'name', 'description', 'infra_driver', 'mgmt_driver']


class ShowVNFD(tackerV10.ShowCommand):
    """Show information of a given VNFD."""

    resource = _VNFD


class CreateVNFD(tackerV10.CreateCommand):
    """Create a VNFD."""

    resource = _VNFD
    remove_output_fields = ["attributes"]

    def add_known_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--vnfd-file', help='Specify VNFD file')
        group.add_argument('--vnfd', help='Specify VNFD')
        parser.add_argument(
            'name', metavar='NAME',
            help='Set a name for the VNFD')
        parser.add_argument(
            '--description',
            help='Set a description for the VNFD')

    def args2body(self, parsed_args):
        body = {self.resource: {}}
        if parsed_args.vnfd_file:
            with open(parsed_args.vnfd_file) as f:
                vnfd = f.read()
                body[self.resource]['attributes'] = {'vnfd': vnfd}
        if parsed_args.vnfd:
                body[self.resource]['attributes'] = {'vnfd': parsed_args.vnfd}

        tackerV10.update_dict(parsed_args, body[self.resource],
                              ['tenant_id', 'name', 'description'])
        return body


class DeleteVNFD(tackerV10.DeleteCommand):
    """Delete a given VNFD."""
    resource = _VNFD


class ShowTemplateVNFD(tackerV10.ShowCommand):
    """Show template of a given VNFD."""

    resource = _VNFD

    def run(self, parsed_args):
        self.log.debug('run(%s)', parsed_args)
        template = None
        data = self.get_data(parsed_args)
        try:
            attributes_index = data[0].index('attributes')
            attributes_json = data[1][attributes_index]
            template = jsonutils.loads(attributes_json).get('vnfd', None)
        except (IndexError, TypeError, ValueError) as e:
            self.log.debug('Data handling error: %s', str(e))
        print(template or _('Unable to display VNFD template!'))
