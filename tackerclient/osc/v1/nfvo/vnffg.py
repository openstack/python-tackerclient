# Copyright 2018 OpenStack Foundation.
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

import yaml

from osc_lib.command import command
from osc_lib import utils

from tackerclient.common import exceptions
from tackerclient.i18n import _
from tackerclient.osc import sdk_utils
from tackerclient.osc import utils as tacker_osc_utils
from tackerclient.tacker import v1_0 as tackerV10

_VNFFG = 'vnffg'    # VNF Forwarding Graph
_NFP = 'nfp'        # Network Forwarding Path
_SFC = 'sfc'        # Service Function Chain
_FC = 'classifier'  # Flow Classifier

nfps_path = '/nfps'
fcs_path = '/classifiers'
sfcs_path = '/sfcs'

DEFAULT_ERROR_REASON_LENGTH = 100

_attr_map_vnffg = (
    ('id', 'ID', tacker_osc_utils.LIST_BOTH),
    ('name', 'Name', tacker_osc_utils.LIST_BOTH),
    ('ns_id', 'NS ID', tacker_osc_utils.LIST_BOTH),
    ('vnffgd_id', 'VNFFGD ID', tacker_osc_utils.LIST_BOTH),
    ('status', 'Status', tacker_osc_utils.LIST_BOTH),
    ('description', 'Description', tacker_osc_utils.LIST_LONG_ONLY),
)

_attr_map_nfp = (
    ('id', 'ID', tacker_osc_utils.LIST_BOTH),
    ('name', 'Name', tacker_osc_utils.LIST_BOTH),
    ('status', 'Status', tacker_osc_utils.LIST_BOTH),
    ('vnffg_id', 'VNFFG ID', tacker_osc_utils.LIST_BOTH),
    ('path_id', 'Path ID', tacker_osc_utils.LIST_BOTH),
)

_attr_map_sfc = (
    ('id', 'ID', tacker_osc_utils.LIST_BOTH),
    ('status', 'Status', tacker_osc_utils.LIST_BOTH),
    ('nfp_id', 'NFP ID', tacker_osc_utils.LIST_BOTH),
)

_attr_map_fc = (
    ('id', 'ID', tacker_osc_utils.LIST_BOTH),
    ('name', 'Name', tacker_osc_utils.LIST_BOTH),
    ('status', 'Status', tacker_osc_utils.LIST_BOTH),
    ('nfp_id', 'NFP ID', tacker_osc_utils.LIST_BOTH),
    ('chain_id', 'Chain ID', tacker_osc_utils.LIST_BOTH),
)

_formatters = {
    'attributes': tacker_osc_utils.format_dict_with_indention,
    'match': tacker_osc_utils.format_dict_with_indention,
    'chain': tacker_osc_utils.format_dict_with_indention,
}


def _get_columns(item):
    column_map = {
        'tenant_id': 'project_id',
    }
    return sdk_utils.get_osc_show_columns_for_sdk_resource(item, column_map)


