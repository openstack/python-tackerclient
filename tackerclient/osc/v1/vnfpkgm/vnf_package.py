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

from functools import reduce
import logging
import sys

from osc_lib.cli import parseractions
from osc_lib.command import command
from osc_lib import utils

from tackerclient.common import exceptions
from tackerclient.i18n import _
from tackerclient.osc import sdk_utils
from tackerclient.osc import utils as tacker_osc_utils

LOG = logging.getLogger(__name__)


formatters = {'softwareImages': tacker_osc_utils.FormatComplexDataColumn,
              'checksum': tacker_osc_utils.FormatComplexDataColumn,
              '_links': tacker_osc_utils.FormatComplexDataColumn,
              'userDefinedData': tacker_osc_utils.FormatComplexDataColumn,
              'additionalArtifacts': tacker_osc_utils.FormatComplexDataColumn}


_mixed_case_fields = ('usageState', 'onboardingState', 'operationalState',
                      'vnfProductName', 'softwareImages', 'userDefinedData',
                      'vnfdId', 'vnfdVersion', 'vnfSoftwareVersion',
                      'vnfProvider', 'additionalArtifacts')


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
            'vnfdVersion': 'VNFD Version',
            'checksum': 'Checksum',
            'additionalArtifacts': 'Additional Artifacts'
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
            columns, formatters=formatters,
            mixed_case_fields=_mixed_case_fields)
        return (display_columns, data)


