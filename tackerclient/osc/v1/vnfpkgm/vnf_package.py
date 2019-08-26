# Copyright (C) 2019 NTT DATA
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

import logging

from osc_lib.cli import parseractions
from osc_lib.command import command
from osc_lib import utils

from tackerclient.common import exceptions
from tackerclient.i18n import _
from tackerclient.osc import sdk_utils
from tackerclient.osc import utils as tacker_osc_utils

LOG = logging.getLogger(__name__)

_attr_map = (
    ('id', 'ID', tacker_osc_utils.LIST_BOTH),
    ('vnfProductName', 'VNF Product Name', tacker_osc_utils.LIST_BOTH),
    ('onboardingState', 'Onboarding State', tacker_osc_utils.LIST_BOTH),
    ('usageState', 'Usage State', tacker_osc_utils.LIST_BOTH),
    ('operationalState', 'Operational State', tacker_osc_utils.LIST_BOTH),
    ('userDefinedData', 'User Defined Data', tacker_osc_utils.LIST_BOTH)
)


_mixed_case_fields = ('usageState', 'onboardingState', 'operationalState',
                      'vnfProductName', 'softwareImages', 'userDefinedData',
                      'vnfdId', 'vnfdVersion', 'vnfSoftwareVersion',
                      'vnfProvider', 'artifactPath', 'imagePath',
                      'diskFormat', 'userMetadata')


def _get_columns(vnf_package_obj):
    column_map = {
        '_links': 'Links',
        'onboardingState': 'Onboarding State',
        'operationalState': 'Operational State',
        'usageState': 'Usage State',
        'userDefinedData': 'User Defined Data',
        'id': 'ID'
    }

    if vnf_package_obj['onboardingState'] == 'ONBOARDED':
        column_map.update({
            'softwareImages': 'Software Images',
            'vnfProvider': 'VNF Provider',
            'vnfSoftwareVersion': 'VNF Software Version',
            'vnfProductName': 'VNF Product Name',
            'vnfdId': 'VNFD ID',
            'vnfdVersion': 'VNFD Version'
        })

    return sdk_utils.get_osc_show_columns_for_sdk_resource(vnf_package_obj,
                                                           column_map)


class CreateVnfPackage(command.ShowOne):
    _description = _("Create a new VNF Package")

    def get_parser(self, prog_name):
        LOG.debug('get_parser(%s)', prog_name)
        parser = super(CreateVnfPackage, self).get_parser(prog_name)
        parser.add_argument(
            '--user-data',
            metavar='<key=value>',
            action=parseractions.KeyValueAction,
            help=_('User defined data for the VNF package '
                   '(repeat option to set multiple user defined data)'),
        )
        return parser

    def args2body(self, parsed_args):
        body = {}
        if parsed_args.user_data:
            body["userDefinedData"] = parsed_args.user_data
        return body

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        vnf_package = client.create_vnf_package(self.args2body(parsed_args))
        display_columns, columns = _get_columns(vnf_package)
        data = utils.get_item_properties(
            sdk_utils.DictModel(vnf_package),
            columns, mixed_case_fields=_mixed_case_fields)
        return (display_columns, data)


class ListVnfPackage(command.Lister):
    _description = _("List VNF Package")

    def get_parser(self, prog_name):
        LOG.debug('get_parser(%s)', prog_name)
        parser = super(ListVnfPackage, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        _params = {}
        client = self.app.client_manager.tackerclient
        data = client.list_vnf_packages(**_params)
        headers, columns = tacker_osc_utils.get_column_definitions(
            _attr_map, long_listing=True)
        return (headers,
                (utils.get_dict_properties(
                    s, columns, mixed_case_fields=_mixed_case_fields,
                ) for s in data['vnf_packages']))


class ShowVnfPackage(command.ShowOne):
    _description = _("Show VNF Package Details")

    def get_parser(self, prog_name):
        LOG.debug('get_parser(%s)', prog_name)
        parser = super(ShowVnfPackage, self).get_parser(prog_name)
        parser.add_argument(
            'vnf_package',
            metavar="<vnf-package>",
            help=_("VNF package ID")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        vnf_package = client.show_vnf_package(parsed_args.vnf_package)
        display_columns, columns = _get_columns(vnf_package)
        data = utils.get_item_properties(
            sdk_utils.DictModel(vnf_package),
            columns, mixed_case_fields=_mixed_case_fields)
        return (display_columns, data)


class UploadVnfPackage(command.Command):
    _description = _("Upload VNF Package")

    def get_parser(self, prog_name):
        LOG.debug('get_parser(%s)', prog_name)
        parser = super(UploadVnfPackage, self).get_parser(prog_name)
        parser.add_argument(
            'vnf_package',
            metavar="<vnf-package>",
            help=_("VNF package ID")
        )
        file_source = parser.add_mutually_exclusive_group(required=True)
        file_source.add_argument(
            "--path",
            metavar="<file>",
            help=_("Upload VNF CSAR package from local file"),
        )
        file_source.add_argument(
            "--url",
            metavar="<Uri>",
            help=_("Uri of the VNF package content"),
        )
        parser.add_argument(
            "--user-name",
            metavar="<user-name>",
            help=_("User name for authentication"),
        )
        parser.add_argument(
            "--password",
            metavar="<password>",
            help=_("Password for authentication"),
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        attrs = {}
        if parsed_args.user_name:
            attrs['userName'] = parsed_args.user_name

        if parsed_args.password:
            attrs['password'] = parsed_args.password

        if parsed_args.url:
            attrs['url'] = parsed_args.url

        file_data = None
        try:
            if parsed_args.path:
                file_data = open(parsed_args.path, 'rb')
            result = client.upload_vnf_package(parsed_args.vnf_package,
                                               file_data, **attrs)
            if not result:
                print((_('Upload request for VNF package %(id)s has been'
                         ' accepted.') % {'id': parsed_args.vnf_package}))
        finally:
            if file_data:
                file_data.close()


class DeleteVnfPackage(command.Command):
    """Vnf package delete

    Delete class supports bulk deletion of vnf packages, and error
    handling.
    """

    _description = _("Delete VNF Package")

    resource = 'vnf-package'

    def get_parser(self, prog_name):
        LOG.debug('get_parser(%s)', prog_name)
        parser = super(DeleteVnfPackage, self).get_parser(prog_name)
        parser.add_argument(
            'vnf-package',
            metavar="<vnf-package>",
            nargs="+",
            help=_("Vnf package(s) ID to delete")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        failure = False
        deleted_ids = []
        failed_items = {}
        resources = getattr(parsed_args, self.resource, [])
        for resource_id in resources:
            try:
                vnf_package = client.show_vnf_package(resource_id)
                client.delete_vnf_package(vnf_package['id'])
                deleted_ids.append(resource_id)
            except Exception as e:
                failure = True
                failed_items[resource_id] = e
        if failure:
            msg = ''
            if deleted_ids:
                msg = (_('Successfully deleted %(resource)s(s):'
                         ' %(deleted_list)s') % {'deleted_list':
                                                 ', '.join(deleted_ids),
                                                 'resource': self.resource})
            err_msg = _("\n\nUnable to delete the below"
                        " 'vnf_package'(s):")
            for failed_id, error in failed_items.items():
                err_msg += (_('\n Cannot delete %(failed_id)s: %(error)s')
                            % {'failed_id': failed_id,
                               'error': error})
            msg += err_msg
            raise exceptions.CommandError(msg)
        else:
            print((_('All specified %(resource)s(s) deleted successfully')
                   % {'resource': self.resource}))
        return