class CreateVNFFG(command.ShowOne):
    _description = _("Create a new VNFFG.")

    def get_parser(self, prog_name):
        parser = super(CreateVNFFG, self).get_parser(prog_name)
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Set a name for the VNFFG'))
        parser.add_argument(
            '--tenant-id', metavar='TENANT_ID',
            help=_('The owner tenant ID'))
        vnffgd_group = parser.add_mutually_exclusive_group(required=True)
        vnffgd_group.add_argument(
            '--vnffgd-id',
            help=_('VNFFGD ID to use as template to create VNFFG'))
        vnffgd_group.add_argument(
            '--vnffgd-name',
            help=_('VNFFGD Name to use as template to create VNFFG'))
        vnffgd_group.add_argument(
            '--vnffgd-template',
            help=_('VNFFGD file to create VNFFG'))
        parser.add_argument(
            '--vnf-mapping',
            help=_('List of logical VNFD name to VNF instance name mapping. '
                   'Example: VNF1:my_vnf1,VNF2:my_vnf2'))
        parser.add_argument(
            '--symmetrical',
            action='store_true',
            default=False,
            help=_('Should a reverse path be created for the NFP '
                   '(True or False)'))
        parser.add_argument(
            '--param-file',
            help=_('YAML file with specific VNFFG parameters'))
        parser.add_argument(
            '--description',
            help=_('Set a description for the VNFFG'))
        return parser

    def args2body(self, parsed_args):
        body = {_VNFFG: {}}
        body[_VNFFG]['attributes'] = {}

        client = self.app.client_manager.tackerclient
        if parsed_args.vnf_mapping:
            _vnf_mapping = dict()
            _vnf_mappings = parsed_args.vnf_mapping.split(",")
            for mapping in _vnf_mappings:
                vnfd_name, vnf = mapping.split(":", 1)
                _vnf_mapping[vnfd_name] = \
                    tackerV10.find_resourceid_by_name_or_id(
                        client, 'vnf', vnf)
            parsed_args.vnf_mapping = _vnf_mapping

        if parsed_args.vnffgd_name:
            _id = tackerV10.find_resourceid_by_name_or_id(
                client, 'vnffgd', parsed_args.vnffgd_name)
            parsed_args.vnffgd_id = _id
        elif parsed_args.vnffgd_template:
            with open(parsed_args.vnffgd_template) as f:
                template = f.read()
                try:
                    template = yaml.load(template, Loader=yaml.SafeLoader)
                except yaml.YAMLError as e:
                    raise exceptions.InvalidInput(reason=e)
                if not template:
                    raise exceptions.InvalidInput(
                        reason='The vnffgd file is empty')
                body[_VNFFG]['vnffgd_template'] = template

        if parsed_args.param_file:
            with open(parsed_args.param_file) as f:
                param_yaml = f.read()
            try:
                param_yaml = yaml.load(
                    param_yaml, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(reason=e)
            if not param_yaml:
                raise exceptions.InvalidInput(
                    reason='The parameter file is empty')
            body[_VNFFG]['attributes'] = {'param_values': param_yaml}
        tackerV10.update_dict(parsed_args, body[_VNFFG],
                              ['tenant_id', 'name', 'vnffgd_id',
                               'symmetrical', 'vnf_mapping', 'description'])
        return body

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        vnffg = client.create_vnffg(self.args2body(parsed_args))
        display_columns, columns = _get_columns(vnffg[_VNFFG])
        data = utils.get_item_properties(
            sdk_utils.DictModel(vnffg[_VNFFG]),
            columns,
            formatters=_formatters)
        return (display_columns, data)


class DeleteVNFFG(command.Command):
    _description = _("Delete VNFFG(s).")

    def get_parser(self, prog_name):
        parser = super(DeleteVNFFG, self).get_parser(prog_name)
        parser.add_argument(
            _VNFFG,
            metavar="<VNFFG>",
            nargs="+",
            help=_("VNFFG(s) to delete (name or ID)")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        failure = False
        deleted_ids = []
        failed_items = {}
        for resource_id in parsed_args.vnffg:
            try:
                obj = tackerV10.find_resourceid_by_name_or_id(
                    client, _VNFFG, resource_id)
                client.delete_vnffg(obj)
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
                                                 'resource': _VNFFG})
            err_msg = _("\n\nUnable to delete the below"
                        " %s(s):") % _VNFFG
            for failed_id, error in failed_items.items():
                err_msg += (_('\n Cannot delete %(failed_id)s: %(error)s')
                            % {'failed_id': failed_id,
                               'error': error})
            msg += err_msg
            raise exceptions.CommandError(message=msg)
        else:
            print((_('All specified %(resource)s(s) deleted successfully')
                   % {'resource': _VNFFG}))
        return