class ListVnfPackage(command.Lister):
    _description = _("List VNF Packages")

    def get_parser(self, prog_name):
        LOG.debug('get_parser(%s)', prog_name)
        parser = super(ListVnfPackage, self).get_parser(prog_name)
        parser.add_argument(
            "--filter",
            metavar="<filter>",
            help=_("Atrribute-based-filtering parameters"),
        )
        fields_exclusive_group = parser.add_mutually_exclusive_group(
            required=False)
        fields_exclusive_group.add_argument(
            "--all_fields",
            action="store_true",
            default=False,
            help=_("Include all complex attributes in the response"),
        )
        fields_exclusive_group.add_argument(
            "--fields",
            metavar="fields",
            help=_("Complex attributes to be included into the response"),
        )
        fields_exclusive_group.add_argument(
            "--exclude_fields",
            metavar="exclude-fields",
            help=_("Complex attributes to be excluded from the response"),
        )
        parser.add_argument(
            "--exclude_default",
            action="store_true",
            default=False,
            help=_("Indicates to exclude all complex attributes"
                   " from the response. This argument can be used alone or"
                   " with --fields and --filter. For all other combinations"
                   " tacker server will throw bad request error"),
        )
        return parser

    def case_modify(self, field):
        return reduce(
            lambda x, y: x + (' ' if y.isupper() else '') + y, field).title()

    def get_attributes(self, extra_fields=None, all_fields=False,
                       exclude_fields=None, exclude_default=False):
        fields = ['id', 'vnfProductName', 'onboardingState',
                  'usageState', 'operationalState', '_links']
        complex_fields = [
            'checksum',
            'softwareImages',
            'userDefinedData',
            'additionalArtifacts']
        simple_fields = ['vnfdVersion', 'vnfProvider', 'vnfSoftwareVersion',
                         'vnfdId']

        if extra_fields:
            fields.extend(extra_fields)

        if exclude_fields:
            fields.extend([field for field in complex_fields
                           if field not in exclude_fields])
        if all_fields:
            fields.extend(complex_fields)
            fields.extend(simple_fields)

        if exclude_default:
            fields.extend(simple_fields)

        attrs = []
        for field in fields:
            if field == '_links':
                attrs.extend([(field, 'Links', tacker_osc_utils.LIST_BOTH)])
            else:
                attrs.extend([(field, self.case_modify(field),
                               tacker_osc_utils.LIST_BOTH)])

        return tuple(attrs)

    def take_action(self, parsed_args):
        _params = {}
        extra_fields = []
        exclude_fields = []
        all_fields = False
        exclude_default = False
        if parsed_args.filter:
            _params['filter'] = parsed_args.filter
        if parsed_args.fields:
            _params['fields'] = parsed_args.fields
            fields = parsed_args.fields.split(',')
            for field in fields:
                extra_fields.append(field.split('/')[0])
        if parsed_args.exclude_fields:
            _params['exclude_fields'] = parsed_args.exclude_fields
            fields = parsed_args.exclude_fields.split(',')
            exclude_fields.extend(fields)
        if parsed_args.exclude_default:
            _params['exclude_default'] = None
            exclude_default = True
        if parsed_args.all_fields:
            _params['all_fields'] = None
            all_fields = True

        client = self.app.client_manager.tackerclient
        data = client.list_vnf_packages(**_params)
        headers, columns = tacker_osc_utils.get_column_definitions(
            self.get_attributes(extra_fields, all_fields, exclude_fields,
                                exclude_default), long_listing=True)
        return (headers,
                (utils.get_dict_properties(
                    s, columns, formatters=formatters,
                    mixed_case_fields=_mixed_case_fields,
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
            columns, formatters=formatters,
            mixed_case_fields=_mixed_case_fields)
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
            raise exceptions.CommandError(message=msg)
        else:
            print((_('All specified %(resource)s(s) deleted successfully')
                   % {'resource': self.resource}))
        return


class DownloadVnfPackage(command.Command):
    _description = _("Download VNF package contents or VNFD of an on-boarded "
                     "VNF package.")

    def get_parser(self, prog_name):
        parser = super(DownloadVnfPackage, self).get_parser(prog_name)
        parser.add_argument(
            "vnf_package",
            metavar="<vnf-package>",
            help=_("VNF package ID")
        )
        parser.add_argument(
            "--file",
            metavar="<FILE>",
            help=_("Local file to save downloaded VNF Package or VNFD data. "
                   "If this is not specified and there is no redirection "
                   "then data will not be saved.")
        )
        parser.add_argument(
            "--vnfd",
            action="store_true",
            default=False,
            help=_("Download VNFD of an on-boarded vnf package."),
        )
        parser.add_argument(
            "--type",
            default="application/zip",
            metavar="<type>",
            choices=["text/plain", "application/zip", "both"],
            help=_("Provide text/plain when VNFD is implemented as a single "
                   "YAML file otherwise  use application/zip. If you are not "
                   "aware whether VNFD is a single or multiple yaml files, "
                   "then you can specify 'both' option value. "
                   "Provide this option only when --vnfd is set.")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        if parsed_args.vnfd:
            if sys.stdout.isatty() and not (parsed_args.file and
                                            parsed_args.type != "text/plain"):
                msg = ("No redirection or local file specified for downloaded "
                       "VNFD data. Please specify a local file with --file to "
                       "save downloaded VNFD data or use redirection.")
                sdk_utils.exit(msg)

            body = client.download_vnfd_from_vnf_package(
                parsed_args.vnf_package, parsed_args.type)

            if not parsed_args.file:
                print(body)
                return
        else:
            body = client.download_vnf_package(parsed_args.vnf_package)

        sdk_utils.save_data(body, parsed_args.file)


class DownloadVnfPackageArtifact(command.Command):
    _description = _("Download VNF package artifact of an on-boarded "
                     "VNF package.")

    def get_parser(self, prog_name):
        parser = super(DownloadVnfPackageArtifact, self).get_parser(prog_name)
        parser.add_argument(
            "vnf_package",
            metavar="<vnf-package>",
            help=_("VNF package ID")
        )
        parser.add_argument(
            "artifact_path",
            metavar="<artifact-path>",
            help=_("The artifact file's path")
        )
        parser.add_argument(
            "--file",
            metavar="<FILE>",
            help=_("Local file to save downloaded VNF Package artifact "
                   "file data. If this is not specified and "
                   "there is no redirection then data will not be saved.")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        if sys.stdout.isatty() and not (parsed_args.file):
            msg = (
                "No redirection or local file specified for downloaded "
                "vnf package artifact data. Please specify a "
                "local file with --file to "
                "save downloaded vnf package artifact data "
                "or use redirection.")
            sdk_utils.exit(msg)
        body = client.download_artifact_from_vnf_package(
            parsed_args.vnf_package, parsed_args.artifact_path)

        if not parsed_args.file:
            print(body)
            return
        else:
            sdk_utils.save_data(body, parsed_args.file)


class UpdateVnfPackage(command.ShowOne):
    _description = _("Update information about an individual VNF package")

    def get_parser(self, prog_name):
        LOG.debug('get_parser(%s)', prog_name)
        parser = super(UpdateVnfPackage, self).get_parser(prog_name)
        parser.add_argument(
            'vnf_package',
            metavar="<vnf-package>",
            help=_("VNF package ID")
        )
        parser.add_argument(
            '--operational-state',
            metavar="<operational-state>",
            choices=['ENABLED', 'DISABLED'],
            help=_("Change the operational state of VNF Package, Valid values"
                   " are 'ENABLED' or 'DISABLED'.")
        )
        parser.add_argument(
            '--user-data',
            metavar='<key=value>',
            action=parseractions.KeyValueAction,
            help=_('User defined data for the VNF package '
                   '(repeat option to set multiple user defined data)'),
        )
        return parser

    def get_columns(self, updated_values):
        column_map = {}
        if updated_values.get('userDefinedData'):
            column_map.update({'userDefinedData': 'User Defined Data'})

        if updated_values.get('operationalState'):
            column_map.update({'operationalState': 'Operational State'})

        return sdk_utils.get_osc_show_columns_for_sdk_resource(updated_values,
                                                               column_map)

    def args2body(self, parsed_args):
        body = {}
        if not parsed_args.user_data and not parsed_args.operational_state:
            msg = ('Provide at least one of the argument from "--user-data"'
                   ' or "--operational-state"')
            sdk_utils.exit(msg)
        if parsed_args.user_data:
            body["userDefinedData"] = parsed_args.user_data
        if parsed_args.operational_state:
            body["operationalState"] = parsed_args.operational_state
        return body

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        updated_values = client.update_vnf_package(
            parsed_args.vnf_package, self.args2body(parsed_args))
        display_columns, columns = self.get_columns(updated_values)
        data = utils.get_item_properties(
            sdk_utils.DictModel(updated_values),
            columns, formatters=formatters,
            mixed_case_fields=_mixed_case_fields)
        return (display_columns, data)
