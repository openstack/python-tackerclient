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

import json
import logging
import os

from osc_lib.cli import format_columns
from osc_lib.command import command
from osc_lib import utils

from tackerclient.common import exceptions
from tackerclient.i18n import _
from tackerclient.osc import sdk_utils

LOG = logging.getLogger(__name__)

_mixed_case_fields = ('vnfInstanceName', 'vnfInstanceDescription', 'vnfdId',
                      'vnfProvider', 'vnfProductName', 'vnfSoftwareVersion',
                      'vnfdVersion', 'instantiationState',
                      'vimConnectionInfo', 'instantiatedVnfInfo')

_VNF_INSTANCE = 'vnf_instance'


def _get_columns(vnflcm_obj, action=None):
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
        '_links': 'Links',
    }
    if action == 'show':
        if vnflcm_obj['instantiationState'] == 'INSTANTIATED':
            column_map.update(
                {'instantiatedVnfInfo': 'Instantiated Vnf Info'}
            )
        column_map.update(
            {'vimConnectionInfo': 'VIM Connection Info',
             '_links': 'Links'}
        )
    return sdk_utils.get_osc_show_columns_for_sdk_resource(vnflcm_obj,
                                                           column_map)


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
        parser.add_argument(
            '--I',
            metavar="<param-file>",
            help=_("Instantiate VNF subsequently after it's creation. "
                   "Specify instantiate request parameters in a json file."))
        return parser

    def args2body(self, parsed_args, file_path=None):
        body = {}

        if file_path:
            return instantiate_vnf_args2body(file_path)

        body['vnfdId'] = parsed_args.vnfd_id

        if parsed_args.description:
            body['vnfInstanceDescription'] = parsed_args.description

        if parsed_args.name:
            body['vnfInstanceName'] = parsed_args.name

        return body

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        vnf = client.create_vnf_instance(self.args2body(parsed_args))
        if parsed_args.I:
            # Instantiate VNF instance.
            result = client.instantiate_vnf_instance(
                vnf['id'],
                self.args2body(parsed_args, file_path=parsed_args.I))
            if not result:
                print((_('VNF Instance %(id)s is created and instantiation'
                         ' request has been accepted.') % {'id': vnf['id']}))
        display_columns, columns = _get_columns(vnf)
        data = utils.get_item_properties(
            sdk_utils.DictModel(vnf),
            columns, mixed_case_fields=_mixed_case_fields)
        return (display_columns, data)


class ShowVnfLcm(command.ShowOne):
    _description = _("Display VNF instance details")

    def get_parser(self, prog_name):
        parser = super(ShowVnfLcm, self).get_parser(prog_name)
        parser.add_argument(
            _VNF_INSTANCE,
            metavar="<vnf-instance>",
            help=_("VNF instance ID to display"))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj = client.show_vnf_instance(parsed_args.vnf_instance)
        display_columns, columns = _get_columns(obj, action='show')
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj),
            columns, mixed_case_fields=_mixed_case_fields,
            formatters={'instantiatedVnfInfo': format_columns.DictColumn})
        return (display_columns, data)


def instantiate_vnf_args2body(file_path):

    if file_path is not None and os.access(file_path, os.R_OK) is False:
        msg = _("File %s does not exist or user does not have read "
                "privileges to it")
        raise exceptions.InvalidInput(msg % file_path)

    try:
        with open(file_path) as f:
            body = json.load(f)
    except (IOError, ValueError) as ex:
        msg = _("Failed to load parameter file. Error: %s")
        raise exceptions.InvalidInput(msg % ex)

    if not body:
        raise exceptions.InvalidInput(_('The parameter file is empty'))

    return body


class InstantiateVnfLcm(command.Command):
    _description = _("Instantiate a VNF Instance")

    def get_parser(self, prog_name):
        parser = super(InstantiateVnfLcm, self).get_parser(prog_name)
        parser.add_argument(
            _VNF_INSTANCE,
            metavar="<vnf-instance>",
            help=_("VNF instance ID to instantiate"))
        parser.add_argument(
            'instantiation_request_file',
            metavar="<param-file>",
            help=_('Specify instantiate request parameters in a json file.'))

        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        result = client.instantiate_vnf_instance(
            parsed_args.vnf_instance, instantiate_vnf_args2body(
                parsed_args.instantiation_request_file))
        if not result:
            print((_('Instantiate request for VNF Instance %(id)s has been'
                     ' accepted.') % {'id': parsed_args.vnf_instance}))
