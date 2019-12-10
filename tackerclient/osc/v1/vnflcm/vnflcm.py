# Copyright (C) 2020 NTT DATA
# All Rights Reserved.
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

from osc_lib.command import command
from osc_lib import utils

from tackerclient.i18n import _
from tackerclient.osc import sdk_utils

_mixed_case_fields = ('vnfInstanceName', 'vnfInstanceDescription', 'vnfdId',
                      'vnfProvider', 'vnfProductName', 'vnfSoftwareVersion',
                      'vnfdVersion', 'instantiationState')


def _get_columns(item):
    column_map = {
        'id': 'ID',
        'vnfInstanceName': 'VNF Instance Name',
        'vnfInstanceDescription': 'VNF Instance Description',
        'vnfdId': 'VNFD ID',
        'vnfProvider': 'VNF Provider',
        'vnfProductName': 'VNF Product Name',
        'vnfSoftwareVersion': 'VNF Software Version',
        'vnfdVersion': 'VNFD Version',
        'instantiationState': 'Instantiation State',
        'links': 'Links',
    }
    return sdk_utils.get_osc_show_columns_for_sdk_resource(item, column_map)


class CreateVnfLcm(command.ShowOne):
    _description = _("Create a new VNF Instance")

    def get_parser(self, prog_name):
        parser = super(CreateVnfLcm, self).get_parser(prog_name)
        parser.add_argument(
            'vnfd_id',
            metavar="<vnfd-id>",
            help=_('Identifier that identifies the VNFD which defines the '
                   'VNF instance to be created.'))
        parser.add_argument(
            '--name',
            metavar="<vnf-instance-name>",
            help=_('Name of the VNF instance to be created.'))
        parser.add_argument(
            '--description',
            metavar="<vnf-instance-description>",
            help=_('Description of the VNF instance to be created.'))
        return parser

    def args2body(self, parsed_args):
        body = {}
        body['vnfdId'] = parsed_args.vnfd_id

        if parsed_args.description:
            body['vnfInstanceDescription'] = parsed_args.description

        if parsed_args.name:
            body['vnfInstanceName'] = parsed_args.name

        return body

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        vnf = client.create_vnf_instance(self.args2body(parsed_args))
        display_columns, columns = _get_columns(vnf)
        data = utils.get_item_properties(
            sdk_utils.DictModel(vnf),
            columns, mixed_case_fields=_mixed_case_fields)
        return (display_columns, data)