class UpdateVNFFG(command.ShowOne):
    _description = _("Update VNFFG.")

    def get_parser(self, prog_name):
        parser = super(UpdateVNFFG, self).get_parser(prog_name)
        parser.add_argument(
            _VNFFG,
            metavar="<VNFFG>",
            help=_('VNFFG to update (name or ID)'))
        parser.add_argument(
            '--vnffgd-template',
            help=_('VNFFGD file to update VNFFG'))
        parser.add_argument(
            '--vnf-mapping',
            help=_('List of logical VNFD name to VNF instance name mapping.  '
                   'Example: VNF1:my_vnf1,VNF2:my_vnf2'))
        parser.add_argument(
            '--symmetrical',
            action='store_true',
            default=False,
            help=_('Should a reverse path be created for the NFP'))
        parser.add_argument(
            '--description',
            help=_('Set a description for the VNFFG'))
        parser.add_argument(
            '--param-file',
            help=_('YAML file with specific VNFFG parameters'))
        return parser

    def args2body(self, parsed_args):
        body = {_VNFFG: {}}
        body[_VNFFG]['attributes'] = {}

        client = self.app.client_manager.tackerclient

        if parsed_args.vnf_mapping:
            _vnf_mapping = dict()
            _vnf_mappings = parsed_args.vnf_mapping.split(",")
            for mapping in _vnf_mappings:
                vnfd_name, vnf = mapping.split(":", 1)
                _vnf_mapping[vnfd_name] = \
                    tackerV10.find_resourceid_by_name_or_id(
                        client, 'vnf', vnf)
            parsed_args.vnf_mapping = _vnf_mapping

        if parsed_args.vnffgd_template:
            with open(parsed_args.vnffgd_template) as f:
                template = f.read()
                try:
                    template = yaml.load(
                        template, Loader=yaml.SafeLoader)
                except yaml.YAMLError as e:
                    raise exceptions.InvalidInput(reason=e)
                if not template:
                    raise exceptions.InvalidInput(
                        reason='The vnffgd file is empty')
                body[_VNFFG]['vnffgd_template'] = template

        if parsed_args.param_file:
            with open(parsed_args.param_file) as f:
                param_yaml = f.read()
            try:
                param_yaml = yaml.load(
                    param_yaml, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(reason=e)
            if not param_yaml:
                raise exceptions.InvalidInput(
                    reason='The parameter file is empty')
            body[_VNFFG]['attributes'] = {'param_values': param_yaml}
        tackerV10.update_dict(parsed_args, body[_VNFFG],
                              ['vnf_mapping', 'symmetrical', 'description'])
        return body

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj_id = tackerV10.find_resourceid_by_name_or_id(
            client, _VNFFG, parsed_args.vnffg)
        vnffg = client.update_vnffg(obj_id, self.args2body(parsed_args))
        display_columns, columns = _get_columns(vnffg[_VNFFG])
        data = utils.get_item_properties(
            sdk_utils.DictModel(vnffg[_VNFFG]),
            columns,
            formatters=_formatters)
        return (display_columns, data)


class ListVNFFG(command.Lister):
    _description = ("List VNFFG(s) that belong to a given tenant.")

    def get_parser(self, prog_name):
        parser = super(ListVNFFG, self).get_parser(prog_name)
        parser.add_argument(
            '--long',
            action='store_true',
            help=_('List additional fields in output')
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        data = client.list_vnffgs()
        headers, columns = tacker_osc_utils.get_column_definitions(
            _attr_map_vnffg, long_listing=parsed_args.long)
        return (headers,
                (utils.get_dict_properties(
                    s, columns,
                ) for s in data[_VNFFG + 's']))


class ShowVNFFG(command.ShowOne):
    _description = _("Display VNFFG details")

    def get_parser(self, prog_name):
        parser = super(ShowVNFFG, self).get_parser(prog_name)
        parser.add_argument(
            _VNFFG,
            metavar="<VNFFG>",
            help=_('VNFFG to display (name or ID)')
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj_id = tackerV10.find_resourceid_by_name_or_id(
            client, _VNFFG, parsed_args.vnffg)
        obj = client.show_vnffg(obj_id)
        display_columns, columns = _get_columns(obj[_VNFFG])
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj[_VNFFG]),
            columns,
            formatters=_formatters)
        return (display_columns, data)


class ListNFP(command.Lister):
    _description = ("List NFP(s) that belong to a given tenant.")

    def get_parser(self, prog_name):
        parser = super(ListNFP, self).get_parser(prog_name)
        parser.add_argument(
            '--vnffg-id',
            help=_('List NFP(s) with specific VNFFG ID'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        _params = {}
        if parsed_args.vnffg_id:
            _params['vnffg_id'] = parsed_args.vnffg_id
        nfps = client.list('nfps', nfps_path, True, **_params)
        for nfp in nfps['nfps']:
            error_reason = nfp.get('error_reason', None)
            if error_reason and \
                    len(error_reason) > DEFAULT_ERROR_REASON_LENGTH:
                nfp['error_reason'] = error_reason[
                    :DEFAULT_ERROR_REASON_LENGTH]
                nfp['error_reason'] += '...'
        data = {}
        data['nfps'] = nfps['nfps']
        data = client.list_nfps()
        headers, columns = tacker_osc_utils.get_column_definitions(
            _attr_map_nfp, long_listing=None)
        return (headers,
                (utils.get_dict_properties(
                    s, columns,
                ) for s in data[_NFP + 's']))


class ShowNFP(command.ShowOne):
    _description = _("Display NFP details")

    def get_parser(self, prog_name):
        parser = super(ShowNFP, self).get_parser(prog_name)
        parser.add_argument(
            _NFP,
            metavar="<NFP>",
            help=_('NFP to display (name or ID)')
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj_id = tackerV10.find_resourceid_by_name_or_id(
            client, _NFP, parsed_args.nfp)
        obj = client.show_nfp(obj_id)
        display_columns, columns = _get_columns(obj[_NFP])
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj[_NFP]),
            columns)
        return (display_columns, data)


class ListFC(command.Lister):
    _description = ("List flow classifier(s) that belong to a given tenant.")

    def get_parser(self, prog_name):
        parser = super(ListFC, self).get_parser(prog_name)
        parser.add_argument(
            '--nfp-id',
            help=_('List flow classifier(s) with specific nfp id'))
        parser.add_argument(
            '--tenant-id', metavar='TENANT_ID',
            help=_('The owner tenant ID or project ID'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        _params = {}
        if parsed_args.nfp_id:
            _params['nfp_id'] = parsed_args.nfp_id
        if parsed_args.tenant_id:
            _params['tenant_id'] = parsed_args.tenant_id
        classifiers = client.list('classifiers', fcs_path, True,
                                  **_params)
        for classifier in classifiers['classifiers']:
            error_reason = classifier.get('error_reason', None)
            if error_reason and \
                    len(error_reason) > DEFAULT_ERROR_REASON_LENGTH:
                classifier['error_reason'] = error_reason[
                    :DEFAULT_ERROR_REASON_LENGTH]
                classifier['error_reason'] += '...'
        data = {}
        data['classifiers'] = classifiers['classifiers']
        data = client.list_classifiers()
        headers, columns = tacker_osc_utils.get_column_definitions(
            _attr_map_fc, long_listing=None)
        return (headers,
                (utils.get_dict_properties(
                    s, columns,
                ) for s in data[_FC + 's']))


class ShowFC(command.ShowOne):
    _description = _("Display flow classifier details")

    def get_parser(self, prog_name):
        parser = super(ShowFC, self).get_parser(prog_name)
        parser.add_argument(
            _FC,
            metavar="<Classifier ID>",
            help=_('Flow Classifier to display (name or ID)')
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj_id = tackerV10.find_resourceid_by_name_or_id(
            client, _FC, parsed_args.classifier)
        obj = client.show_classifier(obj_id)
        display_columns, columns = _get_columns(obj[_FC])
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj[_FC]),
            columns,
            formatters=_formatters)
        return (display_columns, data)


class ListSFC(command.Lister):
    _description = ("List SFC(s) that belong to a given tenant.")

    def get_parser(self, prog_name):
        parser = super(ListSFC, self).get_parser(prog_name)
        parser.add_argument(
            '--nfp-id',
            help=_('List SFC(s) with specific nfp id'))
        parser.add_argument(
            '--tenant-id', metavar='TENANT_ID',
            help=_('The owner tenant ID or project ID'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        _params = {}
        if parsed_args.nfp_id:
            _params['nfp_id'] = parsed_args.nfp_id
        if parsed_args.tenant_id:
            _params['tenant_id'] = parsed_args.tenant_id
        sfcs = client.list('sfcs', sfcs_path, True, **_params)
        for chain in sfcs['sfcs']:
            error_reason = chain.get('error_reason', None)
            if error_reason and \
                    len(error_reason) > DEFAULT_ERROR_REASON_LENGTH:
                chain['error_reason'] = error_reason[
                    :DEFAULT_ERROR_REASON_LENGTH]
                chain['error_reason'] += '...'
        data = {}
        data['sfcs'] = sfcs['sfcs']
        headers, columns = tacker_osc_utils.get_column_definitions(
            _attr_map_sfc, long_listing=None)
        return (headers,
                (utils.get_dict_properties(
                    s, columns,
                ) for s in data[_SFC + 's']))


class ShowSFC(command.ShowOne):
    _description = _("Display SFC details")

    def get_parser(self, prog_name):
        parser = super(ShowSFC, self).get_parser(prog_name)
        parser.add_argument(
            _SFC,
            metavar="<SFC>",
            help=_('SFC to display (name or ID)')
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.tackerclient
        obj_id = tackerV10.find_resourceid_by_name_or_id(
            client, _SFC, parsed_args.sfc)
        obj = client.show_sfc(obj_id)
        display_columns, columns = _get_columns(obj[_SFC])
        data = utils.get_item_properties(
            sdk_utils.DictModel(obj[_SFC]),
            columns,
            formatters=_formatters)
        return (display_columns, data)
